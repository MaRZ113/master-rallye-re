# PS2 Visual Parity Expansion

Status: **IMPLEMENTED_PENDING_USER_RUNTIME** for PORT2/GRASS3 extensions.
The existing Mode4 runtime trace is independently corroborated; new Kia,
destination precision and new-course rendering are not runtime-confirmed.

Repository: `master-rallye-re-general`, `master`. Starting HEAD:
`0bddf7c7bc5e95831f98714ff6231da05ab073ea`. Physics/HUD preservation commit:
`c4ed2db348eae43d7790df561971836bc80f3e80`. Frozen renderer tree:
`e33386bcf682db6983380c499e4928726c758fe0`, unchanged. Source integration and
serial builds were owned by root; two agents independently analyzed reflection
materials and original vegetation sources. No gameplay memory writes, native
spawns, original-asset edits, deployment or push occurred.

## Reflections first

Mode4 is retained with its original source and state policy when the new keys
are0. Its independently checked session13620/frame310 has successful copy,
composition, override/native draw and restoration HRESULTs. New options:

* `ReflectionCoverage=1`: additionally allows only verified Kia Sportage painted group,
  PC record14,234 vertices/206 faces. All206 faces correspond to PS2 root.5
  `carshiny` mode3 at0.001; its full geometry digest is unique across78 protected
  retail vehicle DX files. Tata remains record19,48 vertices/55 faces.
  Kia's `kiabon2`/bonnet diagnostic names are not proof of an isolated hood;
  the complete record spans multiple body regions and is the actual target.
* `ReflectionTargetPrecision=1`: requests private A1R5G5B5 destination storage.
  Unsupported allocation releases any partial pointer and explicitly falls
  back to the existing A8R8G8B8 target. Current generation/native material,
  race ownership, render state and stock coordinate gates remain required.

Per-vehicle shape/hash tables replace the55/48-only prefilter. CPU identity uses
current mirrored VB/IB uploads, resource generations/revisions and draw ranges;
no texture name, historical pointer or draw ordinal selects a body. Diagnostics
are capped separately for Tata/Kia. Original body draws execute once, retain
their native HRESULT and restore texture/COLOROP. Other body/glass/wheel groups
are excluded. Additional instances of these exact verified material groups can
qualify; this is not a player-only or all-vehicles policy.

Audit of the PS2 contract preserves coefficients80/128 ENV and48/128 flipped
framebuffer. D3D8's existing96/255 framebuffer factor remains an approximation
(+0.001470588 absolute). The16-bit control changes destination quantization,
not source decoding/expansion, the blend equation or PS2 GS parity. Raw GXI
alpha does not become that FIX coefficient. Capture remains once/frame before
the first accepted body draw, rather than a guessed PS2 producer checkpoint.
The PC captured texture matrix has +0.5 normal-Y scale versus the PS2 -0.5
expression; basis equivalence is open. Native normal coordinates, projection
and camera behavior are preserved, without a guessed flip or reflection-vector
replacement. MSAA framebuffer copying remains unsupported and fails Stock,
with no stale target use. Reset releases default-pool targets and rebuilds on
a true successful Reset; internal window-mode echo handling is preserved.

## Vegetation second

Fresh canonical material/spatial binding inventory finds generating grass and
shrubs on36/36 courses. Singular `shrub` is not normalized. The verified two-pool
path selects original shared32x32 GRASS1/BUSH1; course-specific particle image
variants are not proved. New Mode2 for each category preloads validated assets
once and selects by exact current certified course, never copying Turkey3 points.
Mode1 remains Turkey3-only. Coverage:

| Course | Grass exact/eligible faces | Grass points | Shrubs exact/eligible faces | Shrubs points |
|---|---:|---:|---:|---:|
| Turkey3 |2797/2912|64900|3702/3835|146498|
| France1 |5192/5193|197680|1463/1463|169932|
| ItalyS1 |3239/3239|125524|1137/1158|75253|

Six full artifacts are pinned by PSM, particle GXI, PC DX and complete artifact
hash. Missing/corrupt/swapped assets reject that course/category. The world
proof is invalidated on course/camera/race/Reset transitions; changing course
clears retained surfaces and uploads the selected private texture once. No
per-frame filesystem reads, full-course scans or additional per-UI Broker
reads were added. Water keeps its original Turkey3-only gate.

Source heights, lattice/jitter, category lifts, textures and duplicate points
are preserved. Only independently exact PC terrain correspondence is used;
nonexact surfaces are explicitly excluded. ItalyS1 route outliers remain in
evidence; no fitted transform removed them. Existing8-unit bins,30-unit window,
distance fade and billboard size defaults0.33/0.4 remain. Full original triangle
activation, host float32 nearest-even reconstruction and view-space billboards
do not reproduce PS2 incremental clipping/history, VU/STQ/projection size caps
or live density. The16384 visible-points/category cap rejects overflow without
thinning.36 inventoried courses does not mean36 runtime-admitted courses.

## Preservation and deferred HUD

RIGID-PORT1–1.3 and HUD0–1.1 source evidence, probes, contracts and blockers were
committed separately.95 unique/local artifact hashes are recorded; ignored
raw captures/collision resources and prior handoffs remain intact. Physics is
paused by user, no investigation continued. `docs/hud-port2-roadmap.md` covers
plate, orange damage, separate rising/fading notification and procedural
RaceLine minimap gates, without implementation or per-draw polling.

## Verification and handoff

Both Win32 Release builds passed, serial `--parallel 1`, canonical reused build
and staging roots. Both generators were rerun twice deterministically; exact
patch/tree checks and proxy exports passed. Baseline24/24 and PS2-enabled30/30
CTest; additional private-input focused7/7 verified ENV/puddles and six grass
assets. Port107 unittest and107 pytest passed. GRASS3 inventory8 tests passed.
PS2 research345 unittest and345 pytest passed with canonical corpora. The broad
frozen renderer Python run has188 passes and1 import error from missingpefile;
that legacy quality-compatibility module is BLOCKED, not silently skipped.
Initial missing Pillow/Capstone attempts and the corrected precision mock and
stale Turkey3-only textual assertion are retained in validation history.

Baseline DLL SHA256:
`011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138`.
PS2-enabled DLL SHA256:
`882555499e7e6854a583dee4b54e289594f350f0ee37324301b704510519bff6`.
Build report and current DLLs are in `dist/current`; original renderer and
read-only Course SDK are unchanged. No new build tree was created. Manual A/B
recipes: `reflection-port2/runtime-ab.md`, then `grass-port3/runtime-ab.md`.
Do not claim PS2 pixel parity from these static/mocked results.

Next: one manual Tata/Kia stock-vs-Mode4/precision comparison, followed by
France1/ItalyS1 switching and HUD/menu checks. HUD implementation follows only
after visual acceptance and widget/resource ownership gates.
