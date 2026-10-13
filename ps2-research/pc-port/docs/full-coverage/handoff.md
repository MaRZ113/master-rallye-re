# PS2 Visual Parity — Full Vehicle & Course Coverage

This archive contains PS2-port sources, exact integration patches, tests,
compact source coverage matrices, build evidence and both verified DLLs.
Original renderer sources, game binaries, models, textures, complete meshes,
private grass resources and raw runtime captures are not included.

Frozen renderer tree: e33386bcf682db6983380c499e4928726c758fe0.
Immutable staging source commit:0bddf7c7bc5e95831f98714ff6231da05ab073ea.
Starting repository HEAD:f9673101b94d2d04407b314de87cac6b08efb4c9.
Ending source commit and SHA-256 values are in release-provenance.json,
build-report.json and SHA256SUMS.txt. No push or automatic deployment.

One reusable build root: `.build/baseline`, `.build/ps2-enabled`; source staging:
`.staging/baseline`, `.staging/ps2-enabled`. Run `python overlay/build_overlay.py`
from the original repository layout. It verifies the frozen Git tree and exact
patches, checks both generators twice, builds Win32 Release serially, runs CTest,
checks exports and PS2 Python tests, then publishes separate DLLs under dist/current.
No clean rebuild or new per-phase build root is needed.

Full build requires the original repository with pinned Git objects, existing
MSVC/CMake/Win32 SDK and the frozen renderer. Handoff-only synthetic tests require
Python and the included source/metadata. Port integration tests require the
verified staging output. Corpus generation requires the canonical PS2 PackFS,
protected PC retail corpus and read-only Course SDK, all external inputs. No
Blender dependency. Native MSAA smoke requires Windows native D3D8 and MSVC;
it creates only its own hidden synthetic test device, never accesses the game.

Source coverage:174 carshiny groups across 24/26 PC families,99 paint and75 other
reflective groups. Forester/Forklift and3 PS2-only families have precise gates.
Vegetation:36 courses/72 source-derived assets, with 2317 nonexact eligible faces
excluded rather than invented. Preserve the accepted Tata/Kia and three-course
runtime observations separately from newly enabled coverage.

Read `runtime-ab.md` for installation prerequisites and controlled comparisons.
The archive DLL is opt-in; the ordinary example remains all-Stock. Native tests
and a real standalone D3D8 resolve test passed, but full-game coverage/FPS and
new-vehicle visual acceptance require the user's game runs.

Physics and HUD implementation are paused. The next bounded action is this
release's game A/B, not another system port.
