# R-UI1-D3a Runtime Validation Handoff

This is the D3a candidate handoff. Verify the DLL SHA256 recorded in [validation.md](validation.md) before use; leave the game executable and assets unchanged. The automated result is `READY_FOR_IN_GAME_VALIDATION`, not visual acceptance. D3a repairs the frontend scene timing gate; it does not change carousel thresholds or prove the visual correction. No Exclusive Fullscreen mode is required.

## Configuration

Use the currently accepted Windowed or Borderless mode at 1920×1080. Keep other display, AF, MSAA, camera, and gameplay settings unchanged during A/B comparison.

```ini
[Display]
Mode=2
Width=1920
Height=1080

[Widescreen]
InterfaceMode=2
CarouselAlignment=1

[Trace]
Enabled=1
FrameSummaries=1
```

The feature is experimental and defaults off. To compare the original behavior, set `CarouselAlignment=0` and restart the game; do not change the setting during a running process.

## Vehicle Select

First run with `CarouselAlignment=0` and record whether the previously observed empty or displaced highlighted slot appears. Restart with `CarouselAlignment=1`, open Vehicle Select, and scroll forward and backward through the beginning, middle, and end of a long list. Keep resolution, display mode, AF, MSAA, camera, and other quality options identical between runs.

Pass when the central card remains under the yellow selection frame throughout scrolling, no card or decoration snaps between margin and center positions, list movement remains responsive, and the large 3D preview still matches the game's selected vehicle. Record any preview mismatch separately; the renderer does not change selection state.

## Race Select

Repeat the enabled test in Race Select, scrolling in both directions through a long list. Pass when the highlighted course/leg card remains aligned, no gap or overlap appears at the left edge, and descriptions stay associated with the game's selected item.

For a representative F10 capture, inspect the bounded UI records for `scene_context_family`, `scene_context_source_frame`, `scene_context_consumer_frame`, `scene_context_age`, `scene_context_phase`, `scene_context_valid`, `scene_context_frontend_allowed`, and `scene_context_rejection_reason`. In the normal UI-before-Source45 order, an early frontend draw should usually show `previous_completed_frame`, source frame N, consumer frame N+1, age 1, valid and frontend allowed. A scene classified earlier in the same frame may show `same_frame_before_draw`. Startup may show `unknown_scene`; a known race should show `race_scene`. Incomplete, stale, or invalidated evidence must not be accepted as frontend.

`carousel_status=context_not_frontend` should no longer be the universal result for eligible frontend draws. `candidate_motion_path` is a valid intermediate state. Promotion requires the existing verified draw and identity checks plus multi-frame travel, retained LEFT evidence, the existing Y lane, center and outer positions, and at least 80 units of observed X travel. A stationary item should not be promoted. `carousel_override=true` is expected only after supported promotion; the selected frame/highlight and unrelated HUD should remain unchanged. The new phase fields distinguish a missing motion proof from an invalid or stale scene context.

## Negative controls and regressions

With the feature enabled, briefly check the main menu and animated decorations, frontend preview, race HUD, pause/unpause, and return from Quick Race. The classifier should affect only packets that exhibit the bounded moving-card signature. Stock and Centered4x3 should retain their original behavior. Keep the currently accepted Windowed or Borderless mode; do not test Exclusive as part of R-UI1-D3.

Fail the test if any unrelated HUD/menu element shifts, a card visibly snaps when its semantic state is learned, the yellow frame and card separate, the list freezes, selection/preview association changes, or Reset/return-to-frontend leaves stale behavior.

## Capture only if the visual test fails or is ambiguous

Press F10 once while the affected element is visible. Keep the matching session JSONL and Trace frame JSONL outside the repository. Do not start another broad capture campaign. Join records using `capture_id` and `trace_frame`; inspect:

- `carousel_status`, `carousel_id`, and `carousel_override`;
- original `anchor_direction` / `margin_requested`, effective `margin_effective_request`, and actual `margin_applied`;
- packet/entity identity, content storage, mode, UI epoch, and current packet X/Y;
- native/effective WORLD transforms, draw HRESULT, and exact restore result.
- scene-context family, producer/consumer frame, freshness phase, frontend authorization, and rejection reason.

On a failed or ambiguous run, report the selected screen, enabled/disabled setting, direction of scroll, element type, whether the draw remained present, and the relevant capture IDs. Do not add raw captures to Git.

Human result checklist:

```text
Vehicle Select forward/backward alignment: PASS / FAIL
Race Select forward/backward alignment: PASS / FAIL
Context no longer universally rejected: YES / NO
Observed candidate/promotion states: ...
One-time snap during classifier learning: YES / NO
HUD/menu decorations unchanged: YES / NO
Large preview still matches selection: YES / NO
Reset and frontend return stable: YES / NO
F10 capture IDs (only on failure/ambiguity): ...
```

If the classifier becomes reachable but the visual result still fails, keep the option opt-in and report `READY_FOR_CLASSIFIER_VALIDATION`; do not loosen thresholds or enable the correction by default. After both carousels and HUD safety pass in-game, a separate R-UI1 closeout may make the correction automatic under PreserveMargins and retire the public `CarouselAlignment` toggle. Until then, keep the A/B control.
