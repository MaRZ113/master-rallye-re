# Michelin Rally Masters — bounded source payload and geometry research

29 October 2026. Parent milestone: Paris-Dakar Source Lab. This secondary
investigation advances the accepted PDI1 directory proof without starting a
Michelin vehicle importer or an MR-native conversion.

## Result and qualification boundary

**PASS:** both selected original PDOs yield 38 exact decoded files: 20 indexed
TGA textures, eight XOBJ models, eight external vertex streams and two PTOCs.
Every compressed member consumes its complete encoded span and produces exactly
its declared decoded length. All original source files retain their hashes,
sizes and modification times.

**WARN L1:** eight XOBJs now have validated positions, triangle indices, indexed
normals, inline corner UVs and original texture-name tables. Unknown source
fields remain explicit. This is actual structural reconstruction, beyond names
or strings. It does not qualify a complete vehicle assembly.

**NOT TESTED L2:** the private texture contact sheets are inspected decoded-image
evidence, not rendered vehicle previews. Wheel resources, wheel hub transforms,
runtime material interpretation, coordinate normalization and original renderer
behavior are unresolved. No Universal Vehicle Scene adapter is claimed for this
title yet. **MR integration and gameplay: NOT TESTED.**

## Original inputs and identity evidence

Actual owner-local root:
`E:/RallyWorkshop_Sources/sources/Michelin Rally Masters`.
Windows x86 installation; exact commercial edition and region are not newly
authenticated by this research. Existing Source Garage corpus metadata remains
the broader installation inventory.

| Relative original path | Bytes | SHA-256 |
|---|---:|---|
| `Data/Objects/Car25A.PDO` | 210875 | `bbbc58fe11456369231e595444d43377f94cc3f19af2e2057a4ec68a07802593` |
| `Data/Objects/Car06A.PDO` | 241685 | `f0a9400812814620832b4a3fe98a024318de72b929ba225a90c4a57e342e1a5b` |
| `RallyMasters.EXE` | 1261568 | `71c6c36505102e75518a7f6843bbc8355f205e439086e389ec877225e3e0a8ae` |
| `Server/Data/Cars.BIN` | 38592 | `bb52e07b8287e28003be86ebb4fc700277b14a6af93cea823dd6dc7535bc730b` |
| `Server/Scripts/singlerace.scr` | 605 | `d2c5cf6d6f236fe284b845c895128a643b3e4e3bd209fb4cd2256a9282b72747` |

The observed 1608-byte Cars.BIN records associate ID6 with **Renault Megane F2**
(record offset0, ID at28, label at32) and ID25 with **Toyota RAV 4** (record
offset28944, ID at28972, label at28976). The literal `cars` row in
`singlerace.scr` contains `06 A` and `25 A`, supporting the selected A variants
and their Car06A/Car25A archive names. These are static catalog/script joins;
the full native catalog consumer is not traced. **Mégane Maxi identity remains
unproven** and is not substituted for the original F2 label.

The current report records these source labels, offsets, source-file hashes and
script pairs in machine-readable `catalog_evidence`. Missing optional catalog
inputs are reported as MISSING INPUT rather than fabricated.

## PDI1 and payload wire evidence

Both files have PDI1 headers, 32 directory slots, directory offset34 and CDI1
offset2210. Toyota uses20 records, Renault22; the remaining entry types are
padding. Records are68 bytes. Types4/24/25 represent observed directory/file
records. File relative offset and length are u32 at record+12/+16; the original
flat filename occupies record+20..+63. All record bytes and directory links are
retained. Directory nesting/end-sentinel semantics are still unresolved, so the
probe exports stable flat names rather than inventing virtual hierarchy.

A file's span starts at `CDI1 offset + relative offset`. The first four bytes
are retained as a separate prefix. At span+4 are decoded length u32, zero u16
and flags u16. Encoded bytes occupy span+12 through the exact span end. The
selected archives have flags16 (TEA only, CHASSI1.TGA) and17 (TEA plus LZSS).
There is no reading past the selected member to round a cipher buffer upward.

The selected payloads decode with standard TEA32 using little-endian words and
independent eight-byte blocks, key `THEEVENTHORIZONS`. Final zero to seven bytes
are retained unchanged. This is validated against complete payload parsing,
including all source texture dimensions and all XOBJ section ranges. The key
literal also occurs in the original executable at file offset1160176
(`0x11b3f0`). That literal is corroboration, not a traced runtime call chain.

The subsequent LZSS stream uses a4096-byte zero-initialized ring, initial write
cursor4078, LSB-first groups of eight flags, one-byte literals and two-byte
back-references. A reference's low byte and high nibble form its12-bit offset;
the low nibble plus3 gives its length. Overlapping references are copied through
the ring. Exact input consumption, exact expanded length and bounded allocation
are required. Truncated streams are errors; no synthetic zero-fill is accepted.

The implementation is independent source code using published cipher and
conventional compression operations. The pinned Game Extractor
[PDI1 reader](https://github.com/wattostudios/GameExtractor/blob/1d3201e2fff3ba3a7fd0f72b12cb9d0738a89e6a/src/org/watto/ge/plugin/archive/Plugin_PDT_PDI1.java)
was a wire-format research lead. Its archive/exporter source headers specify
GPL v2-or-later. No Game Extractor source, binary or implementation is vendored
or redistributed. The local reader adds independent range, budget and exact
completion validation. Other keys, wrapper flags and padding arrangements are
outside this qualification.

## XOBJ structural proof

The decoded `.XO` payloads begin `XOBJ`, not a guessed DirectX format. Their
76-byte header contains four count/offset/length triples at28,40,52 and64:

| Section | Observed stride / content |
|---|---|
| Triangles | 108 bytes per triangle |
| Positions | 12 bytes, little-endian xyz floats |
| Indexed normals | 12 bytes, little-endian xyz floats |
| Texture names | NUL-terminated original ASCII names, followed by N zero bytes for N names |

All four sections are contiguous and end at the exact decoded file boundary.
Within each108-byte record, offsets24/36 hold three position/normal indices;
offset84 holds six finite UV floats. At4 is a finite face-normal vector.
Cross-products of the stored position winding agree in sign with those normals
for all nondegenerate triangles in all eight models. One degenerate triangle
in Renault model0 and one in model3 are retained, not repaired.

At80 is a candidate texture index with values0..N. Zero-as-untextured and
1..N-as-texture-table-index is a plausible interpretation, **not a qualified
native material contract**. Other flags, colors and prefix fields are preserved
explicitly; notably Renault model3 contains nonzero data in fields often zero
in other variants. No renderer behavior or cleanup is inferred from those bits.

| Vehicle / model | Triangles | Positions | Indexed normals | Texture names |
|---|---:|---:|---:|---:|
| Toyota `CAR25A_0.XO` | 652 | 334 | 512 | 9 |
| Toyota `CAR25A_1.XO` | 652 | 334 | 512 | 9 |
| Toyota `CAR25A_2.XO` | 314 | 168 | 266 | 6 |
| Toyota `CAR25A_3.XO` | 314 | 168 | 266 | 6 |
| Renault `CAR06A_0.XO` | 908 | 457 | 850 | 11 |
| Renault `CAR06A_1.XO` | 774 | 403 | 748 | 11 |
| Renault `CAR06A_2.XO` | 328 | 178 | 299 | 7 |
| Renault `CAR06A_3.XO` | 177 | 107 | 157 | 7 |

Toyota models0 and1 are byte-identical after decode, SHA-256
`9e84cead4d277a3d0e5e9a564414c8e1e1a47f56137d4c6edf2a80e013aa3373`.
The lower Toyota pair has identical counts/bounds but different flags/payload
hashes. Original PTOCs retain `PTOC`, header value5 and four matching XO names.
Selection thresholds, model-state meaning and full PTOC record layout remain
unqualified; filename suffixes are not automatically promoted to proven LOD or
damage roles.

The eight `_VERTEX.BIN` payloads contain finite float triples with counts matching
the corresponding XOBJ position sections. **They are not the same positions.**
Maximum coordinate differences are0.17037904262542725 for Toyota models0/1 and
0.13450974225997925 for2/3; Renault differences are0.38999974727630615 for0/1 and
0.22999978065490723 for2/3, in unqualified source units. Both originals remain
separate. This does not establish which stream is the runtime rest/damaged pose.

High-model bounds are:

| Model | x min/max | y min/max | z min/max |
|---|---|---|---|
| Toyota0 | -0.8455364704 /0.8455364704 | -0.2446545213 /1.1342718601 | -1.9915921688 /1.7128062248 |
| Renault0 | -0.9227492213 /0.9227492213 | -0.2134402692 /0.9063184261 | -2.0986509323 /1.7349134684 |

These are decoded object bounds, not full assembled vehicle dimensions. Axis
roles, handedness and real-world units are not independently established.

## Textures and private evidence

All20 decoded textures load as indexed TGAs in Pillow. The bounded reader
separately validates image type1, index8, BGR24 palette with256 entries, exact
pixel extent and any standard26-byte footer. Original bytes, palette and index
hashes are preserved. Toyota body textures are LEFT/RIGHT/BACK256×128,
TOP128×256 and FRONT256×256. Renault side textures are256×128, FRONT256×256,
BACK256×64, TOP128×256 and SPOIL128×32. Both archives also contain original
helmet/body/pillar/chassis textures; Renault has AVGASROR32×32.

Several descriptor bytes declare eight attribute bits despite a24-bit palette
and8-bit indices. The reader does **not** invent a decoded alpha channel,
convert black pixels into holes or infer glass from a dark image region.
Unknown palette/descriptor/runtime transparency semantics remain visible.

Private evidence root:
`.research-output/vehicles/paris-dakar-source/michelin/`:

- `qualified-final/report.json`: original hashes, encoded/decoded member hashes,
  offsets, exact record bytes, catalog evidence, texture metadata and geometry
  summaries.
- `qualified-final/manifest.json`: every exported file hash and size.
- `qualified-final/Car25A.PDO/` and `Car06A.PDO/`: original decoded files plus
  structural JSON arrays retaining source offsets and unknown fields.
- `qualified-repeat/`: independent repeat with identical manifest and47 files,
  total3260564 bytes excluding the manifest itself.
- `evidence/determinism.json`: repeat comparison.
- `evidence/Car25A.PDO.textures.png` and `Car06A.PDO.textures.png`: inspected RGB
  palette contact sheets, showing real original Toyota and Renault liveries.
  These derived images prove texture reconstruction only.

Final manifest SHA-256:
`5026c26772069c5688efe84d76b24dedcfcb187e7c3ee229be3c02955b04c244`.
No proprietary payload or image belongs in source-only review archives.

## Reproduction and validation

From the repository, choose a fresh private output directory outside the source
root:

```powershell
python tools/michelin_source_probe.py --source-root 'E:/RallyWorkshop_Sources/sources/Michelin Rally Masters' --output '.research-output/vehicles/paris-dakar-source/michelin/new-proof'
$env:PYTHONPATH='src;tests/synthetic'
python -m unittest test_michelin_research -v
```

Focused result: **12 tests PASS**. Source-free tests cover a known standard TEA
vector, plaintext tails, overlapping LZSS references, truncation/overrun/trailing
data, malformed PDI1 tables, path/size/count budgets, source immutability,
deterministic output/reopening, malformed geometry indices and nonfinite UVs,
texture channel preservation and explicit unknown semantics. Full-suite results
are recorded by the parent milestone in REGRESSION_MATRIX and COMMIT_LEDGER.

The current module has no proprietary fixture, game execution, installed-file
write, MR resource generator or Universal Scene normalization. Inputs open
read-only; outputs require a fresh directory disjoint from the source root.

## Smallest next evidence gate

Trace the original loader for `XOBJ`, `PTOC`, `_VERTEX.BIN` and the candidate
texture index in this exact executable. Resolve the external-position relation
before selecting a rest geometry. Then locate shared wheel/hub records and
source-coordinate evidence. Only after those checks should a small normalized
scene and neutral textured vehicle preview be proposed. RAV4 remains personally
important; the current advance does not change the historical priority of
Paris-Dakar or start a second large reverse-engineering campaign.
