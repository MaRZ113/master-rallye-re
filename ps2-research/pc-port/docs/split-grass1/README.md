# SPLIT-GRASS1 — PS2 Grass and Shrubs in two-player split screen

Opt-in under the existing `PS2SplitScreen=1` key (with `Grass=1` / `Shrubs=1`). Superset of HUD-PORT5 (`dist/hud-port5`, DLL 9715d54e) and PERF3.1
(`dist/perf3.1`, DLL c4ccd412). No patch 0001 / baseline-lock change; no new INI key.

## Evidence

User F10 capture `MRRRenderer/logs/frame-24180-d1-00000670.jsonl` (split-screen Turkey2, DLL 5d4a6102), one frame:

| event | caller rva | payload |
|---|---|---|
| Clear (target+Z, full) | 0x16ba20 | once, before BeginScene |
| SetViewport (slot 40) | 0x161491 | 0,0,640,238 — camera 1 |
| SetTransform PROJECTION | 0x13fa75 (gameplay) | perspective |
| SetTransform VIEW | 0x161a26 (gameplay) | camera 1 → camera-1 world draws |
| SetViewport | 0x161491 | 0,240,640,238 — camera 2 |
| SetTransform VIEW | 0x161a26 | camera 2 (projection **not** re-set) → camera-2 world draws |
| SetViewport | 0x161491 | 0,0,640,480 |
| SetTransform PROJECTION / VIEW | 0x161ed3 / 0x161fdc | UI |

Static (retail PE, frame scheduler `0x653080`): for every active camera it writes the camera viewport
(`+0x78..+0x84`), binds the camera through the renderer (`vfunc +0x24`), calls `+0x08`, the entity traversal
`0x509680` and `+0x20`. After the loop it writes the **full** viewport into manager camera slot 0, binds that
camera again (`+0x24`), then `+0x08` and `+0x18` (UI). So at the UI boundary the renderer's current camera is
camera slot 0, which the SPLIT-SCREEN1 certificate (`race_split_camera`) accepts as one of the two pass cameras.

Why the old proof never admitted: it was cleared whenever the certified camera changed (camera 2 lost
`projection_site`), `observe_world_draw` required a full-screen viewport, and the UI-boundary viewport (full)
never equalled a half viewport.

## Design

Only when `courseintegration::certificate(d,single,split)` reports a `SplitScreen` certificate
(`Ps2RaceMode::SplitScreen`, i.e. `PS2SplitScreen=1`, two active cameras, the current renderer camera certified):

* `CourseWorldProof::split` (`CourseSplitProof`, `renderer/course_objects.hpp`) keeps one `CourseWorldPass` per
  camera of the frame (max 2; a third camera clears everything): camera, view, projection, viewport, back
  buffer/depth, world draw. Frame, device, reset generation, race generation and owner lifetime are shared keys;
  any change starts over. The existing render-target, Z-clear and BeginScene/EndScene hooks reach the passes
  through `invalidate_depth()` / `clear()` (no patch change).
* Gameplay PROJECTION (0x13fa75): verified native == effective shadow, perspective → pass projection and the
  frame's gameplay projection. Gameplay VIEW (0x161a26): verified view; the pass projection is the current device
  projection only if it equals the effective shadow **and** the matrix proven at the gameplay projection site in
  this frame (camera 2 inherits, nothing else can).
* First world draw of a pass: view/projection unchanged, Z on/LESSEQUAL, target is the back buffer, depth present,
  the draw still belongs to the pass camera (same race/owner), viewport inside the target with depth range 0..1.
* UI boundary (`before_ui`): one full evaluation per frame (`course_split_admission`): all single-path checks per
  pass, exactly two passes of two distinct cameras, the UI certificate is a split certificate of the same course,
  race and owner whose camera is one of the passes, viewports disjoint, current target/depth equal each pass's.
  Then for each pass: capture states + viewport, set the pass viewport, apply the grass states with the pass
  projection (CPU view as in the single path), draw, restore states and finally the UI viewport.
* `CourseObjectTransaction`: optional viewport slot (`capture_viewport`, `apply_viewport`, restored last in
  `restore`, reported to the tracker as slot 40 = `SetViewport` in `method_names.hpp`). A failed viewport setter
  stays pending and is repaired like every other slot; the single-camera transaction never touches it.
* Fail closed: any failure logs one `ps2_grass_gate` with `"mode":"split_screen"` and a reason (e.g.
  `split_pass2_camera_or_world_draw_missing`, `split_ui_camera_not_a_pass`, `split_viewports_overlap`); a draw or
  restore failure disables the category exactly like the single path.

Single camera: identical decisions and calls (the split state stays empty; the transaction reads/writes no
viewport). The Turkey3 puddle preview (`CourseObjects`) is unchanged and still single-camera only.

## Logs (Diagnostics=1)

`ps2_grass_build` (`"mode":"split_screen"`, pass), `ps2_grass_draw` with `"mode":"split_screen"`, `ui_camera`
and per pass `camera`, `viewport`, `sprite_candidates`, capture/viewport/apply/draw/restore HRESULTs.

## Tests

* `ps2_course_objects_contracts`: `split_passes` (pass opening/selection, third camera, key changes, hook
  cascade), `split_viewports`, `split_admission` (every flag, stale keys, UI camera, one pass, duplicate camera,
  overlapping/out-of-target viewports).
* `ps2_course_object_transaction_contracts`: `split_viewport_transaction` (both halves restored to the UI
  viewport, slot 40 records read synchronously, no-op equal viewport, invalid/failed get, failed setter rollback,
  later state failure rolls the viewport back, failed viewport restore stays pending and blocks a new capture,
  single-camera transaction never touches the viewport).

## Not covered

Runtime visibility is PENDING_USER (see `runtime-ab.md`). LAN races stay Stock (SPLIT-SCREEN1).
