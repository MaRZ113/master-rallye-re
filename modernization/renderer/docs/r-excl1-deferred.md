# R-EXCL1 — True Exclusive Fullscreen Recovery

**Status: `DEFERRED_KNOWN_BROKEN`. This is a backlog record, not an active implementation phase.** Windowed and Borderless remain the supported development modes. No Exclusive fix is attempted by the R-GFX5 stable checkpoint.

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

`CONFIRMED_BY_EXE`: owner `+0x1C` is zero for native fullscreen and nonzero for native windowed; the presentation `Windowed` field follows that selection on CreateDevice. The WM_SIZE Reset branch does not first call TestCooperativeLevel. The separate CheckCooperative path distinguishes DEVICELOST from DEVICENOTRESET.

`STRONG_HYPOTHESIS`: if the game's live mode owner remains windowed while the proxy owns a true Exclusive presentation, restored WM_SIZE may enter the immediate Reset path before native device readiness. New traces confirm the owner/presentation mismatch and an early failed Reset, but do not establish the complete causal chain.

## Unknowns to preserve

- Which code path writes the restored decorated style.
- Exact complete call-stack attribution for the fatal recovery path.
- Whether the premature Reset was initiated specifically by WM_SIZE in every failing case.
- Which original game lifecycle boundary can safely synchronize native game mode with proxy presentation.
- Whether a correct recovery can be implemented without breaking resource ownership, Windowed or Borderless.
- Whether the mode mismatch is the sole cause or one contributor.

## R-GFX5-8 — Additional Exclusive Restore Trace Evidence

The following observations were independently inspected during the stable-checkpoint review in two R-GFX5-8 sessions:

| Capture | Mode | Evidence |
|---|---|---|
| `session-20261009-122510-49004.jsonl` | Exclusive 640×480 | `TestCooperativeLevel` returned `D3DERR_DEVICELOST` while minimized (event 51); the pre-Reset query also returned DEVICELOST (event 61), followed by native Reset returning DEVICELOST (event 63). Effective Reset parameters remained 640×480 with `Windowed=FALSE`. |
| `session-20261009-122644-33496.jsonl` | Exclusive 1280×720 | DEVICELOST at event 51; pre-Reset DEVICELOST at 62; native Reset DEVICELOST at 64; pre-Reset `DEVICENOTRESET` at 90; pre-Reset `S_OK` at 100; native Reset `S_OK` at 114 and 123. |

Both captures recorded this simultaneous Exclusive state:

```text
game_windowed_flag_0x1c = 1
game_window_owner.windowed = 1
game_window_owner.presentation_windowed = 0
effective D3D8 Windowed = FALSE
```

`CONFIRMED_BY_TRACE`: the live game owner reports Windowed while the effective D3D8 presentation is Exclusive. `CONFIRMED_BY_EXE`: owner `+0x1C` is zero for native fullscreen and nonzero for native windowed, as documented in the static owner map above. The causal effect of this mismatch remains unproven.

In the 640×480 capture, the restored decorated HWND was observed with outer size 640×480, client size 624×441, style `0x16CF0000`, and ex-style `0x108`. The game requested dimensions corresponding to that client geometry, while the proxy retained the selected 640×480 Exclusive target and `Windowed=FALSE`; native Reset still returned `D3DERR_DEVICELOST`. The failure was therefore not caused by forwarding 624×441 as the effective fullscreen size. The 16×39 difference is specific to this observed window and is not a universal Win32 border delta.

HRESULTs: `D3DERR_DEVICELOST=0x88760868`, `D3DERR_DEVICENOTRESET=0x88760869`, `S_OK=0x00000000`. The 1280×720 trace shows native recovery readiness and later successful Reset calls, but the earlier failed result had already returned to the game and Error 2010 was still reported. Native success alone does not establish application-level recovery.

Static owner facts remain: `0x0055A4D0` handles the original window-message path; `0x0055AE40` wraps native Reset; `0x0055AED0` applies the game's window-mode transition; and `0x0055AF50` handles cooperative-level recovery. The WM_SIZE path can reach Reset without a prior cooperative query, while the separate readiness path treats DEVICELOST and DEVICENOTRESET differently. See [R-GFX5-8 static analysis](r-gfx5-8/exclusive-static-analysis.md) for the full VA/RVA map, conventions and lifetime evidence.

These are trace-review findings, not a new runtime run. The raw JSONL files are not included in the source repository. The capture identifiers and executable/proxy identities are retained here: pristine retail `MRallye.exe` SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`; renderer DLL SHA256 `fda771e03dc3bc5457d995ea755933f9a3982fc280ece061d5b6329ad9f3f543`.

The following remain unresolved: whether focus loss or the owner mismatch is the sole cause; which safe synchronization seam can keep the game HWND owner and native D3D presentation coherent; and whether recovery can preserve genuine native failures without breaking resource ownership, Windowed, or Borderless behavior.

R-GFX5-8 added bounded event ordering, style-change stack context, exact-retail read-only owner observation and a native TestCooperativeLevel probe immediately before Exclusive Reset. The probe records evidence and forwards the real Reset result unchanged; it does not wait, retry, or alter ownership. Those artifacts are described in the [runtime procedure](r-gfx5-8/runtime-handoff.md). No new instrumentation or runtime test is part of this documentation update.

## Resume constraints

When this backlog is explicitly reopened, start by correlating a short complete R-GFX5-8 session JSONL with the corresponding INI and action. Reconfirm the target EXE SHA before interpreting game-specific owner fields. Then establish the first incorrect transition and a safe lifecycle boundary before considering implementation.

Do not fake HRESULT success, suppress DEVICELOST, patch the original EXE, write an unvalidated owner byte, mutate the HWND after Reset, alias Exclusive to Borderless, or add unbounded Reset retries. Preserve native resource-reset and COM lifetime rules. Keep the Windowed and Borderless behavior accepted by the stable checkpoint.
