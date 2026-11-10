"""Zero-edit roundtrip of course GXM v7 sources through course_gxm_writer."""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from master_rallye.course_gxm import parse_course_gxm_model_v7  # noqa: E402
from master_rallye.course_gxm_writer import (  # noqa: E402
    GxmGroup, GxmMesh, decode_materials, encode_gxm_v7, encode_materials)
from master_rallye.course_source import parse_course_txt  # noqa: E402


def rebuild(path: Path) -> tuple[bytes, bytes]:
    txt = parse_course_txt(path.with_suffix(".txt"))
    model = parse_course_gxm_model_v7(path, txt)
    materials = decode_materials(model.materials.raw, model.materials.count)
    if encode_materials(materials) != model.materials.raw:
        raise SystemExit(f"{path.name}: material re-encode differs")
    nodes = {}
    roots = []
    for node in txt.nodes[1:]:
        item = GxmMesh(node.name, node.mesh_index, node.mesh_size) if node.class_name.lower() == "momesh" \
            else GxmGroup(node.name)
        nodes[node.node_id] = item
        (roots if node.parent_id == txt.nodes[0].node_id else nodes[node.parent_id].children).append(item)
    data = encode_gxm_v7(
        colors=list(struct.iter_unpack("<4f", model.colors.raw)), materials=materials,
        normals=list(struct.iter_unpack("<3f", model.normals.raw)),
        texcoords=list(struct.iter_unpack("<3f", model.texcoords.raw)),
        triangles=list(struct.iter_unpack("<13I", model.triangles.raw)),
        positions=list(struct.iter_unpack("<3f", model.positions.raw)),
        root_name=txt.nodes[0].name, children=roots, header_word1=model.counts[0])
    return path.read_bytes(), data


if __name__ == "__main__":
    ok = True
    for arg in sys.argv[1:]:
        original, rebuilt = rebuild(Path(arg))
        same = original == rebuilt
        ok &= same
        print(f"{Path(arg).name}: {'IDENTICAL' if same else 'DIFFERS'} {len(original)} bytes "
              f"sha256 {hashlib.sha256(rebuilt).hexdigest()[:16]}")
    raise SystemExit(0 if ok else 1)
