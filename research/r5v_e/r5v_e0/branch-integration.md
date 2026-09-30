# Release / beta branch integration

## Branches

| Role | Branch | State |
|---|---|---|
| Release feature work | `research/r5v-e0-trooper` | Based on `master`; contains R5V-C implementation, separate R5V-C owner-result closeout, and this E0 work |
| Existing user branch | `research/r5t-course-archaeology` | Preserved; not merged or rewritten |
| Beta/research source | `research/r-demo-pipeline` in `master-rallye-re-rdemo` | Read-only source of selected modules and evidence; left untouched |

No full merge was performed. Selected production modules and their synthetic
tests were copied from the beta branch. The existing R5V-C patcher was
extended in place rather than replaced.

## Reused beta history and files

| Beta commit(s) | Reused files / evidence |
|---|---|
| `73d1921`, `7ca0959` | `demo_dx.py`, `dx_revision_upgrade.py`, `tools/upgrade_dx_131_to_135.py`, converter tests; `demo_dx.py` defers the unrelated collision-oracle import so the bounded converter does not require GXM/oracle dependencies |
| `78d19bf` | `vehicle_config_analysis.py`, `vehicle_config_schema.py`, semantic schema tests |
| `b79c28c`, `9b9bdfe` | `vehicle_family_broker.py`, `vehicle_family_binder.py`, family binding tests |
| `52ccb00`, `6d8dd5c` | `vehicle_model_inventory.py`, `vehicle_composition.py`, `vehicle_physics_binding.py`, composition and physics tests |
| `df9ff16`, `70d75c7` | Vehicle Composer runtime findings and ZIP-compatible SMA package reader behavior used by the composer/package modules |
| `b617dce` and `research/r-cooker1_1/` | Owner-reported retail runtime evidence and exact Trooper input/output hashes for the converted resources |

The release port includes the selected parser/schema, converter, model
inventory, composition, physics-binding, and packaging code plus tests. It
does not include unrelated Blender releases, unrelated vehicle research
assets, raw `.research-output`, demo binaries, or the beta branch history.

## Minimal release-specific changes

- `tools/patch_vehicle_slot25.py` now exposes `astero-proof` and `trooper`
  profiles. Astero's prior output remains deterministic and byte-identical.
- `tools/prepare_r5v_e0_trooper.py` hash-locks retail and the known runtime-
  tested Trooper converter pair, validates source dependencies/config/collision,
  and creates only an ignored candidate plus loose overlay.
- `vehicle_packaging.py` carries the beta ZIP-compatible SMA member reader;
  `demo_dx.py` has a lazy import for its converter-only call path.

The R5V-C closeout is the distinct commit `f3b5883`. The final E0 work is one
additional feature commit. Neither branch is pushed.
