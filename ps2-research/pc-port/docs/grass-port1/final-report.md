Phase: PS2-GRASS-PORT1 — Turkey3 source-derived preview
Repository: D:/Game/Master Rallye/master-rallye-re-general
Branch: master
Starting/ending HEAD: 3f837f4ddcb27ee1034a4b0753634c92009360ec; unchanged
Preflight: prior uncommitted port work and revalidation files preserved
Frozen renderer tree: 7f9f5a7d9464b7b86ff09a9bf6c34b7ce341682d; unchanged
Reference Course SDK:4244fa0c4d878523c9947f54816bf377cdfb2589; clean/read-only
User screenshots: Turkey3 confirmed; advertisement variation excluded
Source: canonical Turkey3 PSM spatial/detail triangles plus verified original GRASS1
PC counterpart: original turkey3.dx SHA724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8
Eligible grass source triangles:2912
Strict PC matched surfaces:2797 at0.001;115 excluded
Independent coordinate proof:420RaceLine anchors, zero residual, identity transforms
Private source-derived points:64900; not a live visible-plant count
Private bins/size:3456/838320bytes
Private asset SHA:6af6393c444a485b2c648c2a6973a91bd5783db3c0f90269a0d653b2f089cfad
Generator: existing GRASS1 grid/hash/jitter/height; nearest-even input; full triangles
Rendering: one added camera-facing sprite batch at verified world-to-UI boundary
Material: raw original32RGBA; alpha test OFF, SRCALPHA/INVSRCALPHA, depth write OFF
Depth: original PC positive-Z/LESSEQUAL; original depth format unchanged
Size/UV/projection/alpha: explicit PC preview adaptations
Native state: exact retained transaction/attempted failure repair; original UI draw/HRESULT
Reset: real-reset release/resume, echo preserved
Defaults: GrassMode0; other pilots0
Baseline Win32 Release: PASS;24/24CTest
PS2 Win32 Release: PASS;30/30CTest
Python:64/64PASS;0FAIL/0SKIP
Exports/generator/compileall/diff-check: PASS
Baseline DLL SHA: 1a9034453258f9f706c907f270466165f459af87b4daa722e3712074198c1f2f
PS2 DLL SHA: 0bd68583e87378931c57a530c5673201bcf8017f593075bd1fe7029e5628c72f
Live grass runtime: NOT_PERFORMED
PS2 visual parity: NOT_ESTABLISHED
Original game/Course SDK/frozen renderer changed: no
Commit/deployment/push: none
Overall status: IMPLEMENTED_PENDING_USER_RUNTIME

The supplied images show separate PS2 ground tufts where the pictured PC view
has ground texture alone. Different sponsor stands are excluded. HUD/minimap,
body brightness and camera differences are visible, but causes need separate
evidence. The PC session used an enabled VFOV60 policy and an older static-only
reflection pilot configuration, so it is not an untouched-retail/newMode4 A/B.
See visual-comparison.md for image/session hashes and the portability matrix.

Grass is now an actual opt-in PC renderer implementation. It uses no terrain-
texture heuristics, random modern scatter, wind or new course mesh. The private
preparer reuses PackFS/PSM/GXI and GEOM1/SDK readers. It selects original detail-
grass material bindings and Ny>.975, then requires exact PC triangle equivalence.
Original source order, float32 pitch1.33, fixedseed0x30ff jitter, original height
plane and+.33lift produce64900 points on that matched subset. Their source datum
is not inferred from the screenshot or from geometry solely sharing broad bounds.

The runtime loads the pinned source pack and indexes8-unit bins. It selects the
snapped width60 region, applies original radial LUT/cutoff and uses the certified
current gameplay view. Tufts become view-facing rectangles with original32RGBA,
white modulation and mapped distance alpha. Original PC projection/clipping,
preview half-size0.33 and no-depth-write/source-alpha blend are explicit port
choices. Native source terrain and all game assets remain unchanged.

The shared object transaction receives a narrow optional depth/address policy:
old puddle defaults remain depth-write TRUE and WRAP; grass explicitly requests
FALSE/CLAMP/CLAMP. All existing tests remain, with new partial-failure/profile
checks. This is entirely PS2-port source, not a frozen-renderer modification.
Independent grass camera/depth proof operates even with CourseObjectsMode0.
No CPU upload mirrors or F10 capture are required by this source-pack feature.

Only live Turkey3, exact supported PC build, same-frame typed gameplay camera,
subsequent world draw, main target/depth/viewport and typed UI boundary authorize
the batch. Native wrappers restore every state/matrix/texture/stream change;
UP stream0 clearing is covered. Wrong course/state/asset or failed native repair
fails closed. The original native UI draw occurs once with its own HRESULT when
safe; unresolved repair blocks it with the real native error. No draw replay,
global sorting, depth readback, source EXE patch or gameplay/collision work exists.

The feature is a preview, not exact PS2 live population. Full-triangle activation
replaces unclosed incremental clipping/history, source ordering is binned, FCSR
rounding is explicitly selected, and VU residency remains unproved. Original
renderer projection factors and the56projected size cap are not mapped to PC.
RGBA alpha normalization, PC UV/projection and batching are not GS pixel parity.
115unmatched eligible surfaces are omitted. Frame sprite_candidates counts are
CPU submissions, not proven visible tufts. No screenshot or unit test upgrades
those unknowns to runtime confirmation.

The implementation and original-asset integration mocks passed; two independent
Release proxies built serially and exports/generator hashes verified. A final
PS2 rebuild clarified the log count field from visible_sprites to sprite_candidates;
all30CTest/64Python checks reran, preserving the separately built baseline.
Old reflection/course handoff hashes are retained. Native/assets/reference
source worktrees remain intact, and no broad commit sweeps prior work into this phase.

The next single step is the Turkey3 GrassMode0/1 A/B from runtime-ab.md: same
Free Camera bookmark/settings, all other pilots0, inspect silhouette, source
height, fading, near-camera size, terrain occlusion and original HUD/car state.
HUD source artwork/minimap math are useful next candidates after this baseline
visual check, but no HUD/camera/reflection expansion is started here.
