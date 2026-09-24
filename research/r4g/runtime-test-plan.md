# R4G isolated human runtime test plan

This is the pre-runtime test procedure. Human results subsequently passed for B1, C1, P1 and W1; see runtime-results.md/json. The instructions and candidate hashes below remain as the original test record.

Use one candidate at a time with the already runtime-confirmed full-tree Python Data.sma workflow. The four candidate directories are ignored local output under .research-output/r4g/runtime-tests/. Each includes an asset, validation.json and TEST_INSTRUCTIONS.txt. Keep game Reflections/settings and original Astero installation comparable. Do not install multiple candidates simultaneously. No new Data.sma is included in this repository.

| ID | Override | Purpose | Candidate SHA-256 |
|---|---|---|---|
| B1 | Astero/car.dx | Raised roof/body triangle beyond old Y maximum; footer recomputed | 7de8988d598de649d993ae132e80353da60b8393a154da73b5fb4b7e08db56ce |
| C1 | Astero/car.dx | Tag101 source-X width +20%; visual mesh stock | 5c7db535a4e37d449ab952c4e1f6c768c20eee62bd7452ae3df1dde27cbac67d |
| P1 | Astero/complete.dx | Existing-draw +3 vertices/+1 triangle in presentation body | a1ce0fbebd8b49dacb0b2890a40b20799fdd4c6a43eac874c7751f6ffa91023f |
| W1 | Astero/wheel.dx | Existing-draw +3 vertices/+1 triangle on wheel side | 7a5d9d8ebad68a7b2827f63bbec75442350526a97b9423d365e46e8bedd510d5 |

B1: original Astero car.dx footer maximum Y is 1.44031584; candidate is 1.52951097. Check game/car load, the raised feature is visible without clipping/disappearance, original collision still works, damage/glass broadly work, and artifacts.

C1: the render arrays are byte-identical to stock. Check game/car load, collision still exists, side-wall contact occurs earlier than the visible body on the widened source-X axis, handling and damage remain usable, and artifacts. This is the runtime gate for collision scaling.

P1: inspect the presentation/menu Astero. Check load, a new hood/body triangle visible, correct texture/shading, and otherwise normal model. Source 2657 vertices/2423 triangles; candidate 2660/2424.

W1: check a race with Astero. Look for the changed wheel visual on all four wheel instances and verify steering/suspension, wheel physics and general behavior remain normal. Source 220 vertices/252 triangles; candidate 223/253.

Automated parsing and binary audits alone did not establish runtime behavior. The later human tests reported PASS for all four IDs, so Vehicle SDK v1 is now frozen as a runtime-confirmed baseline. The next proposed phase is R5T-A course/track asset archaeology. R5V EXE vehicle-slot work remains optional and separate; neither begins in this closeout.
