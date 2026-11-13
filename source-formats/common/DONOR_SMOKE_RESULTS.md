# Evo2 TIFF correction and later pilot checkpoint — 28 October 2026

The phase-1 report below is preserved as historical evidence. Its Evo2 diffuse
row describes Pillow's converted output (alpha 255), not the complete original
TIFF channel layout. Original ART/4RunnerSR5.TIF stores two 8-bit samples with
palette photometric and ExtraSamples=0 (unspecified). Pillow P-to-RGBA discarded
the second sample; opaque output does not establish source alpha semantics.
The later bounded pilot preserves both samples, original 16-bit palette and
entire TIFF, plus bump/other raw channels and malformed tail-IFD warnings.
See [static evidence](EVO2_SOURCE_SEMANTICS.md) and
[adapter results](EVO2_SOURCE_ADAPTER_RESULTS.md). The historical audit's L2
diagnostics remain distinct from the later assembled textured D3D9 preview.

---

# Source Garage: historical real-file smoke results

Date: 2026-10-28. Scope: private donor inspection, no MR-native authoring,
adapter integration, game launch, accepted project change or gameplay claim.
These are exact local collection samples; see `DONOR_CORPUS_MANIFEST.json` for
edition/patch evidence. In particular, the Evo1 installation advertises a
community Build 58 patch: its archive is not represented as untouched retail.
Evo2's executable version/installed hooks likewise do not authenticate every
asset against an original disc.

## Qualification result

| Source / exact representative | L0 | L1 | L2 | Gameplay |
|---|---|---|---|---|
| 4x4 Evolution PC, `T4RSR52.TRK` / `4RSR5.SMF` | PASS POD2 directory | WARN body, wheel variants, UV/material records and indexed textures | WARN diagnostic wireframe/atlas inspected | NOT TESTED |
| 4x4 Evolution 2 PC, `T4RSR52.TRK` / `4RUNNERSR5.SMF` | PASS POD2 directory | WARN body, wheel variants, UV/material records and TIFF | WARN diagnostic wireframe/atlas inspected | NOT TESTED |
| Screamer 4x4 PC, `car/Mitsubishi_Pajero/Multi` | PASS COD directory | WARN body/wheel DAT streams, per-corner UV/normals/material IDs | WARN local geometry and standalone TEX inspected | NOT TESTED |
| V-Rally 2 Expert Edition PC, physical `rootcars.pak` block 1 | PASS PAK directory and all six selected stored CRCs | WARN V3D types 5/6/2 and texture pages | WARN geometry/texture diagnostics inspected | NOT TESTED |
| Sega Rally 2 PC, `BINDATA/DELTA/r_delta.mdl` root node only | PASS loose MDL layout | WARN one root mesh and separate RTEX565 atlas | WARN root geometry/atlas inspected | NOT TESTED |

`WARN` means useful partial evidence with unresolved semantics, not a supported
complete adapter. Automated run reports deliberately emit `L2: NOT TESTED`;
the subsequent `view_image` inspection is recorded separately in private
`visual_review.json`. No screenshot, OBJ, wireframe or texture atlas establishes
source-game parity. No native source-game render was compared in this work.

## Recovered structure and boundaries

Both Evo catalog records explicitly name **Toyota 4Runner SR5 Sport Package 2WD**,
model year 2000, Standard SUV. This is the inspected donor identity; choosing
a 4WD catalog record later would be a separate source selection.

| Requested element | Evo1 / Evo2 | Screamer Pajero | V-Rally 2 block 1 | SR2 Delta |
|---|---|---|---|---|
| Body / hierarchy | 33 named objects each; flat source object order/visibility preserved; parent hierarchy unknown | Body arrays recovered; scene graph unknown | 14 meshes in sub2; node transforms unknown | Root node mesh only; remaining graph not traversed |
| Wheels / placement | Six wheel model candidates parsed and retained privately; four explicit TRK placements | One `kerek` wheel mesh; transforms unknown | Local wheel geometry apparent; placement unresolved, diagnostic overlaps origin | NOT TESTED |
| UV | Every SMF vertex's original UV retained | Complete per-corner stream retained; plugin reverses corners but runtime ordering not qualified | UV streams exported; special auxiliary streams skipped | Root mesh's eight-float vertices retain UV |
| Original materials | Six source text fields plus `v1` bump filename preserved | IDs 1, 2, 3 retained; ID-to-filename mapping unknown | Named page/special slots; runtime shared slots unresolved | Raw material bytes retained |
| Diffuse / alpha | Evo1 RAW+768-byte ACT+OPA decoded, alpha 0..255; Evo2 512-square TIFF decode alpha 255 only | Separate RGB565/ARGB1555 TEX base images decoded; unknown format 8 not guessed | Four + two RGBA pages decoded | Separate 256-square RTEX RGB565 decoded |
| Lamps / decals / glass | Names such as GlassI/E and Light* retained; optional equipment/renderer behavior unqualified | Geometry/data retained, surface roles unqualified | Runtime remapped slots not resolved | NOT TESTED |
| LOD | `lod_info_raw` retained; suffix-0 sibling parsed as candidate, runtime role unknown | Related folders exist; LOD role not assigned | Sub2/sub4/sub5 exported as separate physical resources; exact runtime selection unqualified | Other files discovered, not qualified |
| Variants / colors | Catalog text and candidate models retained; source color selection not implemented | Named color texture directories discovered; no variant selection reconstructed | Physical block identity only; logical display name not established here | Dirt/body atlas siblings discovered, not reconstructed |
| Scale / coordinates | Raw positions retained; importer/explicit TRK light annotations suggest feet, not independently measured | Unknown; apparent rotation in wireframe is diagnostic projection, not source orientation proof | Raw source meshes; no wheel node assembly | Raw local root mesh, source transform fields retained |
| Provenance | Whole POD + selected member offsets/sizes/SHA-256 | Whole COD + selected stream offsets/sizes/SHA-256 | Whole PAK + stored/decoded subblock hashes and CRCs | Loose MDL/TXR hashes and byte sizes |

Evo1 body: 1,682 vertices, 1,971 triangles. Suffix-0 candidate: 17 objects,
468 vertices, 483 triangles. Evo2 body: 2,089 vertices, 1,967 triangles.
Suffix-0 candidate: 26 objects, 691 vertices, 541 triangles. Counts include all
source objects, including optional accessories and lamps; the wireframe plots
all source-visible objects together without choosing runtime equipment.

The four source TRK wheel positions, unchanged in both samples, are
`(+2.470,-0.600,+4.790)`, `(-2.470,-0.600,+4.790)`,
`(+2.455,-0.600,-4.090)`, `(-2.455,-0.600,-4.090)`.
They are retained as source values, not declared MR fitment coordinates.
The `08/12/16` left/right wheel candidates are inspected as named variants;
their numeric suffixes do not authorize an automatic runtime choice.

Screamer body: 885 vertices, 1,148 triangles; local wheel: 82 vertices,
96 triangles. Required `verticle.dat`, `faces.dat`, `mapcoord.dat`, `norms.dat`,
`textures.dat` streams have exact length/count/index checks. Missing UV or
material streams fail instead of silently creating zero UVs/material 0.
The supplied Noesis plugin was read as format research, not executed or copied.

V-Rally 2 sub2: type 5/version 0x12, 2,809 positions, 2,653 exported triangles,
4,106 UV entries, 18 auxiliary primitives skipped. Sub4: type 6/version 0x12,
2,653 triangles, 15 auxiliary primitives skipped. Sub5: type 2/version 0x12,
1,107 triangles, 15 auxiliary primitives skipped. The exporter also excludes
short/degenerate strips (counts in private report). Geometry diagnostics have
local wheel components concentrated at the origin; they are not assembled
source vehicles. Six selected subblocks passed stored-data CRC checks and
bounded decompression. No conclusion about all 29 blocks follows from block 1.

SR2 root mesh: 504 vertices, 416 triangles. The explicit scope is the node
referenced by the MDL header, not a complete vehicle. The wireframe resembles
a body shell and the decoded atlas has recognizable Martini/lamp graphics;
neither observation proves the material binding or missing wheel assembly.

## Exact source identities

| Source file | Bytes | SHA-256 |
|---|---:|---|
| Evo1 `TRUCK.POD` | 63,107,623 | `5f50314eeb0ff244a9a131a1bde671c05775db148be363c6af95b819a70767ea` |
| Evo2 `TRUCK.POD` | 144,691,121 | `5669509d709193621802a43c2c63b32e537fcf93ea3fd5d94af8c66947be6a41` |
| Screamer `Game.cod` | 426,327,547 | `4c0af2ac4ba6967558792837cf017af2e98bc6386a59e365d0f090942778b411` |
| VR2 `rootcars.pak` | 44,294,144 | `f7ef975324a2852ce3bb390663052b69ab64326ff7ea5aba76cf4bda92ca924e` |
| SR2 `DELTA/r_delta.mdl` | 72,096 | `1b3ca8fe3f3539abf1874d163ee9d046629711c6a85f51c9b033bbf7a8c1650c` |

POD member census is archive discovery, not playable vehicle counts:
Evo1 TRUCK has 1,139 members (356 SMF, 235 RAW, 235 ACT, 139 OPA, 174 TRK).
Evo2 TRUCK has 1,126 members (321 SMF, 641 TIFF, 150 TRK, 5 ACT, 5 RAW,
3 OPA, 1 VOX). Screamer Game.cod has 4,100 directory records. Full private
reports record selected-member hashes; proprietary bytes remain outside Git.

Evo2 pilot-specific model `MODELS/4RUNNERSR5.SMF`: 171,308 bytes, SHA-256
`a7f71e0ae1cae2fb64438ce8614bf7db47eb9dfc813d926388da4dfef7b6a11e`;
`TRUCK/T4RSR52.TRK`: 6,674 bytes, SHA-256
`d2ff6c5914e8102116e56704dac800442fed3adfbf42326c6b3311517e8bbcb4`.
POD's stored member checksum algorithm was not qualified, so its field is
retained with `checksum_validation: NOT TESTED`; SHA-256 is independently computed.

## Reproduction and safety

Utility: `tools/source_garage_smoke.py`. Tests:
`tests/synthetic/test_source_garage_smoke.py` (15 asset-independent tests passed
under Python 3.11). Rendering/PNG/TIFF needs Pillow; the supplied VR2 source
also needs NumPy. Runs used the existing bundled Codex Python environment;
no package or legacy executable installation was required.

Example commands from repository root; **replace each output with a fresh
directory** on rerun:

```powershell
$probePython = 'C:/Users/MaRZ/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $probePython tools/source_garage_smoke.py evo --config research/vehicles/source-garage/roots.example.json --protected-root E:/RallyWorkshop_Sources/tools --source 'E:/RallyWorkshop_Sources/sources/4x4 Evo 2' --output E:/RallyWorkshop_Sources/research/source-garage-next/evo2 --model 4RUNNERSR5 --truck T4RSR52
& $probePython tools/source_garage_smoke.py cod --config research/vehicles/source-garage/roots.example.json --protected-root E:/RallyWorkshop_Sources/tools --source 'E:/RallyWorkshop_Sources/sources/Screamer 4x4/Game.cod' --output E:/RallyWorkshop_Sources/research/source-garage-next/screamer
& $probePython tools/source_garage_smoke.py vr2 --config research/vehicles/source-garage/roots.example.json --protected-root E:/RallyWorkshop_Sources/tools --source 'E:/RallyWorkshop_Sources/sources/V-Rally 2/V-Rally2 Expert Edition/CDEuro/rootcars.pak' --tool E:/RallyWorkshop_Sources/tools/VR2_Asset_Explorer_v0.6.11_source/vr2_asset_explorer --output E:/RallyWorkshop_Sources/research/source-garage-next/vr2 --block 1
& $probePython tools/source_garage_smoke.py sr2 --config research/vehicles/source-garage/roots.example.json --protected-root E:/RallyWorkshop_Sources/tools --source 'E:/RallyWorkshop_Sources/sources/Sega Rally Championship 2/BINDATA/DELTA/r_delta.mdl' --output E:/RallyWorkshop_Sources/research/source-garage-next/sr2
py -3.11 -m unittest discover -s tests/synthetic -p test_source_garage_smoke.py -v
```

All configured source roots, the configured base and extra protected roots
are excluded from output. Choose `--protected-root` for the complete shared
tools directory as above; add others when the configuration changes. Output
must be new and disjoint, including not being an ancestor of an input root.
Input/output ancestor symlinks, Windows reparse points and junctions are
rejected. Readers verify size/mtime stability before/after reads, bound files
to 512 MiB and representative members to 32 MiB, check array counts/ranges,
reject non-finite geometry and traversal/duplicate/overlap names, and do not
chmod, patch, repair or execute source-game files. Tests include malformed
streams, truncated payloads, allocation-count rejection, no silent alpha loss,
ancestor-link rejection, read-time mutation detection, and unchanged source
bytes/size/mtime/directory entries.

VR2 runs use only the inspected Python modules with exact SHA-256 allowlist;
optional native helpers are refused. Explorer UI identifies itself as 0.6.11;
its backend initializer separately says 6.2.1, so the source hashes are the
reproducible identity. Final utility disables Python bytecode writes before
external imports. Initial research imports created backend `__pycache__` in
the supplied tool tree; original donor-game files were never written, and
possibly pre-existing tool cache files were not deleted.

PyPOD source is MIT; its local `Constants.py` references `@dataclass` without
an import, so the GUI was not treated as run-qualified. Our POD2 directory
probe uses format fields independently and is not a copied extractor.
SMFImportExport is CC BY-NC-SA 3.0, with an upstream Evo2 texture-alpha warning;
no add-on code is vendored. `io_scene_smf` is for 4x4 Evolution, not Screamer.
Durik256 Noesis sources have no located redistribution license grant and were
read only as format references at commit
`62f052895bbddba980e215e1a9b20052f6821ce7`. No plugin source is bundled.
SR2Tools `texture_tool.detect_texture_type` opens its input `r+b`; that path
was deliberately not run on originals. `triraw.exe` was not executed.
See `DONOR_TOOL_AUDIT.md` for URLs, authors and redistribution boundaries.

## Private outputs and inspection notes

Root: `E:/RallyWorkshop_Sources/research/source-garage-20261028/`.

| Final probe directory | Key private files |
|---|---|
| `evo1-final` | `report.json`, body/suffix-0/wheel source-structure JSON, `body_wireframe.png`, `4RSR5.png` |
| `evo2-final` | `report.json`, body/suffix-0/wheel source-structure JSON, `body_wireframe.png`, `4RunnerSR5.png` |
| `screamer-pajero` | `report.json`, directory metadata, `pajero_body_source_structure.json`, `pajero_wheel_source_structure.json`, wireframes and standalone texture PNGs |
| `vr2-block1-reviewed` | `report.json`, sub2/sub4/sub5 OBJ/MTL, six PNG pages, `body_wireframe.png` |
| `sr2-delta-root` | `report.json`, `root_mesh_source_structure.json`, `root_mesh_wireframe.png`, `body_texture.png` |
| root | `texture_contact_sheet.png`, `visual_review.json` |

Wireframes intentionally retain local coordinates; they do not resolve optional
components, axis conventions, wheel transforms, skinning or runtime passes.
Screamer's apparent near-vertical orientation is explicitly unqualified. Atlas
inspection found recognizable source vehicle surfaces, but no complete textured
vehicle was rendered. Raw decoded proprietary geometry, textures and previews
are excluded from source-only review archives. No first cross-game importer
has been started; this evidence supports the next pilot review only.
