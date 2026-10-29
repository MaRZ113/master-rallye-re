# Dakar 2 source recovery results — 29 October 2026

Xbox selected from actual source/loader evidence. Mitsubishi Pajero (#205 on original texture) and independent Hino truck (#400) recovered into existing Universal Vehicle Scene v1. L0 PASS; L1 PASS structural recovery; **L2 WARN: source culling and complete material stages unresolved**. No MR CarID or native candidate created. GC/PS2 are discovery results, not model-decoder support.

See [platform comparison/hashes](DAKAR2_PLATFORM_AUDIT.md), [format evidence/issues](DAKAR2_FORMAT_REPORT.md) and [corpus manifest](DAKAR2_CORPUS_MANIFEST.json). Public manifest contains metadata/signatures/hashes, not original model or texture payloads.

| Scene | Nodes | Meshes | Vertices | Triangles | Exact original streams |
|---|---:|---:|---:|---:|---:|
| HINO | 39 | 47 | 4417 | 4676 | 235 |
| PAJERO | 42 | 56 | 3689 | 4154 | 266 |

Private scenes: `.research-output/vehicles/dakar2-source/final/{PAJERO,HINO}/scene/scene.json`. Immutable original RBB/selected LOD snapshots, geometry/resource provenance, packed normals/colors/UV1, original BC mip samples and separate decoded RGBA are retained. Pajero has 11 textures, Hino 13. Scenes reopen through existing Source Garage; native Create stays disabled for Dakar 2. This initial recovery does not qualify every source revision or vehicle.

## Repeatability and preview evidence

Two independent generations per vehicle produced byte-identical JSON, manifests and every sidecar. Each retained source stream was independently sliced from the original LOD snapshot and compared byte-for-byte. Derived model counts match original declarations.

Final SHA256:

- HINO: scene `8e2245fd97e3f135766cbd966c1de659f089e1c5562364fc4371ee8beac2f34f`; manifest `559f94c99f928c6fd3491d9011816514542a4b99e60171029ffcc406ade60538`.

- PAJERO: scene `a59790f69d4bc9b653a5a755056b27f01df56d6a1838456f429d6233c15813ce`; manifest `367c6d84099da9f34d569361b45e9f1d408d67b64111f9eada768c190eabf5ed`.

D3D9 captured front/rear/left/right/top/isometric in CW, CCW and no-cull modes: 36 final images under `final/<vehicle>/views-{cw,ccw,none}/`. No-cull is a diagnostic, not a silent two-sided repair or renderer qualification. Pajero's pale wheel interiors and incomplete shader behavior remain visible. Actual Tk Source Garage reopen/GPU preview for both scenes passed without errors; `gui-smoke/validation.json` and its UI screenshots cover the same geometry at the earlier metadata checkpoint. No original Dakar 2 runtime test was performed.

## Measurements

Original unscaled source numerical units. Wheel values are rest-bone origins, not independently verified loaded tire centers or settled suspension. Full original matrices and derived transforms remain in scenes.

| Measurement | Pajero | Hino |
|---|---|---|
| Bounds min XYZ | -1.024549, -0.807681, -1.943266 | -1.207460, -0.412771, -2.663193 |
| Bounds max XYZ | 1.029103, 1.074057, 2.037838 | 1.207459, 2.913994, 3.309252 |
| Front right origin | 0.864299, -0.410854, 1.386823 | 0.984334, 0.187203, 2.090879 |
| Front left origin | -0.846151, -0.410998, 1.386640 | -0.984335, 0.187202, 2.090879 |
| Back right origin | 0.878485, -0.407281, -1.226046 | 0.984335, 0.187204, -1.573706 |
| Back left origin | -0.873475, -0.407281, -1.226046 | -0.984336, 0.187203, -1.573706 |

Do not infer meters, MR alignment, stock suspension behavior or shared Paris-Dakar/MR source geometry.

## Reproduce privately

Run from repository root; choose a fresh output directory, keep scene sidecars together. Source paths are configurable but source revision must qualify. Audit performs full streaming hashes and takes longer than recovery. Python 3.14+ is needed only for RVZ audit.

```powershell
python tools/dakar2_source_lab.py recover --xbox "E:/RallyWorkshop_Sources/sources/Dakar 2 Xbox/Dakar 2 - The World's Ultimate Rally (USA).iso" --vehicle PAJERO --output .research-output/vehicles/dakar2-source/owner-pajero --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe --diagnostic-two-sided
python tools/validate_dakar2_source.py --xbox "E:/RallyWorkshop_Sources/sources/Dakar 2 Xbox/Dakar 2 - The World's Ultimate Rally (USA).iso" --output .research-output/vehicles/dakar2-source/owner-validation --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe
python tools/dakar2_source_lab.py audit --xbox "E:/RallyWorkshop_Sources/sources/Dakar 2 Xbox/Dakar 2 - The World's Ultimate Rally (USA).iso" --gamecube "E:/RallyWorkshop_Sources/sources/Dakar 2 GameCube/Dakar 2 - The World's Ultimate Rally (USA) (En,Fr,De,Es,It).rvz" --ps2 "E:/RallyWorkshop_Sources/sources/Dakar 2 PS2" --output .research-output/vehicles/dakar2-source/owner-audit
```

Reopen `scene.json` in Source Garage. No original installation is changed or duplicated, no game assets downloaded, no new ISO generated.

## Validation and preservation

13 new source-free tests cover malformed RBB/XOR/relocations, SBB containment, geometry indices/strip parity/normals, XDVDFS/FST, RVZ hashes/compression budgets/roundtrip, texture channels/unsupported types, safe outputs and missing sources. Focused UVS/source/bridge suite: 54 tests. Full Windows: 1152 tests OK, two existing optional fixture skips. Private logs record exact execution results.

Protected original games and accepted projects are checked by an 8895-file before/after SHA256 audit, saved as `preservation-validation.json`. No physics values, rosters, original EXE/proxy or accepted project assets changed. Silver #271 owner launch/stiffness remains an independent reversible Physics Studio follow-up, not a new complete gameplay pass.

Source-only and changed-files review archives are generated from committed text blobs, with per-member hashes and ZIP CRC verification. Complete v7.3 and previous native checkpoint remain included. Private source snapshots, geometry, textures, previews and decompiler/binary exports are excluded. Post-commit `review/archive-manifest.json` pins revision and archive hashes. No push/publication.

## Review boundary

Before native import: qualify original culling/mixed facing, shader stage/alpha/vertex colors and active equipment/LOD policy. Nissan rotation needs original transform evidence. Initial L1 recovery and attractive no-cull diagnostics do not authorize an MR conversion. Stop here for review.

## v7.4 follow-up

The original L1 results above remain historical and immutable. New derived source-state previews, native matrix/cull/depth/pass evidence and qualified Nissan rigid-basis recovery are documented in [DAKAR2_RENDERER_RESULTS.md](DAKAR2_RENDERER_RESULTS.md). [DAKAR2_LOST_VEHICLE_COMPARISON.md](DAKAR2_LOST_VEHICLE_COMPARISON.md) adds measured PC RED/Silver versus Xbox comparisons. L2 still WARN; GC/PS2 boundaries and no-native-import scope remain.
