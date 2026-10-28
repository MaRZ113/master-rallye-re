#!/usr/bin/env python3
"""Read-only, bounded Source Garage qualification probes; no MR authoring.

Format references: local PyPOD POD_Handling.py (Johnny Shumway, MIT),
Dummiesman's SMFImportExport (CC BY-NC-SA 3.0), and Spreit/chmcl95
SR2Tools. Those tools are not vendored here. This independent inspector retains
source values and deliberately does not resolve unknown runtime semantics.
VR2 smoke uses the separately supplied, reviewed Explorer Python sources.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import struct
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

MAX_FILE = 512 * 1024 * 1024
MAX_MEMBER = 32 * 1024 * 1024
MAX_ENTRIES = 100_000
MAX_VERTICES = 200_000
MAX_FACES = 400_000
# Exact externally reviewed Explorer snapshot. Updating this allowlist is a new
# tool-source review, not an implicit compatibility claim for later versions.
VR2_REVIEWED = {
    "vr2pak.py": "0735dda51c40ae9a01faed37f3a1e6e3bec72d0a529a2878a8291252ccedf47a",
    "vr2geo_indexed.py": "c0ac1a5bfdc63612770a405b30517795b625510b924cc25bd01caff05bdac52e",
    "vr2tex.py": "f24df8cd8a834f75ed4f0210226da34baf5f6ad09705415519c4060fa2d81e8b",
}


class InspectionError(ValueError):
    """Invalid or unsupported bounded inspection input."""


def checked(data: bytes, offset: int, size: int, label: str) -> bytes:
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise InspectionError(f"{label}: range {offset}+{size} outside {len(data)} bytes")
    return data[offset:offset + size]


def read_bounded(path: Path, limit: int = MAX_FILE) -> bytes:
    ensure_unlinked(path)
    if not path.is_file():
        raise InspectionError(f"not a regular unlinked input: {path}")
    before = path.stat()
    if before.st_size > limit:
        raise InspectionError(f"input exceeds {limit} bytes: {path}")
    with path.open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise InspectionError("input grew beyond size limit")
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or len(data) != after.st_size:
        raise InspectionError("input changed during inspection")
    return data


def ensure_unlinked(path: Path) -> None:
    for part in [path.absolute(), *path.absolute().parents]:
        if part.is_symlink():
            raise InspectionError(f"linked path component: {part}")
        if part.exists() and getattr(part.stat(), "st_file_attributes", 0) & 0x400:
            raise InspectionError(f"reparse/junction path component: {part}")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def raw_rgba(raw: bytes, palette: bytes, opacity: bytes | None = None) -> tuple[int, bytes]:
    width = math.isqrt(len(raw))
    if not raw or width * width != len(raw) or width > 4096:
        raise InspectionError("RAW must have a bounded square pixel count")
    if len(palette) != 768:
        raise InspectionError("ACT must contain exactly 256 RGB entries")
    if opacity is not None and len(opacity) != len(raw):
        raise InspectionError("OPA length must match RAW; refusing silent alpha loss")
    pixels = bytearray()
    for i, index in enumerate(raw):
        pixels.extend(palette[index * 3:index * 3 + 3])
        pixels.append(opacity[i] if opacity is not None else 255)
    return width, bytes(pixels)


def cod_members(data: bytes) -> list[dict]:
    """Independent COD directory probe from documented Game Extractor fields."""
    if checked(data, 0, 24, "COD signature") != b"->Unique Pc HUNGARY<-\0\0\0":
        raise InspectionError("UNSUPPORTED: unexpected Screamer COD signature")
    length = struct.unpack("<I", checked(data, 24, 4, "COD directory size"))[0]
    if length % 136 or not 0 < length // 136 <= MAX_ENTRIES:
        raise InspectionError("COD directory length/count invalid")
    checked(data, 28, length, "COD directory")
    result, seen = [], set()
    for offset in range(28, 28 + length, 136):
        raw_name = checked(data, offset, 128, "COD name")
        if b"\0" not in raw_name:
            raise InspectionError("unterminated COD name")
        try:
            name = safe_name(raw_name.split(b"\0", 1)[0].decode("ascii"))
        except UnicodeError as exc:
            raise InspectionError("non-ASCII COD name") from exc
        start, size = struct.unpack_from("<II", data, offset + 128)
        checked(data, start, size, "COD member")
        if start < 28 + length:
            raise InspectionError("COD member overlaps directory")
        if name.casefold() in seen:
            raise InspectionError("duplicate COD member")
        seen.add(name.casefold())
        result.append({"name": name, "offset": start, "size": size})
    ranges = sorted((r["offset"], r["offset"] + r["size"]) for r in result)
    if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
        raise InspectionError("overlapping COD members")
    return result


def screamer_mesh(streams: dict[str, bytes]) -> dict:
    """Strict DAT-stream structural probe; absent UV/material streams fail."""
    required = ("verticle.dat", "faces.dat", "mapcoord.dat", "norms.dat", "textures.dat")
    if any(name not in streams for name in required):
        raise InspectionError("MISSING INPUT: complete Screamer DAT stream set required")
    verts, indices = streams["verticle.dat"], streams["faces.dat"]
    nv = struct.unpack("<H", checked(verts, 0, 2, "Screamer vertex count"))[0]
    nf = struct.unpack("<H", checked(indices, 0, 2, "Screamer triangle count"))[0]
    expected = {"verticle.dat": 2 + nv * 12, "faces.dat": 2 + nf * 6,
                "mapcoord.dat": nf * 24, "norms.dat": nf * 36, "textures.dat": nf * 2}
    if nv == 0 or nf == 0 or any(len(streams[name]) != size for name, size in expected.items()):
        raise InspectionError("Screamer DAT stream count/length mismatch")
    vertices = [list(v) for v in struct.iter_unpack("<3f", verts[2:])]
    faces = [list(v) for v in struct.iter_unpack("<3H", indices[2:])]
    if any(index >= nv for face in faces for index in face):
        raise InspectionError("Screamer triangle index outside vertex array")
    uvs = [list(v) for v in struct.iter_unpack("<6f", streams["mapcoord.dat"])]
    normals = [list(v) for v in struct.iter_unpack("<9f", streams["norms.dat"])]
    for record in vertices + uvs + normals:
        finite(record, "Screamer geometry/UV/normal")
    return {"vertices_by_frame": [vertices], "faces": faces, "visible": True,
            "per_triangle_uv_source_order": uvs, "per_triangle_corner_normals": normals,
            "material_ids": list(struct.unpack(f"<{nf}H", streams["textures.dat"])),
            "unsupported": ["material ID to texture filename mapping", "source axes and scale", "UV corner-order parity"]}


def cod_smoke(source: Path, output: Path, protected: list[Path] = ()) -> dict:
    data = read_bounded(source)
    entries = cod_members(data)
    out = destination(output, [source.parent, *protected])
    selected = [e for e in entries if any(word in e["name"].casefold() for word in ("pajero", "rav4", "landrover", "cherokee", "vehicle"))]
    if not selected:
        selected = [e for e in entries if "/car" in e["name"].casefold()][:30]
    for entry in selected:
        blob = checked(data, entry["offset"], entry["size"], "selected COD member")
        entry["sha256"] = sha(blob)
        entry["signature_hex"] = blob[:32].hex()
    report = {"schema": "source-garage-smoke/1", "source": identity(source, data),
              "format": "Screamer COD", "L0": "PASS", "L1": "UNSUPPORTED", "L2": "NOT TESTED", "Gameplay": "NOT TESTED",
              "member_count": len(entries), "extensions": dict(sorted(Counter(Path(e["name"]).suffix.casefold() for e in entries).items())),
              "selected_candidates": selected, "warnings": ["Archive directory validated; no COD vehicle mesh decoder was executed or qualified.",
                                                            "Names are source records, not proof of complete vehicle reconstruction."]}
    by_name = {e["name"].casefold(): e for e in entries}
    prefix = "car/Mitsubishi_Pajero/Multi"
    probed = []
    for component in ("", "/kerek"):
        streams, provenance = {}, []
        for filename in ("verticle.dat", "faces.dat", "mapcoord.dat", "norms.dat", "textures.dat"):
            entry = by_name.get(f"{prefix}{component}/{filename}".casefold())
            if entry is None:
                continue
            if entry["size"] > MAX_MEMBER:
                raise InspectionError("Screamer stream exceeds size bound")
            blob = checked(data, entry["offset"], entry["size"], "Screamer representative stream")
            streams[filename] = blob
            provenance.append({**entry, "sha256": sha(blob)})
        if not streams:
            continue
        mesh = screamer_mesh(streams)
        stem = "wheel" if component else "body"
        write_json(out / f"pajero_{stem}_source_structure.json", mesh)
        preview_wireframe([mesh], out / f"pajero_{stem}_wireframe.png", f"Screamer 4x4 Mitsubishi Pajero Multi: {stem} local geometry")
        probed.append({"component": stem, "vertices": len(mesh["vertices_by_frame"][0]), "triangles": len(mesh["faces"]),
                       "material_ids": sorted(set(mesh["material_ids"])), "source_members": provenance})
    if probed:
        report["L1"] = "WARN"
        report["representative"] = {"source_prefix": prefix, "components": probed,
                                    "identity": "source directory Mitsubishi_Pajero; road-car generation not independently established"}
        report["warnings"] = ["Independent bounded DAT parsing; no Noesis binary/plugin code executed or redistributed.",
                              "Body and one local wheel mesh only; no wheel transforms/material filename resolution/scale qualification.",
                              "Original per-corner UV and normals retained; plugin UV reversal remains unverified against game."]
    previews = []
    for filename in ("txt/t1.tex", "txt/red/T10.TEX"):
        entry = by_name.get(f"{prefix}/{filename}".casefold())
        if entry is None:
            continue
        blob = checked(data, entry["offset"], entry["size"], "Screamer TEX")
        fields = struct.unpack("<5I", checked(blob, 0, 20, "Screamer TEX header"))
        if fields[1] > 6 or fields[3] not in (10, 11) or fields[4] != len(blob) - 20:
            continue
        width = 256 >> fields[1]
        pixels = bytearray()
        for value, in struct.iter_unpack("<H", checked(blob, 20, width * width * 2, "Screamer TEX base pixels")):
            if fields[3] == 10:
                r, g, b, a = ((value >> 11) & 31) * 255 // 31, ((value >> 5) & 63) * 255 // 63, (value & 31) * 255 // 31, 255
            else:
                r, g, b, a = ((value >> 10) & 31) * 255 // 31, ((value >> 5) & 31) * 255 // 31, (value & 31) * 255 // 31, (255 if value & 0x8000 else 0)
            pixels.extend((r, g, b, a))
        from PIL import Image
        stem = "pajero_" + filename.replace("/", "_").replace(".", "_") + ".png"
        Image.frombytes("RGBA", (width, width), bytes(pixels)).save(out / stem)
        previews.append({**entry, "sha256": sha(blob), "header_raw": fields, "preview": stem,
                         "binding_to_mesh_material_ids": "UNKNOWN"})
    report["texture_probes"] = previews
    write_json(out / "directory.json", entries)
    write_json(out / "report.json", report)
    return report


def sr2_root_mesh(data: bytes) -> dict:
    """Partial MDL inspection: first header-referenced node and its own mesh.

    SR2Tools documents this node/pointer layout. We intentionally do not infer
    a complete graph traversal, texture binding, or source model variant.
    """
    header = struct.unpack("<8I", checked(data, 0, 32, "SR2 MDL header"))
    size, header_size, relation = header[:3]
    if size != len(data) or header_size != 32 or relation + 32 != size:
        raise InspectionError("UNSUPPORTED: expected observed SR2 PC car MDL layout")
    node = checked(data, relation - 96, 128, "SR2 root node")
    pointers = struct.unpack_from("<I", node)[0]
    if struct.unpack_from("<I", node, 12)[0] == 0xFFFFFFFF:
        raise InspectionError("UNSUPPORTED: SR2 root node has no ordinary mesh")
    position = list(struct.unpack_from("<3f", node, 32))
    scale = list(struct.unpack_from("<3f", node, 64))
    finite(position + scale, "SR2 root transform")
    vo, fo, mo, nv, indices, nm, unknown0, unknown1 = struct.unpack("<8I", checked(data, pointers, 32, "SR2 mesh pointers"))
    if not 0 < nv <= MAX_VERTICES or not 0 < indices <= MAX_FACES * 3 or indices % 3 or not 0 < nm <= 64:
        raise InspectionError("SR2 mesh counts outside bounds")
    vertices = [list(v) for v in struct.iter_unpack("<8f", checked(data, vo, nv * 32, "SR2 vertices"))]
    for vertex in vertices:
        finite(vertex, "SR2 vertex")
    index_values = struct.unpack(f"<{indices}H", checked(data, fo, indices * 2, "SR2 triangle indices"))
    if any(index >= nv for index in index_values):
        raise InspectionError("SR2 triangle index out of range")
    materials = checked(data, mo, nm * 32, "SR2 material records")
    return {"vertices_by_frame": [vertices], "faces": [list(index_values[i:i + 3]) for i in range(0, indices, 3)],
            "visible": True, "position_raw": position, "scale_raw": scale,
            "rotation_u16_raw": list(struct.unpack_from("<6H", node, 48)),
            "relation_raw": list(struct.unpack_from("<8I", node, 96)), "node_offset": relation - 96,
            "material_bytes_hex": materials.hex(), "unknown_pointer_fields": [unknown0, unknown1]}


def sr2_smoke(source: Path, output: Path, protected: list[Path] = ()) -> dict:
    data = read_bounded(source, MAX_MEMBER)
    mesh = sr2_root_mesh(data)
    out = destination(output, [source.parent, *protected])
    write_json(out / "root_mesh_source_structure.json", mesh)
    preview_wireframe([mesh], out / "root_mesh_wireframe.png", "Sega Rally 2 PC Delta: root mesh only, local coordinates")
    report = {"schema": "source-garage-smoke/1", "source": identity(source, data), "format": "SR2 PC MDL",
              "L0": "PASS", "L1": "WARN", "L2": "NOT TESTED", "Gameplay": "NOT TESTED",
              "vertices": len(mesh["vertices_by_frame"][0]), "triangles": len(mesh["faces"]),
              "root_node_offset": mesh["node_offset"], "root_relation_raw": mesh["relation_raw"],
              "warnings": ["Partial: only header-referenced root node mesh, not complete hierarchy/vehicle.",
                           "Source materials retained as raw records, not render-qualified.",
                           "SR2Tools texture_tool.detect_texture_type opens input r+b; not used on originals."]}
    texture_path = source.parent / "body.txr"
    if texture_path.is_file():
        tex = read_bounded(texture_path, MAX_MEMBER)
        if len(tex) >= 4096 and tex[:4] == b"RTEX":
            count, palettes = struct.unpack_from("<II", tex, 4)
            fmt, palette_usage, width, size, palette_index = struct.unpack_from("<2b2xH2xIB3x", tex, 16)
            if count == 1 and palettes == 0 and fmt == 0 and palette_usage == 0 and width <= 4096 and size == width * width * 2:
                from PIL import Image
                pixels = bytearray()
                for value, in struct.iter_unpack("<H", checked(tex, 4096, size, "SR2 RGB565 pixels")):
                    pixels.extend((((value >> 11) & 31) * 255 // 31, ((value >> 5) & 63) * 255 // 63, (value & 31) * 255 // 31))
                Image.frombytes("RGB", (width, width), bytes(pixels)).save(out / "body_texture.png")
                report["texture"] = {**identity(texture_path, tex), "format": "RTEX RGB565", "width": width, "height": width,
                                     "binding_to_root_mesh": "NOT TESTED"}
    write_json(out / "report.json", report)
    return report


def destination(path: Path, sources: list[Path]) -> Path:
    ensure_unlinked(path)
    target = path.resolve()
    for source in sources:
        source = source.resolve()
        if target == source or target.is_relative_to(source) or source.is_relative_to(target):
            raise InspectionError("output and input roots must be disjoint")
    if target.exists():
        raise InspectionError("output directory already exists; choose a fresh run directory")
    target.mkdir(parents=True)
    return target


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def identity(path: Path, data: bytes | None = None) -> dict:
    data = read_bounded(path) if data is None else data
    return {"path": str(path.resolve()), "size": len(data), "sha256": sha(data)}


def preview_wireframe(objects: list[dict], path: Path, title: str) -> None:
    """Diagnostic geometry image, with no claim of native material parity."""
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (1000, 800), (24, 28, 32))
    draw = ImageDraw.Draw(image)
    visible = [o for o in objects if o["visible"] and o["vertices_by_frame"]]
    projected = []
    for obj in visible:
        points = [(v[0] * .8 + v[2] * .45, -v[1] + v[2] * .22) for v in obj["vertices_by_frame"][0]]
        projected.append((obj, points))
    all_points = [point for _, points in projected for point in points]
    if not all_points:
        raise InspectionError("no visible geometry for diagnostic preview")
    xmin, ymin = map(min, zip(*all_points)); xmax, ymax = map(max, zip(*all_points))
    scale = min(900 / max(xmax - xmin, .001), 620 / max(ymax - ymin, .001))
    for index, (obj, points) in enumerate(projected):
        pixels = [(50 + (x - xmin) * scale, 100 + (y - ymin) * scale) for x, y in points]
        color = (110 + index * 17 % 145, 145 + index * 11 % 110, 155 + index * 7 % 100)
        for face in obj["faces"]:
            draw.line([pixels[v] for v in face] + [pixels[face[0]]], fill=color, width=1)
    draw.text((25, 20), title, fill="white")
    draw.text((25, 45), "Source geometry diagnostic; no textures, runtime lighting or fidelity qualification", fill=(220, 190, 120))
    image.save(path)


def evo_smoke(source: Path, output: Path, model: str, truck: str, protected: list[Path] = ()) -> dict:
    data = read_bounded(source / "TRUCK.POD")
    entries = pod2_members(data)
    by_name = {entry.name.casefold(): entry for entry in entries}
    out = destination(output, [source, *protected])
    report = {"schema": "source-garage-smoke/1", "source": identity(source / "TRUCK.POD", data),
              "format": "POD2", "member_count": len(entries),
              "extensions": dict(sorted(Counter(Path(e.name).suffix.upper() for e in entries).items())),
              "L0": "PASS", "L1": "WARN", "L2": "NOT TESTED", "Gameplay": "NOT TESTED",
              "members": [], "warnings": ["No MR files or source game files written; source-only probe is not an importer."]}

    def get(name: str) -> bytes:
        entry = by_name.get(safe_name(name).casefold())
        if entry is None:
            raise InspectionError(f"missing POD member: {name}")
        blob = member_bytes(data, entry)
        report["members"].append({"name": entry.name, "offset": entry.offset,
                                  "size": entry.size, "sha256": sha(blob),
                                  "stored_checksum": entry.checksum, "checksum_validation": "NOT TESTED"})
        return blob

    scene = parse_smf(get(f"MODELS/{model}.SMF"))
    # Preserve source geometry privately; this intermediate is inspection-only.
    write_json(out / "body_source_structure.json", scene)
    report["body"] = {"model": model, "objects": len(scene["objects"]),
                      "vertices": scene["vertices_including_frames"], "triangles": scene["triangles"],
                      "object_names": [o["name"] for o in scene["objects"]],
                      "materials": sorted({o["texture"] for o in scene["objects"]}),
                      "lod_info_raw": scene["lod_info_raw"]}
    positions = [v[:3] for obj in scene["objects"] for v in obj["vertices_by_frame"][0]]
    report["body"]["source_bbox"] = {"min": [min(v[i] for v in positions) for i in range(3)],
                                           "max": [max(v[i] for v in positions) for i in range(3)]}
    report["related_model_candidates"] = []
    sibling_name = f"MODELS/{model}0.SMF"
    if sibling_name.casefold() in by_name:
        sibling = parse_smf(get(sibling_name))
        write_json(out / "suffix0_model_source_structure.json", sibling)
        report["related_model_candidates"].append({"name": sibling_name, "objects": len(sibling["objects"]),
                                                   "vertices": sibling["vertices_including_frames"], "triangles": sibling["triangles"],
                                                   "role": "suffix-0 candidate; LOD/runtime selection UNKNOWN"})
    text = get(f"TRUCK/{truck}.TRK").decode("ascii")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    selected = {}
    for key in ("truckName", "truckMake", "truckModel", "truckModelYear", "truckModelBaseName", "tireModelBaseName",
                "faxle.rtire.static_bpos", "faxle.ltire.static_bpos", "raxle.rtire.static_bpos", "raxle.ltire.static_bpos"):
        if key in lines:
            selected[key] = lines[lines.index(key) + 1]
    report["catalog_record"] = selected
    write_json(out / "catalog_selected_fields.json", selected)
    report["wheel_candidates"] = [e.name for e in entries if Path(e.name).suffix.upper() == ".SMF" and
                                  Path(e.name).stem.casefold().startswith(selected.get("tireModelBaseName", "missing").casefold())]
    wheel_summaries = []
    for name in report["wheel_candidates"]:
        wheel = parse_smf(get(name))
        write_json(out / f"{Path(name).stem}_source_structure.json", wheel)
        wheel_summaries.append({"name": name, "objects": len(wheel["objects"]), "vertices": wheel["vertices_including_frames"],
                                "triangles": wheel["triangles"]})
    report["wheel_structures"] = wheel_summaries
    textures = []
    from PIL import Image
    for texture in report["body"]["materials"]:
        stem = Path(texture).stem
        extension = Path(texture).suffix.casefold()
        if extension == ".raw":
            raw, pal = get(f"ART/{texture}"), get(f"ART/{stem}.ACT")
            opacity = get(f"ART/{stem}.OPA") if f"art/{stem}.opa".casefold() in by_name else None
            width, pixels = raw_rgba(raw, pal, opacity)
            image = Image.frombytes("RGBA", (width, width), pixels)
        elif extension in (".tif", ".tiff"):
            import io
            blob = get(f"ART/{texture}")
            image = Image.open(io.BytesIO(blob))
            if image.width > 4096 or image.height > 4096:
                raise InspectionError("TIFF dimensions outside smoke bound")
            image.load()
            image = image.convert("RGBA")
        else:
            report["warnings"].append(f"unsupported representative texture: {texture}")
            continue
        image.save(out / f"{stem}.png")
        extrema = image.getchannel("A").getextrema()
        textures.append({"source_texture": texture, "width": image.width, "height": image.height,
                         "alpha_min_max": extrema, "runtime_alpha_policy": "UNKNOWN"})
    report["texture_decodes"] = textures
    preview_wireframe(scene["objects"], out / "body_wireframe.png", selected.get("truckName", model))
    report["private_preview"] = "body_wireframe.png (geometry diagnostic only); diffuse PNGs decoded separately"
    report["warnings"].extend(["Wheel transforms retained, no assembled-wheel placement qualified.",
                               "SMF visible flags and unknown fields retained; no lamp/glass semantic inference.",
                               "Evo2 alpha importer issue documented upstream; no automatic repair authorized."])
    write_json(out / "report.json", report)
    return report


def vr2_smoke(source: Path, tool: Path, output: Path, block_index: int, protected: list[Path] = ()) -> dict:
    """Run reviewed source modules in pure Python, with explicit bounded inputs."""
    native_helpers = [p for p in (tool / "backend").iterdir() if p.suffix.lower() in (".dll", ".so", ".dylib")]
    if native_helpers:
        raise InspectionError("refusing optional native helpers; use reviewed pure Python source tree")
    init = read_bounded(tool / "backend" / "__init__.py", 4096)
    if sha(init) != "d5907d57c21121b255fdb91b80397814a6e7b9846625ace4fa1aed2a08eaf023":
        raise InspectionError("unreviewed backend package initializer")
    for name, expected in VR2_REVIEWED.items():
        if sha(read_bounded(tool / "backend" / name, MAX_MEMBER)) != expected:
            raise InspectionError(f"unreviewed VR2 source version: {name}")
    data = read_bounded(source)
    # Third-party imports must not create __pycache__ in the supplied tools.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(tool.resolve()))
    pakmod = importlib.import_module("backend.vr2pak")
    geomod = importlib.import_module("backend.vr2geo_indexed")
    texmod = importlib.import_module("backend.vr2tex")
    pak = pakmod.Pak(str(source))
    if pak.platform != "pc" or not 0 <= block_index < len(pak.blocs):
        raise InspectionError("expected PC block in range")
    for block in pak.blocs:
        for sub in block.subs:
            if sub.size > MAX_MEMBER or sub.unpacked > MAX_MEMBER:
                raise InspectionError("VR2 sub-block exceeds smoke bound")
    out = destination(output, [source.parent, tool, *protected])
    report = {"schema": "source-garage-smoke/1", "source": identity(source, data),
              "format": "Eden PC PAK / V3D", "blocks": len(pak.blocs), "selected_block": block_index,
              "L0": "PASS", "L1": "WARN", "L2": "NOT TESTED", "Gameplay": "NOT TESTED",
              "tool_sources": [identity(tool / "backend" / name) for name in ("vr2pak.py", "vr2geo_indexed.py", "vr2tex.py")],
              "subblocks": [], "warnings": ["Pure Python Eden decoder; no native helper/legacy EXE executed.",
                                            "Runtime remapped shared texture slots and wheel transforms remain unqualified."]}
    for sub in pak.blocs[block_index].subs:
        if not sub.crc_ok():
            raise InspectionError(f"VR2 stored-data CRC failure in sub-block {sub.index}")
        blob = sub.data()
        row = {"index": sub.index, "offset": sub.offset, "stored_size": sub.size,
               "decoded_size": len(blob), "stored_sha256": sha(sub.raw()), "decoded_sha256": sha(blob), "crc": "PASS"}
        if texmod.TexBank.looks_like(blob):
            tb = texmod.TexBank(blob)
            names = texmod.export(blob, str(out), f"bloc{block_index:02d}_sub{sub.index}")
            row.update({"kind": "car texture bank", "pages": tb.page_count, "pngs": [Path(n).name for n in names]})
        elif geomod.Geometry.looks_like(blob):
            geometry = geomod.Geometry(blob)
            stats = geomod.export_obj(geometry, str(out / f"bloc{block_index:02d}_sub{sub.index}.obj"), block_index, sub.index)
            row.update({"kind": "V3D geometry", "object_type": geometry.object_type, "version": geometry.version, **stats})
            if sub.index == 2:
                # Geometry diagnostic only. Source parser does not qualify transforms.
                objects = []
                for mesh in geometry.meshes():
                    faces = []
                    for primitive in mesh.primitives:
                        for strip in primitive.strips:
                            indices = [corner.position for corner in strip.corners]
                            for i in range(len(indices) - 2):
                                face = indices[i:i + 3]
                                if len(set(face)) == 3:
                                    faces.append(face)
                    objects.append({"visible": True, "vertices_by_frame": [mesh.positions], "faces": faces})
                preview_wireframe(objects, out / "body_wireframe.png", f"V-Rally 2 PC physical block {block_index}, sub2")
        else:
            row["kind"] = "uninterpreted preserved identity only"
        report["subblocks"].append(row)
    write_json(out / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    evo = commands.add_parser("evo")
    evo.add_argument("--source", type=Path, required=True)
    evo.add_argument("--output", type=Path, required=True)
    evo.add_argument("--model", required=True)
    evo.add_argument("--truck", required=True)
    vr2 = commands.add_parser("vr2")
    vr2.add_argument("--source", type=Path, required=True)
    vr2.add_argument("--tool", type=Path, required=True)
    vr2.add_argument("--output", type=Path, required=True)
    vr2.add_argument("--block", type=int, default=1)
    cod = commands.add_parser("cod")
    cod.add_argument("--source", type=Path, required=True)
    cod.add_argument("--output", type=Path, required=True)
    sr2 = commands.add_parser("sr2")
    sr2.add_argument("--source", type=Path, required=True)
    sr2.add_argument("--output", type=Path, required=True)
    for command in (evo, vr2, cod, sr2):
        command.add_argument("--protected-root", type=Path, action="append", default=[],
                             help="Additional read-only game/tool root; repeat for shared roots")
        command.add_argument("--config", type=Path, required=True,
                             help="source-garage-roots/1 config; protects every configured source root")
    args = parser.parse_args()
    try:
        cfg = json.loads(read_bounded(args.config, 1024 * 1024).decode("utf-8"))
        if cfg.get("schema") != "source-garage-roots/1":
            raise InspectionError("unsupported source-root configuration")
        base = Path(cfg["base"])
        protected = [Path(__file__).absolute().parent, base,
                     *[Path(g["path"]) if Path(g["path"]).is_absolute() else base / g["path"] for g in cfg["games"]],
                     *args.protected_root]
        for root in protected:
            ensure_unlinked(root)
        # Reject unsafe output before any expensive inspection or external import.
        target = args.output.resolve()
        ensure_unlinked(args.output)
        for root in protected:
            real = root.resolve()
            if target == real or target.is_relative_to(real) or real.is_relative_to(target):
                raise InspectionError("output overlaps configured protected roots")
        if args.command == "evo":
            result = evo_smoke(args.source, args.output, args.model, args.truck, protected)
        elif args.command == "vr2":
            result = vr2_smoke(args.source, args.tool, args.output, args.block, protected)
        elif args.command == "cod":
            result = cod_smoke(args.source, args.output, protected)
        else:
            result = sr2_smoke(args.source, args.output, protected)
    except (InspectionError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"command": args.command, "L0": result["L0"], "L1": result["L1"],
                      "L2": result["L2"], "Gameplay": result["Gameplay"], "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
