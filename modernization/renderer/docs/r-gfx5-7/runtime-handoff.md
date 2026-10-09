# R-GFX5-7 in-game validation procedure

This build is ready for Windowed validation and a diagnostic Exclusive run. Synthetic tests do not establish GPU/runtime success. Keep foliage diagnostics disabled during display acceptance.

## Windowed tests

Use `[Display] Mode=1`, `Width=1280`, `Height=720`, `RefreshRate=0` for W1–W5. Keep the same configuration through each sequence and restart after INI edits.

- **W1 — Initial size:** start the game, visit the frontend, and enter Quick Race. Confirm a 1280×720 client and no reset loop.
- **W2 — Horizontal drag:** drag the left and right edges repeatedly. Confirm the image follows the client without snapping back.
- **W3 — Vertical/corner drag:** resize height and both dimensions. Try an extreme shape such as 1734×480 if the desktop permits. Check aspect and watch for recentering.
- **W4 — Maximize/restore:** after resizing, maximize and restore several times. The maximized client should own its temporary backbuffer; restore should return to the latest accepted normal target.
- **W5 — Initial versus later size:** start at 1280×720 and drag to another size. Confirm both initial sizing and the later resize are honored.
- **W6 — Combined quality:** after W1–W5 pass, enable PreserveMargins, AF16, MSAA4, Gameplay FOV, and the previously verified MenuFreezeFix. Resize in the frontend and race; check HUD/menu animation, aspect, viewport, and Reset behavior.

If `Width=0` and `Height=0` is useful as a separate smoke test, the first game size should be adopted and subsequent corroborated resizing should update the normal target.

## Exclusive tests

Start with a conservative configuration: `[Display] Mode=3`, a supported resolution (1920×1080 where available), `RefreshRate=0`, stock AA, stock widescreen UI, `[PS2FoliagePilot] Mode=0`, and `Diagnostics=0`.

- **E1 — Startup:** stay in the frontend for at least 60 seconds, then start Quick Race. Confirm true Exclusive, no spontaneous DEVICELOST, and no Error 2010.
- **E2 — Modern resolution:** after E1 passes, test a validated 1920×1080 mode with MSAA still off.
- **E3 — MSAA:** only after E1/E2 pass, enable MSAA4 if supported.
- **E4 — Alt+Tab:** after stable startup, Alt+Tab out and restore. A genuine loss must remain visible and must not be reported as success.

If E1 fails, stop there and keep the logs; do not spend time on E2–E4. Include the complete `MRRenderer/logs/session-*.jsonl` from that run. The first `display_cooperative_transition` with `hresult=0x88760868` and following `display_native_attempt` Reset are the key records. They carry device lifetime/reset epoch, requested/effective mode, requested/sent/returned parameters, native HRESULT, HWND focus/activation context, window styles, maximize/minimize state, and both rectangles. Do not trim those transition records or substitute a screenshot for the log.

## Combined regression

Only after the two display paths pass independently, repeat the known-good Borderless baseline with native monitor resolution, PreserveMargins, AF16, MSAA4, Gameplay FOV, MenuFreezeFix, and the previously validated vehicle reflection mode. Run frontend → Quick Race → AI race → pause/unpause → camera changes → Alt+Tab → frontend → quit. Check UI, preview, vehicles, FOV/culling, cursor behavior, Reset/device-loss state, and clean exit. Keep foliage diagnostics off for this acceptance pass.
