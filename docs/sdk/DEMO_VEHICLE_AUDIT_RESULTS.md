# Complete Demo vehicle audit

Read-only milestone, 1 November 2026. Starting checkout: `research/vehicles`,
`7530c525006a6e5778f5dbec40872859c68d96fe`, clean working tree. No branch merge,
original cooking, game installation, DLL/bootstrap edit, physics change or CarID
allocation was performed.

## Result

The examined collection contains **101 family snapshots and 429 model files**,
not101 different vehicles. The first recommended future candidates are the
**9.3.1 Forester, cooked 9.3.1 Rav4, early 8.4.1 WildCat and original 9.3.1 NewRav**. Geometry,
texture completeness and native gameplay readiness are separate decisions.
See [the full matrix](DEMO_VEHICLE_COMPARISON_MATRIX.md) and
[the prioritized shortlist](DEMO_VEHICLE_IMPORT_SHORTLIST.md).

| Examined source | Family snapshots | Interpretation |
|---|---:|---|
| PCG104AXMAS01 vehicle tree | 16 | Includes nested Original; owner-described rebakes, checked against original GXM |
| Nov 2001 vehicle tree | 13 | Includes GXM-only and nested Alpha resources |
| Nov Forester.zip | 2 | 83 members hashed read-only; archival snapshots, not separate cars |
| Original demo-8.4.1 corpus | 16 | Includes Copy of Mercedes and nested lpha/Alpha |
| Original demo-9.3.1 corpus | 13 | Authentic shipped DX availability differs from Nov installation |
| Original demo-9.10.0 corpus | 6 | Later bake comparison reference, not substituted for earlier editions |
| Configured clean retail | 26 | Unpacked resources individually verified against clean Data.sma |
| Accepted SDK import references | 9 | 4Runner, Subaru, Lancer, Mercedes namespace, Pajero85, Trooper, Clio, Silver, Michelin RAV4 |

The matching retail is `D:/Game/Master Rallye/corpora/retail`, derived from the
existing SDK default retail executable and capabilities, **neither demo folder**.
Its Data.sma SHA256 is
`03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f`;
all examined unpacked retail resources matched archive bytes. This is source
provenance, not a runtime executable SHA allowlist.

## Comparison method and limits

Existing Heritage, DX/DXT/GXI, GXM and RDemo comparison readers are reused.
Every local model, texture and sidecar has a source hash/size. Comparisons retain
triangle multiplicity and winding and distinguish position, per-corner UV,
normal/color and material-ownership fingerprints. Vertex numbering, triangle
order and cyclic corner rotation do not create false new geometry. Decoded
texture pixels, dimensions and alpha are compared separately from wrapper bytes.

Native draw-local indices take precedence over a stale global cache. Rev131 is
upgraded only in memory using the qualified prefix conversion. Rev135 is read
directly, including resources rejected by strict authoring checks: their header,
group and collision warnings remain in the report. Rev125/127 comparisons retain
**stored-global-only WARN**, not newly qualified native draw semantics.

Complete native input labels mean resource-role availability, not that strict
Heritage staging or all source validation checks pass. In particular stale
global-table diagnostics remain visible and are not removed by this audit.

GXM triangle/position records are decoded without executing Cooker. Across 79
local matches, the evidenced position correspondence is `(x,y,z) -> (x,z,-y)`.
For GXM-only entries a same-root consensus needs at least two car witnesses and
is explicitly an inferred positional comparison; it does not qualify GXM UV,
hierarchy, visibility, damage playback or cooking. No translation or scale fit
is used to force matches.

Approximate triangle overlap uses 1e-5 source units. Nearest-vertex distances
are bounded samples (up to64 query points /2048 reference points in each
direction), without scaling; RMS is a diagnostic, not a physical size, whole
surface distance or identity proof. A closest unrelated retail/accepted row with
zero overlap is **not** an asset association. In particular, zero exact triangle
matches alone does not prove a genuinely different real-world vehicle.

Of429 model files:221 have decoded native draw surfaces,181 have GXM prefix
records,22 have legacy stored-global-only diagnostics and5 remain unsupported:
`nov-local/JumpAlpha/car.dx` (ambiguous rev131 global-table boundary) and the car/
wheel DXs in `shipped841/Copy of Mercedes/lpha` and `Copy of MercedesAlpha`.
Their GXM evidence is retained. None is silently omitted or called fully cooked.

## Original versus Cooker evidence

83 original/candidate pairs were linked by **identical role-specific GXM bytes**,
not filenames.73 have direct DX buffer/collision comparisons;10 lack a shipped DX
counterpart. Results:20 byte-identical,3 float-drift equivalent,47 structurally
different,3 unresolved. The legacy structurally-different verdict includes
revision headers and draw serialization; it is not a verdict of different body
shape. Canonical decoded surface/UV evidence must also be consulted.

* Main PCG Forester and Nov/original9.3.1 Forester preserve the same car surface,
  UV, normal/color, materials and draw states despite different serialized DX.
  Their original car.gxm hashes match. The directory name does not establish an
 8.4.1 origin for this Forester.
* PCG `Original/Forester/car.dx` is an alternate: same bounds/counts,91.9528%
  quantized triangle overlap with the main car, sampled RMS0.015046. The GXM
  source is identical, but the cause of this alternate bake is unresolved.
  `car111.dx` is byte-identical to main PCG car.dx; complete/wheel also match.
* PCG WildCat8.4.1 matches original8.4.1 car.gxm bytes. Original legacy cache
  versus local draw geometry differs by one approximate triangle (overlap
 0.999394, sampled positional RMS0); this is a legacy/bake boundary, not evidence
  of a new car body.
* Five nested Original families (KiaSportage, megane, Navara, Simmbugghini,
  Wildcat) have all three DX roles byte-identical to the supplied9.10.0 corpus.
  Original/Jump car and wheel do not; complete is absent. Forester and Trooper
  are absent from that9.10 corpus. Their owner-reported9.10 origin is therefore
  not independently proved by the currently available reference.

## Duplicates, renamed sources and actual variants

* Original8.4.1 `Mercedes` and `LandCruiser` have identical car.gxm bytes and
  decoded body/UV evidence. The PCG Mercedes instead matches original
  `Copy of Mercedes`; its decoded car matches the accepted `Mercedes` namespace.
  These names are not evidence for independent new vehicles or brand identity.
* The8.4.1 Alpha aliases split into two car.gxm groups:
  `Copy of Mercedes/lpha` = `Copy of MercedesAlpha`;
  `LandCruiserAlpha` = `Mercedes/lpha` = `MercedesAlpha`.
  Wheel/complete availability and other attributes remain independently listed.
* Local Nov `Wildcat/car.gxm` is identical to9.10 Simmbugghini, not the original
 9.3.1 Wildcat. Use `corpora/demo-9.3.1/.../Wildcat` for the authentic later SUV.
* NewRav and Tata have full three-role native DX sets in the original9.3.1
  corpus, despite missing complete or other DXs in the Nov installation. Original
  source geometry/textures are preferable to inventing replacements.
* Trooper source car surface/UV match across PCG root, Nov and nested Original.
  The accepted Heritage body contains the corresponding source surface with
  authored native states; an additional identity is not justified by filenames.
* Early WildCat, LandCruiser, megane and Tata have meaningful historical body or
  livery variants. Jump is much closer to retail; later KiaSportage/Wildcat
  contain small positional/triangulation differences and are lower priorities.
  Exact figures and side-by-side evidence are in the shortlist and catalog.

## Additional owner-supplied cooked Rav4 9.3.1

`D:/Game/Master Rallye PCG104AXMAS01/DataGx/Vehicles/Rav4` was added while
this audit was being finalized and is included in the **final with-rav4 corpus**.
All33 original GXM/GXI/TXT files match the original9.3.1 Rav4 byte-for-byte:
3 GXM,27 GXI and3 sidecars. All27 derived local DXT pixel arrays equal their
GXI decodes. No texture references are missing. No shipped DX counterpart exists
for these3 roles, hence3 additional MISSING_INPUT cooker-comparison pairs,
not a failed source decode.

| Cooked role | Vertices | Triangles | SHA256 |
|---|---:|---:|---|
| car |2418|1902|75d3a6a37bbeb046408959ddc4e57e31663f6c95fcb39290f01980640e2f0545|
| complete |2608|2366|c45d5da6559c2ab71690105172110ace8a4435227fcd523cd4cb68c2c4e50188|
| wheel |220|252|6cb4f708a52dc25b37470697e63a06d0a2781c2bbc71fd622af5a2a3b8c292ea|

The white/blue source-complete vehicle is textured and assembled in3 actual
D3D9 views in `rav4-preview/`; these are included with the other captures in
`delivery-previews/`. Body bounds extent is1.942616 /1.505594 /4.218722 in
native source-coordinate units (X/Y/Z), not independently qualified metres.
No exact retail or accepted car surface matches were found. Against retail
NewRav:1902 vs1972 body triangles, zero exact/quantized triangle overlap and
unscaled sampled RMS0.127260. The closest sampled retail row is Kangoo, which
is only a numerical nearest-neighbour result, **not a vehicle association**.

All3 native roles are supplied, so this Rav4 is no longer a GXM-only future
cooking task. However, its global index cache disagrees with draw-local indices;
that warning is preserved, not repaired in the original. Body25 tag2 groups
contain no qualified independent glass/brake controllers, and no named local
Rav4 physics row was found in the PCG XML. This is complete, previewable source
input, **not a fully native-authoring-valid or playable candidate**. Rav4Alpha
still lacks complete native inputs. Do not confuse this historical MR Rav4 with
the accepted Michelin RAV4.

## Textures, glass, lights, damage and physics

Local referenced texture inputs are complete except `mastersticker133-tga` in
PCG Original/Simmbugghini, Nov Wildcat and original9.10 Simmbugghini.
A same-name retail DXT exists (SHA256
`1d2ab03e16789ee556f56b242cbf56449ee2405bd4f0712f3ddfea20c168c1b8`),
but authentic source-artwork correspondence is unproved. The audit neither
borrows it nor supplies a placeholder. Unreferenced texture files remain
inventoried and are not misreported as material bindings. `Null` is a sentinel,
not a missing texture. GXI and DXT pixel correspondence is distinct from wrapper
hashes. Native DXT wrappers are not automatically block-compressed DDS.

248 DX entries /206 unique blobs have independent draw/collision inventories.
Primary demo cars expose flat tag2 draws in the examined supported streams;
source text names such as glass/blight do **not** establish working native
breakable glass or brake events. Retail Forester has named screenfront/left/
right/rear and blight states (tag7/tag8); accepted Trooper also has authored
switch/damage states. Retain source glass/lamp geometry and use the existing
bounded native authoring mechanisms in a later reviewed import. Collision tag101,
other tags, validation warnings and sidecar candidates are recorded; collision
presence does not prove equivalent deformation or detached-part playback.

Named `vehicles.xml`/`Modifications.xml` family rows are hashed and inventoried.
They are not proof of original class/CarID, crew/audio association or a safe
retail physics donor. Some Alpha and GXM-only families lack named physics rows.
No physics, suspension, driver identity or runtime registration was changed or
newly qualified. Previously reported Forester/Darren Sutherland identity remains
a separate integration question, not inferred from a texture filename.

## Catalog defects fixed

1. Heritage discovery now walks resource-bearing nested and GXM-only folders.
2. Missing texture sources no longer crash `compare_editions()` or produce a
   false shared-material PASS. Borrowed sibling textures remain explicitly
   unresolved; accepted staging behavior is preserved.
3. Malformed texture input is recorded as INVALID_TEXTURE and blocks staging.
4. Audit texture-reference normalization handles original absolute GXM paths,
   GXI/DXT/TGA suffixes and Null without fake missing entries.
5. Native triangle evidence uses draw-local indices rather than stale caches.
6. RDemo collision comparisons now use pure shared helpers instead of importing
   the absent optional original-cooker oracle. This restored24 previously
   unsupported pair comparisons. Secondary-descriptor permutations remain
   semantically UNRESOLVED and are not confused with core-topology changes.

## Validation and private evidence

Private evidence root: `.research-output/vehicles/demo-audit/`.

* `with-rav4/catalog.json`, `matrix.json`, `shortlist-inputs.json`:101 family records,
  exact resources, comparisons and bounded method annotations. The matrix.json
  and shortlist-inputs.json alongside the catalog use the same final corpus.
* `with-rav4-states/states.json`: independent per-draw state/collision evidence.
* `with-rav4-cooker/cooker-differences.json`:83 GXM-linked pairs.
* `with-rav4/source-contact.png`:66 source snapshot wireframes; per-panel fit,
  not dimension-matched imagery.
* `delivery-previews/textured-contact.png` and `previews.json`:34 selected complete
  models,31 actual textured D3D9 render sets (isometric CW, left CW, isometric
  CCW diagnostic),1 explicitly shared exact-input set and2 missing-input cases.
  No guessed wheel transforms or substitutions.746 baseline and23 new Rav4 input hashes unchanged.
  These are supplied complete-model previews, not race assembly, source-game
  parity or D3D8 qualification. Original931NewRav/Tata/Wildcat are included.
* Source preservation:5330 files /461,860,348 bytes unchanged. Independent
  historical baseline:11,500 files /15,448,297,600 bytes unchanged, no missing
  files. Saves/options are not reset.
* Full Windows regression at the milestone boundary:1303 tests, OK,2 optional
  skips (`full-regression.json`). After the final collision-helper extraction,
 62 focused audit/Heritage/revision-upgrade/feature tests pass
  (`focused-post-collision.json`). Full and focused results have separate
  scopes; no original D3D8 gameplay was exercised by this audit.

## Reproduction

Use a fresh private output directory for each run; the supplied example config
contains paths only, no assets. Accepted reference paths must be supplied from
local private SDK snapshots. Main command derives retail from SDK configuration
and verifies it against the clean archive, rather than accepting a demo as retail.

```powershell
python tools/audit_demo_vehicles.py --config .research-output/vehicles/demo-audit/sources.local.json --output .research-output/vehicles/demo-audit/repeat
python tools/audit_demo_states.py --catalog .research-output/vehicles/demo-audit/repeat/catalog.json --output .research-output/vehicles/demo-audit/repeat-states
python tools/compare_demo_cooker_inputs.py --catalog .research-output/vehicles/demo-audit/repeat/catalog.json --output .research-output/vehicles/demo-audit/repeat-cooker
python tools/preview_demo_audit.py --catalog .research-output/vehicles/demo-audit/repeat/catalog.json --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe --output .research-output/vehicles/demo-audit/repeat-previews
python tools/workshop_tests.py focused --changed src/master_rallye/demo_vehicle_audit.py --module test_dx_revision_upgrade --module test_dx_revision_upgrade_cli
```

No new CarID, installed mod, accepted native project, runtime/DLL change or physics
retune is delivered. Stop for review of the shortlist before another import.
