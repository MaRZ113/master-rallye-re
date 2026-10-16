"""Correct the private OFF ordered UV/index contract to the retail loader winding.

fix1 (lamp-followup/prepare_off.py) hashed car.dx indices in file order. Retail
PID21408 sidecars show `private_off_native_uv_or_layout_rejected` for NewRav,
Bruno and Mattserati. Every non-private fleet-damage dump in the Pristine logs
(250 records: NewRav and KiaSportage, FVF 0x142 and 0x152) has the car.dx
vertex order unchanged and each triangle submitted as (b, a, c) for file
(a, b, c); see flip_rule_evidence.json. Only the ordered UV/index hash depends
on winding; position/UV corners, geometry, ordered XYZ and the deformation
mapping are untouched.

For each family the script proves the old pinned value equals the unswapped
file-order hash, then writes the loader-order hash into
renderer/fleet_private_off_registry.hpp and lamp-followup/contracts.json.
"""
from pathlib import Path
import importlib.util, json, struct, hashlib

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
REGISTRY = PORT / "renderer" / "fleet_private_off_registry.hpp"
CONTRACTS = HERE.parent / "lamp-followup" / "contracts.json"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def uv_index_hash(model, first, count, indices):
    uv = model.uv_sets[0].values
    return hashlib.sha256(b"".join(struct.pack("<2f", *uv[i]) for i in range(first, first + count)) +
                          struct.pack("<%dI" % len(indices), *(i - first for i in indices))).hexdigest()


def loader_winding(indices):
    out = []
    for k in range(0, len(indices), 3):
        a, b, c = indices[k:k + 3]
        out += [b, a, c]
    return out


def main() -> int:
    audit = load("fix2_winding_audit", PORT / "docs/full-coverage/vehicles/audit.py")
    contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    registry = REGISTRY.read_bytes().decode("utf-8")
    report = []
    for row in contracts["families"]:
        path = audit.PC / row["family"] / "car.dx"
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["source_pc_sha256"]:
            raise SystemExit(f"{row['family']}: car.dx hash changed")
        model = audit.parse_dx(path)
        indices = model.draw_global_indices(model.physical_draws[row["native_source_record"]])
        first, count = min(indices), max(indices) - min(indices) + 1
        old = uv_index_hash(model, first, count, indices)
        new = uv_index_hash(model, first, count, loader_winding(indices))
        pinned = row["native_ordered_uv_indices"]
        if pinned == new:
            report.append({"family": row["family"], "status": "already_loader_winding", "sha256": new})
            continue
        if pinned != old:
            raise SystemExit(f"{row['family']}: pinned value is neither file nor loader winding")
        if registry.count(old) != 1:
            raise SystemExit(f"{row['family']}: registry does not contain the old hash exactly once")
        registry = registry.replace(old, new)
        row["native_ordered_uv_indices"] = new
        row["native_ordered_uv_indices_winding"] = "retail_loader_b_a_c"
        report.append({"family": row["family"], "status": "corrected", "file_order": old, "loader_order": new})
    REGISTRY.write_bytes(registry.encode("utf-8"))
    CONTRACTS.write_text(json.dumps(contracts, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
