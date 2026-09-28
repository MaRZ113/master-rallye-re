# R5V-D multi-revision vehicle Blender import

## Scope and result

R5V-D adds direct vehicle import support for the observed revision-127 and
revision-131 demo DX generations and separates revision-135 structural import
validation from exact generated-index validation. Single-resource and folder
imports share the canonical revision dispatcher. Course parsing and all R5T
work remain outside this vehicle-only phase.

The parser accepts revisions 127, 131, and 135. It rejects revision 125 and
unknown revisions. Revision-127/131 material prefix bytes stay raw; their
material flag semantics are unknown. No revision-127/131 writer was added.

## Corpus evidence

The scanner read all 52 DX files supplied under the demo `inputs` directory
and all 78 retail vehicle DX resources. It parsed 128/130 files:

| Source set | Revision | Count | Result |
|---|---:|---:|---|
| supplied demo inputs | 127 | 9 | exact local/global index sequence |
| supplied demo inputs | 131 | 26 | exact local/global index sequence |
| supplied demo inputs | 135 | 15 | 3 exact; 12 structurally equivalent order divergences |
| supplied demo inputs | 125 | 2 | unsupported; nested `8.4.1_Mercedes/lpha` files |
| retail vehicle corpus | 135 | 78 | exact local/global index sequence |

No revision-135 structural failures occurred in this 93-resource scan. The
supplied revision-127 corpus has three resources each in `8.4.1_Jump`,
`8.4.1_Mercedes`, and `8.4.1_Trooper`. The supplied revision-131 corpus has
26 resources across nine directory labels. These counts describe only the
available inputs; they are not exhaustive claims about all demo assets.

Of the 15 revision-135 demo resources, the three `9.10.0_Jump` resources are
exact. The directories `9.10.0_dxForester`, `9.10.0_dxTrooper`,
`9.10.0_Simmbugghini`, and `9.10.0_Wildcat` each contain car, complete, and
wheel resources classified as order divergences. Directory names are retained
as provenance labels; the revision header alone does not identify a cooker or
prove whether a file is native or generated.

The reported Forester trigger,
`!other_research/9.10.0_dxForester/car.dx`, contains 5,592 indices across 15
draws. At the first global index the stored and reconstructed sequences differ;
5,449 covered positions differ in total. All local indices have complete,
disjoint draw coverage, ranges and counts are valid, and each physical draw's
oriented triangle multiset matches. The file therefore imports as
`VALID_WITH_INDEX_ORDERING_DIVERGENCE`; it is not exact writer input.

The independent legacy revision-135 validator from the preserved R-DEMO2
research checkout also passes all 15 supplied revision-135 demo resources by
per-draw oriented topology comparison. That confirms the classification
method against the earlier validator; it does not determine cooker identity.

Machine-readable and Markdown reports:

- `revision-matrix.json` / `.md`: all 130 scanned resources, relative paths,
  revision, resource role, geometry counts, validation profile, collisions,
  and warnings.
- `rev135-index-ordering.json` / `.md`: exact sequence and structural
  equivalence reported independently, with per-directory group totals.
- `rev127.md` and `rev131.md`: observed legacy sample grammar and scope.
- `blender-validation.md`: actual Blender checks and supported sample counts.

The report generator is `tools/scan_vehicle_dx_multirevision.py`. Run it with
read-only demo and retail roots to reproduce the matrix.

## Validation and writer policy

Exact generated validity requires structural validity, exact reconstructed
global sequence, and a writer-supported revision. Import validity requires
valid geometry ranges and counts, complete disjoint draw coverage, and
per-draw oriented triangle multiset agreement. Cyclic triangle rotations are
accepted; reverse winding, missing/duplicate triangles, invalid ranges, and
coverage gaps/overlap are rejected.

The compatibility property `diagnostics.validated` remains the strict exact
generated profile. Existing position, attributes, topology, collision,
vehicle-project, staging/package and CLI writer gates were audited and remain
strict. Blender import alone uses `diagnostics.import_validated`. This lets
the parser read safe legacy/demo geometry without treating it as valid input
to a retail revision-135 writer.

The 11 retail `car.dx` resources whose header top-level count is one less than
the reconstructed root count remain accepted with a warning. Their complete
draw coverage and exact stored index agreement support retaining this known
retail behavior.

## Blender compatibility choices

The add-on retains one mesh per DX file and the existing vehicle resource-role
mapping. It adds DX revision, source filename, structural profile and writer
profile metadata. Folder import summarizes imported files, warnings, and
ordering divergences separately. The Blender panel labels structurally valid
legacy/order-divergent objects as import-only and disables DX/collision
authoring controls unless the strict revision-135 writer profile passes.

Both legacy revisions use the existing direct-source-V UV policy. The
revision-135 material flag mapping is not applied to raw legacy prefixes;
conservative first-texture preview behavior marks legacy blending unknown.
Blender-calculated display normals remain in place and native custom-normal
setters remain unused. Existing DXT PNG vertical-row handling is unchanged.

## Limits

- Legacy grammar confidence applies to the locally supplied revision-127 and
  revision-131 vehicle samples only.
- The two revision-125 `lpha` resources are unsupported and remain unmodified.
- Legacy material, alpha, reflection and blend semantics are not inferred.
- Structural import does not prove original-game runtime acceptance.
- No game source, EXE, course resource, or vehicle asset is modified.
