# R-GFX5-8: initial resize correction and Exclusive ownership checkpoint

Status: **READY_FOR_DIAGNOSTIC_RUNTIME**. Windowed has a causal source fix and temporal synthetic coverage. Exclusive has new static evidence and targeted observation, with no speculative recovery mutation. Both still require in-game validation; R-GFX5 remains open.

The work started at `88bf3decd411b8b65e11e8b801650867097d186b` in `master-rallye-re-general`, branch `master`. The CPU-upload handoff `f43d720e08961791ad46875af0d15430ed555e02` is an ancestor. No branch/worktree was created or switched. Existing Observatory edits are outside this commit. No game binary or PS2 research was edited.

## Windowed cause

`CONFIRMED_BY_SOURCE`: `QualityPipeline::plan()` removes fields that still equal the proxy's previous override by restoring their previous logical value (`UNMIX`). In R-GFX5-7, `select_display()` passed that normalized descriptor to `corroborated_windowed_resize()`. Thus the safety check compared a hybrid descriptor with the real client, rather than comparing the original game request.

| Moment | Original request | Old logical baseline | Old admission input | Actual client | Result before this fix |
|---|---|---|---|---|---|
| Configured CreateDevice | 640×480 | 640×480 | initial target | 640×480 before commit | commit 1280×720 |
| Immediate horizontal drag | 1447×720 | 640×480 | 1447×480 | 1447×720 | reject; native 1280×720 |
| Maximize | 1900×1030 example | new request | actual maximized client | 1900×1030 | adopt temporarily |
| Restore | 1280×720 | refreshed to normal request | 1280×720 | 1280×720 | normal baseline catches up |
| Later horizontal drag | 1384×720 | 1280×720 | 1384×720 | 1384×720 | admit |

The maximized example is a synthetic size, not an observed monitor size. The R-GFX5-8 validation record includes the 1447×720 rejection, 1384×720 later acceptance, and Width/Height=0 944×480 control. Raw session JSONL was unavailable for independent recomputation.

`CONFIRMED_BY_SYNTHETIC_TEST`: the new startup-order test failed against the unchanged R-GFX5-7 source on the first horizontal resize. The same assertion passes after the fix, without a maximize/minimize step. Width/Height=0 previously worked because the unchanged axis did not differ from the 640×480 logical baseline.

## Windowed ownership correction

`select_display()` now evaluates `windowed_resize_decision(requested, current)` using the original descriptor retained by `plan()`. A proven resize updates both logical dimension axes together, as well as the planned native dimensions. This prevents both admission failure and incorrect viewport remapping of an unchanged axis.

The first normal target still comes from INI/game dimensions and is centered by the existing successful native/placement transaction. `initial_window_commit_complete_` becomes true only after matching client synchronization; it does not depend on a timer or maximize. A new normal target is accepted only after native Reset succeeds. A failure preserves the last accepted target and effective descriptor.

Existing guards remain: same HWND, valid nonzero bounded dimensions, actual original-request/client agreement, stable style/ex-style/menu, decorated normal window, no minimize, no renderer commit or shutdown. No style ranges or geometry heuristics were broadened. An uncorroborated game request stays at the accepted target. A successful live resize or move retains the current outer placement without another `SetWindowPos`. Maximize temporarily uses the OS client and preserves the latest normal target. Restore/minimize retain the established contracts.

Equivalent renderer commit echoes still return through the existing dedicated branch, without a native Reset, resource generation transition, or mirror invalidation. New tests cover an echo followed immediately by the first real drag. The `Device8::Reset` resource path was not changed.

## Bounded diagnostics

`windowed_resize_admission` records the raw request, normalized logical dimensions, planned native dimensions, INI initial size, current normal target, actual client, old committed client/outer/style, initialization/commit state, and an explicit decision. It describes a planned admission; `display_native_attempt` supplies the actual native result. There are no invented `pinned_width/height` fields: R-GFX5-7 had already replaced them with the normal target.

The message observer covers only WM_SIZE, WM_ACTIVATE, WM_ACTIVATEAPP, WM_SETFOCUS/KILLFOCUS, WM_STYLECHANGING/CHANGED, WM_ENTERSIZEMOVE/EXITSIZEMOVE, and minimize/maximize/restore WM_SYSCOMMAND. WH_CALLWNDPROC and WH_CALLWNDPROCRET bracket the original WndProc, including a Reset nested inside it. Both always continue the Win32 hook chain. Observation works with AutoHideCursor disabled; cursor behavior remains separate. Both hooks are detached before final native device release. A failed or partial hook installation is reported and cannot repeatedly reinstall hooks each frame.

`display_native_begin`, `display_reset_readiness`, `display_native_attempt`, `display_window_message`, cooperative transitions and display breadcrumbs share a process event sequence. Records also carry device lifetime/successful Reset epoch and HWND/focus/style/rect context. Before each real Exclusive Reset on the creating thread, one direct native TestCooperativeLevel query records readiness. It is diagnostic only: it does not change the game result, retry, wait, defer, or turn DEVICELOST into success. A wrong/unknown creation thread is explicitly reported without probing.

Caps per pipeline: 128 admissions, 128 native attempts/begins/readiness records, 64 cooperative transitions, and 512 message records with one exhaustion marker. Style-changing events and readiness include at most 16 stack frames with module path/return RVA. Stack evidence can attribute a game/runtime call when captured; `game_or_os_unresolved` is retained when attribution is unavailable. This is not a general message recorder. The existing 16 MiB session budget remains.

## Exclusive decision

See [static owner analysis](exclusive-static-analysis.md). The exact retail window owner can now be read safely through two agreeing pointer chains, the vtable, HWND, and validated flags. This is read-only and whole-hash gated only for this new observation; existing feature-local FOV/VehicleSemantics compatibility remains unchanged.

No mode synchronization, original function call, owner write, game code patch, HWND restyling after Reset, silent Borderless fallback, or retry loop was introduced. At this checkpoint there was no runtime proof identifying the writer of `0x16CF0000`, the live game-mode mismatch, or cooperative readiness immediately before the failed Reset. The original WM_SIZE path and the cooperative recovery path differ substantially, so guessing at a single mode byte would be unsafe. The R-GFX5-8 scope decision deferred behavioral changes pending those observations.

## Preserved baseline

PreserveMargins v2, source45 preview, Centered4x3, AF MIN-only, MSAA negotiation, FOV/culling, MenuFreezeFix, shadows, stable vehicle signatures/reflections/brake exclusions, COM identity, and shutdown remain in regression coverage. PreserveMargins still changes only draw-local WORLD and immediately restores it; there are no packet-coordinate writes.

CPU VB/IB Lock/Unlock provenance and all generation/budget rules remain integrated. A new production-wrapper contract confirms: a failed Reset and a suppressed commit echo preserve mirror proof; a real successful Reset poisons even a MANAGED mirror, retains MANAGED resource generation, and removes DEFAULT metadata. Existing conservative poisoning does not automatically revive an old mirror after Reset. F10 remains opt-in; Mode=0/Diagnostics=0 are defaults, requested foliage Mode1 stays blocked/Stock. No new visual override was added.
