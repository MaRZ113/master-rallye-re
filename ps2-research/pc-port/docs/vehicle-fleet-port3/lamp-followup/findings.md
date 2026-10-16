# Three conditional OFF lamp source replacements

These source candidates address precise omissions; they do not authorize a whole light assembly or any brake ON/glow draw.

| Family | Original PS2 conditional path | PC source record label | Source difference |
|---|---|---:|---|
| NewRav | root.26.1.0 | 34 | XYZ residual 2.98e-7, UV exact; native OFF has primary cuindicate64, no secondary reflection texture |
| Bruno | root.20.1.0 | 20 | Original geometry corresponds; source UV differs by 0.0001897215843 |
| Mattserati | root.21.1.0 | 25 | UV exact; original XYZ revision differs by 0.008023202419 |

Record numbers are immutable original resource labels only. Runtime admission must use exact hashes and current queue/chassis ownership, never draw ordinals.

The old registry excluded Bruno/Mattserati intentionally. NewRav was admitted in source but its flat native OFF source cannot satisfy the current native two-texture reflection snapshot. A private original PS2 mesh/material is the narrow common correction. The generator emits three standard PS2MDL02 assets with one original mode-3 carshiny mesh each, untouched original normals/colors/UV/XYZ and original ordered primary/secondary GXI resources. Use the existing source V sampling correction once; do not flip the model or alter normals. Source model coordinates need only the real chassis WORLD.

`off_mapping.hpp` contains pinned loader contracts plus exact original PC healthy geometry, position/UV, ordered XYZ and ordered UV/index hashes. Triangle pairing is complete for all three. The source mapping limits appear only during original asset preparation and explain the measured asset revisions; they must never become runtime geometry tolerances.

For private native damaged OFF clones, retain the actual exact healthy native ordered XYZ array in that owner/race/device lifetime. Current owner, material vector/token, primary texture/generation, current mirrored resource generation/revision and native UV/index topology must remain verified. Each original PS2 vertex maps to one or more native source vertices; add only their current-minus-healthy native XYZ delta, and reject if any candidates disagree beyond 1e-6. Preserve original PS2 normals and UVs. This mapping is source-complete but has no new damaged runtime capture proof yet. Cold damaged admission must retain Stock.

The current PID11316 logs contain two sessions with a reused PID. Frames2529/3858/4096 belong to old proxy9fecebfa, not PORT3. Frames3241/3954/7924 explicitly identify PORT3 proxy638645b7 and the original EXE; current NewRav healthy/private raw pair3241/3954 is valid. Newer PORT3 frames18484+ show accepted OFF transactions for Astero, Forester, Kamaz and megane, with draw/restore HRESULT0. Bruno39380 and Mattserati84112 show healthy ON+glow acceptance and no OFF override, consistent with the excluded profiles. A newer NewRav OFF capture was not available in these files. The current session file is still zero bytes, so no conclusion may rely on missing session events.

A darker OFF zone despite successful reflection may involve diffuse vertex color/material compositing or the separate ON overlay. No global brightness change is justified by these logs. First compare the exact source diffuse colors/normals and state/texture layers for the specific surface against an equivalent PS2 view. No claim of complete GS shader parity is made.

Validation: five focused Python tests pass locally; the private asset test intentionally skips in a clean source handoff without original local assets. No renderer, build tree, game file or frozen source was modified by this source preparation.


