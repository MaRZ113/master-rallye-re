# R5T-E / E.1 GXM topology findings

## Current verdict

**R5T-E.1 PASS. R5T-E final status PASS.** The read-only version-7 source
topology reader is implemented and passes four paired course/developer GXM/TXT
samples. The narrow source startpoint diagnostic now displays decoded
triangles; the standard Retail course importer was not changed. No GXM/course
writer, executable patch, or physical-course interpretation was added.

The earlier R5T-E **MORE WORK NEEDED** result was correct at the blind-scan
checkpoint: candidate words were not yet bound to the right record fields.
Loader-guided analysis later established a mixed 13-u32 triangle record and
position indirection. The earlier result remains recorded in
[`topology-candidates.json`](topology-candidates.json) as a historical
snapshot; it is not the current phase status.

## Exact executable / loader evidence

Demo 9.3.1 `MRallye.exe` SHA-256:

```text
931CFC4E0C520C26581B0C1173D1BEB586FACD17176B885666F455090F646680
```

Using `ghidra-bridge` against the isolated project for this exact EXE:

- `0x005BEA30` reads the packed object DWORD; class is the low byte, version
  the next byte, and child count the upper 16 bits. Class 2 allocates the
  model and calls `0x005BDF40`.
- `0x005BDF40` reads the next seven `uint32` values. Version 7 chooses the
  version-7 material reader and the `0x005BE940` triangle path.
- `0x005BE940` consumes 12, 4, 12, 12, and 12 bytes and advances by `0x34`.
  Its single caller is `0x005BDF40`.

These establish the loader's accepted object-header split, model count block,
version-7 selection, triangle reader width, and mixed chunk widths as
**CONFIRMED_BY_EXECUTABLE**. Field semantics and bank order are separately
checked against bytes and cross-file references; no game semantics are
inferred from node names.

## Version-7 model layout

Packed object word for the tested files:

```text
bits  0..7   object class (0x02: moModel in these samples)
bits  8..15  version (0x07)
bits 16..31  direct child count
```

The remaining seven u32 words are `word1..word7`. Word 1 is zero in all four
samples and remains unknown. Verified ordered banks:

```text
32-byte model header
word2 * 16       color-like float4 records
word3            variable-length raw material block
word4 * 12       normal float3 records
word5 * 12       texcoord-like float3 records
word6 * 52       triangle records
word7 * 12       source position float3 records
paired-TXT-bounded node table
```

No offsets are hardcoded. The parser uses the final position bank and exact
node-table boundary to derive preceding fixed banks, then verifies all banks
are ordered and contained. The material block's byte interval is exact, while
its internal record schema remains opaque. Word 2 is called *color-like* and
word 5 *texcoord-like* pending more semantic proof.

Each 52-byte triangle has 13 little-endian u32 fields:

| Fields | Reference pool | France1 out of range | France1 `0xFFFFFFFF` |
|---|---|---:|---:|
| `[0:3]` | color-like float4 | 0 | 54,516 |
| `[3]` | material | 0 | 18,514 |
| `[4:7]` | texcoord-like float3 | 0 | 55,542 |
| `[7:10]` | source position float3 | 0 | 0 |
| `[10:13]` | normal float3 | 0 | 0 |

The first seven fields allow only observed sentinel values or in-range
references; position and normal references must be in range. Across all four
samples every domain validates without out-of-range references.

## Cross-file result

| Sample | Triangle bank | Triangles | Meshes | Span gaps/overlaps | Index validation |
|---|---:|---:|---:|---|---|
| Demo 8.4.1 France1 | `0x74409F` | 61,917 | 2,283 | none / none | pass |
| Demo 8.4.1 Italy1 | `0x58EDCC` | 47,377 | 1,082 | none / none | pass |
| Demo 8.4.1 Boinds | `0x107E96` | 9,404 | 2 | none / none | pass |
| Demo 9.10.0 AI Track | `0x32A7A` | 3,528 | 2 | none / none | pass |

For France1, Italy1 and Boinds, `word4 == 3 * word6`; this now follows from
word4 normal-record count and word6 triangle count (three corner normals per
triangle in these samples), not from a generic unnamed corner-index bank.
Every mesh span lies within the triangle bank, and the spans exactly cover it.
Full counts, hashes, offsets, per-domain min/max/sentinel totals, and each
mesh-span result are in [`course-gxm-v7.json`](course-gxm-v7.json).

### Prior candidate correction

- **Italy1 `0x58EDCC`:** exact triangle-bank start. The blind scan found the
  right bytes but misread independent mixed reference fields as a homogeneous
  position-index array.
- **Boinds `0x107E94`:** two bytes before the exact triangle-bank start
  `0x107E96`.
- **France1 `0x6E956C`:** inside the texcoord-like bank, not topology. The old
  uint16 diagnostic is rejected as a bank-boundary observation.

### France1 `startpoint`

The paired TXT/GXM node table gives literal `moMesh "startpoint"`, `Index 0`,
`Size 12`. Its triangle positions resolve through u32 fields `[7:10]` to
indices 0–7 and the eight expected coordinates. Derived proof:

- 12 triangles; 8 unique position indices;
- bounds `(-987.055542, -473.666718, 48.539051)` to
  `(-977.055542, -463.666718, 58.539051)`;
- dimensions `10 × 10 × 10`; centroid
  `(-982.055542, -468.666718, 53.539051)`;
- 18 unique edges, all with incidence 2; each vertex link is one cycle;
- 36 referenced normals group into six axis-aligned directions, six corners
  per direction.

Therefore this decoded mesh is a closed triangulated two-manifold box by
binary-derived topology. Exact triplets, points, normal groups, edge
incidence, and the calculated result are in
[`startpoint-proof.json`](startpoint-proof.json).

### Controlled +3 source-point edit

The original Demo 8.4.1 France1 GXM and the existing ignored
`modified-source/France1.gxm` are available for a reproducible binary
comparison. The file size is unchanged (11,489,135 bytes), exactly 12 bytes
changed, and those bytes are the X components of positions 0–7, each `+3`.
Counts, triangle records, colors, material bytes, normals and texcoords are
identical. This verifies the topology-to-position bank separation at source
level. The earlier R5T-B.1 controlled cooker result independently showed a
deterministic tag100 response to an isolated source point change; no new cook
was run in E.1.

## Course SDK and scope limits

`CourseProject.source_geometry` now carries the typed read-only version-7
model, and `CourseProject.source_meshes` exposes literal mesh name, hierarchy,
source ordinal, `Index`/`Size`, triangle span, position indices, unique source
positions, bounds, and evidence. `COLLIDE_*`, `_raceline`, `$boinds`, and
`$bsp` retain their literal names and `UNKNOWN` gameplay role. The source-only
diagnostic uses this read model; the standard course importer remains
unchanged.

Blender 5.2.2 headless checks pass: the source-only France1 helper imports
8 vertices, 12 polygons, and 18 edges; the existing Retail Italy1/France1
course import smoke remains PASS; and the packaged add-on install/import smoke
passes with the France1 GXM topology. The package build contains 58 Python
files. No manual viewport or game-render parity claim is made.

Still unknown: exact color semantics, texcoord third-component meaning, full
material-record schema, source-name gameplay semantics, `$bsp -> tag100`, and
tag100 physical meaning. No writer or physical-course work is part of this
phase.

## Validation command

```powershell
$env:PYTHONPATH = 'src'
python tools/r5t_e1_course_topology.py
```

This regenerates both compact JSON artifacts using only the available course
and test GXM/TXT pairs; vehicle resource paths are excluded.
