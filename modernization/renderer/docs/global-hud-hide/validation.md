# Global HUD Hide — validation

## Attract Demo and startup countdown diagnosis

The supplied 12 October captures exposed two additional HUD-only gaps. In Attract Demo, the committed scene is `Hud/AttractMode`, parented to a successful `Racetest/france2` load, with typed `Race/AttractMode=1`, `Race/Type=14`, four readable live participants, and a successful child commit. The existing classifier admitted only `Hud/Hud0`; moreover, the Attract child was treated as a new race generation, so the completed owner proof no longer correlated. This made the exact Attract HUD fail open and could leave the next context unknown until another supported race lifecycle completed.

During the start countdown, the capture shows `Hud/Hud0`, `RaceState=1`, and SceneManager countdown value `1`. The observer correctly labeled RaceState 1 as a startup transition, but the HUD gate reused the stricter participant-state rule and rejected it. HUD suppression accepts phases 0/1/2 after all participant values have been read and validated; phase 1 additionally requires the live SceneManager countdown to be positive and is reported as `gameplay_start_countdown`. This relaxation is confined to the visual HUD context. Camera/freecam and race-write certificates still use their original stricter checks.

Attract admission is separate: the lifecycle must pair the exact `Hud/AttractMode` child and its data source with the successful track root and current live owner; the typed race fields must identify the offline Attract mode and participant count must match. It does not require the absent pause Broker entry, but it still requires the exact D3D UI consumer, current device/render thread, verified resource identity, and FVF/primitive signature. F10 lifecycle records now include each scene request's native origin to validate the captured Attract route at runtime.

The source frames diagnose these causes; they do not establish a visual pass for the new candidate.

## Replay diagnosis

The latest supplied F10 frame was captured during replay. Its trace showed that the H preference changed, but `hud_hide` stayed fail-open with `current_ui_context=unknown`, `policy_ready=false`, and zero suppressed draws. The race snapshot identified a committed `RaceTest/France1` root with its `Hud/Hud0` child, one local participant in running state, no network players/sync, no attract mode, and `Race/PlaybackReplay=1`.

The rejection came from sharing the camera/freecam race-context gate with HUD visibility. That gate intentionally rejects `PlaybackReplay`, so the race HUD policy never reached its already verified UI packet draw checks. The fix adds a separate HUD-only context check: it requires the replay value to be a typed boolean exactly equal to 1, then reruns the strict offline, one-player, owner, participant, course, and Hud0 checks with only that replay bit normalized for the shared base validator. Ghost/network activity, malformed or missing fields, and other unsupported context still fail open. Attract Demo is now admitted only through its separately documented `Hud/AttractMode` lifecycle and typed context. The camera/freecam certificate remains unchanged and continues to reject replay and Attract mode.

The first replay fix learned identities during certified playback and suppressed those matches while paused, but the pause window remained visible. New same-session captures `frame-46552-d1-00010546.jsonl`, `frame-46552-d1-00010826.jsonl`, and `frame-46552-d1-00010920.jsonl` show 32 complete UI identities with `Race/PauseMenu/Enabled=false`. Paused capture `frame-46552-d1-00012158.jsonl` shows the same running identities plus three complete pause-only identities (24, 180, and 2 draws); earlier paused captures `frame-46552-d1-00009649.jsonl` and `frame-46552-d1-00009966.jsonl` show four pause-only identities. The old policy forwarded these identities because they were absent from the learned running-HUD registry. The revised rule hides every complete current draw at the exact UI packet consumer when exact replay, typed pause, current owner/device/scene, FVF `0x142`, triangle-list, and positive-count gates all pass. Incomplete/stale identity and every non-replay pause or frontend context remain fail-open. The new `replay_pause_overlay_suppressed_draws` counter distinguishes pause-only UI from previously learned HUD identities. This is capture-backed classification evidence, not post-fix visual confirmation.

## Automated checks

- `python modernization/renderer/tools/build.py`: Win32 Release build completed; native CTest passed 24/24, including full replay-pause UI suppression, non-replay pause preservation, incomplete-identity fail-open, identity capacity, Reset clearing, and existing ABI contracts.
- `python -m unittest discover -s modernization/renderer/tests -q`: 193 tests passed (150.691 seconds).
- `python -m unittest discover -s tests/synthetic -v`: 630 tests passed.
- `python -m compileall -q modernization`: passed.
- `python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll`: valid PE32/I386 DLL; direct exports `Direct3DCreate8`, `ValidatePixelShader`, and `ValidateVertexShader`; imports `bcrypt.dll`, `USER32.dll`, and `KERNEL32.dll`; no recursive D3D8 import. SHA256: `bd1df3765e09cc9a034c89ef523772adec282c795043df47da954240a4732674`; size: 2,311,680 bytes.
- `git diff --check`: passed; Git emitted CRLF normalization notices for existing Windows-style files, with no whitespace errors.

## Runtime status

The candidate is **ready for human runtime testing**, not visually confirmed. Install the rebuilt DLL using the existing local procedure and test the start countdown, ordinary gameplay, Attract Demo, active replay, replay-pause window hiding, and menu protection in [runtime-handoff.md](runtime-handoff.md). On hidden replay-pause frames expect `current_ui_context=replay_paused`, positive `suppressed_hud_draws`, and positive `replay_pause_overlay_suppressed_draws` when pause-only packets are drawn. Static tests cannot establish visual completeness.

## Freecam recovery and pause behavior

The 12 October captures showed invalid lens bounds (`10 / 10 / 120`) and blanket paused replay pass-through. The parser now isolates invalid optional lens settings from Freecam activation and clamps a nonzero initial FOV target within valid configured limits. The active INI is `30 / 30 / 110` degrees; zero inherits native FOV, and Z/X adjust within the range. Native tests cover live Freecam admission, FOV bounds, replay-pause overlay suppression, and paused-Freecam Clean View. The updated behavior still needs a human run; automated results do not establish visual success.

## Paused replay fix evidence

The active and paused captures are from the same replay generation, owner, UI epoch, FVF, and native consumer callsite. The revised policy requires a complete current identity and exact replay context before suppressing any draw. During active replay it learns known HUD identities; during a certified replay pause it also suppresses new pause-window identities and reports them separately. The learned HUD set remains bounded to 512 entries, scoped by device/race/owner/UI epoch, and cleared across Reset or semantic-owner changes. Incomplete identity, stale scene/owner, wrong callsite, wrong FVF/topology, or non-replay pause remains fail-open. No visual confirmation exists yet for the rebuilt candidate.
