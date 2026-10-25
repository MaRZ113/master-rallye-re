# COURSE-RENDER-FIX1 — in-game checks (kit `dist/course-render-fix1`)

Install: copy `d3d8.dll` beside `MRallye.exe` (it replaces the previous PS2 proxy DLL) and use the supplied
`PS2Port.diag.ini` as a template for the `[PS2Port]` section of the existing `PS2Port.ini` (all your other keys stay). Nothing
else changes; assets are the ones already in the game folder. Keep `ReflectionDebug=2` while checking the reflection; set it back to 0
afterwards.

## A. SpainS2 reflections (about 3 minutes)

1. `Reflection=4`, `ReflectionCaptureTiming=auto`, `ReflectionStageDiag=1`, `ReflectionDebug=2`, `Diagnostics=1`.
2. Same car as before. Start SpainS2, wait for the countdown, drive 10 s, take a screenshot at second 5 (the 64x64 target is
   at the top centre). **Expected: the ground half of the target is no longer black (brown/grey from the terrain), the car body
   reflects ground and surroundings and the target changes while the car turns/moves.**
3. Quit to the menu, start Italy3 (stock PC course) with the same car, same screenshot. **Expected: unchanged from the
   previous build** (auto keeps the first-car-draw capture; the log says `timing_now:"inframe"`).
4. Look in `MRRRenderer/logs/ps2diag-*/` for `stage-r*.png` and in `ps2diag-*.jsonl` for `ps2_reflection_stage`:
   * SpainS2: the first reports `inframe` with `world_incomplete:true` and `bottom_third.black` ~1.0; after about 50 captures
     (`probe.incomplete:3`) `timing_now:"late"` and the later reports show `bottom_third.black` ~0 and a lit
     `env minus static` tile;
   * Italy3: `world_incomplete:false`, `timing_now:"inframe"` throughout.
5. A/B of the fix itself: `ReflectionCaptureTiming=inframe` reproduces the black ground on SpainS2 (the old behaviour),
   `late` gives the fixed look from the first frame.
6. The cars are now sorted behind the course by the proxy (`ReflectionWorldFirst=1`): on SpainS2 the in-frame capture must already
   show the ground (`timing_now:"inframe"`, `world_incomplete:false` in the stage reports of all races) and the car is not in the
   target (the car is not drawn when the capture happens). `render_order` in the stage record: `installed:true`,
   `last.vehicles` > 0 and `last.reason:"vehicles_moved_last"` on SpainS2; on a stock course `"vehicles_already_last"` or
   `"vehicles_moved_last"`. `ReflectionWorldFirst=0` is the A/B (old engine order, black ground, `auto` then switches to `late`).
7. Send `ps2diag-*.jsonl` of a SpainS2 race and a stock race (Italy3 or Spain2) in the same session: the `ps2_render_queue` records
   show the material ids of the terrain and the cars on both courses.

## B. Race cycles (about 25 minutes)

1. `Diagnostics=1` (this switches `RaceLedger` on), `PS2Water=1`, `SplineObjects=1`, `GroundDetail=1`, `Grass=1`, `Shrubs=1`,
   `RaceFleet=1` as in your normal setup. `ReflectionStageDiag=0` for this run (less readback).
2. Follow `race-cycle-plan.md` (14 entries, the same car, Esc -> Quit between entries, no game restart). If the effects
   disappear, note the entry number where you first see it. The loss reported after about 15 NEW courses was the race
   observer's 32768 bound on the game string pool (README, "Cause found in the second run"); go past 20 different courses in
   one session (more than the plan, every course only needs to be loaded once) and check that the effects are still there.
3. After the run:

       python tools/analyze_race_lifecycle.py --diag logs/ps2diag-<stamp>.jsonl --session logs/session-<stamp>.jsonl --md report.md --json report.json --min-races 12
       python tools/race_cycle_plan.py check --plan race-cycle-plan.json --diag logs/ps2diag-<stamp>.jsonl

   `report.md` has one row per race (draws counted per effect, `/F` failures, `/off` intentional gate). A finding names the
   race, course and effect. Send `ps2diag-*.jsonl`, `report.md` and the `stage-*.png` of the run.
4. What to look for:
   * `ps2_effect_disabled` lines: an effect switched off for the session (effect + reason + race);
   * `EFFECT_LOST` / `NO_DRAWS_ACTIVE`: the effect stopped drawing; the outcome counters of that race give the reason;
   * an effect with draws counted but nothing on screen: use A (stage PNG) for reflections, the screenshot of that race for the
     rest, and send both;
   * `state.resources.tracked` growing by hundreds per race (`RESOURCE_GROWTH`).

## C. Quick regression (same session)

Car, HUD, lighting, grass, water, birds, boats on SpainS2/France1: compare with the previous kit; nothing is expected to change
except the reflection on converted courses. Alt+Tab once during a race and once in a menu: effects must come back (existing
lifecycle path, unchanged).

## Cost

`auto` reads 150 rows of the 640x448 frame five times per race (less when the first three samples agree); the stage report
reads about 1.5 MB at seven captures per race. `RaceLedger` writes about 2 KB per race. No readback in a race with
`ReflectionCaptureTiming=inframe` and `ReflectionStageDiag=0`.
