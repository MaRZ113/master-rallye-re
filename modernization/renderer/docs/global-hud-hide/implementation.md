# Global HUD Hide — implementation and evidence

Status: **GLOBAL_HUD_HIDE_READY_FOR_RUNTIME**. The candidate is built and the static/native policy tests pass. A human gameplay run has not yet been performed.

## Exact native boundary

The target was verified as the pristine retail `MRallye.exe`, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, size 3,121,214 bytes, PE32/I386, ImageBase `0x00400000`.

REA 6.4.0 was run against that exact image with its Ghidra provider, Ghidra 12.1.4. The provider reported an x86 PE executable and an ephemeral, source-immutable analysis session. Its function dossier for `0x0056D110` (`FUN_0056d110`) reports the complete body `0x0056D110–0x0056DB0F` (2,560 bytes). The decompiler reads the packet pointer from `entity+0x4c`, checks packet flags/mode, and submits FVF `0x142` before the native packet draw. Ghidra's bounded incoming-reference query returned `0x0056BAE1` and `0x0056CE0A`; that operation does not label edge kinds, so the addresses are retained as references rather than promoted to caller semantics. Existing A3h evidence and the production callsite verifier identify the final `DrawPrimitive` return site as VA `0x0056D7C4`, RVA `0x0016D7C4`.

That consumer is shared by HUD and frontend packet rendering. A 2D FVF, triangle topology, or callsite alone therefore cannot authorize hiding. Existing renderer work already owns the exact-retail consumer hook and current packet identity check; this feature adds no second UI hook. At each candidate draw, the new gate also re-reads the live native race/UI context rather than trusting a prior frame snapshot.

The race-context proof requires the exact retail image, intact observer/UI hooks, render thread, current D3D scene/device, current consumer identity, committed scene name `Hud/Hud0`, a correlated successful `RaceTest/<course>` root and exact `DataScene/Hud/Hud0.xml` child, exactly one local participant, local participant state 0, and a readable typed `Race/PauseMenu/Enabled` boolean. Normal gameplay keeps the original strict offline context gate. HUD policy has one narrow replay exception: typed `Race/PlaybackReplay=1` is accepted only when network sync, attract mode, ghost playback, network players, and unsupported race settings remain clear and the same owner/course/Hud0 checks pass. The camera-write certificate still rejects replay. Suppression additionally requires pause disabled and the exact `DrawPrimitive` site, FVF `0x142`, triangle list, and positive primitive count. The lifecycle selector at VA `0x004AA0C1` is reused as evidence that the `Hud/Hud0` request belongs to the current race root. If any read, generation, scope, identity, or state is uncertain, that draw is forwarded.

This confines hiding to the verified race packet stream in gameplay and active replay. Frontend, loading, results, interactive pause (including paused replay), unsupported builds, and stale scene snapshots fail open. Participant states other than the confirmed running state also fail open. The existing paused-Freecam Clean View remains behind its prior strict admission checks and can suppress the pause overlay only when that independent native policy admits it.

## One preference and one H edge

`Device8::hud_visibility` owns the session preference. The proxy polls the configured virtual key once at `Present`, only while the game HWND is foreground and not minimized; it observes the high key-state bit without consuming input. Focus loss resets the edge detector. The request survives camera changes, Freecam changes, pause, scene transitions, and device Reset. It starts visible by default.

`[FreeCameraKeys] ToggleCleanView` is now a legacy alias for `[HUD] ToggleKey`; it has no second toggle handler. `GameFov` receives the same preference, while the established Clean View admission still decides whether the pause overlay can be suppressed. The stock `DataGame/options.xml` does not bind DirectInput scan code `DIK_H` (`0x23`, decimal 35) to either keyboard layout. The default H binding therefore does not collide with pristine controls. Native input remains untouched; if a user rebinds a game control to H, the proxy key can be changed in the INI.

The production Win32 INI reader now reads `ToggleEnabled`, `ToggleKey`, `HiddenAtStartup`, and `PreserveMenus`. `PreserveMenus=0` is forced to true. Existing configurations without a `[HUD]` section keep H through the old `ToggleCleanView=H` alias. Legacy `CleanViewEnabled=1` maps to `HiddenAtStartup=1` only when the new key is absent.

F10 frame metadata contains `hud_hide` with requested/effective state, policy readiness/reason, current context (`gameplay_running`, `replay_running`, or a preserved paused/unknown context), replay flag, exact-build/device/hook status, verified and suppressed draw counts, and ambiguous rejections. `effective_hidden` means at least one draw was actually suppressed in the captured frame; it does not merely mean H was accepted. Menu draw count remains `null` because the shared consumer does not expose an independently proven menu category.

## Analysis tool availability

The REA CLI reported version 6.4.0, Node 24.19.0, and Ghidra 12.1.4 when `GHIDRA_INSTALL_DIR` was supplied for the analysis process. The Codex Ghidra-bridge MCP tools were not exposed in this task's active tool catalog, so no claim is made that a bridge call was run in this turn. Existing A3h Ghidra findings were read and preserved; the new REA/Ghidra analysis used only the pristine image and a temporary provider session. No Ghidra database or game binary was modified.

## Remaining runtime evidence

Static ownership and fail-open gates are implemented. Runtime must still establish that the full ordinary-race HUD is emitted through this packet stream on the user's selected France1 path, and that the typed pause/player fields match on every supported transition. Use the test sequence in [runtime-handoff.md](runtime-handoff.md). Do not describe this build as visually confirmed until that run passes.
