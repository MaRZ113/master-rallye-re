"""Build the private NewRav OFF identity fixture for PORT3 fix2.

The runtime OFF lamp of NewRav is submitted by the retail game as a flat
XYZ|DIFFUSE|TEX1 draw (FVF 0x142, stride 24, 18 vertices, 10 triangles; F10
frame 42468 of PID 26244). This script rebuilds exactly that native buffer
layout from the hash-pinned original PC car.dx record 34 so the real C++
identity functions can be exercised on original bytes. Diffuse is not part of
any identity hash and is written as opaque white.

Output (ignored, never distributed): ps2-research/data/fix2/<family>-off.bin for every
private OFF profile in lamp-followup/contracts.json.
  magic b'MRRF2OFF' | u32 vertices | u32 triangles | u32 min_index | u32 fvf (0x142 or 0x152)
  vertices * stride (24 or 36) | triangles * 3 u16 indices in retail loader winding
"""
from pathlib import Path
import importlib.util, json, struct, hashlib

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
OUT = PORT.parent / "data" / "fix2" / "private-off"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(audit, contract, flat):
    path = audit.PC / contract["family"] / "car.dx"
    if hashlib.sha256(path.read_bytes()).hexdigest() != contract["source_pc_sha256"]:
        raise SystemExit(f"{contract['family']}: car.dx does not match the pinned source hash")
    model = audit.parse_dx(path)
    indices = model.draw_global_indices(model.physical_draws[contract["native_source_record"]])
    first = min(indices)
    count = max(indices) - first + 1
    if (count, len(indices) // 3, first) != (contract["native_vertices"], contract["native_triangles"],
                                             contract["native_first_source_vertex"]):
        raise SystemExit(f"{contract['family']}: native record no longer matches the pinned shape")
    uv = model.uv_sets[0].values
    pos = model.vertices.positions
    if flat:  # FVF 0x142: xyz, diffuse, uv (observed NewRav retail OFF draw)
        vertices = b"".join(struct.pack("<3fI2f", *pos[first + i], 0xFFFFFFFF, *uv[first + i]) for i in range(count))
    else:  # FVF 0x152: xyz, normal, diffuse, uv (two-texture lamp records)
        vertices = b"".join(struct.pack("<3f3fI2f", *pos[first + i], 0.0, 0.0, 1.0, 0xFFFFFFFF, *uv[first + i])
                            for i in range(count))
    corners = sorted(struct.pack("<3f2f", *pos[i], *uv[i]) for i in indices)
    if hashlib.sha256(b"".join(corners)).hexdigest() != contract["native_position_uv"]:
        raise SystemExit(f"{contract['family']}: position/UV corner hash differs from the pinned contract")
    # Retail loader winding: file (a, b, c) is submitted as (b, a, c) (fix2/flip_rule_evidence.json).
    loader = [v for k in range(0, len(indices), 3) for v in (indices[k + 1], indices[k], indices[k + 2])]
    return (b"MRRF2OFF" + struct.pack("<4I", count, len(indices) // 3, first, 0x142 if flat else 0x152) + vertices +
            struct.pack(f"<{len(loader)}H", *loader))


def main() -> int:
    audit = load("fix2_audit", PORT / "docs/full-coverage/vehicles/audit.py")
    rows = json.loads((HERE.parent / "lamp-followup/contracts.json").read_text())["families"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    report = []
    for row in rows:
        payload = build(audit, row, row["family"] == "NewRav")
        target = OUT.parent / f"{row['family'].lower()}-off.bin"
        target.write_bytes(payload)
        report.append({"family": row["family"], "fixture": target.name, "sha256": hashlib.sha256(payload).hexdigest()})
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
