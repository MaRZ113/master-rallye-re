# Source Garage — donor tool audit

Research date: **2026-10-28**. Scope: existing extraction and inspection tools for
16 new donor titles. Original game data and third-party tool implementations are
not redistributed here. The existing GT3/GT4 pipelines are outside this discovery
scope. `DONOR_TOOL_SOURCES.json` pins the actual local tool files by SHA-256;
directory suffixes such as `-main` are not commit identifiers.

## Evidence and result boundaries

- **Source reviewed** means the implementation or author's documentation was
  inspected. It does not mean the tool ran against the user's game build.
- **Author claim** identifies advertised behavior that still needs a local test.
- Actual local compatibility, representative hashes, decoded counts and failures
  belong to `DONOR_CORPUS_MANIFEST.json`, the smoke-test reports and
  `DONOR_FORMAT_MATRIX.md`. Those are authoritative over general tool claims.
- `NOT TESTED` is different from `UNSUPPORTED`. A bounded unsuccessful search is
  not proof that no decoder exists anywhere. Archive extraction is L0; a model
  parser is L1; an image is insufficient to establish original rendering parity.

## Tool versions, provenance and redistribution

| Tool | Author / primary source | Inspected version / scope | License / distribution finding |
|---|---|---|---|
| PyPOD | Johnny Shumway / jShum00; [repository](https://github.com/JShum00/PyPOD) | Local README v1.1; `POD_Handling.py`, `Constants.py`; POD1, POD2, POD3 and EPD1 branches | MIT, local LICENSE present. Attribution and license notice accompany copied code. No copying required for this audit. |
| SMFImportExport | Dummiesman; [repository](https://github.com/Dummiesman/SMFImportExport) | Local `SMFImportExport-main/io_scene_smf/__init__.py` v1.1.1, Blender minimum 3.1; separate old loose `io_scene_smf` is v0.0.2 | Source headers explicitly CC BY-NC-SA 3.0. Do not mistake public source for permissively licensed SDK code; no implementation copied. |
| Poddy | Dummiesman; [repository](https://github.com/Dummiesman/Poddy) | Upstream credited by PyPOD; not locally installed/tested in this audit | License/version not independently pinned here; PyPOD's MIT notice does not establish Poddy's license. |
| triraw | Dummiesman; local readme, 2023-01-07 BETA; [community tools notice](https://4x4evolution.net/doku.php?id=start) | Local EXE and readme only; RAW→PNG, common images→RAW/OPA/ACT according to readme | No source/license found in local package. Not executed or bundled. |
| Nice Slice | Local `NiceSlice_005` readme, v0.5 public ALPHA; [community project](https://4x4evolution.net/doku.php?id=start) | Texture tile slicing/RAW/ACT authoring; no mesh reader. Readme calls it extremely buggy and its instructions outdated | Author/license not identified in supplied package. Not needed for read-only donor extraction; not executed or bundled. |
| Z3D_1x_Import | Dummiesman; [repository](https://github.com/Dummiesman/Z3D_1x_Import) | Local v0.0.1; Blender metadata 2.90.1, README says built with 2.91; geometry/materials/textures/matrices/hierarchy for ZModeler v1.x | CC BY-NC-SA 3.0 headers; README acknowledges some ZModeler 2 source-derived code. A conversion bridge, not evidence any donor format is understood. |
| VR2 Asset Explorer | Timo “dr_vannacut” Borg; [author's format reference](https://vannacut.com/2026/08/12/v-rally-2-pc-psx-reverse-engineering-pak-exporter/) | Actual local source 0.6.11, Python 3.11+, Pillow, NumPy; PC/PSX only | No LICENSE/COPYING or explicit grant found in local source package. Link and inspect; do not incorporate or redistribute its implementation without resolving permission. |
| SR2Tools / sr2mdl | Spreit, chmcl95; [repository](https://github.com/Spreit/SR2Tools) | Local changelog v0.6; Blender model addon v0.0.6, Blender 4.0; Python3.12/Pillow/NumPy tool suite | No license file or explicit source grant found in local tree; no implementation copied. |
| Game Extractor | watto studios; [author site](https://www.watto.org/game_extractor.html), [source](https://github.com/wattostudios/GameExtractor) | Source tree pinned to `1d3201e2fff3ba3a7fd0f72b12cb9d0738a89e6a`; selected archive/viewer plugins inspected remotely | Selected source headers GPL v2-or-later; commercial Full and free Basic distributions have different feature sets. Reading source does not establish availability of every preview in Basic. No binary downloaded/executed. |
| Screamer Noesis plugins | Durik256; [author repository](https://github.com/Durik256/Noesis-Plugins) | Source commit `62f052895bbddba980e215e1a9b20052f6821ce7`; `fmt_cod.py`, `fmt_4x4.py`, `tex_tex_32a.py`; author posts 2024-04 | No explicit license found in inspected source headers/repository root. No plugin implementation copied into SDK. Noesis host license is separate. |
| Screamer QuickBMS script | h3x3r; [author's post](https://reshax.com/topic/633-screamer-4x4/) | COD unpacker posted 2024-04-05; version unspecified | No redistribution grant identified in post. Layout independently corroborated by Game Extractor. QuickBMS host license is separate. |
| 3D Object Converter | János Kárpáti; [author site](http://3doc.i3dconverter.com), [author's Screamer announcement](https://reshax.com/topic/633-screamer-4x4/) | Author announced v10.603 Screamer DAT/HEIGHT and selected texture loaders in April2024 | Proprietary tool; not downloaded/executed. Announcement does not establish wheels, hierarchy, native shaders or tested local build. |
| iRipper | David Skotnicki / Racer_S; local original ReadMe and [author homepage](http://www.tocaedit.com) | Local v1.9, 2006-02-24, VB6 binary; earlier CMR3 TAG reader, BIG/TBF/BGX and textures; v1.9 adds CMR5 | Readme says free of charge/use at own risk; no source or general redistribution license found. No binary executed/bundled. |
| Ego PSSG Editor / EgoEngineLibrary | Petar / Ryder25; [current source](https://github.com/EgoEngineModding/Ego-Engine-Modding), [creator's tool page](https://p2t5r.itch.io/ego-pssg-editor) | Creator page latest listed PSSG Editor12.1.1+20240414; .NET6 desktop. Source inspected at `f3fe9ee0f6e8379c64bc4a29e1d1b586bba5d1c1` | Current repository MIT. External dependencies/tool distributions must retain their own notices; no downloaded executable used. |
| sega_rally_2007.bms | Luigi Auriemma; [original script URL](https://aluigi.altervista.org/bms/sega_rally_2007.bms), [author's release reply](https://zenhax.com/viewtopic.php%40t%3D1862.html) | Posted 2015-11-26; original server returned403 during audit, so script bytes/version/license not verified | Use as discovery lead only; independently available Game Extractor source is stronger evidence here. |

Exact tool hashes refer to local bytes, not verified authorship or executable
safety. No old tool binary was executed. The audit uses source inspection and
bounded independent data probes; it does not install plugins into the user's
Blender or overwrite game installations.

## Per-title extraction paths

| Donor title | Archive/container path | Geometry / UV / materials / textures | Wheels, hierarchy, LODs and limitations | Tool assessment before local smoke |
|---|---|---|---|---|
| Paris-Dakar Rally (2001) | No matching existing decoder established by bounded primary-source/tool search. Local `.tc` files require format-specific examination. Generic extension matches are insufficient. | No reviewed existing mesh/texture decoder established. Do not label opaque `.tc` resources as unsupported merely because GT tools cannot read them. | Pajero filenames are leads; V60/V20 identity and any prerelease MR relationship need catalog and geometry evidence. | Existing tool path **NOT TESTED / unresolved**; historical priority remains high. |
| Dakar2: The World's Ultimate Rally (2003) | No verified donor-specific extractor found in bounded search; platform-specific input discovery first. | No established mesh decoder in inspected tools. | Do not infer compatibility from Paris-Dakar name or developer association, or from another console port. | **NOT TESTED / unresolved**; significant RE likely, conditional on actual containers. |
| 4x4 Evolution (2000) | PyPOD/Poddy POD-family extraction; check actual POD magic/version. | Dummiesman SMF addon: C3DModel text meshes, named objects, triangle indices, UVs, reflective/transparent flags, RAW/ACT/OPA textures. | Separate TRK configuration is essential for wheels and vehicle positioning; addon alone is not a complete vehicle assembler. Additional animation frames are skipped. Console SMB is a separate binary layout. | Strong reviewed existing path for PC text SMF; local structural test required. |
| 4x4 Evolution2 (2001) | Same POD-family tools, still verify local revision. | Same SMF importer; v1 material branch, TIF/bump texture support. | **Author documents incorrect imported texture alpha for Evo2**. Do not turn its Blender output into accepted glass/paint semantics. TRK wheel placement and separate wheel files still need qualification. | Strong geometry opportunity with explicit alpha **WARN**. |
| Screamer4x4 (2000) | COD_UNIQUE Game Extractor plugin; h3x3r QuickBMS; Durik256 Noesis COD unpacker. | Separate verticle/faces/mapcoord/norms/textures DAT streams; Durik256 plugin supports positions/triangles/UVs/normals and material IDs; texture plugin for TEX/32/32A. | No verified wheel bones/transforms in mesh plugin. Generic material names are IDs, not complete native material binding. Plugin silently substitutes missing UV/material streams; `.tre` track meshes are a different format. | Feasible bounded reconstruction; completeness must be checked independently. |
| Michelin Rally Masters | Game Extractor `Plugin_PDT_PDI1`: PC PDT/PDI1 directory, PDO payloads and DTA-related resources. Local extension is not the format gate; magic is. | Archive exposure does not decode the inner model semantics. Standard TGA/WAV members are promising; no reviewed complete PDO vehicle mesh importer found. | RAV4/Mégane Maxi identity must be resolved from original scripts/catalog; never guess a CarNN mapping. Nested resources may be compressed/encrypted. | Positive archive research path; geometry **NOT TESTED**. Elevated personal attention independent of readiness. |
| Rally Championship Xtreme (2001) | No matching existing tool established in bounded primary-source search. | No reviewed mesh/texture decoder established. | Do not substitute Mobil1 Rally Championship1999, NetworkQ or Rally Trophy tooling. Local format inspection is required. | **NOT TESTED / unresolved**. |
| Colin McRae Rally3 | Local iRipper1.9 documentation explicitly supports CMR3 resources, TAG reading and BIG-family archive operations; Game Extractor also advertises BIG support. | iRipper textures/INI/TXT/LNG and DDS/TIF conversion are documented. This does **not** establish PCF mesh/UV/hierarchy decoding. | PC/Xbox and PS2 variants need separate gates; iRipper's partial Xbox note is not universal console support. | Archive/texture opportunity; complete vehicle reconstruction **NOT TESTED**. |
| Colin McRae Rally04 | Supplied shared iRipper package is a candidate; local ReadMe does not give a CMR04-specific build guarantee. | Do not extrapolate geometry support from skin editing or CMR3/CMR5 archive claims. | Model layout, wheels, damage states and LODs require exact-build tests. | Candidate archive path, **NOT TESTED** until actual file validation. |
| Colin McRae Rally2005 | iRipper1.9 explicitly adds CMR5; local binary not executed. | Archive and DDS/TIF exposure supported by documentation; complete mesh importer not established in primary-source audit. | Historical conversion credits mention a separate MaxScript, but an unverified conversion asset is not tool provenance and was not downloaded. | Archive/texture opportunity, model decoder remains unresolved. |
| V-Rally2 | VR2 Asset Explorer0.6.11 PC/PSX PAK/PAX+Eden LZ77, logical car/script joins, CRC verification; ZAP/scripts. | Local implementation exposes PC/PSX indexed OBJ/MTL, textures and source sub-blocks; names from ROOTCARS.SCR; high/medium/low outputs. | PSX runtime_shared_texture remains unresolved; animated textures become frame1; unknown auxiliary renderer passes skipped. OBJ does not preserve all source semantics. PC and PSX are separate schemas; no Dreamcast guarantee. | Most comprehensive installed source-inspectable competitor to SMF. Local car smoke required. |
| V-Rally3 | Game-specific BNK/G2D/G3D investigation needed; V-Rally2 tool does not claim support. | No reviewed complete current importer established. A historical author discussion of TDU BNK extraction/G2D/G3D is a lead, not an accepted decoder. | Same studio/BNK extension is insufficient; coordinate/hierarchy/material version remains unknown. | **NOT TESTED / unresolved**; do not mark supported by V-Rally2 success. |
| Sega Rally2 Championship | SR2Tools: PC BIN data and textures; Dreamcast SARC BIN containers separately documented. | sr2mdl0.0.6: nodes, geometry, UV data, material records; texture tools support TXR/BG and partial MTEX per changelog. | Source TODOs include texture autoload, material representation, relation hierarchy and node position/scale updates on save. GUI also contains EXE/DLL patcher, outside audit authorization. | Promising L1 path; selected source/platform must match, no patcher used. |
| Sega Rally Revo | Game Extractor `Plugin_SBF_SBZ1`: SBZ1+zlib, archive directory and texture payloads; Luigi script lead. | `Viewer_SBF_SBZ1_MESH` reads multipart vertices/triangle strips, but sets every UV to zero and explicitly says UV location unknown. Type4 members expose DDS after headers. | Geometry preview is partial. No complete UV/material/wheel/LOD reconstruction established. No evidence its files are PSSG or compatible with Ego tools. | Archive+partial mesh opportunity, full reconstruction **UNSUPPORTED by this specific viewer**. |
| Colin McRae: DiRT (2007) | PSSG, handled separately from DiRT2; inspect exact local node/schema revision. | Current MIT Ego library has an explicit `DirtCarExteriorPssgGltfConverter` for Dirt1, selecting exact VISIBLERENDERNODE. Creator's PSSG editor supports DDS and glTF exports. | This is stronger than a generic EGO claim but still requires a local export. Native shader inputs are not reproduced by glTF and UV-role mappings can be arbitrary. No assumed visual parity. | Concrete source-backed candidate, local reconstruction **NOT TESTED** until exporter is exercised. |
| Colin McRae: DiRT2 (2009) | PSSG; current EgoEngineLibrary and documented older Ryder editor support. | Distinct exterior path uses matrix-palette joint render instances; current creator docs include car glTF/DDS. | Shared texture dependencies, wheel/rig, damage/LOD/livery selection and shader translation must be qualified. Do not transfer a success to DiRT2007. | Strong published tool path; actual local build/export **NOT TESTED** here. |

The table deliberately has no single compatibility score. Historical/personal
priority is recorded separately in the format matrix and pilot decision.

## Static implementation findings relevant to smoke tests

### POD / SMF

The inspected PyPOD loads archives with `rb`, but its convenience `extract()`
joins archive paths to the output directory without containment checks or member
budgets. Its POD2/3 loops do not by themselves enforce the audit's memory budget.
Do not call bulk extraction on unqualified inputs. A bounded table inspector can
validate every selected offset, length and destination before reading a member.

SMFImportExport checks `C3DModel`, reads model/object versions, object visibility,
material flags, vertex/normal/UV fields and triangle indices. Its Blender transform
uses feet-to-metres0.3048 and maps `(x,y,z)` to `(-x,-z,y)`. These are **tool
interpretations**, not independently proven game coordinate semantics. It merges
equal position/normal vertices, preserves UVs on loops and skips extra animation
frames; a source-preserving intermediate should keep original indices and frames.
The old v0.0.2 source and newer v1.1.1 must not be treated as identical.

### Screamer

Durik256's mesh typecheck accepts any `.dat`. Its failure paths create zero UVs or
material0 when companion streams are missing. Require all original companion
streams before calling reconstruction complete. The plugin does not implement
native wheel hierarchy or bind material IDs to original texture paths. The
author's later update corrects UV/normal handling; the initial “faces+vertices”
post is not the final plugin capability.

The COD signature is `->Unique Pc HUNGARY<-` (21bytes), followed by three padding
bytes and a little-endian directory byte count at24. Records begin at28 and
contain name128, absolute offsetu32 and lengthu32 (136bytes total). Check exact
divisibility and all ranges. This wire-layout description is corroborated by
independent tools; no third-party source implementation is copied here.

### Michelin PDI1

At offsets4/8 are counts, at16 the directory offset (46 is only the tool's match bonus), and at20 a
CDI1-related payload base stored four bytes before the base used by the reader.
Directory entries are68bytes: u16 type at0; file types24/25 have relative offset
at12, length at16, filename44 at20. Directory type4 uses signed directory ending
IDs at4/6 and name44 at20. Padding entries are distinct. Files may have a separate
compression/encryption wrapper; raw member discovery alone must not label model
or texture content decoded. Negative/end sentinels and directory bounds need
explicit handling. Original scripts/catalog joins are still required to identify
RAV4 and Mégane Maxi.

### Revo SBZ1

The reviewed archive reader handles SBZ1 with advertised expanded size at4 and
zlib stream at8. The expanded directory has a count at20 and hash/offset pairs
starting24. Member boundaries are sorted offsets plus end-of-file. Type4 members
skip32bytes of member header plus36bytes of texture header before DDS; type1 is a
mesh candidate. The model viewer duplicates triangle faces for two-sided display
and supplies zero UVs. Neither behavior preserves original rendering semantics.
Expansion budgets, exact stream completion and offset overlap checks must be
added around any independent probe.

### Early Neon versus later EGO

The MIT source has separate Dirt1 and Dirt2+ converter paths rather than one
unqualified “PSSG supported” assertion. Dirt1 uses VISIBLERENDERNODE; the later
exterior path consumes matrix-palette joint render streams. The creator's glTF
documentation warns that shader meaning is not exported faithfully and maps
UV0..3 into conventional glTF texture channels as placeholders. Preserve original
shader/stream identifiers and unknowns in a future Universal Vehicle Scene.

## Bounded search record and unresolved work

Queries on2026-10-28 covered each named game with extractor/model/importer/QuickBMS
terms and exact-title variants. Primary GitHub repositories and local supplied
tools were favored over reposts. For Paris-Dakar, Dakar2 and RCX, no matching
source-inspectable complete model tool was established; that is a bounded audit
result, not a claim of global absence. For CMR geometry and V-Rally3, historical
community discussion exists but a legitimate, versioned, tested complete decoder
was not obtained. No unknown binaries or proprietary donor assets were downloaded.

Next technical comparisons should use actual local representative results:
SMF+TRK wheel assembly versus V-Rally2 complete logical car export, then Screamer
material/transform binding. Michelin deserves an early PDI1/catalog probe despite
its lower mesh readiness. Paris-Dakar remains the first historical investigation;
opaque TC reconstruction should not delay delivery of this audit or silently turn
into the first importer implementation. The bounded first adapter is selected in
`DONOR_FIRST_PILOT_DECISION.md`, after these local tests, and requires owner review
before implementation.

## Primary references inspected

- [4x4 Revival format notes](https://4x4evolution.net/doku.php?id=file_formats):
  SMF/console SMB distinction, RAW/ACT/OPA and Evo2 TIF alpha convention.
- [PyPOD source](https://github.com/JShum00/PyPOD) and
  [Dummiesman SMF source](https://github.com/Dummiesman/SMFImportExport).
- [Screamer author discussion](https://reshax.com/topic/633-screamer-4x4/) and
  [Durik256 source](https://github.com/Durik256/Noesis-Plugins/tree/62f052895bbddba980e215e1a9b20052f6821ce7).
- [Michelin PDI1 source](https://github.com/wattostudios/GameExtractor/blob/1d3201e2fff3ba3a7fd0f72b12cb9d0738a89e6a/src/org/watto/ge/plugin/archive/Plugin_PDT_PDI1.java),
  [COD source](https://github.com/wattostudios/GameExtractor/blob/1d3201e2fff3ba3a7fd0f72b12cb9d0738a89e6a/src/org/watto/ge/plugin/archive/Plugin_COD_UNIQUE.java),
  [Revo archive source](https://github.com/wattostudios/GameExtractor/blob/1d3201e2fff3ba3a7fd0f72b12cb9d0738a89e6a/src/org/watto/ge/plugin/archive/Plugin_SBF_SBZ1.java),
  [Revo partial mesh viewer](https://github.com/wattostudios/GameExtractor/blob/1d3201e2fff3ba3a7fd0f72b12cb9d0738a89e6a/src/org/watto/ge/plugin/viewer/Viewer_SBF_SBZ1_MESH.java).
- [VR2 author's reference](https://vannacut.com/2026/08/12/v-rally-2-pc-psx-reverse-engineering-pak-exporter/)
  and actual local0.6.11 README/backend sources.
- [SR2Tools source](https://github.com/Spreit/SR2Tools), local changelog/sr2mdl/SARC sources.
- [Ego source/license](https://github.com/EgoEngineModding/Ego-Engine-Modding/tree/f3fe9ee0f6e8379c64bc4a29e1d1b586bba5d1c1),
  [Dirt1 converter](https://github.com/EgoEngineModding/Ego-Engine-Modding/blob/f3fe9ee0f6e8379c64bc4a29e1d1b586bba5d1c1/src/EgoEngineLibrary/Formats/Pssg/DirtCarExteriorPssgGltfConverter.cs),
  [creator's PSSG Editor documentation](https://p2t5r.itch.io/ego-pssg-editor).

Links are research provenance. Third-party authors' results are not this
repository's local acceptance evidence.

## Dakar 2 follow-up — 29 October 2026

The phase-1 no-decoder finding is historical. New original project source readers qualify the exact Xbox RBB/SBB/HIR/XMD/XTX subset against native x86 loading and D3D8 declarations. Existing UVS v1/D3D9 preview reused; no third-party importer implementation vendored. Pajero/Hino L1 passes, L2 WARN culling and complete shader stages. GC RVZ/FST and PS2 extraction audit do not qualify their mesh pipelines. REA XBE/raw-x86 admission was unavailable; installed Ghidra 12.1.4 used directly, PS2 entry independently cross-checked with Rabbitizer. Full build boundaries, tools, license/use notes, source URLs and unresolved issues: DAKAR2_PLATFORM_AUDIT.md and DAKAR2_FORMAT_REPORT.md.
