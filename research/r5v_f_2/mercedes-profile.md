# Planned Mercedes profile — not implemented

The common physical registry expansion and F.1 cleanup remain the regression baseline. No `mercedes` profile has been added because the distinct source model cannot yet be converted and validated as retail revision135.

| Profile field | Intended value | Evidence/status |
|---|---|---|
| physical slot / class-local | ID26 / class0 T1 local7 | Already proven by F/F.1; keep IDs0–25 and T2/T3 mappings unchanged |
| internal/runtime family | `Mercedes` | Literal demo registry name; retail XML has compatible named family |
| resource folder | `DataGx/Vehicles/Mercedes` | Target overlay path; source to be converted from root `Copy of Mercedes` |
| model roles | Mercedes `complete.dx`, `car.dx`, `wheel.dx` | Source packages exist at rev127; retail output is the blocker |
| physics | retail `Vehicles/Mercedes` | 144-field schema compatible; runtime must wait for P1 |
| display | `MERCEDES ML-320` | Historic EXE string; implement as ID26-only override, keeping 0x33/0x34/0x35 distinct |
| Vehicle Select art | frame4 on T1_Car8 | Historic ID2/local2 slot mapping; art is not Mercedes-exclusive |
| SmallCarSheet | donor frame9 for controlled P0 | Historic ID2 final integer 0 is not independently semantically proven in demo |
| frontend stats | 4 / 3 / 6 / 5 | Raw historical initializer values |
| race colour | retain red canary for first identity P0, then explicit custom RGBA if needed | No comparable historic RGBA field in demo record |
| unlock policy | ID26-only test unlock | Existing F1 test policy; campaign persistence remains unproven |

Keep the existing donor-cleanup profile unchanged. When the conversion gate closes, add a separate Mercedes profile whose asset staging and display strategy are manifest-driven; do not scatter Mercedes literals through physical registry patch code. Candidate generation stays forbidden until model conversion, complete asset validation, dependency staging, cleanup regression, and collision checks pass.
