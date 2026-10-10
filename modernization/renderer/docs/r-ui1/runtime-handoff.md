# R-UI1-D3 Runtime Validation

This build is an opt-in visual-fix candidate. It is not runtime-accepted. Verify the DLL SHA256 in `validation.md` before using it; keep the game executable and assets unchanged. No Exclusive Fullscreen mode is required.

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

First run with `CarouselAlignment=0` and record whether the previously observed empty or displaced highlighted slot appears. Restart with `CarouselAlignment=1`, open Vehicle Select, and scroll forward and backward through the beginning, middle, and end of a long list.

Pass when the central card remains under the yellow selection frame throughout scrolling, no card or decoration snaps between margin and center positions, list movement remains responsive, and the large 3D preview still matches the game's selected vehicle. Record any preview mismatch separately; the renderer does not change selection state.

## Race Select

Repeat the enabled test in Race Select, scrolling in both directions through a long list. Pass when the highlighted course/leg card remains aligned, no gap or overlap appears at the left edge, and descriptions stay associated with the game's selected item.

## Negative controls and regressions

With the feature enabled, briefly check the main menu and animated decorations, frontend preview, race HUD, pause/unpause, and return from Quick Race. The classifier should affect only packets that exhibit the bounded moving-card signature. Stock and Centered4x3 should retain their original behavior. Keep the currently accepted Windowed or Borderless mode; do not test Exclusive as part of R-UI1-D3.

Fail the test if any unrelated HUD/menu element shifts, a card visibly snaps when its semantic state is learned, the yellow frame and card separate, the list freezes, selection/preview association changes, or Reset/return-to-frontend leaves stale behavior.

## Capture only if the visual test fails or is ambiguous

Press F10 once while the affected element is visible. Keep the matching session JSONL and Trace frame JSONL outside the repository. Do not start another broad capture campaign. Join records using `capture_id` and `trace_frame`; inspect:

- `carousel_status`, `carousel_id`, and `carousel_override`;
- original `anchor_direction` / `margin_requested`, effective `margin_effective_request`, and actual `margin_applied`;
- packet/entity identity, content storage, mode, UI epoch, and current packet X/Y;
- native/effective WORLD transforms, draw HRESULT, and exact restore result.

On a failed or ambiguous run, report the selected screen, enabled/disabled setting, direction of scroll, element type, whether the draw remained present, and the relevant capture IDs. Do not add raw captures to Git.

Human result checklist:

```text
Vehicle Select forward/backward alignment: PASS / FAIL
Race Select forward/backward alignment: PASS / FAIL
One-time snap during classifier learning: YES / NO
HUD/menu decorations unchanged: YES / NO
Large preview still matches selection: YES / NO
Reset and frontend return stable: YES / NO
F10 capture IDs (only on failure/ambiguity): ...
```

After visual acceptance, close R-UI1 and return to R-CAM1-A3. Do not begin camera implementation before this handoff is resolved.
