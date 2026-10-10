# R-CAM1-A3d validation — 2026-10-10

Status: **READY_FOR_IN_GAME_VALIDATION**. Actual Freecam code is implemented;
live flight and the newly built DLL's regression smoke test are **PENDING**.
No game launch, deployment, on-disk EXE patch, branch/worktree creation or push.

Repository `D:/Game/Master Rallye/master-rallye-re-general`, branch `master`,
clean starting HEAD `4de97f086cdae687360df335878235932d0bafa3`.
Every phase change lives under `modernization/renderer/`; retired trees and
existing external Ghidra projects remain unchanged.

| Executed check | Result | Evidence boundary |
| --- | --- | --- |
| Full renderer Python | **153/153 PASS**, 108.006 s | Golden capture excerpts, old/new native guards, controls/preset metadata, prior renderer regressions |
| Root synthetic | **630/630 PASS**, 11.455 s | Existing project synthetic suite; fake Win32 test output is not live interaction |
| Full native CTest | **13/13 PASS** | Includes actual native contract fixtures; canonical final rebuild after Python generator tests |
| Race epoch/native observer | PASS | Production hierarchy, reader, certificate predicate, pool/list/typed fields, thread/error/ABA/Reset/ancestry negatives |
| Existing observer x86 ABI | **62 cases PASS** | Includes new native request-prefix/outer return-PC fixture |
| New scheduler x86 ABI | **7 cases PASS** | Enabled/disabled repeated calls and reentry; RET4 argument/output/FPU/register/stack preservation |
| Existing traversal x86 ABI | PASS | Actual GameFov submit bridge, RET8, patched CALL, FPU/register preservation |
| Freecam | PASS | Actual INI reader with Trace=0, default OFF/invalid config, WASD/Numpad/Custom, focus/toggle, displayed VIEW inversion, movement, 176-byte scope/restore/unowned writers |
| Production snapshot JSON | PASS | Actual native serializer parses as JSON; unsupported host has no certificate/flight |
| Compileall | PASS | Renderer and tools/runtime, redirected pycache under ignored renderer scratch |
| Exact retail static inspector | **89 anchors PASS** | 86 historical anchors plus three A3d installer guards; SHA, ImageBase and relative targets |
| Win32 x86 Release | PASS | Visual Studio 18 2026 / MSVC, canonical build.py |
| PE verifier | PASS | PE32/I386; required three direct exports; no recursive d3d8.dll import/delay imports |
| Git whitespace/boundary | PASS | Only renderer files; no proprietary/generated binaries staged |
| In-game flight | **PENDING** | Human procedure in runtime-handoff.md |

The first renderer Python run found one historical-map reproducibility failure
(152 tests). New A3d guards had been appended to the historical A3c anchor set.
They were separated into `A3D_SITES`; all historical assertions remain intact.
The final full 153-test run passed. No prior renderer assertion was weakened.

The new ABI and FrustumFrame tests are native synthetic fixtures, not execution
of the actual game's renderer, particle/debug consumers or a visual flight.
The scope ordering comes from exact retail EXE evidence plus tested production
bridges/owned-field helper. Native runtime correspondence is the first-flight gate.
In particular, source names for the owner job must be recorded freshly because
the poisoned A3c traces lost their queue payloads and successful callbacks.

Candidate path: `modernization/renderer/.build-msvc/Release/d3d8.dll`.
Final SHA/size and test durations are recorded in the accompanying
[candidate manifest](../../research/r-cam1-a3d/candidate.json).
Exports are Direct3DCreate8 ordinal 5, ValidatePixelShader ordinal 2 and
ValidateVertexShader ordinal 3. No proprietary binary or raw capture is committed.

Ignored artifacts: `.analysis/handoff/r-cam1-a3d/` holds the runtime DLL/INI/handoff
and manifest; `.analysis/archives/` holds a changed-phase archive and a separate
clean source/docs/tests handoff. Neither carries raw Ghidra databases/runtime logs,
game assets, EXEs, PDB/OBJ/LIB or diagnostic build directories.

Accepted baseline (human statement in the A3d request): R-OBS1b combined
Broker/Dump/F10, supported Windowed/Borderless, cursor/lifecycle and R-UI1/UI;
ordinary Restart/idle Attract accepted. R-ATTR1's separate previously reported
`applied=false, not_verified_initial_factory_phase` discrepancy is not converted
to an applied-guard claim. Its source/gates were not changed. Existing AF/MSAA,
FOV, shadows, vehicle semantics/reflections and foliage diagnostics remain covered
by regression suites; no new visual runtime PASS is transferred to this candidate.
