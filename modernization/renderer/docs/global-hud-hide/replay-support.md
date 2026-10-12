# Replay HUD visibility support

The supplied replay frame showed a working H preference but no effective suppression: the runtime classified the UI context as unknown and kept `policy_ready=false`. The same frame's race snapshot established a committed `RaceTest/France1` lifecycle, committed `Hud/Hud0`, one running local participant, offline/non-attract state, and typed `Race/PlaybackReplay=1`.

`check_race_context` is intentionally shared with camera and freecam safety, where replay remains unsupported. Global HUD visibility now uses the separate `check_race_hud_context` path. It admits a replay only when the replay field is present, has the expected Broker type, and is exactly 1. It then delegates all other context validation to the existing strict offline/player/owner checks, normalizing only the replay field for that call. The native Hud0/course ancestry, current owner generation, single local player, running participant state, current scene, render-thread/device scope, exact UI consumer, FVF, topology, and draw-count checks remain required before a draw is suppressed.

The user preference is unchanged by replay or pause transitions. Active certified replay uses the existing HUD packet suppression. Paused replay remains visible, as do frontend, results, loading, and uncertain UI. The camera-write certificate still rejects `PlaybackReplay`; this exception grants no camera, physics, or native game-state permission.

The supplied trace is diagnostic evidence for the former failure, not runtime proof of the fix. Automated checks passed: native CTest 24/24, renderer Python 193/193, root synthetic 630/630, compileall, and PE32/I386 proxy verification. Human confirmation remains required for full visual HUD coverage and usable replay controls.
