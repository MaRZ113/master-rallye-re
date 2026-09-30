# Course GXM structure

Status: **version-7 geometry decoded, read-only**. Cross-validated on Demo
8.4.1 France1, Italy1, developer Boinds, and Demo 9.10.0 AI Track paired GXM/TXT
samples. Other versions remain unsupported by the topology decoder.

## Loader evidence

The exact Demo 9.3.1 executable (SHA-256
`931CFC4E0C520C26581B0C1173D1BEB586FACD17176B885666F455090F646680`) was
inspected with `ghidra-bridge`:

- `0x005BEA30` reads the packed object DWORD: class is bits 0–7, version bits
  8–15, and child count bits 16–31. The class-2 model path calls
  `0x005BDF40`.
- `0x005BDF40` reads seven `uint32` count words after the packed object DWORD.
  Version 7 selects the version-7 triangle reader.
- `0x005BE940` reads per record: 12 bytes, 4 bytes, 12 bytes, 12 bytes, and
  12 bytes, then advances by `0x34` bytes. This proves the loader stride is
  52 bytes and the record contains 13 32-bit fields.

Evidence: **CONFIRMED_BY_EXECUTABLE**. The associated pool roles and indices
below are independently checked against actual bytes and paired TXT hierarchy.

## Version-7 object header and pools

The first DWORD for the tested `moModel` is:

| Bits | Field | Evidence |
|---|---|---|
| 0–7 | object class (`0x02` = `moModel` in tested samples) | **CONFIRMED_BY_EXECUTABLE / CORPUS** |
| 8–15 | version (`0x07`) | **CONFIRMED_BY_EXECUTABLE / CORPUS** |
| 16–31 | direct child count | **CONFIRMED_BY_EXECUTABLE / paired TXT** |

The next seven u32 values are words 1–7. Word 1 is zero in current samples
and remains unnamed. Version 7 bank ordering and strides are:

| Header word | Bank | Stride | Status |
|---|---|---:|---|
| 2 | color-like float4 records | 16 | structural bank confirmed; exact color semantics conservative |
| 3 | variable-length material records | variable | count matches TXT material count; raw block preserved |
| 4 | normal float3 records | 12 | **CONFIRMED_BY_EXECUTABLE / BINARY_STRUCTURE** |
| 5 | texcoord-like float3 records | 12 | structural bank confirmed; third component meaning unknown |
| 6 | triangle records | 52 | **CONFIRMED_BY_EXECUTABLE / BINARY_STRUCTURE** |
| 7 | source position float3 records | 12 | **CONFIRMED_BY_EXECUTABLE / BINARY_STRUCTURE** |

The 32-byte header plus count-derived banks and TXT-bounded object table
determine all offsets. The material block is retained raw between the end of
the color bank and the start of the normal bank. No offsets are hardcoded.

## Triangle record

Each record is 13 little-endian u32 values:

| u32 fields | Reference domain |
|---|---|
| `[0:3]` | color-like records |
| `[3]` | material record |
| `[4:7]` | texcoord-like records |
| `[7:10]` | source positions |
| `[10:13]` | normals |

The five domains are range-checked separately. `0xFFFFFFFF` appears as an
allowed sentinel in color, material, and texcoord references in the tested
corpus; position and normal references have no such sentinel. Any observed
out-of-range index fails parsing.

`moMesh.Index` and `moMesh.Size` select triangle-record ranges. All tested
mesh spans are in range and cover the complete triangle bank without gaps or
overlaps. This is **CONFIRMED_BY_BINARY_STRUCTURE** across the four samples.

## Paired TXT node table

The trailing node table remains parsed against its paired TXT. The TXT node
inventory bounds its start; names, classes, mesh spans, child counts, and EOF
are verified. Names remain literal source labels and carry no gameplay role by
themselves.

## France1 startpoint proof

France1 `startpoint` (`Index 0`, `Size 12`) resolves to 12 triangles, 8 source
positions, 18 unique edges, and edge-incidence histogram `{2: 18}`. Bounds are
10 × 10 × 10; its 36 corner-normal references group into six axis directions
with six references each. This is a closed two-manifold box by direct
topological calculation. See
[`research/r5t_e/startpoint-proof.json`](../../research/r5t_e/startpoint-proof.json).

## Evidence progression and limits

The earlier blind-scan candidate at Italy1 `0x58EDCC` was exactly the triangle
bank, but its mixed fields were misread as a uniform position-index sequence.
Boinds' old `0x107E94` candidate was two bytes before the actual `0x107E96`
bank. France1 `0x6E956C` falls inside the texcoord-like pool and is superseded
as a diagnostic-only window.

`CourseProject.source_geometry` exposes the decoded source model and
`source_meshes` exposes literal names, hierarchy, spans, position indices, and
bounds with gameplay roles left unknown. This parser is read-only. The full
corpus validation is in [`research/r5t_e/course-gxm-v7.json`](../../research/r5t_e/course-gxm-v7.json).

Still unknown: exact color semantics, texcoord third-component meaning,
material record schema, node-name gameplay semantics, `$bsp -> tag100`, and
tag100 physical meaning. No writer or physical-course interpretation was
added. The small source startpoint diagnostic consumes this decoder; the
standard Retail course importer is unchanged.
