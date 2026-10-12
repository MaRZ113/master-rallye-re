# R-CAM1-A3h.3 — Clean View Pilot

## Scope

This change adds one opt-in `CleanViewPilot` action for the verified native UI consumer stream. It does not independently classify HUD, pause overlay, or frontend elements. The evidence in A3h.1/A3h.2 established the consumer scope and a typed pause signal, while leaving some individual UI owners unresolved; therefore the pilot suppresses only the entire proven UI consumer scope while the game is paused and Freecam is active.

The hook reuses the exact-retail `DrawTextPacket` consumer bridge at VA `0x0056D110` / RVA `0x0016D110`. No additional game hook site is installed. Its final draw admission is exact-retail `DrawPrimitive` at RVA `0x0016D7C4`, within the active native consumer scope, with current FVF `0x142`, `D3DPT_TRIANGLELIST`, and a complete identity reread that still matches the entity, packet, point storage, content storage, mode, and UI epoch captured on consumer entry. Packet modes other than the known `1` or `2` remain fail-open.

## Arming and lifetime

`FreeCamera.CleanViewPilot=1` enables the experimental control. `CleanViewEnabled=1` optionally arms it on the first valid paused-Freecam context; the default is `0`. The default `FreeCameraKeys.ToggleCleanView=H` binding is read through the existing game-window input sampler and is not consumed. It is edge-triggered. Invalid configuration disables only Clean View; it does not disable Freecam, cinematic FOV, or roll.

An armed request is admitted only on the exact pristine retail image, the renderer thread, a valid current race certificate, active Freecam pose scope, typed read-only `Race/PauseMenu/Enabled == true`, focused/intact game HWND, active D3D scene/device scope, and intact UI consumer hook. Leaving any required Freecam, race, pause, focus, or device lifecycle context disarms the request. No game key or pause value is written.

When admitted, the wrapper returns `S_OK` for the eligible `DrawPrimitive` without calling the native draw. It preserves packet updates, state setup, all other draw calls, and all D3D state. Calls that fail any check are forwarded normally. Existing reflection repair runs before this decision. `UiMargins` metadata adds bounded decision counters and the last admission/scope reason; detailed ownership rows remain limited to the existing F10 capture.

## Evidence boundary

The production gate is covered by the `clean_view_contracts` synthetic test, and the config/pause readers have native contracts. This demonstrates fail-closed implementation predicates only. It does not prove that the native consumer callsite is reached during the paused Freecam runtime path, nor that the user considers the full suppressed stream visually clean. Those remain human runtime checks in [runtime handoff](runtime-handoff.md).
