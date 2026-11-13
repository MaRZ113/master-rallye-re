# Source Garage — historical priorities and Neon/EGO probes

28 October 2026. Actual owner-local sources under
`E:/RallyWorkshop_Sources/sources`; read-only metadata probes only.
Private exact report: `.research-output/vehicles/source-garage/priority-probe-validated.json`.
All 11 selected files retained their SHA256 after inspection. No original game
code was run, no asset exported, no model importer implemented and no MR project
or accepted resource changed.

## Paris-Dakar Rally: retain historical priority

| Original file | Bytes | SHA256 |
|---|---:|---|
| `Data/PajeroRED.tc` | 4,187,796 | `38b1d5ba438b3b384e029ab4feb395907ea7f6436e27dc40efa0ed0e53964d7d` |
| `Data/PajeroSilver.tc` | 4,187,796 | `fe5b111f88309fa8167d9df8a996a8d478c912a2a189126d5534bad3f14a82ae` |

Both begin with an opaque binary header. Literal source observations, with
zero-based decimal file offsets:

- `RallyCar 1.00` at 2048 in both (there is a space before `1.00`).
- First `ArchList` at 2168 in both; 28 occurrences below 10,000 bytes in each.
- `Gex#MainBody.x` at 10240 in both.
- Read-only string inspection also exposes body, body-shadow and wheel resource
  declarations and references ending `.3df`. They are format leads; embedded
  `.x` names alone do not establish an ordinary exportable DirectX `.x` member.

L0 **WARN**: original resources and embedded identifiers confirmed, container
layout unresolved. L1 **UNSUPPORTED**; L2 **NOT TESTED**; Gameplay **NOT TESTED**.
Equal file length and similar identifier positions do not prove equal geometry,
a colorway-only difference or shared source geometry with Master Rallye.
`PajeroRED` / `PajeroSilver` are filename leads; V60 versus Evolution V20 identity
remains unresolved. Do not assign generation from the filename or header text.

Next historical research question: independently map bounded TC sections,
resource tables, mesh and texture payloads, then recover actual topology and
compare original geometry. This is a separate research priority from selecting
the fastest first adapter. No geometry-sharing claim is supported here.

## Michelin Rally Masters: concrete source-backed personal targets

The loose `Server/Data/Cars.BIN` is 38,592 bytes, SHA256
`bb52e07b8287e28003be86ebb4fc700277b14a6af93cea823dd6dc7535bc730b`.
An observed 24-record, 1608-byte stride places a candidate car ID at record+28
and primary label at record+32. This local structural association is useful;
the full record schema and runtime consumer remain undecoded.

| Target source label | Record / offset | Observed ID | Script association | Actual local candidate |
|---|---|---:|---|---|
| `Renault Megane F2` | 0 / 0; label at32 | 6 | `06 A` | `Data/Objects/Car06A.PDO` |
| `Toyota RAV 4` | 18 / 28944; label at28976 | 25 | `25 A` | `Data/Objects/Car25A.PDO` |

The ID/letter pairs occur in the `cars` declaration on line10 of original loose
`Server/Scripts/singlerace.scr` (605 bytes, SHA256
`d2c5cf6d6f236fe284b845c895128a643b3e4e3bd209fb4cd2256a9282b72747`).
This is stronger evidence than guessing vehicle identity from a PDO filename.
It is a static catalog/script/resource association, not proven runtime dispatch.
The original label says **Megane F2**; its identification as the requested
Mégane Maxi geometry still requires actual model reconstruction/inspection.

### Actual PDI1 directory and wrapper smoke tests

An independent metadata reader cross-checked public field descriptions in
[GameExtractor Plugin_PDT_PDI1, pinned commit1d3201e](https://github.com/wattostudios/GameExtractor/blob/1d3201e2fff3ba3a7fd0f72b12cb9d0738a89e6a/src/org/watto/ge/plugin/archive/Plugin_PDT_PDI1.java).
No GPL source or TEA/LZSS implementation was copied; GameExtractor was not run.
Its extension match for PDT does not itself qualify PDO/DTA model reconstruction.

| Original file | Bytes / SHA256 | Used records / file records | Directory / CDI1 offsets |
|---|---|---:|---:|
| `Car01D.PDO` | 230711 / `329ef34d17df87ad2d2e68f3eeef8fb11247a0097da6754630af64ef8651c221` | 22 /20 | 34 /2210 |
| `Car06A.PDO` | 241685 / `f0a9400812814620832b4a3fe98a024318de72b929ba225a90c4a57e342e1a5b` | 22 /20 | 34 /2210 |
| `Car25A.PDO` | 210875 / `bbbc58fe11456369231e595444d43377f94cc3f19af2e2057a4ec68a07802593` | 20 /18 | 34 /2210 |
| `Track01_long.PDT` | 3277897 / `09cb688f6f29db1a0f210c68206eb1d2cc7cb6dfbfee1305c62737acbe8330e3` | 134 /133 | 50 /10930 |
| `RallyMasters.DTA` | 36586950 / `e3fc64fdf2647041d8f1795dda8557075a0573b39b6a2a4e90fa1d53f5f2713c` | 1051 /956 | 162 /71970 |

All five **PASS** the bounded directory/header/wrapper-range probe. Counts at
header+8 include both files and directories, excluding padding; they are not a
directory count. Header+4 includes padding records. Directory offset is read
from header+16 and validated against the complete record span. The community
reader's match bonus for46 is not a mandatory layout rule: these actual files
use34,50 and162.

The probe validates `PDI1`, the fixed68-byte directory-record boundaries,
record names, record types, disjoint encoded ranges, `CDI1`, and encoded wrapper
length/flags. It retains raw directory-link words without claiming a fully
reconstructed virtual hierarchy. For these inputs the stored CDI1 offset plus
relative record offset begins a bounded record span; the wrapper starts four
bytes later. The published exporter additionally accounts for a12-byte
overhead. These spans are metadata observations, not a standalone asset export.

Both target PDOs expose four numbered `.XO` records (`_0` through `_3`), four
corresponding `_VERTEX.BIN` records, `INDEX.TOC`, and named `.TGA` records.
They are candidate models/LODs and textures until decoded, not four confirmed
usable LOD meshes. Most payload flags are17 (community reader associates TEA
and LZSS8); the chassis image has flag16 (TEA). Payload decoding was **NOT
TESTED**. No image dimensions, wheel positions, UVs, hierarchy, actual materials
or transparent roles are recovered merely from the directory.

Michelin readiness: L0 **PASS** for these container directories, identity join
**WARN** with the explicit static boundary above; L1 **UNSUPPORTED** pending
validated encryption/compression and XO/vertex decoding; L2 and Gameplay **NOT
TESTED**. Keep early research attention on RAV4/ID25 and Megane/ID6. The first
remaining gate is a bounded original payload decode, followed by structural
mesh/texture inspection; this task stops before that implementation.

## DiRT 2007 and DiRT 2: same magic, distinct dictionaries

| Original representative | Bytes / SHA256 | Dictionary result |
|---|---|---|
| DiRT `cars/131/131_gen_high.pssg` | 3260900 / `a5c558b70e1f25fb232584e5040383c42729084b6c08b45f0e62dffc94eaa9a5` | 223 node types;404 attribute entries; ends at14190; **WARN** |
| DiRT2 `cars/350/350_highLOD.pssg` | 2535477 / `67233a1d98b12aa5e1e175ab3614a6d1d3fd88ba5694ec0948d2ee9380859187` | 152 node types;361 attribute entries; ends at11567; **PASS** |

Both have `PSSG` and a big-endian size field at+4 equal to file size minus8;
the attribute-entry and node-type counts are at+8/+12. The metadata probe reads
only the bounded dictionary, not the following scene or binary payloads.

The DiRT2007 dictionary begins `/`, `NEANIMTARGETS`, `NETARGETREF` and includes
Neon animation names. It also declares `VISIBLERENDERNODE`. Its
`PNTEXTURESETTINGS` declares attribute186 twice for `realwidth` and `realheight`,
leaving185 absent. Both occurrences are retained; lookup ambiguity is reported,
not silently overwritten or repaired.

The DiRT2 dictionary begins `CHANNELREF`, `KEYS`, `ANIMATIONCHANNELDATABLOCK`;
it includes `MATRIXPALETTEJOINTRENDERINSTANCE` and `PSSGMESH`. These are declared
type dictionaries, not evidence that every declared type occurs in this model.
Different dictionary structure and renderer associations require separate
qualification. A modern tool with explicit DiRT1 code is a meaningful candidate,
but this probe does not qualify its export:
[Ego Engine Modding's separate DiRT exterior conversion paths](https://github.com/EgoEngineModding/Ego-Engine-Modding/blob/f3fe9ee0f6e8379c64bc4a29e1d1b586bba5d1c1/src/EgoEngineLibrary/Formats/Pssg/DirtCarExteriorPssgGltfConverter.cs).

For both selected files, source header/dictionary observations are L0; body
geometry, wheels, UVs, materials, textures and scene reconstruction are **NOT
TESTED**, as are L2 and Gameplay. Codes131 and350 are source path identifiers;
no exact vehicle identity is inferred here.

## Reproduction and checks

From this checkout:

```powershell
python tools/source_garage_priority_probe.py --sources-root E:/RallyWorkshop_Sources/sources --output .research-output/vehicles/source-garage/priority-probe-next.json
python -m unittest discover -s tests/synthetic -p test_source_garage_priority_probe.py -v
```

Ten synthetic tests **PASS**: malformed PDI directory/ranges, path names,
overlaps, compression budgets/flags, variable directory positions, PSSG byte
size/string/count budgets, duplicate dictionary preservation, explicit missing
sources, source-read/output isolation and unqualified catalog rejection.
Fixtures are invented metadata only. The private report binds the probe SHA256
and original file hashes and preserves per-file status. No rendered previews
were possible in this bounded probe; screenshot or gameplay acceptance is not
claimed. Tool research, observed file structure and inferred catalog layout
remain separate in the report.
