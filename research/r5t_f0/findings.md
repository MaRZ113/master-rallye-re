# R5T-F.0 — France1 named source geometry

**Status: STATIC_COMPLETE / MANUAL_COOKER_RUNS_REQUIRED.** The source topology,
spatial measurements, exclusive ownership, and one controlled source-copy
mutation are validated. The original Demo 9.10.0 runtime is available only as
a manually selected cook path; no course cook or gameplay result is claimed in
this closeout.

## Inputs and coordinate spaces

The decoded source is Demo 8.4.1 France1 `France1.gxm` (11,489,135 bytes,
SHA-256
`56ebbf03fe681d730e796a40d455562b5f9976d794c710e73d5c9be32e4e86b2`) with
paired `France1.txt` (SHA-256
`71ea372203bcc6e84bfee87e7d2f410e22c1fdcdc5f653c87274100df38c0d43`). The
RaceTest comparison uses Retail France1 XML (474,787 bytes, SHA-256
`beaa2180912ffd54f313a149962e295f9894239014481d2c7ba2db84fb1e08e1`).

The report keeps source GXM `(x,y,z)`, runtime/XML `(x,z,-y)`, and Blender
coordinates explicit. For this established composition, source GXM coordinates
align approximately with Blender by identity; that alignment remains a
**HIGH_CONFIDENCE_INFERENCE**.

## Decoded mesh measurements

All four literal nodes are under
`Model/$autovsphere_300/$bsp/$nodraw`. `Index` and `Size` identify a 24-record
triangle span. Each span references 14 unique position records; every
undirected edge has incidence 2. These binary observations do not assign
gameplay or physical meaning.

| Literal source node | `Index` / `Size` | Source centroid `(x,y,z)` | Runtime centroid `(x,y,z)` | Runtime dimensions `(x,y,z)` | Nearest StartArea edge (X/Z) | Nearest FinishArea edge (X/Z) |
|---|---:|---|---|---|---|---|
| `COLLIDE_finishline01` | 47011 / 24 | (-1643.6646, -172.2437, 57.1413) | (-1643.6646, 57.1413, 172.2437) | (0.9006, 9.5769, 1.0400) | 0 / 6.3953 | 0 / 213.6514 |
| `COLLIDE_finishline` | 47035 / 24 | (-1652.7400, -156.5247, 57.3762) | (-1652.7400, 57.3762, 156.5247) | (0.9285, 9.4427, 1.0720) | 0 / 6.9652 | 0 / 231.7036 |
| `COLLIDE_finishline02` | 47059 / 24 | (-1470.0256, -370.6216, 68.4540) | (-1470.0256, 68.4540, 370.6216) | (1.0352, 9.6084, 0.9464) | 0 / 266.1144 | 3 / 0.0892 |
| `COLLIDE_finishline03` | 47083 / 24 | (-1471.7653, -352.5542, 68.4258) | (-1471.7653, 68.4258, 352.5542) | (1.0671, 9.4428, 0.9755) | 0 / 251.8496 | 3 / 0.1869 |

The full min/max bounds, all four marker-edge distances, marker distances,
hierarchy paths, edge-incidence histograms, and source IDs are in
[`france1-named-geometry-correlation.json`](france1-named-geometry-correlation.json).

## Pair correlations

| Pair | Pair separation | Midpoint in runtime/XML space | Candidate area edge | Direction difference | Pair midpoint to edge midpoint (X/Z) | Pair midpoint to edge segment (X/Z) |
|---|---:|---|---:|---:|---:|---:|
| `COLLIDE_finishline01` + `COLLIDE_finishline` vs StartArea | 18.1523 | (-1648.2023, 57.2587, 164.3842) | 0 | 2.2580° | 6.5982 | 6.5835 |
| `COLLIDE_finishline02` + `COLLIDE_finishline03` vs FinishArea | 18.1510 | (-1470.8954, 68.4399, 361.5879) | 3 | 0.8716° | 0.3535 | 0.0489 |

The JSON reports every edge. The chosen correlation summary reports the
closest segment among edges aligned within 3 degrees; the 10-unit proximity
and 3-degree limits are descriptive thresholds. Both measured relationships
are classified **STRONG_SPATIAL_CORRELATION**, not semantic matches. Runtime
evidence independently establishes that StartArea controls the geometric
starting-grid frame and FinishArea contributes to the race-completion region;
it does not link either named mesh to those systems.

## Position ownership and one mutation

Each mesh's 14 unique positions is referenced only by triangles in that same
`moMesh` span. For `COLLIDE_finishline03`, all position indices 26107–26120 are
exclusive; no shared references were found. The reviewed research-copy edit
translates only those positions by source X `+20.0` (expected runtime delta
`(+20,0,0)`). It changes 28 bytes in 14 two-byte ranges at offsets 11,151,688
through 11,151,845. The float32 exponent/high bytes remain unchanged for this
delta; the decoded values were separately checked.

| State | France1 GXM SHA-256 | Size |
|---|---|---:|
| Baseline source | `56ebbf03fe681d730e796a40d455562b5f9976d794c710e73d5c9be32e4e86b2` | 11,489,135 |
| Modified research copy | `2e93f6291f9b5e4b0606b218e42f7926a7d4f0d37a1eb76f359d9ccbff4dc2a2` | 11,489,135 |

Baseline target centroid is `(-1471.7653, 68.4258, 352.5542)` in runtime/XML
space; modified centroid is `(-1451.7653, 68.4258, 352.5542)`. The baseline
runtime AABB is min `(-1472.2988, 63.6745, 352.0665)`, max
`(-1471.2317, 73.1173, 353.0419)`. The modified AABB adds 20 to X only.

The manifest records exact offsets and before/after float3 values. It confirms
unchanged file size, node table, color/material/normal/texcoord banks, triangle
records, all non-target positions, position indices, and target topology.
RaceTest XML was not edited by the source-mutation tool.

## Cook stage and current boundary

The manually invoked Demo 9.10.0 runtime copy has executable SHA-256
`13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78`. The
prepared baseline and modified clones are under ignored
`research-output/r5t_f0/cooker-lab/`. Their only course source-input difference
is the target France1 GXM. Both clones retain the same Demo 9.10 RaceTest XML
(SHA-256
`6048ed26c78118f3f82d9ddbcaf4f75c6655b24d805189d3cf3bd772202dc0df`); this is
distinct from the Retail XML used for the spatial report. The cook script
removes generated DX/DXT caches only inside these two new clones.

Staging removed 67 generated files per clone (one course DX and 66 DXT files);
both course folders now begin with zero DX/DXT outputs. The unchanged seed
runtime remains separate.

No snapshots exist yet. Revision-135 DX parse coverage, repeated tag100
stability, stable baseline/modified tag100 differences, and decoded render
response are **PENDING**. Do not treat the stage as cooked. Follow
[`runtime-probe-handoff.md`](runtime-probe-handoff.md) and
`research-output/r5t_f0/cooker-lab/COOK-INSTRUCTIONS.md` to make three cold
cooks per cohort with the original runtime. After the final `compare` passes,
the last cooked runtime in each cohort is kept for the separate human
observation. No mesh semantics, tag100 semantics, or physical role are
confirmed by this static phase.

## Blender diagnostic

The developer-only Blender 5.2.2 diagnostic scene was generated under ignored
`research-output/`, not the add-on or a committed game-asset scene. It contains
the four decoded source meshes alongside source-ordered StartArea and
FinishArea marker outlines. The smoke report records 24 triangles / 14 unique
vertices per source object and retains `gameplay_semantics = UNKNOWN`.

The existing add-on ZIP built from current repository sources installed and
registered in a separate Blender profile. The existing retail-course import
smoke also passed for Italy1 (`track01.dx`: 54,612 vertices, 41,722 triangles,
837 draws, 75 DXT-backed material slots) and France1 (`france1.dx`: 65,206
vertices, 64,577 triangles, 995 draws, 97 DXT-backed material slots). Both
remain revision 135, read-only, with tag100 semantics `UNKNOWN`. These checks
validate the existing importer path; the spatial overlay is a separate
developer diagnostic, not add-on UI work.

## Evidence summary

- **CONFIRMED_BY_BINARY_STRUCTURE:** source spans, indices, topology, bounds,
  ownership, source-copy byte changes, and unchanged data banks.
- **CONFIRMED_BY_CORPUS:** the named France1 nodes and selected RaceTest lists
  exist in their respective local source files.
- **CONFIRMED_BY_RUNTIME_EDIT:** StartArea and FinishArea roles from earlier
  controlled RaceTest edits; no runtime claim about these source meshes follows.
- **STRONG_SPATIAL_CORRELATION:** the two quantitative mesh-pair comparisons.
- **UNKNOWN / NOT PROVEN:** visual rendering, physical interaction, race logic,
  collision role, and any relationship to trailing DX `tag100`.

## Validation

- `python -m unittest discover -s tests\synthetic -p "test_*.py" -v` — 180
  passed, 0 failed, 0 skipped.
- `python -m compileall -q src tools tests\synthetic tests\blender` — passed.
- `git diff --check` — passed.
- Blender 5.2.2 named-source overlay smoke — passed; 4 mesh objects and both
  four-marker areas present.
- Blender add-on install smoke — passed. Blender emitted a non-fatal denied
  attempt to write its global extension compatibility cache; installation and
  operator registration completed from the isolated profile.
- Retail Italy1/France1 course import smoke — passed with the counts above.
- Correlation report, source-probe manifest, cooker-stage manifest, and
  Blender smoke reports all parse as JSON.
