"""Bounded Evo PC wire readers, promoted from our Source Garage research.

Original SDK research implementation f2714b1; no third-party plugin code is
vendored. Format-field knowledge is distinct from any native rendering claim.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from pathlib import PurePosixPath
import struct
import hashlib
MAX_MEMBER=32*1024*1024
MAX_ENTRIES=100000
MAX_VERTICES=200000
MAX_FACES=400000


def decode_classic_tiff(data: bytes):
    """First IFD, unsigned8, uncompressed chunky RGB/palette; preserve all samples.

    Evo2 files have malformed/overlapping next-IFD words. We never follow those
    words or discard an unspecified sample as Pillow's P-mode conversion does.
    Original whole TIFF, raw samples and raw16-bit palette remain independently
    hash-bound. The RGBA cache is a declared neutral preview interpretation.
    """
    if len(data)>32*1024*1024 or data[:4]not in (b'II*\0',b'MM\0*'):
        raise ValueError('unsupported TIFF header/byte budget')
    endian='<'if data[:2]==b'II'else'>'
    def unpack(fmt,at):
        size=struct.calcsize(endian+fmt)
        return struct.unpack(endian+fmt,checked(data,at,size,'TIFF field'))
    first,=unpack('I',4);count,=unpack('H',first)
    if not 1<=count<=256:raise ValueError('TIFF IFD entry budget')
    end=first+2+count*12;checked(data,first,2+count*12,'TIFF directory')
    tags={};spans={}
    for i in range(count):
        at=first+2+i*12;tag,kind,n,value=unpack('HHII',at)
        if tag in tags:raise ValueError('duplicate TIFF tag')
        # Unknown metadata is retained in the original TIFF, not allocated.
        if tag not in (256,257,258,259,262,273,274,277,278,279,284,320,338,339):continue
        if kind not in (1,3,4)or not 1<=n<=65536:raise ValueError('unsupported TIFF field type/count')
        size={1:1,3:2,4:4}[kind];offset=at+8 if n*size<=4 else value
        vals=unpack(str(n)+{1:'B',3:'H',4:'I'}[kind],offset)
        tags[tag]=list(vals);spans[tag]=[offset,n*size]
    def one(tag,default=None):
        vals=tags.get(tag)
        if vals is None and default is not None:return default
        if vals is None or len(vals)!=1:raise ValueError('missing/non-scalar TIFF field')
        return vals[0]
    w,h,spp=one(256),one(257),one(277,1)
    if not 1<=w<=4096 or not 1<=h<=4096 or not 1<=spp<=4 or w*h*spp>64*1024*1024:
        raise ValueError('TIFF dimensions/sample budget')
    bits=tags.get(258,[1]);photo=one(262)
    if bits not in ([8],[8]*spp)or one(259,1)!=1 or one(284,1)!=1 or one(274,1)!=1:
        raise ValueError('unsupported TIFF bits/compression/planar/orientation')
    if any(v!=1 for v in tags.get(339,[1])):raise ValueError('unsupported TIFF sample format')
    if not ((photo==3 and spp in (1,2))or(photo==2 and spp in (3,4))or(photo in (0,1)and spp==1)):
        raise ValueError('unsupported TIFF channel layout')
    offsets,sizes=tags.get(273),tags.get(279);rows=one(278,h)
    if not offsets or not sizes or len(offsets)!=len(sizes)or rows<1 or len(offsets)!=(h+rows-1)//rows:
        raise ValueError('invalid TIFF strip table')
    chunks=[];ranges=[]
    for i,(offset,size)in enumerate(zip(offsets,sizes)):
        expected=min(rows,h-i*rows)*w*spp
        if size!=expected or offset<end:raise ValueError('TIFF strip size/overlap')
        chunks.append(checked(data,offset,size,'TIFF strip'));ranges.append((offset,offset+size))
    ranges.sort()
    if any(a[1]>b[0]for a,b in zip(ranges,ranges[1:])):raise ValueError('overlapping TIFF strips')
    samples=b''.join(chunks);palette=b'';colors=[]
    if photo==3:
        if len(tags.get(320,[]))!=768:raise ValueError('missing/invalid TIFF color map')
        offset,size=spans[320];palette=checked(data,offset,size,'TIFF palette')
        cmap=tags[320];colors=[tuple((cmap[k*256+i]+128)//257 for k in range(3))for i in range(256)]
    extras=tags.get(338,[]);base=1 if photo in (0,1,3) else 3
    if len(extras)>spp-base or any(v not in (0,1,2)for v in extras):raise ValueError('unsupported TIFF extra samples')
    # Only explicit TIFF alpha tags1/2 can supply a preview alpha channel.
    alpha_index=base if len(extras)==1 and extras[0]in (1,2)else None
    rgba=bytearray(w*h*4)
    for i in range(w*h):
        v=samples[i*spp:(i+1)*spp]
        rgb=colors[v[0]]if photo==3 else tuple(v[:3])if photo==2 else (v[0]if photo==1 else 255-v[0],)*3
        rgba[i*4:i*4+4]=bytes((*rgb,v[alpha_index]if alpha_index is not None else 255))
    unknown_extra=spp-base>0 and alpha_index is None
    next_ifd=unpack('I',end)[0]if end+4<=len(data)else None
    metadata={'samples_per_pixel':spp,'bits_per_sample':bits,'photometric':photo,'extra_samples':extras,
              'raw_sample_bytes':len(samples),'raw_samples_sha256':hashlib.sha256(samples).hexdigest(),
              'palette_bytes':len(palette),'palette_sha256':hashlib.sha256(palette).hexdigest()if palette else None,
              'sample_extrema':[[min(samples[k::spp]),max(samples[k::spp])]for k in range(spp)],
              'first_ifd_offset':first,'next_ifd_word':next_ifd,'next_ifd_policy':'not followed; original nonconformant/opaque data retained',
              'tiff_tags':{str(k):v for k,v in tags.items()if k!=320},
              'preview_policy':'palette/RGB preserved; unspecified channels retained separately; opaque cache is an explicit interpretation'if unknown_extra else'RGB/palette and explicit TIFF alpha only',
              'unknown_extra_sample':unknown_extra,'alpha_association':'UNRESOLVED'if unknown_extra else extras,
              'source_alpha_was_not_inferred_from_pillow':True}
    return {'width':w,'height':h,'source_channels':metadata},bytes(rgba),samples,palette

class InspectionError(ValueError):
    """Invalid or unsupported bounded inspection input."""

def checked(data: bytes, offset: int, size: int, label: str) -> bytes:
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise InspectionError(f"{label}: range {offset}+{size} outside {len(data)} bytes")
    return data[offset:offset + size]

def safe_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    parts = normalized.split("/")
    if normalized.startswith("/") or ":" in normalized or ".." in parts:
        raise InspectionError(f"unsafe member name: {name!r}")
    result = str(PurePosixPath(normalized))
    if result in ("", ".") or "\0" in result:
        raise InspectionError("empty or NUL member name")
    return result

@dataclass(frozen=True)
class PodMember:
    name: str
    offset: int
    size: int
    timestamp: int
    checksum: int

def pod2_members(data: bytes) -> list[PodMember]:
    """The observed Evo PC samples are POD2; other versions fail explicitly."""
    if checked(data, 0, 4, "POD signature") != b"POD2":
        raise InspectionError("UNSUPPORTED: expected observed POD2 signature")
    count, _audit = struct.unpack("<II", checked(data, 88, 8, "POD2 counts"))
    if not 0 < count <= MAX_ENTRIES:
        raise InspectionError("POD2 member count outside bound")
    checked(data, 96, count * 20, "POD2 directory")
    names_base = 96 + count * 20
    records = [struct.unpack_from("<5I", data, 96 + i * 20) for i in range(count)]
    names_end = min(record[2] for record in records)
    if names_end < names_base or names_end > len(data):
        raise InspectionError("POD2 names overlap directory or exceed file")
    result, seen = [], set()
    ranges = []
    for name_off, size, offset, timestamp, checksum in records:
        start = names_base + name_off
        if not names_base <= start < names_end:
            raise InspectionError("POD2 name offset outside name table")
        end = data.find(b"\0", start, min(start + 4097, names_end))
        if end < 0:
            raise InspectionError("POD2 name is unterminated or exceeds 4096 bytes")
        try:
            name = safe_name(data[start:end].decode("ascii"))
        except UnicodeError as exc:
            raise InspectionError("POD2 non-ASCII member name") from exc
        if name.casefold() in seen:
            raise InspectionError(f"duplicate POD2 member: {name}")
        seen.add(name.casefold())
        checked(data, offset, size, "POD2 member")
        if offset < names_end:
            raise InspectionError("POD2 member overlaps directory/name area")
        ranges.append((offset, offset + size))
        result.append(PodMember(name, offset, size, timestamp, checksum))
    ranges.sort()
    if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
        raise InspectionError("overlapping POD2 members")
    return result

def member_bytes(data: bytes, entry: PodMember) -> bytes:
    if entry.size > MAX_MEMBER:
        raise InspectionError("representative member exceeds limit")
    return checked(data, entry.offset, entry.size, entry.name)

def finite(values: list[float], label: str) -> None:
    if not all(math.isfinite(v) for v in values):
        raise InspectionError(f"non-finite {label}")

def parse_smf(data: bytes) -> dict:
    """Inspect text C3DModel v1..4. Preserve frames, object/material raw fields."""
    if len(data) > MAX_MEMBER:
        raise InspectionError("SMF exceeds size limit")
    try:
        # Retail files contain CR CR LF; ignore blank separators consistently.
        lines = [line.strip() for line in data.decode("ascii").splitlines() if line.strip()]
    except UnicodeError as exc:
        raise InspectionError("SMF is not ASCII text") from exc
    cursor = 0

    def take() -> str:
        nonlocal cursor
        if cursor >= len(lines):
            raise InspectionError("truncated SMF")
        value = lines[cursor]
        cursor += 1
        if len(value) > 4096:
            raise InspectionError("SMF line exceeds limit")
        return value

    def number() -> int:
        try:
            return int(take())
        except ValueError as exc:
            raise InspectionError("SMF expected integer") from exc

    if take() != "C3DModel":
        raise InspectionError("UNSUPPORTED: expected C3DModel")
    version, count = number(), number()
    if version not in (1, 2, 3, 4) or not 0 < count <= 4096:
        raise InspectionError("unsupported SMF version or object count")
    lod_info = take() if version >= 4 else None
    objects, total_v, total_f = [], 0, 0
    try:
        for _ in range(count):
            name = take()
            visible = number() if version >= 2 else 1
            if visible not in (0, 1) or number() != 1:
                raise InspectionError("unsupported SMF visibility/object version")
            info = [int(v) for v in take().split(",")]
            if len(info) != 4:
                raise InspectionError("unsupported SMF object field count")
            nv, frames, nf, unknown = info
            total_v += nv * max(frames, 1)
            total_f += nf
            if not 0 <= nv <= MAX_VERTICES or not 1 <= frames <= 256 or not 0 <= nf <= MAX_FACES:
                raise InspectionError("SMF object count outside bounds")
            if total_v > MAX_VERTICES or total_f > MAX_FACES:
                raise InspectionError("SMF total counts outside bounds")
            material_version, material, bump = "legacy", take(), None
            if material == "v1":
                material_version, material = "v1", take()
                bump = take().strip('"')
            fields = material.split(",")
            if len(fields) != 6 or fields[3] not in ("0", "1") or fields[4] not in ("0", "1"):
                raise InspectionError("unsupported SMF material fields")
            texture = safe_name(fields[5])
            vertices = []
            for _frame in range(frames):
                frame_vertices = []
                for _vertex in range(nv):
                    vals = [float(v) for v in take().split(",")]
                    if len(vals) != 8:
                        raise InspectionError("SMF vertex expected position/normal/UV (8 floats)")
                    finite(vals, "SMF vertex")
                    frame_vertices.append(vals)
                vertices.append(frame_vertices)
            faces = []
            for _face in range(nf):
                face = [int(v) for v in take().split(",")]
                if len(face) != 3 or any(v < 0 or v >= nv for v in face):
                    raise InspectionError("SMF face index outside vertex array")
                faces.append(face)
            objects.append({"name": name, "visible": bool(visible), "unknown_object_field": unknown,
                            "material_version": material_version, "material_raw": fields,
                            "texture": texture, "bump_texture": bump, "vertices_by_frame": vertices,
                            "faces": faces})
    except (ValueError, OverflowError) as exc:
        if isinstance(exc, InspectionError):
            raise
        raise InspectionError(f"malformed SMF value: {exc}") from exc
    if cursor != len(lines):
        raise InspectionError(f"unparsed SMF tail: {len(lines) - cursor} lines")
    return {"format": "C3DModel", "version": version, "lod_info_raw": lod_info,
            "objects": objects, "vertices_including_frames": total_v, "triangles": total_f,
            "coordinate_contract": "raw source values; tool documents feet, Y up; no MR transform",
            "unsupported": ["runtime reflection", "runtime damage/animation semantics", "color selection policy"]}
