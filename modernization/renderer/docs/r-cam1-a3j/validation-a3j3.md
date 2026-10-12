# R-CAM1-A3j.3 — Validation and handoff

## Target and repository

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`
- Branch: `master`
- Starting and ending HEAD: `676ed24b2d32543c3b9356ed359e280f2b36a309`
- Target executable: pristine `MRallye.exe`, 3,121,214 bytes, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
- Target PE: PE32 / I386, timestamp `0x3C02695D`, ImageBase `0x00400000`, entry VA `0x005C4602` / RVA `0x001C4602`
- Ghidra: 12.1.4; isolated analysis scratch `D:\CodexScratch\A3j3`, outside the repository

The exact target hash was independently recomputed during this phase before using its instruction addresses. The working tree already contained unrelated uncommitted A3h/A3i renderer changes at the start; they were preserved. No files were staged, no commit was created, and nothing was pushed.

## Build and automated checks

| Check | Result |
|---|---|
| `python modernization/renderer/tools/build.py` | PASS; Win32 x86 Release build and native CTest |
| Native CTest | PASS, 16/16, including `physics_probe_contracts` |
| `python -m unittest discover -s modernization/renderer/tests -v` | PASS, 160/160; run sequentially because one integration test reads about 7.9 GB of retained frame logs |
| `python -m unittest discover -s tests/synthetic -v` | PASS, 630/630 |
| `python -m compileall -q modernization/renderer` | PASS |
| `python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll` | PASS; PE32/I386 DLL, required direct exports present, no recursive `d3d8.dll` import, no delay-import directory |
| `physics-transaction-map.json` parse | PASS |
| `git diff --check` | PASS; Git printed only existing CRLF/LF normalization warnings for already-dirty renderer files |

Built local validation artifact (ignored under `.build-msvc`, not included in source handoff):

- DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll`
- Size: 2,063,872 bytes
- SHA-256: `5127f7b8498752b9db74c5e3eb8af18dde46ded11c08d54ed6d5daf03e38ee5d`
- Machine: `0x014C` / I386; PE32; image base `0x10000000`
- Direct exports: `Direct3DCreate8` ordinal 5, `ValidatePixelShader` ordinal 2, `ValidateVertexShader` ordinal 3
- Imported DLLs: `bcrypt.dll`, `USER32.dll`, `KERNEL32.dll`
- This is build/package verification only. The observer was not run in Master Rallye and the DLL has no `CONFIRMED_BY_RUNTIME` result.

## Runtime state

No game was launched and no stock recovery was triggered in this phase. There is no `physics_probe` runtime capture. Static evidence proves the stock controller Broker route and local controller/substep call order; it does not prove velocity policy, wheel/suspension/contact reconciliation, broadphase coherence, cross-job scheduling, pause behavior, destination safety, or Undo.

## Deliverables

- [`complete-relocation-analysis.md`](complete-relocation-analysis.md) — consolidated transaction, ownership, scheduler, physical-state, destination, startup, probe, and runtime handoff analysis.
- [`physics-transaction-map.json`](physics-transaction-map.json) — machine-readable exact-build map with evidence grades and unresolved gates.
- [`relocation-safety-matrix.md`](relocation-safety-matrix.md) — per-subsystem safety disposition.
- [`teleport-implementation-decision.md`](teleport-implementation-decision.md) — explicit no-write decision and remaining safety gates.
- `physics_probe_model.hpp/.cpp`, `physics_probe.hpp/.cpp`, `physics_probe_tests.cpp` — opt-in bounded observer and deterministic native contract checks.
- `research-handoff-a3j3.zip` — clean A3j.3 source delta, tests, and documents; no game binary, built DLL, runtime log, or Ghidra database.

## One next action

For the required human observation, enable `[PhysicsObserver] Enabled=1` and `Trace.Enabled=1` in the A3j.3 renderer config. Run one exact-pristine offline France1 race, drive on clear road, invoke the game's ordinary recovery once, let the car settle, drive briefly, and exit normally. Provide the single bounded `physics_probe` JSONL session from `MRRRenderer/logs`. Do not use any experimental relocation or pause/restart during this capture.
