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

## R-DEMO source formats (research branch)

The demo corpora expose GXI, GXB, GXP, and GXM. Strict GX image structure is corpus-confirmed; 1,450/1,483 same-build GXI/DXT candidates reproduce complete DXT bytes, and 31/38 November GXP images reproduce 146 indexed DXT tiles. GXM material/geometry prefixes are parsed for 80/109 files, while 29 variants remain opaque after their headers. November Jump `$chull` geometry has a float-precision numeric correspondence with retail Jump tag101. First-pass human Trooper 8.4.1 tests confirm live GXM Vector C body geometry and car/complete/wheel visual roles; DX file-access order remains unknown; R-DEMO2 later confirmed exact runtime DXT regeneration, 9.3.1 model-cache generation/fallback, and a crashing isolated `$chull` edit. These findings do not change the retail writer. See `docs/demo-development-pipeline.md` and `research/r-demo/findings.md`.

## R-DEMO2 original cooker/cache research (isolated branch)

The tested 8.4.1 Trooper Black GXI regenerates a DXT byte-identical to the shipped original and offline converter (**CONFIRMED_BY_RUNTIME + CONFIRMED_BY_BYTES**). In 9.3.1, GXM can generate persistent DX and existing DX can load without GXM for observed complete/wheel paths (**CONFIRMED_BY_RUNTIME**, human). Original and one regenerated car DX retain major topology and draw/material bytes but differ in float fields and unresolved secondary tag101 descriptor ordering; full semantic equivalence is not yet claimed. Two repeated 9.3.1 car DX rebuilds are byte-identical. A controlled one-coordinate source edit generated a DX with one changed render position and recomputed marker-1339; the user confirmed visible DX-only loading. The isolated `$chull` edit **CRASHED_IN_RUNTIME** in both demos. See `research/r-demo2/findings.md`.
