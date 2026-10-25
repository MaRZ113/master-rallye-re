# COURSE-RENDER-FIX1 — SpainS2 reflections and race lifecycle

Scope: the PS2 port proxy only (`PS2-pc-port-proxy`, one `d3d8.dll`). The course converter, the physics and the birds are not
touched. Everything new is off or measured: Stock stays the default of every other feature.

Input of this phase: session log `session-20261025-044803-10960.jsonl` (7 races, cut at 16 MiB), a screenshot of the
ReflectionDebug=2 view on SpainS2, the F10 draw-order captures of earlier sessions and the current sources.

## 1. Black ground in the SpainS2 reflections

### Cause (proven offline, two independent pieces of evidence)

The environment target of a car is `0.625 x static term + 0.375 x flipped frame buffer` (64x64). The frame buffer is copied
when the first car draw of the frame arrives, as on the PS2 (the PS2 draws the course first, then the car).

* **The target itself** (`evidence/spains2-env-view.png`, `tools/reflection_evidence.py`): subtracting the static term
  (`PS2EnvSource64x64.gxi` x 80/128, rows reversed as uploaded) leaves a frame buffer term of exactly 0 (|difference| < 1 on
  a 0..255 scale) in target rows 0..19 (= the lower 30% of the screen, the ground) and 78..92 (= 0.376 x ~240, a bright sky
  gradient) from row 24 on. Hills, trees and road are absent from the rows between: the capture saw the sky and nothing else.
* **The draw order** (`evidence/evidence.json`): the F10 capture of SpainS2 (`frame-18300-d1-00051123`, the same race as
  the session grass records) draws, before the first car draw (index 59 of 156 indexed draws), **0 of the 6,215 triangles of
  the terrain class** (vertex format 0x242/0x252: ground with the second noise UV set) and 41 terrain draws after the car.
  All four stock-course captures of earlier sessions (`A-start-stationary`, `E-combined-race-start`, `capture2.0cam`,
  `turkey3` of the stock PC course) draw **100%** of their terrain-class triangles before the first car draw and none after it.

Inside one frame the engine draws in groups of one vertex format, each group sorted by the creation serial of its base
texture (F10 capture: 322-class draws on textures 626..1092, the car 634..651, the terrain 1067..1086 in the converted frame).
Where the car group lands between the other groups is decided by the engine's draw queue and by the data of the course;
in the converted SpainS2 frame it lands before the terrain group, in every stock capture after it. The queue order was not
analysed further (it is engine code, not the converter output), which is why the fix measures the captured frame per race instead
of assuming an order: the order can differ per course, and the same course can differ between sessions or races if the queue
depends on load order.

So on a converted course DX the terrain is drawn after the car; the PS2-faithful capture point (first car draw) then holds
only the sky, which is the static black region the owner saw. It does not change with the car because the terrain never is in
the frame at that moment; the sky changes only with the camera pitch.

### The chain that was checked (what is correct, what was the problem)

| Stage | Result |
|---|---|
| Capture moment | first car draw each frame (`MixedReflectionCapture::capture`, `race_car_fleet_native`/`Scope`); **problem**: before the terrain on converted DX |
| Source frame buffer | MSAA 4x resolved with `CopyRects` (`capture_hresult` 0, `copy_hresult` 0, `capture_source_multisample` 4, 640x480, X8R8G8B8): resolve works, the sky is in it |
| Intermediate textures | 640x480 copy and the 640x448 PS2 frame (box downsample of the copy) are produced from the same call; the flip (frame bottom = target top) is the one confirmed by the quadrant pattern of DIAGNOSTIC ReflectionDebug=1 (docs/diag-reflection2) |
| Final 64x64 target | static pass + framebuffer pass at 96/255, A1R5G5B5; target minus static term = 0.376 x frame (the arithmetic above) |
| Static term | identical to the asset x 80/128 with rows reversed (difference < 0.5 everywhere the frame term is empty): correct |
| Dynamic term | zero in the ground half only because the frame had no ground |
| UV, stage states, blend | unchanged and course independent (docs/reflection-static1, diag-reflection2); the new stage report records the number of env lookups per frame (`served`) and the target hash so the update between frames is visible |
| Converted DX, MSAA, render targets | MSAA and the private targets are fine; the converted DX only changes the **draw order** |

### Fix

`ReflectionCaptureTiming` (PS2Port.ini, default `auto`):

* `inframe` — the old behaviour (first car draw).
* `late` — the target is composed at the typed pre-UI boundary (first UI draw: the whole world and the cars are in the frame
  buffer) and used by the NEXT frame; the in-frame capture of that frame then does no work.
* `auto` — in-frame, but each race measures its own capture: at the 1st, 16th, 48th, 120th and 300th capture of a race the
  bottom third of the 640x448 PS2 frame is read back (150 rows, a few GPU readbacks per race, never in a stock race that
  passes). Three empty samples (>= 85% of the pixels with r+g+b <= 12) switch that race to `late`; three good samples settle
  it in-frame. The decision restarts with every race generation, so a stock course is never switched by an earlier race.

The reading is the proof: the measured quantity is the symptom itself (an empty ground in the captured frame).
Not changed: brightness, car materials, UV, the 80/128 + 96/255 weights, the stage states.

Limits (kept visible): a late capture contains the car itself (the PS2 capture does not) and lags the frame by one; the first
~50 captures of a race on a converted course (about a second at the start line) are still in-frame until three samples agree;
the capture point is a measured proxy for the PS2 order, not a reproduction of the PS2 display list.

### Diagnostics for the next run

`ReflectionStageDiag=1` writes, at captures 1, 2, 3, 30, 120, 480 and 1200 of every race (<= 64 per session), a
`ps2_reflection_stage` record and one PNG (`ps2diag-*/stage-r<race>-f<frame>-<inframe|late>.png`: source frame | PS2 frame |
env target | env minus static term x2.7) with, per stage, the mean colour, the share of black pixels, 8 horizontal bands and a
content hash, the MSAA/format data, the copy/restore HRESULTs and the env lookups per frame. `ps2_reflection_order` lists the
indexed draws of the frame (count, triangles, per vertex format) before the capture and for the whole frame.
`tools/analyze_race_lifecycle.py` prints both as tables.

## 2. Effects after repeated races

### What the log shows

`session-20261025-044803-10960.jsonl` (7 races: SpainS2, ItalyM1, Spain2, Spain1, Turkey1, Turkey3, Italy3):

* single D3D8 device, no Reset; race generations 6, 13, 20, 27, 34, 43, 50; owner lifetimes 1..7; `request_generation` ==
  `successful_generation` in every snapshot; the course certificate was valid in 56 of 97 snapshots (race) and invalid in the
  41 menu/loading ones (`no_current_owner_lifetime`, `pending_or_nonunique_live_membership`);
* `AWAITING_RACE_OWNER` is the `state` field of all 97 snapshots, certified or not: it is the observer state that never
  advances past "waiting" (its `status` field carries the certificate verdict) and therefore **not** a cause;
* grass/shrubs (build + draw), PS2 water (SpainS2, Spain2, Turkey3), HUD damage/map/strips/blur and the fleet participants are
  recorded in every race up to the 6th; no `ps2_effect_*`/`unknown_query_interface`/restore-failure record exists;
* the log stops inside the 7th race: 16,777,215 bytes, 29% of them `race_epoch_snapshot`, 59% `frame_summary`. Anything after
  that is not recorded. Most PS2 diagnostics are claimed once per vehicle or per session, so a failure in a later race could
  not appear in them either;
* intentional gates are visible and are not failures: spline objects on Spain2/Italy3 (`stock_pc_course_no_loose_course_dx`),
  no spline asset on ItalyM1/Spain1/Turkey1/Turkey3, water only where the course has water.

**The failure the owner saw is therefore not in this log and its cause is not established.** No effect was force-enabled and
no global reset was added.

### What the code audit found (and what was changed)

| Latch | Trigger | Reset | Verdict |
|---|---|---|---|
| Grass/shrubs `disable(failure)` after a failed vertex build (single and split path) | one frame with a camera matrix outside the orthonormal tolerance, a non-finite position, or > 16,384 visible points | never (process lifetime) | **defect**: a per-frame data condition switched the layer off for every later race. Now the frame is skipped, counted, and the proof cleared |
| Spline objects `disable("spline_world_vertices_nonfinite")` | one non-finite pose | never | same defect, same fix |
| Reflection `permanently_unsupported_` after a failing MSAA `CopyRects` (INVALIDCALL/NOTAVAILABLE) | a call result of one frame | only Reset | the only latch driven by a runtime result: now cleared once at the next race generation (one fresh attempt per race); format/caps/size latches are facts and stay |
| Pilot/model `disable()` after a failed private draw or restore | device-level failure | process lifetime | kept (the native state cannot be trusted), but every `disable()` is now an event (`ps2_effect_disabled`) with effect, reason, frame, race, course |
| Once-per-session log claims (reflection material, ground detail reasons, spline/grass/water logs) | - | session | logs only; the reflection claims restart with each race generation |
| `ResourceRegistry` (8,192 entries, clears when full) | 1,551 creations in 7 races (about 110 per race) | - | not reachable in this session; recorded per race (`resources.tracked/serial`) |
| `claim_frontend_probe_attempt` (128) | read-only diagnostic | - | not an effect |

These two grass/spline defects are real and fixed, but the log does not show that either happened; they are not claimed as the
cause.

### Diagnostics for the next run (`RaceLedger`, default = `Diagnostics`)

`MRRRenderer/logs/ps2diag-<date>-<time>-<pid>.jsonl` (own 4 MiB stream; never cut by the session log cap) holds per race.
A race is open from its first certified frame until its race generation changes or the certified race HUD has been absent for
30 consecutive presents (about half a second), and at shutdown:

* `ps2_race_start`: course, race generation, owner lifetime, frame, state of every pilot at the start (so state left over from
  the previous race is visible);
* `ps2_race_summary`: course, generation, owner, frames, end reason (`race_left`, `new_race`, `shutdown`), the race epoch
  numbers (`request_generation`, `race_lifecycle_generation`, `successful_*`), per-effect outcome counters (reflection capture and
  body, fleet body/parts/wheels, grass, shrubs, ground detail, water, spline, HUD layers, post effects, models) with the reason
  of every skipped or failed draw (for the PS2 car paths the gate number where a recognised car draw fell back to the PC model:
  `fleet_gate_N`, `model_gate_N`), and the state at the end (requested/active/blocked/reason of each pilot, reflection cache
  occupancy, capture resources, probe decision, tracked resources, session-wide disables);
* `ps2_effect_disabled` the moment any effect is switched off for the session.

`tools/analyze_race_lifecycle.py` turns it into a table and findings: `EFFECT_LOST` (drew on a course in an earlier race,
nothing now), `NO_DRAWS_ACTIVE`, `DISABLED`, `RESOURCE_GROWTH`, `GENERATION_ORDER`, `RACE_NOT_CLOSED`,
`REFLECTION_WORLD_INCOMPLETE`. Intentional gates (course without asset, stock course) are told apart from failures by their
reason. `tools/race_cycle_plan.py` is the repeatable 14-entry sequence (SpainS2, Turkey3, France1, Turkey2 and the stock
controls Italy3, Spain2, ItalyM1, the same car throughout) and checks that the log follows it.

An effect that keeps reporting draws while the screen shows nothing is the second case the owner asked about: the summary then
shows `drawn` counts for the effect and the stage report/PNG shows what the target held; the two together separate "not drawn"
from "drawn but empty".

## 3. Tests and what they prove

* `ps2_diag_tests` (new): JSON, PNG (round trip, CRCs), image statistics, draw ledger, timing decision (schedule, latch, per-race
  reset), 200 simulated races of the ledger (record size bounded), disable log, capped stream.
* `ps2_reflection_capture_tests`: late capture (slot, no work in the consuming frame, failures, state restore), probe latch for an
  empty and a lit ground, readback failures, stage report content, MSAA resolve latch per race; the old in-frame tests unchanged.
* `ps2_port_extension_tests`: 25 simulated race cycles through the extension ledger (25 starts, 25 summaries, shutdown record,
  disable event, stream content).
* `ps2_reflection_pilot_tests`: ini keys, default `auto`, status record.
* `tests/test_course_render_fix1.py`: patch hooks, absence of the session latches, disable log coverage, ini defaults, analyzer
  (healthy 14 races, an effect lost after race 6, disables, growth, generations), the recorded evidence.
* Not proven without the game: that `auto` switches SpainS2 and leaves stock courses alone, the visual result, the readback
  cost, and the cause of the effect loss the owner observed. `docs/course-render-fix1/runtime-ab.md` lists the checks.
