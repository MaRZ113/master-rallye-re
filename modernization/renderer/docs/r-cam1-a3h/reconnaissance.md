# R-CAM1-A3h — renderer seam reconnaissance

Status: **PARTIAL / implementation blocked on draw ownership evidence**. No runtime feature, key binding, native patch, Broker write, or renderer suppression was added. The starting tree was clean at `master` / `40e96a879d81dbe8fece1af65f8ccec3ec1334fd`.

## Evidence inspected

The two supplied exact-build captures, `frame-41672-d1-00029502.jsonl` and `frame-41672-d1-00036939.jsonl`, identify pristine retail SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and report a live France1 race certificate. They contain full D3D8 frame events and draws, but no UI entity/packet semantic records. In both frames the dominant UI packet draw uses `DrawPrimitive` at VA `0x0056D7C4` / RVA `0x0016D7C4`, FVF `0x142`; the same callsite is the R-GFX5 final UI consumer. World draw calls also exist in the frame, so filtering every 2D-looking call by generic pipeline state is not a supported HUD/overlay classifier.

Additional captures under the pristine installation corroborate the shared path: `P4_Pause.jsonl` has 494 `DrawPrimitive` records at RVA `0x0016D7C4`, while `P1_HOORAAY!!_NORMALHUD_race.jsonl` has 286. The captures differ in output geometry/configuration and do not provide entity names, so counts or raw resource pointers cannot identify pause-only content. `D_floaty-racehud-pause.jsonl` likewise has no entity-bearing records. These data are read-only inputs; no logs or binaries were copied into the repository.

The unpacked `DataScene/Hud/Hud0.xml` does provide semantic source-level separation. `PauseMenuTiles` and `PauseMenuChooser` are separate Eggs; the chooser's `gaFrontendPauseMenuAI` reads `Race/PauseMenu/Enabled`, `List`, `Index`, and `Text`, and names `PauseMenuTiles`. HUD objects such as `SpeedDial`, GPS, split/record text, wrong-way, and progress are separate Eggs. This proves the content model, but the current renderer trace does not correlate those Egg identities to individual D3D draws. The existing UI consumer hook receives an entity pointer and packet identity internally, but its F10 output is bounded margin/position diagnostics and does not serialize stable semantic ownership for general draw suppression.

## Safety decision

The existing `VisualPolicy::suppress` path is an exact stock-shadow filter for one draw site; it is not a general overlay filter. The established final UI consumer at `0x0016D7C4` is shared by the visible race UI packet stream. Suppressing that stream would hide both HUD and pause visuals, so it cannot satisfy the independent-toggle combinations. The current live race certificate does not expose native pause state, and writing `Race/PauseMenu/Enabled` would alter native menu data/ownership rather than remain a renderer-only visual operation. Neither approach is used.

Accordingly no H/J controls were added: a hotkey whose requested visual effect cannot be safely classified would be misleading. The accepted Freecam, QPC, FOV, roll, camera ownership, race certificate, pause behavior, and input-forwarding code remain untouched.

## Minimum evidence needed to resume implementation

1. Add a bounded diagnostic-only record at the existing proven `DrawTextPacket` consumer that associates each final UI draw with the active `entity`, packet, point/storage generation, packet mode, and current draw arguments/states. It must not write to game memory or suppress calls.
2. Capture consecutive normal-race and paused-race F10 windows from the same session/build, with the HUD visible and pause overlay visible, recording the transition into pause. Keep session and frame JSONL together.
3. Correlate the runtime entities with the two named pause Eggs and the individual `Hud0` Eggs through validated native ownership evidence. Establish a reliable native pause-state read without changing it.
4. Prove negative controls: world geometry is never a candidate; ordinary HUD remains drawable while only pause visuals are hidden; pause visuals remain drawable while only race HUD is hidden; frontend/attract/replay scenes do not inherit either mode.

Only after these signals are demonstrated should independently controlled visual suppression be enabled at the narrowest proven UI draw boundary. Then add edge-triggered configurable keys, default-off state, race-lifecycle reset, independent/combined synthetic tests, and the requested runtime handoff.

## Runtime status

No candidate DLL was built or deployed because the requested behavior could not be safely implemented from the available ownership evidence. There is no runtime PASS claim. This checkpoint is not `READY_FOR_IN_GAME_VALIDATION`; it is a scoped blocker report to avoid shipping an all-UI suppression disguised as independent HUD and pause controls.
