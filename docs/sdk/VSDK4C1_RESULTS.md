# V-SDK4C.1 — material and visibility stabilization

26 October 2026, `research/vehicles`. **Offline and Windows application validation;
new candidates are not yet gameplay-qualified.** No Paint Studio phase started.
Old runtimes were retained after the owner's instruction to continue without deletion.

## Run and compare

- Studio: repository `Rally-Workshop.cmd`.
- Pajero only: `.research-output/vehicles/vsdk4c1/candidate-pajero-final/Launch-SDK-Roster.cmd`.
- Subaru glass only: `.research-output/vehicles/vsdk4c1/candidate-subaru/Launch-SDK-Roster.cmd`.
- Detailed private evidence: `.research-output/vehicles/vsdk4c1/`.
- Editable, source-only profiles and audit: `research/vehicles/vsdk4c1/`.
- To edit the updated Pajero in Studio, Open project:
  `.research-output/vehicles/vsdk4c1/pajero-author-r3/project`.
  Existing owner Workshop projects are not silently replaced.

The two candidates deliberately do not combine the new Pajero and Subaru changes.
They preserve the existing 30-entry roster, identities, UI, physics, audio and
cameras. Previous candidates remain available. Do not migrate experimental saves
between candidates; ordinary per-candidate settings remain editable as before.

## Functionality matrix

| Feature | Implemented behavior | Boundary |
| --- | --- | --- |
| Texture Binding v2 | Existing owned slot 0; existing opaque environment slot 1; variable-length names and different power-of-two dimensions | No new stage activation, unknown special shaders, or uncoordinated native light/glass switch edits |
| Structural writer | Length-prefixed record splice, reparse and exact other-record/geometry/UV/suffix checks | Receipts describe splices; shifted suffixes are not misreported as arbitrary binary differences |
| Alpha compatibility | Opaque alpha interpreted by native state; blended opacity classes checked; cutout coverage retains both sides of threshold128 | Different alpha distributions can visibly change opacity/masking; explicit warnings, not a promise of interchangeable art |
| Picker | Compatible-first, search, compatible-only filter, counts, compact rows and independent large texture preview | Existing project-owned resources only; no implicit import/recolor of shared art |
| Reflection Strength | Source-relative vertex-alpha multiplier0..2 for independent opaque environment draws; save/reopen/build/history | Source zero stays zero, saturation clamps; blend/test/shared vertices and special families remain read-only |
| Reflection mask | D cycles composed/base/vertex/mask; mask is texture-alpha × vertex-alpha, non-env dark | Diagnostic overrides coverage; not a native beauty render or semantic paint mask |
| Previewer controls | F3 mode statuses, permanent F1 hint, complete F1/offline Help; K/W/E/B/D/Z/C/A and layer/model controls | NONE is marked preview-only; C switches generic cases, not simulated impacts |
| Pajero | Source-cull-disabled reverse faces; qualified opaque layered island and reflection mask; contoured lamp housing | GT4 environment image and housing remain documented MR approximations |
| Subaru | UV-only continuation of V-SDK4C repaired glass, with stock-MR repeating crack placement | Four logical controllers; physical side windows share their zone; no third shattered state |

All edits use shared Core and existing writers. Texture pixels are not mutated
by rebinding. The SDK's16MiB per-texture/power-of-two admission policy is a bounded
authoring gate, not a new claim about the maximum possible engine texture size.

## Native and GT4 evidence

Exact PC EXE SHA256 is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA/Ghidra inspection of loader `005528B0` confirms sequential u32-length strings;
same-name-length and same-image-dimensions were writer limitations. Existing
shader evidence at `00586150` qualifies environment stage COLOROP18:
`baseRGB + baseAlpha * environmentRGB`, with baseAlpha from texture and vertex
alpha. This is why opaque reflection weighting is separate from window opacity.
Source/assembly notes: `research/r4d_1/texture-stage-map.md`, `alpha-path.md`;
new private REA snapshot/evidence and exact-byte disassembly are in
`vehicles_scratch/vsdk4c1-*`. Pseudocode is analysis evidence, not original source.

Original GT4 inputs are now under
`E:/Games/GT_Model-Tools/VOL/GT4-Beta_Extracted/extracted`.
Menu/race `mits0038` SHA256 still match `ff5b4e22…b2e207f` /
`3bc554b1…bd9aea7`. Final reconstruction was rebuilt and validated from these
originals; the retained old decoded cache was not used as final build authority.

### Pajero materials and visibility

The apparent Nikon-side defect includes cabin/frame geometry in a mixed-opacity
atlas: source shape8/packet1 becomes frontend draw74 plus an opaque continuation
(race draw73 plus continuation). Complete filtered UV-footprint proof identifies
18 unity-opacity triangles. Remaining18 stay blended. Unique oriented-triangle
partners in source alpha-only shape10 and generated-environment shape9 recover
the reflection weights; RGB/UVs are preserved. Alpha-only weights are never used
as window opacity. The large exterior livery's existing environment assignment
is retained rather than blindly making every draw reflective.

Source `cull=false` was being lost. Opt-in `source_backfaces` emits only missing
reverse triangles with independent inverted normals:43 menu and28 race source
draws, including guard, mudflaps and relevant interior details. Existing reverse
faces are detected to avoid duplicates. Source `cull=true`, wheels and global MR
culling are unchanged. This is geometry representation of a source render state,
not a speculative winding flip or global cull hook.

Both old rear caps had matching winding/normals. With owner approval the new
`contour_housing` uses the actual sloped glass perimeter, a1mm rearward inset,
inward wall normals and rear planes behind source lens bounds. It replaces the
earlier AABB walls, which protruded, and the rear-cap-only lateral gap. Original
glass/lens geometry and images remain. Extreme oblique views can still hide some
deep lens detail behind the source frame; do not infer a missing lens from that
alone. Actual race views remain an owner acceptance gate.

Final resources: complete10531 vertices/8780 triangles/227 draws;
race4067/2862/123; wheel1192/1076/24 unchanged. Only Pajero car.dx, complete.dx
and one additional reflection-weight atlas differ from the previous package.
Existing DXT bytes are identical. Per-vertex native damage masks are regenerated
for the new topology, so the Pajero extension/patch payload hashes legitimately
change; allocation/preflight and original-instruction replay pass.

Texture charge increases13,086,724→13,611,012 bytes (+512KiB), within the
vehicle's16MiB policy. A four-family serialized race sequence with explicit
synthetic8MiB world/UI reserve charges33,092,868 bytes, with zero warm-pass
evictions. This is a bounded LRU prediction, **not measured gameplay FPS** or
proof of arbitrary track residency. PERF2 bulk-reader code remains unchanged.

### Subaru glass

Input is the actual V-SDK4C candidate race DX
`ebfa6be3987ab9c97de01253b75bd61e49e0a0e8d7c4714b9a3f36f46b4eec39`,
not the original frozen mixed-glass mesh. The side shell is continuous across
physical panes. Previous normalized0..1 UVs stretched one crack pattern across
the side. New explicit projection ranges follow Navara's repeating side/rear
layout; front uses the stock inset range. This is intentional adapted stock MR
art, not recovered GT damage data. Source positions, normals, vertex colors,
intact UVs, lamps, textures, controls and collision suffix are unchanged.

Output car SHA256:
`3a3e00915a1406029485c08da9863587d64c2f21f175f429f89bb32811b73f91`.
Ordered hash-pinned glass profile layers reproduce original redistribution then
UV continuation; each intermediate hash is enforced. Native extension/patch ops
and plan are byte-identical to the V-SDK4C baseline. Front/rear/left/right remain
the only proven logical controllers. Offline case selection is not impact routing.

## Validation and evidence index

- `tests-final.txt`:822 Windows synthetic tests PASS,1 optional skip.
- `zoom-windows/validation.json`:56 fresh actual Windows zoom captures, seven
  scales in embedded/detached windows; channels/nearest/cursor anchor and original
  BGRA/PNG invariance PASS.
- `gui-binding/gui-validation.json`: actual Tk picker, visible addon/stock GPU
  edits, save/reopen, builds, Undo/Redo/Restore; restored stock emits zero overrides.
- `picker-full-preview.png`, `picker-preview-evidence.json`: mapped picker with
  real delayed texture raster, not an empty unmapped-window screenshot.
- `gui-reflection/gui-validation.json`: same full workflow for native opaque
  reflection weight;25,564 addon /132,906 stock changed GPU bytes at multiplier.25.
- `stock-controls.json`, `addon-controls.json`: actual native window key events,
  K render-state cycle, mode-label roundtrips, orbit/pan/zoom/pick/focus/reload.
- `pajero-final-source-validation.json`: source decoding, deterministic rebuild,
  native resource semantics and every texture reference PASS.
- `pajero-final-visibility/`:64 fixed-camera CW/CCW/NONE and env/mask captures;
  `lamp-close-*` comparisons inspect both front sides. GPU inspection only.
- `glass-validation/`:64 captures, named zone ownership, exact UV continuation,
  original x86 switch replay and byte-identical native deformation PASS.
- `pajero-native-damage.json`: original native instructions, ABI/passthrough and
  alpha ownership; four additional GPU captures from actual replay buffers with
  reflections on/off (`damage-preview-evidence.json`); coincident position groups
  split0, coverage alpha lost with
  adapter0. `pajero-native-brake-validation.json` and final brake captures PASS.
- `candidate-preservation.json`: resource ownership, untouched other families,
  physics/UI/audio/camera and original EXE/DLL hashes. Only documented mutable
  player-state paths are excluded, using the existing runtime policy.
- Both candidates: sealed resource, launch-environment and private native
  allocation self-tests PASS. None of these launches a race.

## Owner gameplay checklist

1. Launch **Pajero final**. Inspect intact front-left/right and rear-left/right;
   check headlamp backing, guard and front/rear mudflaps under normal game culling.
2. Inspect Nikon-side frame/livery with reflections on/off, then after damage.
   Check for transparent solid trim, bright seams or alpha loss. Brake/release
   from both rear sides; confirm no regressions in lamps, fitment or menu speed.
3. Launch the separate **Subaru** candidate. From a fresh undamaged race, test
   front, rear, left and right impacts independently; compare cracks to Navara.
   Side windows sharing a zone is expected. Headlamps/intact other zones must remain.
4. For both: stock/Lancer/Subaru/Pajero mixed player/AI use, finish/Results/re-entry.
   Actual collision-to-zone triggers, D3D8 ordering, damaged reflections and
   performance remain human gameplay gates.

Source-only archives are in `.research-output/vehicles/vsdk4c1/review/`.
No retail/GT resources, captures, compiled executables or private REA snapshots
are included. Local phase commit IDs are recorded in COMMIT_LEDGER.md; no push.
