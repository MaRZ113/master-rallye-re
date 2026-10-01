# Format status (Phase R4D.1 vehicle-material hardening)

R4F human runtime testing confirmed the Astero `car.dx` existing-draw topology writer: +3 serialized vertices and +1 triangle are visible in-game, with normal collision, damage, glass and wheels. This confirmation is limited to the tested `car.dx` candidate; see `research/r4f/runtime-results.md`.

| Family | Current interpretation | Confidence | Evidence / limit |
|---|---|---|---|
| `.dx` | Shared header/vertex/normal/color/UV/local-index prefix, followed by resource/build-specific draw and tail grammars. | **HIGH** vehicle grammar; **CONFIRMED_BY_CORPUS** retail course render grammar; **PARTIAL** tag100 wire grammar | All 78 vehicle DX files reconstruct stored global indices exactly. The revision-135 course reader validates render geometry in all 36 retail files; the standalone F.2 reader parses each tag100 tree, while later regions and most semantics remain unresolved. See `docs/formats/dx-common.md`, `docs/formats/dx-course.md`, and `research/r5t_f2/`. |
| `.dxt` | Custom 20-byte wrapper around one uncompressed 32-bit BGRA pixel plane. It is not DDS or DXT1/3/5 block compression. | **CONFIRMED** structure / **HIGH** BGRA | All 6,960 files satisfy `20 + W*H*4`; synthetic channel tests and directional Astero body textures support the interpretation. |
| `.dxb` | Compiled 2D/font/sprite-batch-like resource. | **LOW** | All 113 begin `0x0000F001, 125`; record layout is not mapped. |
| `.hnt` | Plain-text dependency manifest, including course model/texture declarations. | **CONFIRMED** as a text/resource list; runtime necessity is unresolved | Retail course graph: 36 manifests, 2,842 exact resolutions, one unresolved reference, no ambiguous paths. |
| `.sfl` | 20-byte header plus a single `W*H` byte raster plane. Semantic meaning is unresolved. | **HIGH** structural / **UNKNOWN** semantic | Exact size invariant in all 36 retail files, 2 Demo 9.3.1 matches, and 30 Demo 9.10.0 ICont files. |
| `.fl` / `.sf` | Historical 20-byte-header fields with four payload bytes per cell in scanned Demo 8.4.1 candidates. | **CONFIRMED** structure / **UNKNOWN** semantic | Ten candidates satisfy `20 + W*H*4`; direct semantic equivalence to SFL is not established. |
| `.txt` adjacent to `.dx` | Optional export/diagnostic sidecar carrying material, texture, hierarchy, and source mesh-span metadata. | **HIGH** | Vehicle DX parses without it; Evidence-scored resolution selects a TXT candidate for all 78 vehicle resources, including 12 non-exact filenames. |
| `.xml` | Human-readable scene/config broker data and asset identifiers. | **CONFIRMED** | All 122 XML files parse successfully. |
| Course RaceTest `.xml` | Ordered MarkerLists and Egg/AI component hierarchy; typed projections for StartArea, FinishArea, matrices, and split-time records. | **CONFIRMED_BY_CORPUS** structure; SplitTime0 center **CONFIRMED_BY_RUNTIME_EDIT / DEBUGGER** | All 41 retail RaceTest XML files parse. In France1, `SplitTime0` Egg Row3 drives both the visual sign and gameplay center; `gaRaceSplitTimeAI/Radius` is the 3D sphere radius. SplitTime1/2 have matching structure but were not independently moved in runtime tests. See `docs/course-importer.md` and `research/r5t_d1/`. |
| Course SDK | Typed `CourseProject` composition, read-only compiled/source geometry, and G0 allowlist-constrained RaceTest XML authoring. | **IMPLEMENTED; BOUNDED AUTHORING** | Only StartArea/FinishArea marker positions and main SplitTime Row3 XYZ, Radius, and Split Time ID can be exported. No geometry/physical writer exists. The standalone tag100 parser remains structural, with broader physical semantics **PARTIAL/UNKNOWN**. See `docs/course-sdk.md`, `docs/course-race-logic-authoring.md`, and `research/g0/`. |
| Course `.gxm` | Demo 8.4.1 / 9.10.0 paired version-7 source models, fixed attribute/triangle/position banks, and TXT-cross-validated node table. | Triangle grammar and `moMesh` spans **CONFIRMED_BY_EXECUTABLE / BINARY_STRUCTURE**; color-like / texcoord-like semantics conservative. | France1, Italy1, Boinds, and Demo 9.10 AI Track pass all five independent reference-domain checks and complete mesh-span coverage. France1 `startpoint` resolves to a closed 12-triangle box. Gameplay meaning of node names remains **UNKNOWN**. See `docs/formats/gxm-course.md` and `research/r5t_e/`. |

## Course status (R5T-C evidence closeout)

- **HIGH_CONFIDENCE_INFERENCE:** the measured Demo 8.4.1 course point bank
  maps to DX positions by `(x, z, -y)`; the established DX-to-Blender
  transform composes to identity. This is not a per-node geometry mapping.
- **CONFIRMED_BY_SOURCE_COMPILED_PAIR:** one France1 source float changed by
  +1.0; three baseline and three modified cooks show stable tag100 within each
  cohort and distinct tag100 hashes across cohorts. Render prefixes vary
  naturally.
- **CONFIRMED_BY_RUNTIME (owner observation):** the edited course loaded in
  Demo 9.10 with no obvious starting-grid or gameplay difference. The edit
  changed one corner, not the whole candidate volume, so no spawn/trigger
  conclusion follows.
- **HIGH_CONFIDENCE_INFERENCE:** a read-only diff of the controlled one-point
  tag100 change finds 11 unit-normal-like float4 windows in three broad changed
  neighborhoods. None satisfies either tested plane equation on the eight
  startpoint-box corners under the current global coordinate hypothesis.
- **CONFIRMED_BY_SOURCE_COMPILED_PAIR:** a rigid +3 source-X translation of all
  eight candidate points changes 263 bytes in 142 tag100 ranges, repeatably in
  a 2+2 cook. The six affected unit-normal-like float4 candidates fit neither
  tested plane-translation equation within 0.01.
- **CONFIRMED_BY_RUNTIME (owner observation):** in the Demo 9.10 baseline vs
  modified comparison, player and AI positions/order, countdown, and race start
  did not visibly change. This does not prove the candidate has no spatial
  helper role because the translated boxes overlap.
- **CONFIRMED_BY_RUNTIME (owner cross-runtime control):** the player was
  observed at the front in 8.4.1, second in 9.3.1, and in the normal retail
  order in Retail. Both old-source cook outputs placed in Retail also showed
  the normal retail order. This supports version-dependent participant-slot
  assignment; it does not locate physical start slots or prove they are
  runtime-only.
- **UNKNOWN:** exact per-car slot interpolation, `$bsp -> tag100`, and tag100
  physical meaning. R5T-D.0 later confirmed the France1 RaceTest StartArea
  geometry controls grid placement and heading; see the current race-logic
  status below.

## Course race-logic status (R5T-D.0 / D.1 closeout)

- **CONFIRMED_BY_RUNTIME_EDIT:** translating, rotating, or scaling the four
  France1 `MarkerLists/StartArea` positions moves, rotates, or expands the
  physical starting grid; headings follow its orientation. This does not prove
  a one-marker-to-one-car mapping or exact interpolation math.
- **CONFIRMED_BY_RUNTIME_EDIT:** expanding `MarkerLists/FinishArea` advances
  race completion. The list contributes to the completion region; exclusivity
  is not established.
- **CONFIRMED_BY_RUNTIME_EDIT / CONFIRMED_BY_DEBUGGER:** France1 SplitTime0's
  main Egg `en3d Matrix` Row3 drives the yellow sign position and gameplay
  trigger center. Baseline and StartArea-relocated debugger captures showed the
  runtime XYZ at `P+0x4C/+0x50/+0x54` matching Row3, and a separate nearby
  on-road edit triggered the split earlier at the moved location. SplitTime1/2
  were not separately moved in runtime tests.
- **CONFIRMED_BY_EXECUTABLE / CONFIRMED_BY_RUNTIME_EDIT:**
  `gaRaceSplitTimeAI/Radius` is the threshold for a 3D spherical proximity
  test, `distance < Radius` for finite values. The update reads the center from
  `P = *(context+0x50)` and XYZ at `P+0x4C/+0x50/+0x54`; SplitTime0's `P`
  values matched Egg Row3 in two debugger captures.
- **CONFIRMED_BY_EXECUTABLE / SUPPORTED_BY_DEBUGGER:** Split Time ID is loaded
  at `this+0x14` and selects the split event/state identity. Debugger condition
  ID `0` isolated France1 SplitTime0. Broader race-order semantics are not
  claimed.
- **CONFIRMED_BY_DEBUGGER:** each car has its own one-shot state byte. The
  SplitTime0 acceptance path was reached for cars 0–3 during startup when the
  relocated sphere overlapped StartArea.
- The earlier apparent failure after moving Egg Row3 to StartArea is
  **SUPERSEDED_BY_LATER_DEBUGGER_AND_RUNTIME_EVIDENCE**: the sphere had already
  accepted all four cars during startup, so later driving could not activate
  their one-shot events again.
- **CONFIRMED_BY_RUNTIME_EDIT:** moving the visible `SplitTime0-0..3`
  checkpoint Eggs moved those objects but did not relocate SplitTime0's
  gameplay center. Their transforms are **NOT_SUPPORTED** as SplitTime0's
  direct center source. The analogous SplitTime1/2 transforms were not tested.
- **NOT_SUPPORTED:** RaceLine[112] as the direct SplitTime0 center. The
  initializer instead maps the already-existing split center to its nearest
  RaceLine point and stores a percentage; exact runtime indices for France1
  remain unmeasured.
- **UNKNOWN:** exact `ExtraTime` semantics and the runtime type of spatial
  object `P`. The direct XML source for SplitTime0 is established; broader
  RaceLine behavior remains outside this result.
- **R5T-D.1: PASS.** The runtime source field and trigger behavior are closed
  for France1 SplitTime0.
- The runtime-dependent player-to-slot ordering across 8.4.1, 9.3.1, and
  Retail is separate from this physical geometry question and was not analyzed
  here.
- The small complete developer Boinds pair has no `$bsp` node and uses revision
  125, unsupported by the current course parser. Other local small `$bsp`
  sources lack matching TXT/DX, so no isolated `$bsp` edit is prepared.
- The tag100-starting suffix has a loader-guided read-only structural parser
  from R5T-F.2. The tested source collider's plane records are inside the
  parsed tree, but runtime swaps included later tag1339/tag1400 data. `$bsp ->
  tag100`, broader physical semantics, and helper ownership remain unresolved.
  Compiled course parsing and diagnostics remain read-only; G0 later adds a
  bounded RaceTest XML writer without changing this geometry boundary.

## Course SDK foundation (R5T-SDK1)

The read-only semantic layer composes the canonical raw readers and leaves
unknown source structures available. `CourseStartArea`, `CourseFinishArea`,
and `CourseSplitTime` preserve source references and ordered markers. Split
centers derive from Egg Row3 only when the serialized matrix is valid; trigger
shape is the executable-confirmed 3D sphere. France1 SplitTime0's direct
runtime/debugger result is recorded in R5T-D.1; the generic parser no longer
assigns that record-specific evidence by filename. It separates semantic-rule
evidence from record-specific evidence.
HNT entries, structural SFL statistics, source TXT/GXM probes, and neutral
tag100 offsets/hash/status are available from partial `CourseProject` objects.
The existing Blender add-on consumes the semantic model and draws split sphere
helpers and separate visual companions. G0 adds a bounded RaceTest XML
exporter; it does not write compiled or source geometry. See `docs/course-sdk.md`
and `docs/course-importer.md`.

## Course SDK G0 — RaceTest authoring v0

**PASS — READY_FOR_RUNTIME_AUTHORING_TEST.** `CourseRaceLogicAuthoring`
provides allowlist setters for four StartArea/FinishArea marker positions and
main SplitTime Row3 XYZ, Radius, and Split Time ID. The source-span writer
returns original bytes on no-op, preserves bytes outside the edited attributes,
and applies a parsed-tree semantic diff guard. Export is to a new XML path with
a source/output hash manifest; no course archive or compiled resource is
modified.

The curated Retail corpus passes 36/36 principal XML no-op exports byte for
byte. StartArea: 36/36 supported; FinishArea: 34/36; SplitTime: 110 records.
ItalyS4 and TurkeyS1 have five-marker FinishAreas and are safely refused.
France1 static scenarios for StartArea translation, FinishArea expansion,
SplitTime center and Radius pass. Blender 5.2.2 source and built-ZIP tests cover
no-op and edited export. No G0 export has been runtime-tested yet. See
[`docs/course-race-logic-authoring.md`](course-race-logic-authoring.md),
[`research/g0/findings.md`](../research/g0/findings.md), and the optional
[`research/g0/runtime-handoff.md`](../research/g0/runtime-handoff.md).

## R5T-E.1 GXM source topology closeout

**R5T-E.1 PASS; R5T-E final status PASS.** The exact Demo 9.3.1 loader
confirms the packed model header, seven count words, and 52-byte version-7
triangle record reader. France1, Italy1, Boinds, and Demo 9.10 AI Track all
pass color/material/texcoord/position/normal index validation and complete
`moMesh` range coverage. France1 `startpoint` computes to a closed 12-triangle,
8-position box with 18 edges, each used twice. The earlier R5T-E blind-scan
`MORE WORK NEEDED` was correct at that point in the research and is preserved
as a historical result; loader-guided analysis resolved the missing grammar.
The narrow source GXM startpoint diagnostic now displays the decoded mesh; the
standard Retail course importer is unchanged. No writer, EXE patch, or
gameplay inference from node names was added. See `docs/formats/gxm-course.md`, `docs/course-source.md`,
`research/r5t_e/findings.md`, `research/r5t_e/course-gxm-v7.json`, and
`research/r5t_e/startpoint-proof.json`.

## R5T-F.0 named source geometry (historical checkpoint; tag100 carrier later confirmed in F.1)

The four Demo 8.4.1 France1 `COLLIDE_finishline*` meshes decode to 24
triangles and 14 unique positions each. The `01`/unnumbered pair is strongly
spatially correlated with a StartArea edge; the `02`/`03` pair is strongly
correlated with a FinishArea edge. These are measured spatial relationships,
not assignments of gameplay, render, or physical meaning. All target positions
are exclusive to their corresponding mesh spans. A single +20.0 source-X copy
of `COLLIDE_finishline03` is hash-pinned and byte-audited; original GXM and
RaceTest XML remain unchanged. Six manual cold cooks from two isolated Demo
9.10.0 copies validate revision-135 DX outputs and a byte-stable trailing
`tag100` difference: 3,294,483 changed byte positions in the 10,114,844-byte
common prefix, plus a 3,404-byte baseline-only tail. Full DX render prefixes
vary within both cohorts. A human runtime test confirmed that the source edit
moved physical collision about +20 runtime X while visible support geometry
stayed at its old location; the unchanged RaceTest FinishArea still completed
the race. At the F.0 checkpoint the compiled carrier was still under test; the
later reciprocal F.1 result is recorded below. See
[`research/r5t_f0/findings.md`](../research/r5t_f0/findings.md).

## R5T-F.1 reciprocal tag100-starting suffix swap (PASS)

Baseline-03 and modified-03 France1 DX files were split at their parser-derived
tag100 offsets and reciprocally combined through end-of-file. Both hybrids
parse as validated revision-135 courses, retain byte-exact prefix/suffix donor provenance, and
were installed into runtime clones whose only difference is `france1.dx`.
The human runtime result was reciprocal: Hybrid A (baseline prefix, modified
tag100) lost the old support collision and gained collision at the translated
location; Hybrid B (modified prefix, baseline suffix) retained the old
collision and had no translated collision. Visible finish geometry and
FinishArea completion stayed at their original locations in both. This is
**CONFIRMED_BY_SOURCE_RUNTIME_EDIT**, **CONFIRMED_BY_COOKER_DIFFERENTIAL**,
**CONFIRMED_BY_RECIPROCAL_REGION_SWAP**, and **CONFIRMED_BY_RUNTIME_TEST** for
the tested `COLLIDE_finishline03` state only. The runtime test did not isolate
the tag100 tree from following tag1339/tag1400 records. Do not generalize this
to all tag100 data, all `COLLIDE_*` objects, or a complete tag100 grammar. See
[`research/r5t_f1/findings.md`](../research/r5t_f1/findings.md) and the
[runtime handoff](../research/r5t_f1/runtime-handoff.md).

## R5T-F.2 tag100 physical grammar archaeology (PASS, bounded)

Retail executable SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` dispatches
tag 100 to a recursive reader at `0x0057E2D0` / `0x0057E550`. The read-only
parser validates its 24-byte header, variable-length child/sibling records,
20-byte float4/code records, and optional 20-byte list items. In the France1
baseline/modified source pair, 12 unique planes from the 24-triangle
`COLLIDE_finishline03` mesh match records in the tree; under the `+20 X` source
translation, matched plane `d` values follow `d' = d - 20*n.x` within
`4.15e-05` maximum residual. Repeated records prevent one-to-one triangle
mapping. This geometry binding is **HIGH_CONFIDENCE_INFERENCE**; the F.1
runtime result remains suffix-level because a later tag1400 region also differs
in 64 byte positions. `$bsp -> tag100`, complete tree semantics, and tag1400
meaning remain **UNKNOWN**. The parser is read-only and has no writer API. See
[`research/r5t_f2/tag100-physical-grammar.md`](../research/r5t_f2/tag100-physical-grammar.md),
[`research/r5t_f2/tag100-layout.json`](../research/r5t_f2/tag100-layout.json),
and [`research/r5t_f2/collide-finishline03-binding.json`](../research/r5t_f2/collide-finishline03-binding.json).

## R1 vehicle-corpus evidence

- All **78/78** vehicle DX resources are `PARSED` and `VALIDATED`; all 78 stored
  global tables exactly match reconstructed draw indices. **CONFIRMED for the
  vehicle corpus**.
- The exact relationship is
  `(local[1] + vertex_base, local[0] + vertex_base, local[2] + vertex_base)`.
  The corrected R0.5 four-file subtotal is **14,844** validated indices. **CONFIRMED**.
- Tags 2, 7, and 8 occur in 78, 25, and 25 files respectively; no unseen draw
  tag occurred. Type-7 direct child count is its fifth control word. **HIGH**.
- Every vehicle sample has complete, disjoint local-index coverage and complete,
  disjoint vertex-range coverage. These remain validation diagnostics, not
  mandatory grammar rules; synthetic valid unused/shared-range cases parse.
- 49 resources end in the recognized 56-byte bounds form and are `FULLY
  ACCOUNTED`; 29 have opaque trailing data and are `PARTIALLY ACCOUNTED` even
  though their known geometry validates exactly.
- Reconstructed winding agrees with stored vertex normals for 119,454 triangles,
  opposes for 98, and is near zero for 425. This independently supports using
  the stored global order in glTF. **HIGH**.

## Material and texture status

Binary texture bindings are matched to sidecar materials using **normalized
ordered texture-tuple matching**, padding missing sidecar slots with `Null` to
the binary tuple width. There is still no material-index field. The corpus has
1,365 unique, 99 ambiguous, and 14 unmatched draw matches after R4D evidence-scored resolution; ambiguity is preserved as a candidate list. No referenced texture was missing.

For preview only, glTF uses the first non-`Null` slot as `baseColorTexture`.
The DX-to-runtime alpha and feature-mask mappings are **CONFIRMED_BY_EXECUTABLE**; slot-to-stage resource binding and multi-texture appearance remain **PARTIAL**. Raw `DxtTexture.bgra`
preserves stored rows; PNG presentation explicitly reverses their vertical
order. A new raster-corrected comparison on asymmetric Astero panel, sticker,
and door textures independently supports glTF `V' = 1 - V` at **HIGH**
confidence. These are two separate transforms, and both UV modes remain
available.

## Still outside the claim

Header words `135` and `1337`, draw flags/control semantics beyond known
boundaries, runtime material blending, and course DX variants remain
unresolved. R4B used targeted reader/writer inspection only for the formerly
opaque collision prefix; it did not perform broad executable analysis.

## R2 Blender integration status

- **PASS, tested in Blender 5.2.2 LTS.** The installable add-on imports one
  vehicle DX or every DX directly in a selected vehicle folder.
- Shared conversion maps source/glTF `(X, Y, Z)` to Blender `(X, -Z, Y)` at
  scale 1.0. This is a handedness-preserving rotation; stored-global winding
  and imported normals are retained.
- One editable mesh per DX preserves all triangles, all UV sets, exact source
  normal float32 bits, raw color-like bytes, point source IDs, and face
  draw/triangle/group IDs. Draw tags 2/7/8 and group hierarchy remain
  structured object metadata.
- Texture handling now states three independent policies: decoded PNG rows use
  `flip-vertical`; the accepted R1 glTF preview uses `V' = 1 - V`; Blender
  uses direct source V after a real directional-art A/B test. This does not
  change DXT structure/BGRA confidence or R1 geometry findings.
- Blender-calculated display normals are used for stability because both native
  Blender 5.2.2 custom-normal entry points produced access violations during
  repeated real imports. Exact source normals and diagnostics remain preserved.
  This supported strategy is metadata, not a warning for valid normals.
- Headless synthetic import, ZIP installation, save/reload, Astero/Pajero
  folder discovery, and 19 diverse real resources passed. This is importer
  validation, not a new binary-format confidence promotion.
- Runtime alpha blend/test states and stage-0/env stage-1 operations are traced; exact body-helper appearance remains **UNKNOWN**. Blender Preview V2 is an evidence-backed approximation, not runtime parity.

## R2.5 legacy consolidation status

- Recovered texFinder components are classified under `research/legacy`; no
  legacy code, game asset, or derived conversion output was vendored.
- Conservative DXT replacement is **HIGH** for same-size template use:
  1,143/1,143 modern and 6/6 actual legacy-pipeline samples were byte-identical.
- Evidence-scored sidecar resolution selected a unique best candidate for all
  78 vehicle DX files, 12 with non-exact names. Selection confidence remains
  evidence-relative; alternate candidates are preserved.
- TXT `HasAlpha`, `UsesAlpha`, and `IsNoise` are preserved independently.
  Runtime meanings remain **UNKNOWN**.
- Legacy v1 supports the **HIGH**-confidence safe-template-patch principle for
  fixed-size positions. Legacy v3 topology rebuild is **CONTRADICTED** by modern
  local/global index validation.
- Blender 5.2.2 synthetic and 19-resource real regression tests still pass.

## R3 safe writer status

- **PASS (automated):** 78/78 vehicle DX files produce byte-identical zero-edit
  output and 78/78 pass a temporary AABB-safe single-position patch.
- The writer patches only parsed 12-byte XYZ records, audits all byte changes,
  reparses output, preserves non-position section hashes, and refuses new
  warnings or structural differences.
- Blender 5.2.2 passed untouched, one-vertex, provenance-rejection, and
  save/reload export tests. Twelve diverse real resources exported
  byte-identically through Blender.
- Source SHA-256 and byte size are import metadata; export requires the same
  template, identity object transforms, complete provenance, unchanged
  topology/draw membership, and a different output path.
- Support remains **EXPERIMENTAL / POSITIONS ONLY / SAME TOPOLOGY / TEMPLATE
  PRESERVING**. Runtime status is **RUNTIME VALIDATED — PASS** for
  same-topology vertex-position edits in `complete.dx` presentation/menu and
  `car.dx` race contexts (2026-09-22).
- The tested `car.dx` edit retained collision, damage/deformation, and glass
  breakage. This validates writer output, not a claim that collision data is
  stored in `car.dx`.
- At this R3 milestone, topology-changing, UV, normal and material writing were **NOT YET RUNTIME CONFIRMED**. Later R4E.1, R4F and R4G human tests supersede this historical status; see the later sections below.
- The conservative DXT encoder remains ready for a later stage, but Blender DXT
  export was not added.

## R4A vehicle runtime-role status

- **RUNTIME OBSERVATION / CONFIRMED:** `complete.dx` is used for presentation,
  `car.dx` for the race body/chassis, and `wheel.dx` is separately instantiated
  during a race.
- **STATIC FORMAT FACT:** all 26 car resources have trailing data whose first
  u32 is tag `101`; 25/26 car resources contain a literal `$chull(...)`;
  24 standard TXT spans differ from compiled render triangles by exactly the
  named hull span.
- **DATA LINK / HIGH:** `collision.xml` defines `ConvexHull/PlaneThickness`
  and named overrides matching nine literal `$chull` names. R4B now maps the
  exact tag-101 wire schema; runtime activation remains unresolved.
- **HIGH:** 25/26 car resources use tag-7/tag-8 state groups, predominantly
  `screen*` and `blight`; complete and wheel resources use tag 2 only.
- **HIGH:** all 25 separate wheel resources are 252-triangle tag-2 visual
  templates. Wheel/suspension physics remains separate in `vehicles.xml`.
- **UNRESOLVED:** the complete-for-car lift is not assigned to bounds, wheel
  duplication, or suspension transforms without another controlled test.

## R4B collision-hull status

- **HIGH structural:** tag 101 is base GeometryBlock + float + two repeated,
  counted convex-hull representations. All nested counts and reference domains
  have strict bounds/index validation.
- The 78-file vehicle scan found tag 100/101/102 in **0/28/53** resources.
  Twenty-seven tag-101 hulls are finite and validated; Forklift is the one
  structurally parsed but non-finite static-only outlier.
- **CONFIRMED_BY_CORPUS:** the base scalar is a bounding radius (27/27) and
  each face scalar is polygon area in both representations (27/27).
- **HIGH:** representation A is an 8-vertex/12-triangle AABB helper;
  representation B is a closed convex polyhedron with Euler characteristic 2.
- Tag 102 is structurally two float32 values after its tag; meanings remain
  **UNKNOWN**. Tag 100 is distinct but absent from this corpus and remains raw.
- Blender 5.2.2 read-only overlays use the shared coordinate transform and do
  not enter the R3 export path. R4B implements no collision writer.

## R4C collision-writer status

- **CONFIRMED_BY_WRITER_READER:** 28/28 tag-101 payloads and 28/28 complete DX
  zero edits are byte-identical, including Forklift's preserved non-finite bit
  patterns.
- **CONFIRMED_BY_CORPUS:** base, A geometry-B, and B geometry-B points are
  arithmetic means of their associated positional vertices across all 27
  finite hulls. This closes the translation dependency map.
- **PASS automated:** 27/27 validated hulls translate in memory, retain radius,
  topology, adjacency, pairwise distances, face areas, and centroid/AABB
  relationships, and reparse inside otherwise byte-identical DX templates.
- Forklift translation remains refused. No validation was weakened.
- The Astero collision-only candidate moves source X by `+0.40`; 132 bytes in
  39 authorized X components change, with zero visual-mesh or unexpected
  changes.
- **CONFIRMED_BY_RUNTIME:** project owner reports successful R4C collision translation testing on 2026-09-23. Detailed observations were not supplied with this update.
- Scale, rotation, individual hull editing, topology changes, BSP/tag-100 and
  cylinder/tag-102 writing remain unsupported.

## R4D material-semantics status

- **CONFIRMED_BY_CORPUS:** 1,478/1,478 physical vehicle draws inventoried; 18 neutral structural signatures. Current evidence-scored sidecar resolver yields 1,365 unique, 99 multiple, and 14 unmatched draw matches. These counts reflect the current resolver.
- **CONFIRMED_BY_EXECUTABLE:** original PE imports Direct3D 8; registered shader families include base, alpha, alphatest, environment, noise, water, and particle.
- **HIGH_CONFIDENCE_INFERENCE:** inspected COM wrappers correspond to SetRenderState and SetTextureStageState; vehicle-specific stage mapping and operations remain UNKNOWN.
- **PARTIAL:** Blender material preview remains first non-Null texture because the DX-to-runtime shader linkage is unresolved. No material writer was added.
- **R4D VERDICT: MORE WORK NEEDED; next phase R4D.1.** See docs/vehicle-materials.md and research/r4d/findings.md.

## R4D.1 material update

The tag-2 loader maps serialized flag bytes to runtime +0x22/+0x23/+0x20/+0x21 and unknown_0x24 to runtime feature mask +0x34. The base shader uses source-alpha blending (Z writes off) or alpha test >128 (Z writes on). The observed vehicle corpus has no alpha-test byte set. Stage 1 of the environment shader uses camera-space normals and a COUNT2 transform. Four same-size DXT tests now have human in-game results: body and chrome helpers disappear with Reflections OFF; glass and active brake-glow alpha vary continuously. See research/r4d_1/runtime-results.md. See research/r4d_1/findings.md.

## R4E authoring status

The same-topology DX attribute patcher passes 78/78 real vehicle zero edits
with positions, normals, UVs, and raw colors supplied, including the Blender 5.2.2 full-corpus export. The DXT PNG-to-DXT zero-edit path is byte-identical for 6,960/6,960 files. E1-E4 controlled edits pass reparse, field diff, topology and collision preservation. Human testing confirms E1 UV, E3 vertex color, and E4 alpha flag. E2 limited normal edit remains inconclusive. Same-size DXT authoring preserves the observed
20-byte header and BGRA dimensions. The exact vehicle dependency resolver
and staging helper are automated. A full Python-generated SMA candidate
passes ZIP CRC/member-hash checks; E5 human testing confirms the game accepts the full-tree Python archive and loads its E1 override.
See docs/vehicle-authoring.md, docs/texture-authoring.md and
docs/vehicle-packaging.md.

## R4E.1 same-topology SDK v1 closeout

N1 human testing confirmed that rotating all 192 Astero draw-11 normals changed the target chrome/chromebar reflection/shading without moving geometry. M1 human testing confirmed that clearing environment mask bit 0x04 on Astero body draw 7 removed its reflection contribution while preserving slot-0 livery and unrelated reflective materials. Both writer paths are **CONFIRMED_BY_RUNTIME**. The **SAME-TOPOLOGY VEHICLE SDK V1 BASELINE is FROZEN**: position, normal, UV, color, DXT-content, alpha and environment state edits, tag-101 translation, dependency resolution, bundling and full-tree Python SMA packaging. Unknown fields remain raw. Topology-changing DX output is not part of this baseline. See research/r4e_1/runtime-results.md.

## R4F experimental topology rebuild

The same-topology SDK v1 remains frozen and runtime-confirmed. R4F maps the topology-dependent vehicle DX render fields and adds a separate experimental rebuild path. Across the protected 78-resource corpus, vertex/index draw ranges are contiguous and disjoint, and a zero-edit rebuild is byte-identical in 78/78 files. The writer retains draw/material identity, collision and bounds footer bytes; Blender compiles existing-draw triangle corners with deterministic UV/normal/color splitting. One Astero +3-vertex/+1-triangle F1 candidate has zero unexplained external differences and matched the Blender export SHA-256. **The F1 topology edit is CONFIRMED_BY_RUNTIME.** Course DX writing and new materials/draws remain unsupported. R4G subsequently confirmed the bounded out-of-donor-bounds path and limited collision scale in the B1/C1 human tests. See research/r4f/ and docs/dx-render-rebuilder.md.

## R4G marker-1339 and vehicle SDK status

The final 44-byte marker-1339 block is typed as center, radius/scalar, min and max. All 78 vehicle resources agree with render plus detailed tag101-B extrema within 1e-6; 77/78 radius values agree within 1e-5, with WildCat/car.dx the documented exception. A conservative recompute writer and four isolated B1/C1/P1/W1 candidates are structurally validated. Later original-game B1/C1/P1/W1 tests all passed: expanded bounds, collision scale, complete.dx topology and wheel.dx topology are CONFIRMED_BY_RUNTIME in their tested Astero contexts. MASTER RALLYE VEHICLE SDK v1 is a RUNTIME-CONFIRMED BASELINE; see research/r4g/runtime-results.md. See docs/vehicle-bounds.md and research/r4g/findings.md.

## R5V-B dormant vehicle slot audit

Retail record 25 has a vtable, empty owned-name pointer and four float32 1.0 defaults, while ID/class/stat integers are left unwritten. The frontend class-2 count is compiled as 11, and its `VehicleList` vector contains class labels. The retail unlock switch has case 25, but this does not establish a playable record. R5V-B verdict: **MORE RESEARCH NEEDED; no executable/data patch or runtime candidate.** See `research/r5v_b/findings.md`.

## R5T-A course archaeology and Blender import

The frozen Vehicle SDK v1 remains unchanged. The course corpus has 36 retail folders and four build snapshots of France1/Italy1. The common DX prefix is shared; revision-135 course draw batches are parsed by an additive read-only course interpretation. All 36 retail course DX files pass complete, disjoint index/vertex validation and reach tag100 at the render tail. The existing Blender add-on passed a headless Blender 5.2.2 import smoke test for Italy1 and France1; no manual viewport/game-render parity claim is made. The project owner reports that the Demo 9.10.0 runtime cooker converts 8.4.1 course source to revision-135 output that loads with working AI in the 9.10.0 runtime. R5T-B reproduced the exact UI trigger and retained the user's log screenshots as local ignored inputs. The separate retail-package compatibility observation (retail works in 9.10.0, fails to load the course in 9.3.1/8.4.1) remains **CONFIRMED_BY_RUNTIME** with its cause unknown. No course writer or EXE patch exists. See `docs/course-assets.md`, `docs/course-importer.md`, and `research/r5t_a/runtime-closeout.md`.

## R5T-B historical course cooker and source semantics

Two forced France1 cooks in an isolated Demo 9.10.0 clone used identical 8.4.1 source. Both output revision-135 DX that passes render validation, but DX render counts and hashes vary across runs. All 172 non-DX files match byte-for-byte across runs; the raw tag100 region hash also matches. The course cooker is the runtime UI path: launch the game and select France1. Paired GXM/TXT node-table parsing validates all 2,322 France1 and 1,117 Italy1 records. At the R5T-B checkpoint, source coordinates and transforms had not yet been correlated. R5T-B's two-run result remains the natural-variance baseline. See `docs/course-cooker.md`, `docs/course-source.md`, and `research/r5t_b/findings.md`.

## R5T-B.1 GXM geometry and controlled cooker proof

Across three Demo 8.4.1 GXM/TXT/DX pairs (France1, Italy1, developer Boinds), the bounded float3 bank has a strongest global source-to-DX match of `(x, z, -y)` among all 48 signed axis transforms. Composed with the existing DX-to-Blender `(x, -z, y)`, this gives source-to-Blender identity as a **HIGH_CONFIDENCE_INFERENCE**; per-node point/index association remains unknown. The existing add-on displays France1's eight startpoint candidate points with no inferred connectivity. A +1.0 source-X edit to one candidate point was cooked in three baseline and three modified runs. The raw tag100 region was stable within each cohort and changed across cohorts, confirming a source-to-tag100 compiled effect. The owner observed no obvious starting-grid/gameplay difference from this one-corner tracer. At this historical B1 checkpoint the whole-volume probe was still pending; the later 2+2 rigid-translation and runtime result is recorded under R5T-C below. See `research/r5t_b1/findings.md`, `research/r5t_b1/multi-cook-method.md`, and `research/r5t_b1/blender-validation.md`.

## R5T-C France1 whole-volume source probe

Two baseline and two modified Demo 9.10 cooks verified a rigid +3 source-X translation of the eight-point France1 candidate. The 10,118,248-byte tag100 suffix is byte-identical within each cohort and different across cohorts; the edit changes 263 bytes in 142 ranges. Render prefixes vary between repeat cooks. The owner observed no change to player/AI positions, formation, countdown or race start, so a direct grid-anchor role is not supported by this movement. At the R5T-C checkpoint the grid source was still open; later R5T-D.0 Retail edits confirmed that RaceTest `MarkerLists/StartArea` drives the physical grid frame and headings, while exact per-car interpolation remains unknown. A non-overlap `X += 12` GXM test could test the remaining containment/helper possibility but is not the current grid-placement test. `$bsp -> tag100` and tag100 physical meaning remain **UNKNOWN**. See `research/r5t_c/whole-x3-closeout.md`, `research/r5t_c/findings.md`, and `research/r5t_d0/findings.md`.

## R5V-C ID25 experimental runtime status

The allocated retail ID25 now has an automated, hash-locked duplicate-Astero EXE-copy candidate. Static patch validation passes; **RUNTIME VALIDATION: WAITING FOR HUMAN P0**. There is no confirmed 26th playable vehicle yet, and P1 race testing must wait for a human P0 menu/preview pass. See research/r5v_c/validation.md.

## R5T-F.2.1 tree/tag1400 causal isolation — PASS

**PASS — TREE_CARRIER_CONFIRMED.** The T-only modified hybrid produced the NEW tested collision; the U-only modified hybrid retained OLD. The visible support and FinishArea completion remained unchanged. Tag1400 is neither sufficient nor required for this tested translation; its broader runtime role remains unknown. F.1 remains the full-suffix result, F.2 the bounded parser/plane-correlation result, and F.2.1 the tree-only runtime proof. See `research/r5t_f21/runtime-results.md` and `research/r5t_f21/findings.md`. No course writer or EXE patch was added.
