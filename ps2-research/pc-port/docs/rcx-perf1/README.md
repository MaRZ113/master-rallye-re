# RCX-PERF1: course culling for imported courses

## Problem (owner: RCX stages cost much more than retail ones)

PerfTiming logs of host-rcx-01 (2026-11-14 .. 11-17), race windows only, overlay off:

| Course | atmo_world | atmo_upload | course draws accepted / frame | bytes copied / frame |
|---|---|---|---|---|
| Italy2 (retail) | 1.22 ms | 0.26 ms | 119 | 0.32 MB |
| France1 (retail) | 1.14 ms | 0.30 ms | 90 | 0.45 MB |
| RcxScottish2 (RCX-07/08, with lighting package) | 4.3-4.7 ms | 1.5-1.8 ms | 396 (constant) | 8.1-8.4 MB |
| RcxScottish2, night (headlights) | + atmo_headlight 5.6-5.9 ms | | | |

(`ui_collision` 3 ms in some RCX windows is the F11 collision overlay; 0.02 ms when it is off.)

The RCX numbers are the same in every window: the whole course is submitted every frame. Retail course DX
files carry hierarchical render batches plus a sector visibility graph (tag1500, 48 batches in France1), so
the game submits only the batches visible from the camera's sector. Course Studio writes the Retail cooker's
flat layout (one batch, no tag1500), and its records were chunked in authoring order, so each of the 407
RcxScottish2 records spans ~770 m of the 2.4 x 3.1 km stage (Italy2: 981 records, ~100 m each).
Every submitted draw pays the renderer's per-draw work (Atmosphere relight + ring upload, one headlight
pass per lit draw at night, classifiers) and the GPU cost.

## Fix

1. **Converter** (evotracks `tools/evo2_tracks/render_batches.py`, `rcx_to_course.py --render-tile 256`):
   a material's triangles are grouped by the 256 m ground tile of their centroid before the Retail-sized
   chunking (<= 2000 vertices / 4800 indices), so each record covers at most one tile.
2. **Renderer** (`renderer/course_cull.hpp`, `course_cull_native.hpp`): for course draws of the native course
   loop (0x57707e) with identity WORLD, during a valid race certificate, on courses listed in
   `PS2Port.ini [CourseCull] Courses` (default `Rcx,Evo2`), the world box of the draw's vertex range
   (cached per buffer generation/revision) is tested against the VIEW*PROJECTION frustum and, with linear
   fog, against FOGEND as an eye depth. A culled draw is decided in `atmosphereintegration::observe`
   (first handler), skipped by `atmosphereintegration::begin` and consumed by `groundintegration::draw`
   (handled, S_OK, nothing drawn). Retail courses are not touched by default.

```
[CourseCull]
Enabled=1          ; Ctrl+Alt+K toggles at runtime (course_cull_toggle record)
Courses=Rcx,Evo2   ; RaceTest ids or prefixes, * = all courses
FogCull=1          ; skip boxes deeper than the linear fog end
MaxDistance=0      ; optional radial limit, m
Margin=2           ; m
Stats=1            ; course_cull_stats every 600 frames
```

## Offline estimate (evotracks `tools/rcx_tracks/rcx_cull_eval.py`)

Chase cameras along the route, vertical FOV 55 deg, 16:9; see the host owner note for the table of the
installed packs.

## Not done

* A real tag1500 / hierarchical batch writer in Course Studio (Retail-equivalent native culling) needs RE of
  the runtime sector traversal (render queue 0x562810 is fed by it); the renderer cull covers the cost now.
* The flat layout still makes the game traverse every record on the CPU (cheap: the per-draw cost is in the
  renderer and the GPU).
