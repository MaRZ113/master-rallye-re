# R-GFX5-8 — in-game validation procedure

Status at the time of this phase: **READY_FOR_DIAGNOSTIC_RUNTIME**. Windowed had a source-level correction and synthetic coverage. Exclusive had additional static evidence and bounded diagnostics, but no recovery fix. The game was not launched during the R-GFX5-8 implementation session.

## Candidate identity

DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll` in `master-rallye-re-general`. SHA256 `fda771e03dc3bc5457d995ea755933f9a3982fc280ece061d5b6329ad9f3f543`, size **1,531,392 bytes**, PE32/I386. A new session JSONL header should contain `proxy_version=R-GFX5-8` and this `proxy_sha256`. The EXE, INI and previous candidate remain unchanged; automatic deployment is not part of this procedure.

Use the current build containing PC-VISUAL-PILOT1 upload provenance; do not substitute the earlier pre-foliage DLL. Source, tests and documentation are included in the [source handoff](R-GFX5-8-handoff.zip); the DLL and game assets are excluded.

## Windowed W1–W6

Start with `[Display] Mode=1, Width=1280, Height=720`. Keep AA/UI at Stock, FOV off and foliage diagnostics off. Do not maximize or minimize before W1/W2.

| Test | Action | PASS criteria |
|---|---|---|
| W1 | Immediately drag the right edge after startup | Width and native backbuffer follow the HWND; height remains 720; no snap-back or Error 2010 |
| W2 | Restart and immediately drag a corner | Both axes follow the HWND without an initial Maximize/Restore |
| W3 | Set `Width=0, Height=0`, restart and drag horizontally | Existing auto-size behavior remains intact |
| W4 | Resize the normal window, then maximize and restore several times | Maximized backbuffer uses the OS client; restore uses the latest normal target |
| W5 | Minimize/restore, then perform another normal resize | No 0×0 target, stale size pinning or Reset loop |
| W6 | Resize to a wide client near 1734×480, then to a narrow shape | Backbuffer/aspect remain stable; validate PreserveMargins separately |

`windowed_resize_admission` should show original requested dimensions equal to actual client dimensions, `initial_window_commit_complete=true`, `decision=accepted_hwnd_client_change`, and both `normalized_logical` axes equal to the new client. The following `display_native_attempt` Reset should send these dimensions and return S_OK. Admission alone does not prove native success. On failure, retain the corresponding decision, previous committed style/ex-style and actual result.

## Exclusive E1–E6

Start with `[Display] Mode=3, Width=640, Height=480, RefreshRate=0`; keep AA/UI at Stock, FOV off, MenuFreezeFix off, foliage Mode=0 and Diagnostics=0. Keep the remaining settings fixed for the control run.

| Test | Action | PASS criteria |
|---|---|---|
| E1 | Remain in the frontend for at least 60 seconds | True `Windowed=FALSE`; startup and initial Reset succeed; no spontaneous Error 2010 |
| E2 | Minimize or Alt+Tab once, then restore | Device recovery completes without Error 2010 |
| E3 | Only after E2 passes, repeat several cycles | No accumulating Reset/resource/focus errors |
| E4 | Use an enumerated 1920×1080 mode and repeat E1–E3 | True Exclusive recovery works at the higher resolution |
| E5 | Only after conservative settings pass, enable MSAA4 | Native capability and Reset remain valid |
| E6 | Frontend → Quick Race → race → frontend → quit | Device remains usable and exits normally |

If E2 produces Error 2010, stop that run and retain one shortest complete session JSONL from `MRRenderer/logs/`, the matching INI and the exact minimize/restore action. Further high-resolution/MSAA/race repetitions and large F10/RAM/VRAM dumps are unnecessary at that point. A pristine retail executable is preferred for read-only game-owner observation; message/native diagnostics remain available on modified executables, while the new owner observation remains unknown. Existing feature-local compatibility is unchanged.

## Evidence supplied by a new capture

1. `display_window_message`: the first WM_STYLECHANGING record, old/new style and `transition_stack` identify possible style-change ownership. A stack supports call attribution; it is not by itself a causal verdict.
2. Before/after WM_SIZE records establish whether Reset is nested inside the game WndProc and show preceding activation/focus events.
3. `window_context.game_window_owner` on a validated pristine executable records `+0x1C` (`windowed`), PP.Windowed, HWND, saved style and flags. `windowed=1` with `native_windowed_flag=0` establishes disagreement between native owner and presentation state.
4. `display_reset_readiness` records the cooperative HRESULT immediately before native Reset. DEVICELOST indicates the device is unavailable; DEVICENOTRESET before a failed Reset requires another explanation. The probe does not change the result.
5. `display_native_begin` → readiness → `display_native_attempt` records parameters and results. Shared `event_sequence` and `device_lifetime_id`/epoch correlate them with window and focus events. Native errors remain genuine.

`transition_owner=renderer_window_commit` identifies a renderer-owned Windowed/Borderless placement. `game_or_os_unresolved` means attribution remains unavailable. Preserve the `display_watch` quality metadata; if it reports partial/unavailable observation or `display_message_budget_exhausted`, retain that limitation with the log.

Create a compact summary with:

```powershell
python modernization/renderer/tools/audit_quality_runtime.py "PATH\session-R-GFX5-8.jsonl"
```

`observed_reset_while_device_lost` is not a visual PASS/FAIL result; it preserves cooperative readiness alongside the native result. The original JSONL is required to establish the first style/focus event.

## Combined regression after independent PASS

Use the previously accepted Borderless or Windowed mode with PreserveMargins, AF16, MSAA4, Gameplay FOV, MenuFreezeFix and ViewDependent2D. Run Frontend → Quick Race → AI race → pause/resume → camera changes → Alt+Tab → frontend → quit. Check HUD stability, preview/FOV/culling, AI reflections, brake lamps, cursor behavior and clean exit. Keep foliage diagnostics off. Backdrop status remains `BACKDROP_ASSET_EXTENSION_REQUIRED`.

Record W1–W6 and E1/E2 results (then E3–E6 if E2 passes), Error 2010 occurrence, and combined-regression result. R-GFX5 closeout requires independent in-game PASS for both display modes. R-CAM1, Photo Mode and HD UI are outside this validation procedure.
