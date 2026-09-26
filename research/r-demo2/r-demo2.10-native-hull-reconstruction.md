# R-DEMO2.10 — Native Convex Hull Core Reconstruction

## Objective and boundary

This phase tests whether a Rep-B collision hull can be predicted from GXM
`$chull` source alone. The source-side builder completes before the scanner
opens a native DX file. Native DX is consumed only by a separate comparator;
it is not used to select vertices, build faces, order predicted loops, or make
predicted triangles.

The result is an analysis-only geometric control, not a native cooker clone.
No proprietary input was modified, no DX was serialized or overwritten, and
no game was launched. Secondary descriptors remain out of scope.

Evidence labels in this report:

- **CONFIRMED** — directly checked against the exact controlled oracle or
  repeated on the named same-build corpus controls.
- **CORPUS-SUPPORTED** — repeated on the listed shipped DEMO 9.3.1 DX assets;
  these are not described as runtime-regenerated outputs.
- **UNRESOLVED** — observed bytes/structure have no established generation
  rule, or the source-only policy does not reproduce native behavior.

## Golden oracle and frozen metadata

The compact tracked fixture is
[`r-demo2.10-golden-fixture.json`](r-demo2.10-golden-fixture.json). It stores
hashes and non-proprietary counts/index metadata, not source or DX bytes.

| Input | Size | SHA256 |
|---|---:|---|
| Original DEMO 9.3.1 Trooper `car.gxm` | 222,754 | `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` |
| +0.10 X candidate GXM | 222,754 | `b7a4da48f32ce0e4e9802e0656f79905b23af373d0dc0a397e8f2f64c973c5b3` |
| `car_baseline_A.dx` | 124,568 | `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` |
| `car_baseline_B.dx` | 124,568 | `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` |
| `car_chull_xplus010.dx` | 124,568 | `5947d0b0cd2d9d16fbbd52bf69a34a7f0eb4581e74379f6559d8f9fccd5fb78c` |

Baseline A and B are byte-identical. The R-DEMO2.9 candidate pair is therefore
a deterministic same-source/same-build control for this asset and environment.
The separate R-DEMO2.9 analysis accounts for all 182 changed bytes from
baseline to candidate; this phase does not redo that accounting.

## Source extraction and transform

The sidecar identifies `$chull(Trooper)` at half-open triangle-record range
`[1911, 1979)`: 68 records reference 36 unique Vector C positions. The exact
source C set is:

`[1317, 1318, 1319, 1320, 1321, 1322, 1323, 1324, 1325, 1326, 1327, 1328, 1329, 1330, 1331, 1332, 1333, 1334, 1335, 1336, 1337, 1338, 1339, 1340, 1341, 1342, 1343, 1344, 1345, 1346, 1347, 1348, 1349, 1350, 1351, 1352]`

The source-only builder applies the already tested coordinate transform
`GXM (x,y,z) -> DX (x,z,-y)`. Each of the 28 predicted hull positions maps to
the matching native Rep-B vertex within `1e-5`; baseline maximum residual is
`6.677050543111643e-6`.

## Source-only implementation

Reusable analysis code:

- `src/master_rallye/gxm_chull.py::analyze_gxm_chull` extracts the directive,
  records, and referenced source C points.
- `src/master_rallye/native_hull_reconstruction.py::build_rep_b_core_from_gxm_chull`
  accepts only GXM bytes, a sidecar path, a directive, and a geometric policy.
- `build_rep_b_core_from_source_points` enumerates all triples from the source
  point set, rejects degenerate/non-supporting triples, groups coplanar point
  sets, computes polygon boundaries, then builds an edge graph and fan
  triangulation. It checks closed loops, two incident faces per edge, opposite
  edge directions, and Euler `V-E+F=2`.
- `triangulate_polygon_faces` is explicitly a deterministic generic fan
  policy. Its output is a prediction, not an assertion about native triangles.
- `src/master_rallye/hull_oracle_compare.py` maps and compares a completed
  prediction to parsed native Rep B. Loop-order and native fan diagnostics are
  oracle-only and run after prediction.
- `tools/scanner/r_demo2_10_native_hull.py` constructs first, then optionally
  opens `--native-dx`. Full traces and mappings go only to ignored
  `.research-output` JSON. Standard output is a count/boolean summary.
- `src/master_rallye/collision_oracle_analysis.py::map_gxm_chull_to_rep_b`
  remains **TARGET_ASSISTED** because callers provide target vertices and a
  retained-index set. It is not used by the source-only builder.

The source point order is first occurrence through the `$chull` triangle
records. Reversing the source point enumeration on Trooper preserves the
generic predictor's retained set, polygon face sets, and edge set. That shows
this geometric control does not need source triangle connectivity to determine
the point-set hull for this case. It does not prove the native cooker is
insensitive to record order or native near-plane tie cases.

## Plane and polygon reconstruction result

The generic policy uses support tolerance `1e-6` and area epsilon `1e-10`.
These are explicit analysis settings, not recovered DEMO 9.3.1 native values.
For Trooper the deterministic trace classifies 7,140 point triples:

| Decision | Count |
|---|---:|
| Degenerate triple | 0 |
| Not supporting | 7,066 |
| Inserted supporting-plane group | 41 |
| Deduplicated supporting triple | 33 |

The source-only result predicts 28 hull vertices, 41 polygon faces, 67
undirected edges, and 52 generic fan triangles. Against the Trooper baseline
Rep B, it has:

- exact retained source C membership: 28/28;
- exact per-face vertex sets and face-list order;
- the same face cycles up to rotation and winding (21 keep the predicted
  orientation; 20 are reversed);
- exact undirected edge set and edge-to-face adjacency;
- the same polygon shell, but a different native triangle partition.

The 28 source positions retained as distinct Rep-B vertices are:

`[1317, 1318, 1319, 1320, 1321, 1322, 1323, 1324, 1327, 1328, 1329, 1330, 1331, 1332, 1333, 1334, 1335, 1336, 1337, 1338, 1339, 1340, 1347, 1348, 1349, 1350, 1351, 1352]`

The eight source positions not retained as distinct final Rep-B vertices are
`[1325, 1326, 1341, 1342, 1343, 1344, 1345, 1346]`. No reason is assigned to
their omission.

## Native loops, triangulation, and ordering

The predicted and native Trooper hulls both contain 52 triangles, but count
equality is not topology equality. The current source-only fan produces 10
unoriented triangles absent from native Rep B and misses 10 native triangles;
the difference is confined to five quadrilateral faces. The comparator reports
`SAME_POLYGON_DIFFERENT_TRIANGULATION`.

A new **oracle-only** check found a consistent conditional rule: native
triangles are exactly a fan from the **second vertex of each stored native
face loop** on all checked files:

| DEMO 9.3.1 asset | Native faces matching fan from stored loop vertex 1 |
|---|---:|
| Trooper baseline A | 41/41 |
| Trooper baseline B | 41/41 |
| Trooper +0.10 X runtime-cooker output | 41/41 |
| Trooper shipped corpus DX | 41/41 |
| Jump shipped DX | 37/37 |
| NewRav shipped DX | 38/38 |
| Tata shipped DX | 24/24 |

This does **not** yet make native triangles source-predictable: the builder
does not know the native edge-loop start vertex or traversal direction. The
native loop start equals the earliest source first-occurrence C index on only
30/41 Trooper, 28/37 Jump, 27/38 NewRav, and 19/24 Tata faces. Simple global
source-order starts therefore do not explain the stored loops. Predicted
vertex ordering and edge ordering also differ from native ordering. Face list
order does match on all four inspected vehicles and both Trooper cooker
outputs; this does not imply exact ordered loops.

### Ordering levels

- **GEOMETRIC_HULL_EQUIVALENT:** yes for the tested four 9.3.1 vehicles.
- **CORE_TOPOLOGY_EQUIVALENT:** the polygon shell, edge graph, and adjacency
  match; the triangulated core is not equivalent yet because triangle
  partitions differ.
- **NATIVE_SERIALIZATION_ORDER_EQUIVALENT:** no. Vertex and edge order differ;
  face-loop start/direction and native triangle winding/order are not
  reconstructed.

## Cross-corpus checks

Each corpus input below is a same-build DEMO 9.3.1 source GXM paired with its
shipped `car.dx`; these are static corpus controls, not runtime-cooker
experiments. The shipped Trooper DX is a distinct file from generated
`car_baseline_A.dx` (shipped hash `bf644c05...fa041`, generated baseline hash
`8238078c...2d5b1`). Full GXM/DX hashes and sizes are in the fixture.

| Asset | Source C / records | Predicted vertices | Native vertices | Polygon faces | Edges | Triangles | Vertex, face-set, edge, adjacency |
|---|---:|---:|---:|---:|---:|---:|---|
| Trooper controlled baseline A/B | 36 / 68 | 28 | 28 | 41 | 67 | 52 | exact |
| Trooper shipped corpus DX | 36 / 68 | 28 | 28 | 41 | 67 | 52 | exact |
| Jump shipped | 34 / 64 | 26 | 26 | 37 | 61 | 48 | exact |
| NewRav shipped | 36 / 68 | 26 | 26 | 38 | 62 | 48 | exact |
| Tata shipped | 18 / 32 | 18 | 18 | 24 | 40 | 32 | exact |

For all four, generic triangles have the right count but a different partition
from native triangles. The shell and adjacency results are corpus-supported
for these four assets only; they do not establish behavior for every vehicle
or demo build.

## +0.10 X invariance

The original and candidate GXM independently produce the same source-only
retained C IDs, polygon face/list order, edge graph, and generic triangle set.
All predicted Rep-B X coordinates move by `+0.10` within `1e-7`; Y and Z stay
unchanged within `1e-7`. The candidate DX separately confirms exact retained
membership, face sets, edges, and adjacency. The native candidate also follows
the second-stored-loop-vertex fan rule on all 41 faces. Native triangle
partition remains different from the generic source fan, as on baseline.

## Native evidence and the 8.4.1 negative control

The existing 8.4.1 static exports support nested point-triple enumeration
(`005B9F10`), plane construction/orientation (`005C3A40`), normal/distance
plane comparison (`005C3E10`), and endpoint-linked face-loop traversal
(`005C43A0`). They do not establish the DEMO 9.3.1 default plane tolerance or
the source-only native loop seed/traversal rule. The available 9.3.1 static
extract identifies `$chull` orchestration and reads `ConvexHull_PlaneThickness`,
but does not recover the default value or a complete tie policy. The generic
`1e-6` support tolerance must not be presented as native `PlaneThickness`.

The separate 8.4.1 +0.4 X replay remains a negative control only:

| Replay | Baseline faces | Candidate faces |
|---|---:|---:|
| Stock `PlaneThickness = 0.0005000000237487257` | 37 | 38 |
| Override `PlaneThickness = 0.00052` | 37 | 37 |

The replay is Python binary64 analysis on the pinned 8.4.1 source/EXE inputs.
The human runtime result for the same +0.4 candidate is separately recorded:
stock tolerance crashed in hull construction; at `0.00052` construction
completed, loading continued, and collision visibly changed. This closes the
immediate old crash question for that exact 8.4.1 experiment; it does not
provide a 9.3.1 hull policy and no crash investigation was resumed here.

## Failure handling and tests

The predictor rejects invalid policy values, non-finite or duplicate source
positions, mismatched source IDs, insufficient/degenerate 3D inputs,
non-manifold edges, inconsistent face orientation, and failed Euler closure.
The tolerance is configurable and reported in every prediction. The builder
does not claim it can detect every native ambiguity around unknown 9.3.1
thresholds; ambiguous near-coplanar native behavior remains a limitation.

Focused coverage is in
[`test_r_demo2_10_native_hull.py`](../../tests/synthetic/test_r_demo2_10_native_hull.py).
It covers the source-only API boundary, tetrahedron/cube and invalid inputs,
plane trace accounting, Trooper source membership/counts, coordinate mapping,
face/edge/adjacency comparison, fan diagnostics, baseline byte identity,
+0.10 invariance, four-asset checks, and the 8.4.1 stock/override replay.
The scanner writes full JSON reports under ignored
`.research-output/r-demo2/2.10-hull/`.

Example source-only prediction followed by optional separate oracle comparison:

```powershell
$env:PYTHONPATH = 'src'
python tools/scanner/r_demo2_10_native_hull.py `
  --gxm 'D:\Game\Master Rallye\corpora\demo-9.3.1\DataGx\Vehicles\Trooper\car.gxm' `
  --sidecar 'D:\Game\Master Rallye\corpora\demo-9.3.1\DataGx\Vehicles\Trooper\Trooper.txt' `
  --directive '$chull(Trooper)' `
  --native-dx '.research-output\r-demo2\931-chull-oracle\input\car_baseline_A.dx' `
  --output '.research-output\r-demo2\2.10-hull\trooper-baseline.json'
```

## Readiness A–O

| Component | Status | Evidence boundary |
|---|---|---|
| A. `$chull` source extraction | `CONFIRMED` | Sidecar and GXM parser recover exact record range and C references. |
| B. GXM to DX coordinate transform | `CONFIRMED` | All retained source positions map within `1e-5` on the controlled outputs and four checked assets. |
| C. Retained hull vertex selection | `IMPLEMENTABLE_WITH_CONSERVATIVE_POLICY` | Source-point extreme selection predicts the exact retained set on four 9.3.1 assets; native algorithm identity is not claimed. |
| D. Supporting-plane generation | `IMPLEMENTABLE_WITH_CONSERVATIVE_POLICY` | Deterministic generic triple enumeration reproduces tested geometric shells. |
| E. Plane deduplication / PlaneThickness | `NEEDS_MORE_ORACLE_DATA` | Exact 9.3.1 default and near-plane decision/tie policy remain unknown. |
| F. Polygon face construction | `CONFIRMED` | Per-face vertex sets match across four assets; generic cycles are geometrically equivalent. |
| G. Native face-loop ordering | `NEEDS_TARGETED_STATIC_ANALYSIS` | Start and traversal policy are not predicted from source; first-occurrence heuristic is incomplete. |
| H. Core edge graph | `CONFIRMED` | Undirected edge set matches all four checked assets. |
| I. Edge-face adjacency | `CONFIRMED` | Adjacency matches after face identity mapping on all four. |
| J. Native triangulation | `NEEDS_TARGETED_STATIC_ANALYSIS` | Fan from native stored-loop vertex 1 is corpus-supported, but the source-only loop needed to apply it is unknown. |
| K. Native vertex ordering | `NEEDS_TARGETED_STATIC_ANALYSIS` | Predicted source-first order differs; no source-only native ordering rule established. |
| L. Native face-list ordering | `IMPLEMENTABLE_WITH_CONSERVATIVE_POLICY` | Predictor order matches all four checked assets and controlled candidate; broader scope untested. |
| M. Native edge ordering | `NEEDS_TARGETED_STATIC_ANALYSIS` | Sorted predicted edges differ from native order; geometry is exact, order policy is unknown. |
| N. Rep-B core serialization readiness | `NEEDS_MORE_ORACLE_DATA` | Native triangle partition/order and vertex/edge array order are not reproduced. No writer was added. |
| O. Secondary descriptors | `UNRESOLVED` | Explicitly out of scope and not needed for geometric comparison. |

**Can the source-only predictor now construct a native-equivalent Rep-B core?**
Not yet. It reconstructs the tested geometric polygon shell, retained source
positions, edge graph, and adjacency. It does not reproduce native
triangulation or exact serialization order.

**Narrowest next blocker:** recover how the native cooker chooses the first
endpoint and traversal direction for each stored face loop from source-side
data. Once that loop is predictable, the observed fan from its second stored
vertex gives a testable native triangle-set rule. Exact vertex/edge array
serialization order remains a separate closeout requirement before writing a
byte-compatible Rep B.

## R4G and production boundary

This phase adds no production behavior. Existing marker-1339 recomputation
evidence remains supported by R-DEMO2.9 and its controlled/corpus checks; this
phase contributes a source-only path to a validated Rep-B polygon shell but
does not change a production writer. The hull predictor is analysis-only and
does not serialize arbitrary or guessed DX data.

## Recommended next phase

Perform a narrowly scoped ordering study of the existing hull-builder edge
loop assembly, centered on the endpoint-list insertion and loop seed used by
`005C43A0` and its callers. Reuse the current Ghidra exports first. Extend
source-only diagnostics only when a concrete source-side rule is supported.
Keep native DX in the comparison role and preserve the four-asset corpus
controls. Do not start a full cooker or byte writer until the loop rule,
triangulation, and required native array orderings are independently
reproducible.
