# Global HUD Hide — validation

## Replay diagnosis

The latest supplied F10 frame was captured during replay. Its trace showed that the H preference changed, but `hud_hide` stayed fail-open with `current_ui_context=unknown`, `policy_ready=false`, and zero suppressed draws. The race snapshot identified a committed `RaceTest/France1` root with its `Hud/Hud0` child, one local participant in running state, no network players/sync, no attract mode, and `Race/PlaybackReplay=1`.

The rejection came from sharing the camera/freecam race-context gate with HUD visibility. That gate intentionally rejects `PlaybackReplay`, so the race HUD policy never reached its already verified UI packet draw checks. The fix adds a separate HUD-only context check: it requires the replay value to be a typed boolean exactly equal to 1, then reruns the strict offline, one-player, owner, participant, course, and Hud0 checks with only that replay bit normalized for the shared base validator. Attract, ghost, network, malformed, missing, and other unsupported context fields still fail open. The camera/freecam certificate remains unchanged and continues to reject replay.

Active, certified replay can now suppress only the existing verified race-HUD packet draws. Paused replay remains visible so its interactive pause UI is preserved. Frontend, loading, results, unknown scenes, and uncertain ownership remain fail-open. The latest trace diagnosed the cause; it is not a post-fix runtime pass.

## Automated checks

- `python modernization/renderer/tools/build.py`: Win32 Release build completed; native CTest passed 24/24, including replay HUD admission, strict camera-certificate rejection, paused replay preservation, lifecycle Reset handling, and existing ABI contracts.
- `python -m unittest discover -s modernization/renderer/tests -v`: 193 tests passed.
- `python -m unittest discover -s tests/synthetic -v`: 630 tests passed.
- `python -m compileall -q modernization`: passed.
- `python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll`: valid PE32/I386 DLL; direct exports `Direct3DCreate8`, `ValidatePixelShader`, and `ValidateVertexShader`; imports `bcrypt.dll`, `USER32.dll`, and `KERNEL32.dll`; no recursive D3D8 import. SHA256: `c83befd2398000d88ff9dff39820994ae37ef2e7ccbf5e1f55b4fd8a4825211c`; size: 2,287,616 bytes.
- `git diff --check`: passed; Git emitted CRLF normalization notices for existing Windows-style files, with no whitespace errors.

## Runtime status

The candidate is **ready for human runtime testing**, not visually confirmed. Install the DLL using the existing local procedure and repeat the active replay test in [runtime-handoff.md](runtime-handoff.md). A pass requires `replay_running`, `replay_mode=true`, and positive `suppressed_hud_draws` while hidden, then complete HUD restoration when shown. Also verify paused replay controls, ordinary race HUD, and menu protection. Static tests cannot establish that every visible replay overlay belongs to the admitted native packet stream.
