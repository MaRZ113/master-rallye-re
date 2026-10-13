# Turkey3 grass and frontend slowdown correction

Status: implemented; post-fix gameplay confirmation pending.
Evidence source: October13 user sessions and F10 captures using PS2 DLL
0bd68583e87378931c57a530c5673201bcf8017f593075bd1fe7029e5628c72f.

User reports puddles visible, grass absent, startup/menu freezes with either
layer enabled, and recovery after entering/exiting any race. USER_RUNTIME_OBSERVATION.

## Grass rejection

Grass asset verified and loaded64900 sourcepoints in the affected sessions.
No ps2_grass_draw record appeared. The captured gameplay VIEW in
frame-20476-d1-00005663 sequence5 is orthonormal with determinant
-0.9999997573. The old camera helper required +1 and rejects these bytes.
CONFIRMED_BY_SOURCE_AND_CAPTURE_BYTES: deterministic rejection, not a GPU or
texture failure. This is a PC adaptation bug, not a revision of PS2 research.

The camera inverse -translation*R^T is valid for both determinant signs.
Accept orthogonal ±1 matrices; continue rejecting shear, scale, projective or
nonfinite matrices. Reuse native VIEW without invented axis swaps. Native tests
include the actual16 float32 words and a synthetic point five units in front.
No point asset/texture/placement changes, no new material modes.

The first menu gate log had consumed the only rejection log, hiding later
build errors. A separate opt-in one-shot ps2_grass_build record now reports
success/reason/candidate count, even after a menu rejection.

## Frontend work

Both layers previously called live_race_certificate and multiple native state
getters on each typed UI draw before rejecting missing world-frame proof.
live_race_certificate resolves nine race keys. Missing keys invoke full string
pool scans; successful keys are cached. That explains a source mechanism
consistent with cold menus being slow and first-race recovery. STATIC_CAUSAL
HYPOTHESIS until post-fix timings/user test; no fabricated profiler results.

Both private passes now reject missing/stale world proof, wrong thread, scene,
UI consumer, state blocks or an already consumed boundary BEFORE Broker/GPU
queries. The shared certificate helper first requires the existing typed race
HUD context, whose frontend/lifecycle gate precedes missing-key resolution.
Full live camera/course and native target/depth/state validation still follows
for eligible batches. No cached certificate grants later-frame ownership.

Object/grass identity observation also previously triggered the unrelated
France1 foliage48-triangle snapshot probe. The existing draw hook now gates
that probe on FoliageMode/pixel probe only. Observer/raw-interface safety gates
remain shared and unchanged. No additional CPU upload mirror for object/grass.

## HUD fix

User-provided four-file HUD patch is preserved separately as
0003-hud-context-cache.patch. requested_clean_view no longer bypasses the
per-D3D-frame HUD context cache. Strict Clean View/Freecam admission remains
per draw. Original baseline Git objects are unchanged; existing working HUD
edits were neither overwritten nor used as baseline build inputs.

## Validation boundary

See validation.md and build-policy/ for both builds, tests, hashes and an
identical-input incremental rerun. CPU tests/source contracts do not confirm
post-fix gameplay FPS or visible grass. Existing private draws preserve native
state restoration and original game draw HRESULTs; transaction tests retained.

No auto-installation, push, original asset edits or legacy-directory deletion.
