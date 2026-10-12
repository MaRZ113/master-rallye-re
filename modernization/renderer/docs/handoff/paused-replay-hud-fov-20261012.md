# Replay-pause HUD and Freecam FOV handoff

Status: candidate rebuilt and automated checks passed; the updated replay-pause window behavior still needs human runtime confirmation.

Target game: pristine retail `MRallye.exe`, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, PE32/I386, ImageBase `0x00400000`.

Candidate proxy: `modernization/renderer/.build-msvc/Release/d3d8.dll`, SHA256 `bd1df3765e09cc9a034c89ef523772adec282c795043df47da954240a4732674`, 2,311,680 bytes, PE32/I386, exports and non-recursive imports verified.

Runtime diagnosis used same-process frames from the user's latest session. With replay pause disabled, three frames show 32 complete native UI identities. The paused frame `frame-46552-d1-00012158.jsonl` shows 35 identities: the running HUD set plus three pause-only identities with 24, 180, and 2 draws. Two earlier paused frames show four additional identities. The old logic preserved new pause identities, leaving the pause window visible after H hid the learned race HUD.

The corrected rule suppresses every complete current UI identity at the exact native packet consumer only while exact-retail, live replay, typed pause, current scene/owner/device, render-thread, FVF `0x142`, triangle-list, and positive primitive-count checks all pass. Incomplete/stale identities and ordinary non-replay pause, frontend, results, and loading contexts fail open. `replay_pause_overlay_suppressed_draws` counts pause-only identities; `replay_pause_suppressed_draws` counts all suppressed replay-pause draws. The learned running-HUD registry remains as provenance and is not a prerequisite for hiding a newly observed pause window.

Freecam remains independent of this HUD rule. `AllowUnpaused=0` remains the safe example default; the user's local INI opted into live camera flight. Optional cinematic FOV values are in degrees, supported limits are 30–110, a nonzero startup target is clamped to configured bounds, and zero inherits gameplay FOV.

Validation: Win32 Release build, native CTest 24/24, renderer Python 193/193, root synthetic 630/630, compileall, PE32/I386/export verification, and `git diff --check` passed. These checks do not establish visual behavior; run the focused replay-pause test in `modernization/renderer/docs/global-hud-hide/runtime-handoff.md`.

The companion ZIP contains source, configuration example, tests, and current handoff documents only. It excludes the game EXE, active user INI, built DLL/PDB/OBJ/LIB, runtime JSONL/frame captures, and older handoff archives. Shared files are complete source snapshots, not patches against `HEAD`.
