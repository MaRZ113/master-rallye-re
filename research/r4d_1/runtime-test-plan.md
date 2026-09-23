# Controlled runtime tests

Generate ignored candidates with `py -3 tools/scanner/material_runtime_probes.py "..\Data.sma_unpacked\DataGx\Vehicles" --output ".research-output/r4d_1/runtime-tests"`. Every candidate keeps the 20-byte DXT header, dimensions, and file size. M2/M4 also keep RGB exactly. The generator verifies that the source file remains byte-identical and writes only to the ignored output tree. Every folder includes validation.json and TEST_INSTRUCTIONS.txt.

| Test | Astero target | Variants | Observation |
|---|---|---|---|
| M1 body helper | whitepaint-tga.dxt, car draw 7 and related body draws | white/black/gray, original alpha | Color, brightness, reflection, masking, unchanged? |
| M2 windscreen | windscreen32-tga.dxt, car draw 23 | alpha 255/128/0, original RGB | Transparency, threshold, sorting/Z artifacts? |
| M3 envmap | chrome-tga.dxt, car draws 11/17/18 | asymmetric pattern | View-rotating UV, camera normal, or another transform? |
| M4 brake/glow | breaklightsonglow-tga.dxt, car draw 30 | alpha 255/128/0, original RGB | Same alpha behavior as glass, dynamic pass, or other effect? |

Use a disposable game copy, one candidate at a time. Keep the same lighting/camera/settings, and record Reflections on/off for M1/M3. Record game build, screenshots, observations, and restore result. **Prepared, not tested in runtime**; human in-game observation is the evidence gate.
