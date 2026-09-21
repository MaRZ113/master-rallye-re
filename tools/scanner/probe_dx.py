#!/usr/bin/env python3
"""Conservative structural probe for Master Rallye .dx model candidates."""
from __future__ import annotations
import argparse, json, math, re, struct
from pathlib import Path

def ascii_strings(data: bytes, minimum: int = 4):
    rx = re.compile(rb"[\x20-\x7e]{%d,}" % minimum)
    return [{"offset": f"0x{m.start():X}", "text": m.group().decode("ascii")} for m in rx.finditer(data)]

def sidecar_info(path: Path):
    if not path.exists(): return None
    text = path.read_text(encoding="latin-1")
    mm = re.search(r"Materials\(Size\s+(\d+)\)", text)
    meshes = [{"name": m.group(1), "index": int(m.group(2)), "size": int(m.group(3))}
              for m in re.finditer(r"moMesh\(Name \[(.*?)\] Index (\d+) Size (\d+)\)", text)]
    textures = [Path(m.group(1).replace("\\", "/")).name for m in re.finditer(r"Name\[([^\]]+\.tga)\]", text, re.I)]
    return {"material_count": int(mm.group(1)) if mm else None, "mesh_count": len(meshes),
            "mesh_span": max((m["index"] + m["size"] for m in meshes), default=0),
            "mesh_size_sum": sum(m["size"] for m in meshes), "meshes": meshes,
            "texture_names": sorted(set(textures), key=str.lower)}

def probe(path: Path, root: Path | None = None):
    data = path.read_bytes()
    display = path.name
    if root is not None:
        try:
            display = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            display = path.name
    if len(data) < 16: return {"path": display, "size": len(data), "error": "too short"}
    words = struct.unpack_from("<4I", data)
    count = words[3]
    position_end = 16 + count * 12
    positions = []
    finite = True
    if position_end <= len(data):
        for off in range(16, position_end, 12):
            xyz = struct.unpack_from("<3f", data, off)
            finite &= all(math.isfinite(v) for v in xyz)
            positions.append(xyz)
    bbox = None
    if positions and finite:
        bbox = {"min": [min(v[i] for v in positions) for i in range(3)],
                "max": [max(v[i] for v in positions) for i in range(3)]}
    targets = {count}
    sidecar = sidecar_info(path.with_suffix(".txt"))
    if sidecar:
        targets.update(v for v in (sidecar["material_count"], sidecar["mesh_span"]) if v is not None)
    hits = {}
    for target in sorted(targets):
        packed = struct.pack("<I", target)
        offsets=[]; start=0
        while True:
            found=data.find(packed,start)
            if found < 0: break
            offsets.append(f"0x{found:X}"); start=found+1
        hits[str(target)] = offsets[:64]
    boundary = data[max(0, position_end-32):min(len(data), position_end+96)]
    return {"path": display, "size": len(data),
            "header": {"raw_hex": data[:16].hex(" "), "u32_le": list(words)},
            "position_hypothesis": {"count": count, "offset": "0x10", "end": f"0x{position_end:X}",
                                    "fits_file": position_end <= len(data), "all_finite": finite, "bbox": bbox,
                                    "boundary_hex": boundary.hex(" ")},
            "candidate_u32_hits": hits, "ascii_strings": ascii_strings(data), "sidecar": sidecar}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("files", nargs="+", type=Path); ap.add_argument("--output", type=Path); ap.add_argument("--root", type=Path)
    args=ap.parse_args(); result={"schema_version":1,"files":[probe(p.resolve(), args.root) for p in args.files]}
    payload=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if args.output: args.output.write_text(payload,encoding="utf-8")
    else: print(payload,end="")
if __name__ == "__main__": main()
