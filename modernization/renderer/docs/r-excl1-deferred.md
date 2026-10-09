# R-EXCL1 — True Exclusive Fullscreen Recovery

**Status: `DEFERRED_KNOWN_BROKEN`. This is a backlog record, not an active implementation phase.** The user has chosen to proceed on supported Windowed/Borderless modes. No Exclusive fix is attempted by the R-GFX5 stable checkpoint.

## User-visible failure

**`CONFIRMED_BY_RUNTIME`, FAIL:** minimizing or losing focus and then restoring a true Exclusive session can produce Error 2010 (“Could not reset the Direct3D device”). This does not mean every Exclusive startup fails: earlier traces showed successful true Exclusive CreateDevice and initial Reset.

The R-GFX5-8 trace summary records a restore case with Exclusive target/outer size 640×480, client size 624×441, style `0x16CF0000`, ex-style `0x108`, and `GetFocus=0`. The game requested Reset at 624×441; the proxy supplied 640×480 with `Windowed=FALSE`; native D3D8 returned `D3DERR_DEVICELOST`. The 16×39 difference is that observed window geometry, not a universal Win32 border constant. Raw capture files are not packaged with this checkpoint, so the historical measurements are preserved as the supplied trace summary rather than presented as a new independent audit.

## Static evidence and current diagnosis

Pristine retail EXE SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, ImageBase `0x00400000`. Read the [R-GFX5-8 static analysis](r-gfx5-8/exclusive-static-analysis.md) for function boundaries, calling conventions, owner lifetime, vtable, exact-build gate and evidence.

| Retail function | VA / RVA | Relevant behavior |
|---|---|---|
| Native owner constructor | `0x00558D50` / `0x00158D50` | Creates/publishes the window/device owner |
| Retail WndProc thunk | `0x00558E90` / `0x00158E90` | Dispatches messages to the native owner |
| Window message handler | `0x0055A4D0` / `0x0015A4D0` | WM_SIZE path can call Reset before forwarding the message |
| CreateNativeDevice | `0x0055AB90` / `0x0015AB90` | Copies selected mode to owner `+0x1C` and `PP.Windowed` |
| ResetNativeDevice | `0x0055AE40` / `0x0015AE40` | Calls native device Reset and resource callbacks |
| ApplyNativeWindowMode | `0x0055AED0` / `0x0015AED0` | Applies the game's saved window/fullscreen transition |
| CheckCooperative | `0x0055AF50` / `0x0015AF50` | Queries cooperative level and has a separate recovery path |
| Native owner teardown | `0x00559260` / `0x00159260` | Releases the device and restores saved HWND state |
| Renderer recreation | `0x0053F350` / `0x0013F350` | Rebuilds the owner and reports mode to Broker |
| Frontend owner comparison | `0x00653080` / `0x00253080` | Compares Broker fullscreen selection with owner mode |

`CONFIRMED_BY_EXE`: owner `+0x1C` is zero for native fullscreen and nonzero for native windowed; the presentation `Windowed` field follows that selection on CreateDevice. The WM_SIZE Reset branch does not first call TestCooperativeLevel. The separate CheckCooperative path distinguishes DEVICELOST from DEVICENOTRESET. This static distinction alone does not show which path executed at the human failure or what native readiness returned at that instant.

`STRONG_HYPOTHESIS`: if the game's live mode owner remains windowed while the proxy owns a true Exclusive presentation, restored WM_SIZE may enter the immediate Reset path before native device readiness. The hypothesis explains the geometry and ordering concerns, but is unconfirmed.

## Unknowns to preserve

- The exact writer of the decorated restore style.
- The native game-owner mode byte at the failure.
- Whether the failing Reset was reached through WM_SIZE before focus/activation completed.
- The native cooperative HRESULT immediately before that Reset.
- Whether focus loss, window ownership mismatch, or both cause the failure.
- A safe synchronization seam that keeps the game HWND owner and native D3D presentation coherent.
- Whether the game can recover without suppressing a genuine native failure.

R-GFX5-8 added bounded event ordering, style-change stack context, exact-retail read-only owner observation and a native TestCooperativeLevel probe immediately before Exclusive Reset. The probe records evidence and forwards the real Reset result unchanged; it does not wait, retry, or alter ownership. Those artifacts are described in the [runtime handoff](r-gfx5-8/runtime-handoff.md). This checkpoint performs no new instrumentation or runtime test.

## Resume constraints

When this backlog is explicitly reopened, start by correlating a short complete R-GFX5-8 session JSONL with the corresponding INI and action. Reconfirm the target EXE SHA before interpreting game-specific owner fields. Then establish the first incorrect transition and a safe lifecycle boundary before considering implementation.

Do not fake HRESULT success, suppress DEVICELOST, patch the original EXE, write an unvalidated owner byte, mutate the HWND after Reset, alias Exclusive to Borderless, or add unbounded Reset retries. Preserve native resource-reset and COM lifetime rules. Keep the Windowed and Borderless behavior accepted by the stable checkpoint.
