# Current focused source follow-up —29 October2026

The phase-1 matrix below is preserved as historical audit evidence. Its opaque
Paris-Dakar/Michelin decoder boundaries are superseded only for the explicitly
qualified resources in this focused follow-up:

| Source | Priority | Current local technical readiness |
|---|---|---|
|Paris-Dakar PajeroRED/PajeroSilver|Historical HIGH|L0/L1 source decode PASS; UVSv1+actual textured neutralD3D9 L2WARN; material/runtime pose/parity unknown. Patrol validates decoder generalization.|
|Michelin RAV4/ID25 and Megane F2/ID6|Personal HIGH|38 exact payloads,8XOBJ structures,20TGA decoded; complete assembly/alternate vertices unresolved, L2 NOT TESTED.|

See PARIS_DAKAR_SOURCE_REPORT.md and MICHELIN_SOURCE_REPORT.md. No fleet or
native imports started. Prior first-pilot choice and all earlier work remain
recorded below.

---

# Source Garage — donor format/readiness matrix

28 October2026, `research/vehicles`, inspected clean baseline `b9a24f7`.
All16 configured new-game directories are populated. This is a local-source
finding, not authentication of original retail editions. Exact file identities,
counts, sizes, executable hashes and candidate paths are in
[DONOR_CORPUS_MANIFEST.json](DONOR_CORPUS_MANIFEST.json); the pinned external full
inventory contains every enumerated file rather than only the sample candidates.

## Status vocabulary and evidence scope

**PASS** means the named check passed; **WARN** means useful partial evidence with
explicit unresolved semantics; **FAIL** means a requested check failed;
**UNSUPPORTED** names the selected reader's known missing capability;
**NOT TESTED** means no such test was run; **MISSING INPUT** means required local
input is absent. A reader limitation is not a claim that all tools lack support.

Every present root has a file/signature/hash census. The L0 column below goes
further and describes source/container interpretation; an L0 PASS does not
imply a complete vehicle catalog or every archive parsed. L1 means structural
reconstruction. L2 **WARN diagnostic** means an actual private geometry render
was inspected, with source transforms/materials or renderer behavior unresolved.
It never means original visual parity. Texture-only previews do not qualify
vehicle L2. **Gameplay is NOT TESTED for every new donor in this matrix.**

## Independent priority and technical readiness

| Game / actual platform | Personal / historical priority | Observed resources and representative | L0 interpretation | L1 | L2 | Technical readiness / remaining work |
|---|---|---|---|---|---|---|
| Paris-Dakar Rally2001 / Windows x86 | **Historical HIGH**, Pajero V60/Evolution V20 hypothesis | `dakar.exe`;222 TC files; `PajeroRED.tc`,`PajeroSilver.tc`; loose WAV/AIF; embedded RallyCar/ArchList/Gex names | WARN, TC layout unresolved | UNSUPPORTED by current probe | NOT TESTED | Dedicated section/mesh/texture RE. No geometry relation to MR established. |
| Michelin Rally Masters / Windows x86 | **Personal HIGH**, RAV4/Megane | PDI1 PDO/PDT/DTA; loose Cars.BIN/script joins: ID25 `Toyota RAV 4`→Car25A, ID6 `Renault Megane F2`→Car06A | PASS five PDI directories; identity join WARN | UNSUPPORTED payload/mesh decode | NOT TESTED | Bounded TEA/LZSS decode then XO/vertex semantics. Maxi geometry identity remains open. |
| 4x4 Evolution / Windows x86 | Technical opportunity | POD2→C3DModel/SMF, TRK, RAW/ACT/OPA; Toyota4Runner SR5 | PASS TRUCK.POD directory,1139 members | WARN, body/wheels/UV/materials recovered | WARN diagnostic | Small adapter opportunity; local community Build58/2020 provenance, equipment/pose/alpha semantics unresolved. |
| 4x4 Evolution2 / Windows x86 | Technical opportunity, SUV fit | POD2→SMF/TRK/TIFF; Toyota4Runner SR5 Sport Package2WD | PASS TRUCK.POD directory,1126 members | WARN,33 body objects+six wheel variants | WARN diagnostic | **Proposed first pilot**. Four source placement records; assembly/units/alpha still need qualification. |
| Screamer4x4 / Windows x86 | Technical opportunity, SUV fit | COD_UNIQUE→Mitsubishi_Pajero/Multi DAT body/wheel streams; TEX/32A | PASS Game.cod directory,4100 records | WARN, body885v/1148tri; wheel82v/96tri; UV/normals/material IDs | WARN diagnostic | Feasible parser path; material-ID→texture filename binding, axis/hierarchy/wheel transforms unresolved. |
| V-Rally2 Expert Edition / Windows x86 | Technical opportunity | `rootcars.pak`, CRC-checked physical block1, Eden LZ77, V3D/texture subblocks | PASS selected archive/block | WARN geometry/UV/OBJ/MTL/textures | WARN diagnostic | Wheel/node assembly unresolved; physical block not yet exact display-car identity; exporter license unresolved. |
| Dakar2 / PS2 ELF machine8 | Rally-raid | `SLES_508.79`,SYSTEM.CNF; extracted RES directories named ALL.VSR,*.FEK,*.LVL; inner RBB/SBB/BNK/PHY/STR | WARN filesystem/boot identity; container tree already extracted | NOT TESTED | NOT TESTED | No matching complete model decoder established. Do not parse directory suffixes as unopened archive files. R5900 path separate from PC REA. |
| Rally Championship Xtreme / Windows x86 | Rally | Data/Cars,CarStats; RCX/TEX/COG; loose WAV/MP3 | WARN filename/signature census only | NOT TESTED | NOT TESTED | Source-inspectable matching decoder unresolved. Do not substitute1999 Rally Championship tools. |
| Colin McRae Rally3 / Windows x86 | Rally | Data/Cars; BIG,BGX,COC,TBF,PCX/TAG; DDS; patched executable environment | WARN census only | NOT TESTED | NOT TESTED | iRipper archive/texture claim source-reviewed via docs; old EXE not executed. Mesh/UV/wheels unresolved. |
| Colin McRae Rally04 / Windows x86 | Rally | Data/Cars; BIG,BGX,COC,TBF,P3D; DDS; wrappers present | WARN census only | NOT TESTED | NOT TESTED | Matching archive revision and geometry decoder unqualified; no inference from shared iRipper package label. |
| Colin McRae Rally2005 / Windows x86 | Rally | data/Cars; BIG/TBF/T0X/T1X/T2X/CSC; DDS | WARN census only | NOT TESTED | NOT TESTED | iRipper1.9 documents CMR5 archive/textures; actual model extraction not tested. |
| V-Rally3 / Windows x86 | Rally | Euro/Bnk and Scripts; BNK/DAT/SCN/VMF | WARN census only | NOT TESTED | NOT TESTED | BNK/G2D/G3D candidate tools remain unverified; VR2 success does not transfer. |
| Sega Rally2 Championship / Windows x86 | Rally | BINDATA/DELTA root node/geometry + TXR atlas; loose MDL/TXR/MOT | PASS selected bounded root mesh/texture records | WARN504v/416tri root mesh, material/UV records | WARN diagnostic | SR2Tools source supports inspection; complete node hierarchy and material/texture assembly unresolved. |
| Sega Rally Revo / Windows x86 | Rally | Main_release/cars `205_t16gravel_model.sbf`; LE4 directory;5 DDS, one mesh candidate | WARN9 valid members, unknown types2/3 | NOT TESTED | NOT TESTED | Archive/individual texture path validated. Existing viewer invents zero UVs, insufficient for faithful model export. |
| Colin McRae: DiRT2007 / Windows x86 | **HIGH special vehicles**, complex | PSSG; `131_gen_high.pssg`,223 types/404 attribute entries; Neon names | WARN duplicate attr186 retained | NOT TESTED | NOT TESTED | Separate existing MIT Dirt1 converter exists; no actual export qualified. Early Neon not treated as DiRT2. |
| Colin McRae: DiRT2 / Windows x86 | Special vehicles | PSSG; `350_highLOD.pssg`,152 types/361 attribute entries; matrix-palette schema | PASS selected dictionary only | NOT TESTED | NOT TESTED | Published distinct Ego converter path; scene/rig/shader/texture dependencies untested. |

The16-game audit includes no absent whole-game root at this snapshot. The
configurable scanner still reports **MISSING INPUT** for absent roots, and
individual missing source dependencies remain separate from decoder limitations.
GT3/GT4 remain established supported research adapters; no discovery workload,
compatibility claim or regression of those adapters is implied by this table.

## Editions, versions and catalog limits

Most exact retail edition/region identities are **UNKNOWN**. Multiple language
files, English labels, a directory called Euro or a file-version string do not
authenticate a region. The installations contain modifications/wrappers in
several titles. In particular Evo1's Build58 readme describes a2020 community
patch; Evo2 has TRIHook; CMR3 has SilentPatch; CMR04 has dgVoodoo/DSOAL components.
No pristine-source claim is made for any unchecked archive.

Static executable resource observations: Evo2 `1.00.139`; CMR04 and CMR2005
`1,0,0,0`; DiRT `1,2,0,0`; DiRT2 game `1,1,0,0`; Revo `4,0,6,0`; SR2
`2,0,0,2`; VR2 game `1,0,0,31`. Paris-Dakar and Michelin have no RT_VERSION
in the REA resource inventory. Paris readme says PC ReadMev1.01/24August2001;
Michelin readme is dated16February2000. These are document observations, not
executable revisions. Dakar2 SYSTEM.CNF declares `SLES_508.79`, `VER=1.02`,
`VMODE=PAL`; the latter two are boot configuration fields, not a verified game
version/region catalog. Exact executable byte hashes always take precedence.

Counts of filenames/containers, source catalog entries, decoded triangles and
qualified vehicles have different denominators. No new donor here is playable
in MR. No source audio has been claimed to be a complete original vehicle mix.

## Evidence and next gate

- [Tool audit](DONOR_TOOL_AUDIT.md) and [tool hashes](DONOR_TOOL_SOURCES.json):
  primary sources, authors, exact inspected versions, rights and limitations.
- [Structural smoke results](DONOR_SMOKE_RESULTS.md): five representative PC
  probes, ten-component coverage and private inspected diagnostics.
- [Priority probes](DONOR_PRIORITY_RESULTS.md): historical TC, Michelin
  catalog/PDI and separate Neon/Ego dictionaries, with exact original offsets.
- [Revo probe](DONOR_REVO_RESULTS.md): one actual car SBF and individual DDS.
- [First pilot decision](DONOR_FIRST_PILOT_DECISION.md): proposed Evo2 4Runner,
  trade-offs, known unknowns and success criteria; importer waits for review.
- [Universal Vehicle Scene](UNIVERSAL_VEHICLE_SCENE_PROPOSAL.md): interface
  proposal only. Current shared GT compiler/Classic gate is not universal yet.
- [External layout/reproduction](SOURCE_GARAGE_LAYOUT.md).

This phase ends at the audit. Original games and accepted Workshop projects,
alternative CarID29 rosters and the known30-entry limit remain intact.

## Dakar 2 follow-up — 29 October 2026, Master Plan v7.3

This newer checkpoint supersedes Dakar 2 readiness in the historical phase-1 rows without rewriting that audit. Actual Xbox USA ISO, GameCube GPDE51 RVZ and PS2 SLES_508.79 extraction now inventoried with full hashes. All share RBB/SBB resource families but use different payload layouts. Xbox selected from original native loader/declaration evidence: Pajero and Hino recovered into UVS v1, L1 PASS; L2 WARN for culling/mixed facing and incomplete shader stages. GC/PS2 remain container-only. PS2 original ISO MISSING INPUT. Personal priority remains Pajero, independently of readiness. No new MR import. See DAKAR2_PLATFORM_AUDIT.md, DAKAR2_FORMAT_REPORT.md and DAKAR2_SOURCE_RESULTS.md; exact corpus is DAKAR2_CORPUS_MANIFEST.json.
