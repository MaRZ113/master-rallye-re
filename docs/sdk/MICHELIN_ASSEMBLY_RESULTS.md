# Michelin Rally Masters — original neutral vehicle assemblies

29 October 2026. Initially clean `research/vehicles`, baseline `60ef21ce6e9828a635c4b15652e3e0d5f357c7ee`. Owner v7.6 authorizes two neutral source recoveries and a small optional Pajero probe, not a native MR import. Complete previous Master Plan is an exact text prefix of v7.6; complete attachment retained separately.

## Result and evidence boundary

Toyota **RAV 4, ID25/A** and Renault **Megane F2, ID6/A** now have reopenable UVS v1 scenes with original textured body LOD0 and four authentic, catalog-selected Michelin wheels. Both render in the existing D3D9 Previewer and real Tk Source Garage; native Create remains disabled. No direct MR compiler, substitute wheel geometry, body retouching, project registration or CarID.

**L1 PASS for selected static body/wheel resource assembly; L2 WARN.** Native initial hub arithmetic is qualified. Zero steering/spin, wheel side matrices, gravity-settled suspension, full renderer lighting/glass/cutout filtering and dynamic damage remain separate, unqualified runtime behavior. These are useful neutral assemblies, not claims of exact original running cars. Original EXE was analyzed statically only. Catalog evidence says F2; no Maxi rename.

## Exact owner-local inputs

Root: `E:/RallyWorkshop_Sources/sources/Michelin Rally Masters`. Existing PDI1/TEA/LZSS/XOBJ/TGA decoder reused without replacement or third-party vendoring.

| Resource | SHA256 |
|---|---|
| Data/Objects/Car25A.PDO | bbbc58fe11456369231e595444d43377f94cc3f19af2e2057a4ec68a07802593 |
| Data/Objects/Car06A.PDO | f0a9400812814620832b4a3fe98a024318de72b929ba225a90c4a57e342e1a5b |
| RallyMasters.EXE | 71c6c36505102e75518a7f6843bbc8355f205e439086e389ec877225e3e0a8ae |
| Server/Data/Cars.BIN | bb52e07b8287e28003be86ebb4fc700277b14a6af93cea823dd6dc7535bc730b |
| Data/Objects/Tarmac_t0004.pdo | 51a4958b2a5d8b8eff55a9455b1ac439e3ed970add60606f26e49391e8d9cf33 |
| Data/Objects/Tarmac_t0022.pdo | 649edf6cb2c989f86fd721456c9a79fdc3650946771cf31637e76900b7c5d6f8 |

These hashes are enforced before selected assembly construction. Tyre choice is explicitly **Tarmac entry0**, not a claim about the owner's default race. Unqualified alternate wheel banks fail closed. Each source scene snapshots every decoded body-bank member, including all four XOs and differing external streams; exact TGA palettes and original bytes remain in original resources. Selected wheel-bank members also remain private. Public MICHELIN_ASSEMBLY_PROVENANCE.json contains hashes/counts/measurements only.

## Native loader findings

REA Ghidra12.1.4 analyzed exact x86 EXE; original bytes/file mappings independently checked. For this build `.text`/`.rdata`/`.data` offsets map as VA = file offset +0x400000 within their actual PE sections. Decompiler output is an interpretation, not original source. Full private evidence and immutable snapshot: `.research-output/vehicles/michelin-assembly/native/` (59 retained observations). No executable patch or execution.

| Original procedure / instruction | Observed relationship |
|---|---|
| 004bcf00 | Loads index.toc, compares PTOC at004bcf8b (`813e50544f43`), reads count and 54-byte records, verifies checksum: signed footer minus sum(bytes8..footer) = -0xcc11bc |
| 004bcf00 →004b6490/004baaa0 | Type3 record loads XO. First is root; subsequent distance/name records append through004b6650 →004b53f0, whose original diagnostic explicitly names ObjectAddLOD |
| 004baaa0 | Copies original positions/normals; retains ordered vertex/normal indices, texture selector at source triangle+0x50, six UV floats at+0x54..+0x68, source flags/colors. Selected triangle stride108 remains valid |
| 004ba6c0 | Allocates N+1 texture handles, sets slot0 empty, fills1..N by original names. At004ba98e `668b38` loads selector;004ba9a6 `8b3cbe` indexes table. Earlier one-based hypothesis is now source-backed |
| 00405830 | Loads all four external vertex arrays into state+0x1c..+0x28; copies XOBJ original positions into separate backup+0x2c..+0x38 using004b7350 |
| 004856c0 | Deformation updates original model positions toward corresponding external target positions under collision/damage-related state; does not select external arrays as default rest vertices |
| 0048b9b0 | Restores backup original XOBJ positions. Thus external BINs are damage targets; never average/mix them into source rest geometry |
| 00405b10..00405b63 | Source catalog tyre index uses car-record+(road+16)*20+choice*4. Tarmac road0 gives offset0x140. Formats original Tarmac_t0NNN bank and XO names |
| 00405c7c..00405c83 | `8b542410`, `8b4e04`, `e8f8100b00`: EDX=wheel, ECX=body, attach via004b6d80, repeated four times. Pseudocode had misleading zero parameters; instruction check resolves this |
| 00417dc0 | Fetches body matrix and four successive child matrices; corroborates four wheel attachments |
| 004890e0 | Copies four XYZ rows at Cars.BIN record+0x1d0+12*i, subtracts initial radius from Y. Radius is 0.34 for these tyre IDs (other branch0.306 not applied) |

Both selected PTOCs name body LOD0..3 at distances **0,15,30,50**, source units. Root type0 record is retained raw and its miscellaneous float is not a LOD distance. RAV4 body triangle counts652/652/314/314; Mégane908/774/328/177. They are alternatives, never four simultaneous body parts. All corresponding external streams remain independently preserved; LOD0 differs at178 RAV4 and328 Renault positions. Mégane LOD2 has eight triangles /24 corners with zero indexed normals: neutral preview explicitly falls back to their nonzero **original face normals**, recording every offset/index. Original indexed zeros remain in source snapshots/inspection; default LOD0 has no such fallback. No per-car polygon fix.

## Materials, UVs and coverage

Original paletted TGA RGB samples and UVs are retained. No black-pixel transparency or alpha invented from descriptor attribute bits. Source flags/colors are recorded per triangle;004baaa0 converts source RGB words into BGRA and selects uniform0x5e for flag0x10000. Neutral preview uses source-backed RGB, keeping glass opaque until original blend behavior is qualified.

The wheel magenta regions were investigated rather than painted over. **004ba190** checks palette0 B>=241, G<=14, R>=241 and selects alpha-capable formats. **00408720 →00408520 →00407fe0 case1** converts palette index0 to coverage0, all other indices to255. The adapter reproduces that native-qualified coverage only when this original dispatch sentinel is present; a synthetic test verifies black index1 stays opaque. This is a **derived preview coverage mask**, not a newly discovered alpha channel in the original 24-bit palette. Exact source bytes/palettes remain unchanged. Original palette0 averaging, hardware texture format/filter/mipmap behavior and cutout thresholds are not reproduced; edge fringes remain possible. D3D9 blending is an approximation of original cutout behavior.

Normalized front=-Z follows source FRONT/BACK panel placement (+Z front), +Y roof; the reversible Z reflection is an inspection convention, not proof of original engine handedness or physical metres. Shared preview code handles inverse-transpose normals and determinant winding. Source-local inspection remains available with identity basis. No manual UV edits, atlas replacement, arbitrary nonuniform scale, global polygon reversal or claim of culling parity. Diagnostic no-cull captures are explicitly neutral, not original renderer proof.

## Measured static assembly

| Measure (source units; metres unproven) | RAV4 | Mégane F2 |
|---|---:|---:|
| Catalog record offset |28944|0|
| Tarmac entry0 selector offset |29264|320|
| Selected tyre ID |4|22|
| Front hubs X |±0.700000|±0.780000|
| Rear hubs X |±0.700000|±0.780000|
| Front hubs Y after native radius subtraction |-0.160745|-0.095000|
| Rear hubs Y after native radius subtraction |-0.170000|-0.095000|
| Front Z |1.005960|0.968213|
| Rear Z |-1.407980|-1.430000|
| Wheelbase |2.413939|2.398213|
| Track, front/rear |1.400000|1.560000|
| Selected wheel geometry Y/Z radius |0.340000|0.340000|

Source catalog Y values before subtraction and exact offsets are retained in each node/manifest. No wheel-arch visual fitting. Wheel spin/steer identity is an explicit neutral inspection assumption; side-specific runtime basis and suspension settlement remain unknown. RAV4 source scene has15 unique mesh groups /5 nodes,652 body+152 unique wheel triangles; four wheel instances yield1260 rendered triangles. Renault has17 groups /5 nodes,908+152 unique triangles,1516 rendered. Do not confuse unique geometry counts with four-instance counts.

## Private delivery and reproducibility

`.research-output/vehicles/michelin-assembly/final/Car25A/assembly/scene/scene.json` and equivalent `Car06A` open through Source Garage. Each assembly and each independent LOD has front/rear/left/right/top/isometric D3D9 captures. Validation folder contains six-view contact sheets, LOD sheets (each independently auto-framed, not a dimensional overlay) and original wheel isolation views. Real GUI captures are under `gui/`. No donor payloads in review ZIPs.

```powershell
python tools/michelin_scene_lab.py --source-root 'E:/RallyWorkshop_Sources/sources/Michelin Rally Masters' --output .research-output/vehicles/michelin-assembly/new-scenes --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe
python tools/validate_michelin_scenes.py --source-root 'E:/RallyWorkshop_Sources/sources/Michelin Rally Masters' --scenes .research-output/vehicles/michelin-assembly/new-scenes --output .research-output/vehicles/michelin-assembly/new-validation --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe
python tools/rally_workshop.py --source-scene .research-output/vehicles/michelin-assembly/final/Car25A/assembly/scene/scene.json
```

Validation: ten scenes reopen and regenerate with identical scene/manifests and MRPV bytes; all original snapshot hashes verified. Real GUI reopening/rendering succeeds for both cars, native Create disabled. Focused38 PASS, including12 new source-free tests. Full Windows1178 tests OK, two optional skips (see exact final log). Protection audit:11500 files /15448297600 bytes, zero changed/missing. Private validation records and repeat scenes supply source/output hashes. Previous adapters/accepted vehicles are covered by full regression and preservation; this is not a new D3D8 gameplay test.

## Unresolved, and stop boundary

- Original wheel rotation/side matrices under runtime steering/spin and settled suspension, tyre-default selection in a specific race, full units/handedness proof.
- Original glass and dynamic blend/culling/material-light dispatch, camera-dependent LOD transitions, cutout filtering and secondary shading. Grey windows are neutral opaque, not recovered glass parity.
- Damage-target relationship is statically proven, but no deformation animation playback implemented. Cabin-only insideNN archives are referenced by the original loader; outside neutral scenes do not claim the full cockpit camera configuration.
- No complete fleet, native MR addon/CarID, physics adjustment, Blender Bridge or further livery work. Stop after these two neutral scenes for review.
