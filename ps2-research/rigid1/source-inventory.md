# Authored source inventory

Fresh PackFS extraction of the 36 canonical paired RaceTest XML resources reproduces **83 gaAiRigidBody records in nine courses: 58 haybales and 25 tumbleweed** (`CONFIRMED_BY_BYTES`). These are authored AI/Egg records, not live body, active-body or visible-object counts.

| Course | Haybale records | Tumbleweed records |
|---|---:|---:|
| ITALY2 | 11 | 0 |
| ITALYS1 | 14 | 0 |
| ITALYS4 | 10 | 0 |
| ITALYW1 | 10 | 0 |
| ITALYW2 | 13 | 0 |
| TURKEY1 | 0 | 7 |
| TURKEY3 | 0 | 6 |
| TURKEYM | 0 | 9 |
| TURKEYS2FLIP | 0 | 3 |

`rigid-course-inventory.json` retains resource and decoded hashes, PackFS offsets, source list/Egg/AI indices, original parameter names/types/values/order, literal model reference and a hash of the parsed float32 4x4 matrix bytes. Full Row0..Row3 values can be reproduced with `parse_authored` and remain in ignored local diagnostics. Original lexical matrix text remains in the immutable XML payload. Stable source IDs distinguish duplicate placements; nothing is deduplicated by transform.

ItalyS1 has 14 records and 13 distinct matrix hashes. Both coincident records remain in inventory. Runtime source-to-instance multiplicity is not captured. Lists vary: ItalyS1 uses `Physics`; Turkey1 and Italy2 use `IContManager`. A list name is not the constructor or physical activation mechanism.

Hay aliases `misc\haybale\haybale` and `misc\objects\haybales\haybale` both decode to 6636 bytes, SHA256 `cd6da2625e707387c8b18e02f42fcf655d5135fa8e9986cb8894bf10734447cb`. Tumbleweed `misc\objects\tumbleweed\tumblweed` decodes to 9819 bytes, SHA256 `eb959250d0bdb6fa051fb69f4a852c4789be200613eb8e90678d36a48ab54bf4`. Preserve the spelling `tumblweed`.
