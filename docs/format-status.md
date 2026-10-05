# Format status (Phase R4D.1 vehicle-material hardening)

R4F human runtime testing confirmed the Astero `car.dx` existing-draw topology writer: +3 serialized vertices and +1 triangle are visible in-game, with normal collision, damage, glass and wheels. This confirmation is limited to the tested `car.dx` candidate; see `research/r4f/runtime-results.md`.

| Family | Current interpretation | Confidence | Evidence / limit |
|---|---|---|---|
| `.dx` | Compiled 3D model data: vertex arrays, local `uint16` triangle indices, variable draw records, a stored global `uint32` index table, and resource-dependent trailing data. | **HIGH** vehicle grammar | All 78 vehicle DX files parse and reconstruct their stored global indices exactly. Course DX remains untested. |
| `.dxt` | Custom 20-byte wrapper around one uncompressed 32-bit BGRA pixel plane. It is not DDS or DXT1/3/5 block compression. | **CONFIRMED** structure / **HIGH** BGRA | All 6,960 files satisfy `20 + W*H*4`; synthetic channel tests and directional Astero body textures support the interpretation. |
| `.dxb` | Compiled 2D/font/sprite-batch-like resource. | **LOW** | All 113 begin `0x0000F001, 125`; record layout is not mapped. |
| `.hnt` | Plain-text dependency manifest for scene/frontend resources. | **CONFIRMED** | 54 readable files name models/textures used by adjacent scene XML. |
| `.sfl` | 20-byte header plus a single `W*H` byte raster plane. Semantic meaning is unresolved. | **HIGH** structural / **UNKNOWN** semantic | Exact size invariant in all 36 files. |
| `.txt` adjacent to `.dx` | Optional export/diagnostic sidecar carrying material, texture, hierarchy, and source mesh-span metadata. | **HIGH** | Vehicle DX parses without it; Evidence-scored resolution selects a TXT candidate for all 78 vehicle resources, including 12 non-exact filenames. |
| `.xml` | Human-readable scene/config broker data and asset identifiers. | **CONFIRMED** | All 122 XML files parse successfully. |

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

The same-topology SDK v1 remains frozen and runtime-confirmed. R4F maps the topology-dependent vehicle DX render fields and adds a separate experimental rebuild path. Across the protected 78-resource corpus, vertex/index draw ranges are contiguous and disjoint, and a zero-edit rebuild is byte-identical in 78/78 files. The writer retains draw/material identity, collision and bounds footer bytes; Blender compiles existing-draw triangle corners with deterministic UV/normal/color splitting. One Astero +3-vertex/+1-triangle F1 candidate has zero unexplained external differences and matched the Blender export SHA-256. **The F1 topology edit is CONFIRMED_BY_RUNTIME.** Course DX and new materials/draws remain unsupported. R4G subsequently confirmed the bounded out-of-donor-bounds path and limited collision scale in the B1/C1 human tests. See research/r4f/ and docs/dx-render-rebuilder.md.

## R4G marker-1339 and vehicle SDK status

The final 44-byte marker-1339 block is typed as center, radius/scalar, min and max. All 78 vehicle resources agree with render plus detailed tag101-B extrema within 1e-6; 77/78 radius values agree within 1e-5, with WildCat/car.dx the documented exception. A conservative recompute writer and four isolated B1/C1/P1/W1 candidates are structurally validated. Later original-game B1/C1/P1/W1 tests all passed: expanded bounds, collision scale, complete.dx topology and wheel.dx topology are CONFIRMED_BY_RUNTIME in their tested Astero contexts. MASTER RALLYE VEHICLE SDK v1 is a RUNTIME-CONFIRMED BASELINE; see research/r4g/runtime-results.md. See docs/vehicle-bounds.md and research/r4g/findings.md.

## R5V-B dormant vehicle slot audit

Retail record 25 has a vtable, empty owned-name pointer and four float32 1.0 defaults, while ID/class/stat integers are left unwritten. The frontend class-2 count is compiled as 11, and its `VehicleList` vector contains class labels. The retail unlock switch has case 25, but this does not establish a playable record. R5V-B verdict: **MORE RESEARCH NEEDED; no executable/data patch or runtime candidate.** See `research/r5v_b/findings.md`.

## R5V-C ID25 runtime status

The allocated retail ID25 is initialized by an automated, hash-locked duplicate-Astero EXE-copy candidate. The owner reports P0 FULL PASS and P1 FULL PASS, including frontend preview, Quick Race behavior, stage completion, results, return to menu, and continued use of the original Astero. The report says retail debug output showed Astero resources loading from ID25. Raw logs and screenshots were not added to the repository; see `research/r5v_c/runtime-results.md`. This proves the slot path with a duplicate payload and does not establish independent vehicle payload support.

## R5V-E0.1b frontend diagnostics

The Vehicle Select updater reads Speed, Acceleration, Handling and Endurance
directly from the selected VehicleRecord fields `+0x0C..+0x18`, and the scene
binds four independent bars to those properties. A hash-locked, ignored
ID25/Trooper stats-only candidate with values `(3,4,6,10)` changes exactly four
immediate bytes versus the Trooper + SmallCarSheet29 baseline. The owner reports
FULL PASS: all four Vehicle Select bars followed those values while Trooper
configuration remained active. This confirms the fields as frontend presentation
controls for the tested build.
R5V-E0.1b stats are **FULL PASS**: the owner observed `(3,4,6,10)` on the four
Vehicle Select bars while Trooper configuration remained active. These values
are frontend presentation controls; physical Trooper behavior was not part of
that test. See `research/r5v_e/r5v_e0_1b/`.

### R5V-E0.1d.2 race progress-marker tint

The VehicleRecord tail is runtime-confirmed as race marker colour:
`+0x24=R`, `+0x28=G`, `+0x2C=B`, and `+0x30=A`. Static tracing follows the
record selected by `Race/CarN/CarID` into `Race/CarN/Colour`, which the generic
progress-marker renderer consumes. The owner reports the isolated red-ID25
A/B changed only Trooper's marker; stock Astero and opponent colours remained
unchanged. This result supersedes the earlier E0.1c unknown-source report. See
`research/r5v_e0_1d_2/findings.md`.

## R5V-E0 Trooper ID25 candidate

The retail ID25 patcher has a Trooper profile. Its candidate composes the demo-9.3.1 revision-131 Trooper model converted to revision 135, 24 referenced Trooper DXT dependencies, retail Trooper physics, and authentic Trooper tag101 collision. Automated conversion, composition, physics-schema, and collision-structure checks pass. The owner reports R5V-E0 P0/P1 FULL PASS: Trooper preview/race/wheel resources, physics, collision and damage work; a full stage, Race Results and return to menu work; original vehicles remain available. The reported frontend identity is `STEEL MONKEYS FORKLIFT`, Astero-derived stats, and a missing Vehicle Select icon. E0.1a selector diagnostics were owner-confirmed: the top-left participant and Race Results icons display Forklift frame 29; the progress marker remains aquamarine. The tested EXE hash and raw captures were not supplied. See `research/r5v_e/r5v_e0/` and `research/r5v_e/r5v_e0_1/`.

## R5V-F retail physical registry expansion

Static retail analysis and candidate construction extend the heap registry
from 26 to 27 `0x34`-byte VehicleRecords. Record26 is at registry `+0x54C`;
the adjacent 39-row RaceTest array moves from `+0x54C` to `+0x580`, and the
allocation grows from `0xC00` to `0xC34`. Constructor/destructor counts,
exception-unwind paths, all 39 secondary initializers and 11 direct readers
are included in the hash-locked candidate. T1 local7 maps to ID26 and reverse;
T2 and T3 IDs remain unchanged, with capacities 7 and 12. ID26 uses a
Landcruiser ID0 value duplicate and the original full owned-string initializer.

The owner reports runtime confirmation that ID26 is selectable at T1 local7,
previews, starts Quick Race, drives normally, completes a full stage, reaches
Race Complete, and returns to the frontend. This confirms the core physical
expansion and offline race path, but not that ID26 is independent from donor
ID0: both records still use the same values. The proof candidate exposed an
extra T2 local7 that maps to the canonical T3 Bowler, and Quick Race displayed
`GALOCAL UNKNOWN` for ID26. R5V-F.1 addresses these as cleanup defects before
testing a red ID26-only race-colour canary. Campaign persistence and network
support remain unproven. See `research/r5v_f/` and `research/r5v_f_1/`.

R5V-F.1 statically corrects the T1/T2 capacity coupling (`T1=8`, `T2=7`,
`T3=12`), maps ID26 to donor selector0 only for Quick Race group `0x35`, and
initializes a red race-marker canary only in VehicleRecord26. The archive is
unchanged. The owner reports cleanup P0 FULL PASS, a valid Quick Race name, and
the red ID26 marker for the exact cleanup candidate hash documented in
`research/r5v_f_1/validation.md`. The ID0 stock-marker comparison was not
reported and is not a gate for F.2's source audit. R5V-F.2a statically traced
retail's native GXM→DX and GXI→DXT cache paths; the DX writer emits revision
135. Mercedes P0 remains blocked before candidate generation: its distinct
demo source is revision127, the supported SDK conversion starts at revision131,
and the source-specific retail path has not been run. The embedded absolute GXI
root and writable cache mapping are unresolved; Cook A/B and output validation
remain unrun. Retail Mercedes physics is schema-compatible and source collision
has separate bounded structural evidence; neither establishes a retail-ready
model or runtime behavior. No Mercedes profile or candidate was created. See
`research/r5v_f_2/findings.md`, `research/r5v_f_2/mercedes-model-conversion.md`,
and `research/r5v_f_2a/findings.md`.

### Current R5V-F.2 / F.2f status

The later F.2e owner runtime report confirms the Mercedes ID26 Vehicle Select
presentation and core race behavior (model, textures, handling, physics,
collision and damage); it does not establish a full stage/results/return
lifecycle. Three paired Broker Observatory captures show the remaining defect
is frontend-only: `FUN_0047A540` sends physical ID26 to Race Options localization
groups `0x33` (manufacturer) and `0x34` (model), while the separate
`FUN_0047B040` group-`0x35` Quick Race writer already produces the combined
`MERCEDES ML-320` string. F.2f adds two ID26-only wrappers at `0x0047A65F` and
`0x0047A6C4`; all other IDs retain the original lookup and physical ID26 is
unchanged. The candidate is **READY FOR HUMAN P0**, not runtime-confirmed.
See `research/r5v_f_2f/`.

The forward vehicle roadmap is R5V-G.1 unlock architecture, R5V-G.2 audio
identity/sound-family architecture, R5V-H AI pools, R5V-I multi-slot registry
expansion qualified by a T2 vehicle, then R5V-J generic addon tool/SDK. T2
qualification and independently configurable add-on sound family are required
before claiming the generic SDK complete; these are not part of F.2f.
