"""Strict RGBA8 PNG input for same-size Master Rallye DXT replacement."""
from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path

from .dxt import PNG_ROWS_FLIP_VERTICAL, encode_dxt_pixels, parse_dxt, write_png

SIGNATURE=b"\x89PNG\r\n\x1a\n"


def decode_rgba_png(data: bytes):
    if not data.startswith(SIGNATURE):
        raise ValueError("not a PNG")
    position=8
    width=height=None
    payload=bytearray()
    seen_end=False
    while position<len(data):
        if position+12>len(data):
            raise ValueError("truncated PNG chunk")
        size=struct.unpack_from(">I",data,position)[0]
        kind=data[position+4:position+8]
        end=position+12+size
        if end>len(data):
            raise ValueError("truncated PNG payload")
        chunk=data[position+8:position+8+size]
        expected=struct.unpack_from(">I",data,position+8+size)[0]
        if zlib.crc32(kind+chunk)&0xffffffff!=expected:
            raise ValueError("PNG CRC mismatch")
        if kind==b"IHDR":
            if width is not None or size!=13:
                raise ValueError("invalid PNG IHDR")
            width,height,depth,color,compression,filtering,interlace=struct.unpack(">IIBBBBB",chunk)
            if not (0<width<=16384 and 0<height<=16384 and (depth,color,compression,filtering,interlace)==(8,6,0,0,0)):
                raise ValueError("PNG must be noninterlaced RGBA8")
        elif kind==b"IDAT":
            payload.extend(chunk)
        elif kind==b"IEND":
            seen_end=True
            if end!=len(data):
                raise ValueError("trailing PNG data")
            break
        elif kind[0]&32==0:
            raise ValueError(f"unsupported critical PNG chunk {kind!r}")
        position=end
    if width is None or not seen_end:
        raise ValueError("incomplete PNG")
    stride=width*4
    packed=zlib.decompress(bytes(payload))
    if len(packed)!=height*(stride+1):
        raise ValueError("PNG decompressed byte count mismatch")
    output=bytearray()
    previous=bytearray(stride)
    for row in range(height):
        start=row*(stride+1)
        mode=packed[start]
        current=bytearray(packed[start+1:start+1+stride])
        if mode not in range(5):
            raise ValueError("unsupported PNG row filter")
        if mode:
            for index in range(stride):
                left=current[index-4] if index>=4 else 0
                up=previous[index]
                upper_left=previous[index-4] if index>=4 else 0
                if mode==1: predictor=left
                elif mode==2: predictor=up
                elif mode==3: predictor=(left+up)//2
                else:
                    estimate=left+up-upper_left
                    distances=(abs(estimate-left),abs(estimate-up),abs(estimate-upper_left))
                    predictor=(left,up,upper_left)[distances.index(min(distances))]
                current[index]=(current[index]+predictor)&255
        output.extend(current)
        previous=current
    return width,height,bytes(output)


def _reverse_dependencies(source: Path):
    if not any((source.parent/name).is_file() for name in ("car.dx","complete.dx","wheel.dx")):
        return None
    from .vehicle_packaging import texture_users
    return texture_users(source.parent,source.name)


def export_texture(source: Path, output: Path):
    source=Path(source).resolve()
    output=Path(output).resolve()
    if source==output:
        raise ValueError("refusing to overwrite DXT source")
    texture=parse_dxt(source)
    write_png(texture,output,PNG_ROWS_FLIP_VERTICAL)
    return {"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"output_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"dimensions":[texture.width,texture.height],"row_policy":PNG_ROWS_FLIP_VERTICAL,"reverse_dependencies":_reverse_dependencies(source)}


def replace_texture(source: Path, edited_png: Path, output: Path, *, expected_source_sha256: str):
    source=Path(source).resolve()
    output=Path(output).resolve()
    if source==output or output==Path(edited_png).resolve():
        raise ValueError("refusing to overwrite an input")
    original=source.read_bytes()
    if hashlib.sha256(original).hexdigest().casefold()!=expected_source_sha256.casefold():
        raise ValueError("DXT template SHA-256 mismatch")
    template=parse_dxt(source)
    width,height,rgba=decode_rgba_png(Path(edited_png).read_bytes())
    data=encode_dxt_pixels(template,rgba,width,height,row_policy=PNG_ROWS_FLIP_VERTICAL)
    parsed=parse_dxt_bytes_safe(data)
    if parsed.header!=template.header or len(data)!=len(original):
        raise ValueError("DXT replacement header or byte size changed")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(data)
    return {"source_sha256":hashlib.sha256(original).hexdigest(),"output_sha256":hashlib.sha256(data).hexdigest(),"dimensions":[width,height],"same_header":True,"same_size":True,"runtime_status":"SAME_DIMENSION_REPLACEMENT_CONFIRMED_BY_RUNTIME","reverse_dependencies":_reverse_dependencies(source)}


def parse_dxt_bytes_safe(data):
    from .dxt import parse_dxt_bytes
    return parse_dxt_bytes(data)
