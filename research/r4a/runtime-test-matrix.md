# R4A minimal controlled runtime test matrix

These are proposals only. R4A does not modify the installation or generate new
unsupported binaries. Each experiment requires a clean backup, one change at
a time, and restoration before the next test.

| Priority | Single change | Question answered | Observe | Stop condition |
|---:|---|---|---|---|
| 1 | Make Astero `wheel.dx` temporarily unavailable while retaining original `car.dx` | Is separate wheel DX visual-only, and does race physics continue without its render resource? | load result, visible wheels, ride/collision/steering | restore immediately after one race start |
| 2 | Substitute another known-valid 252-triangle `wheel.dx` for Astero's wheel only | Are four instance positions/transforms supplied outside `wheel.dx`? | whether replacement appears four times at Astero wheel locations | do not infer physics from appearance alone |
| 3 | Substitute SeatBuggy `complete.dx` for its own `car.dx` | Is the presence of `$chull` plus marker-101 sufficient for race collision activation? | collision, lift, damage, double wheels | a failure disproves sufficiency; a pass does not prove exact layout |
| 4 | Repeat complete-for-car on forklift | Does the only tag-2-only/no-named-hull car follow a different binding path? | collision, lift, damage, wheel duplication | treat forklift as an explicit structural outlier |

Do not patch trailing bytes, draw tags, indices, bounds, materials, normals, or
UVs for these tests. Such writers do not exist within the runtime-confirmed R3
safety envelope.
