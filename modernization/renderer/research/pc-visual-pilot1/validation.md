# Validation and acceptance gates

Baseline:reviewed native8/8 and Python100/100 PASS. The restricted baseline Python run had5 WinError5 temp-cleanup errors;the reviewed unchanged-suite rerun passed. No baseline behavior was silently repaired. Native build/proxy verification completed before Python capture checks.

Final available checks:9/9 native suites;114 unittest tests,0fail/error/skip;renderer-recon11/11;compileall and diff-check PASS. Pytest: 114 PASS and 15 subtests PASS, 52.16s. The extracted source-only handoff independently passed 9 native suites (3.88s), 114 Python tests (5.235s, no failures/errors/skips) and proxy verification without game data. Details are in validation.json. New focused tests include a production F10 serializer capture from a synthetic native backend;its UNKNOWN_BUILD header remains separate from live PC evidence.

All995 France1 source groups and939 Turkey3 controls were scanned. CanonicalPS2 four-input full hashes,France1/Turkey3DX andTXT source hashes were refreshed;24/24 PS2sourcefaces match at0.001,max2.288818359375e-05. RepeatedsourceJSON identicalSHA643d3bee1c15319611b90acf1adec01d84d228bb3e3f89aa66eb53e4f23bcf08. SDKHEAD4244fa0c4d878523c9947f54816bf377cdfb2589 remainsclean. No native frame identified the selected bush draw.

| Gate | Status | Evidence/boundary |
|---|---|---|
| 1 Repository hygiene | PASS | master,scopedrenderer;pre-existingObservatory work excluded |
| 2 Baseline | PASS | 8native/100reviewedPython/proxy |
| 3 PS2 evidence | PASS | canonical inputs,material and24/24surface correspondence |
| 4 PC geometry | PASS | exactdraw54metadata;995groups/25texturecontrols |
| 5 Runtime target identity | BLOCKED | no actualcourse/resource/uploadownership |
| 6 False positives | PARTIAL | source+syntheticcontrols;livecontrols pending |
| 7 Configuration | PASS | opt-in diagnostics;missing/invalid/version/build failclosed;effectiveMode0 |
| 8 Material state | BLOCKED | no override before identity proof |
| 9 Draw preservation | PARTIAL | productionStock native once/HRESULT tested;activeoverride notimplemented |
| 10 Native restoration | NOT_APPLICABLE | no foliage state setters;readonlylocks tested |
| 11 Resource lifecycle | PARTIAL | freshprobe/recreation tests;mutable activation ownershipunproved |
| 12 Existing features | PASS | existing8native and100Python regressions retained |
| 13 Tests | PASS | 9native,114Python,proxy,compileall,diffcheck |
| 14 Diagnostics | PASS | boundedF10nativecontent/stateprobe |
| 15 Texture policy | PASS | stockonly;Mode2invalid/deferred |
| 16 PC runtime | BLOCKED | humancapture required |
| 17 PS2 reference | BLOCKED | humanreference pending |
| 18 Visual assessment | BLOCKED | no activefeature or visualacceptance |
| 19 No original asset edits | PASS | read-onlycorpora,SDKclean |
| 20 Scope discipline | PASS | no course/asset/EXE/deployment/push or broadfeature |

Original draw states remain UNKNOWN. A passed algorithm/mock test is not a live identity or PS2 visual PASS. No active override is committed.

The initial unbuilt archive run failed because older tests require native executables and the archive omitted the unchanged general Python library and empty scratch directory. Packaging now includes those dependencies; no existing test was weakened. The built isolated rerun passed. Final archive SHA/commit are in its generated receipt and MANIFEST.json.

Additional unchanged modernization/d3d8-proxy suite: 28 tests, 1 explicit native-capture dependency SKIP, no failures/errors. No second proxy was built or deployed.

## 2026-10-09 CPU-provenance continuation

| Check | Result | Evidence |
|---|---|---|
| Canonical MSVC x86 build | PASS | `python modernization/renderer/tools/build.py` completed configure, Release build and `RUN_TESTS` |
| Native CTest | PASS | 9/9 contracts, including the expanded foliage CPU-mirror test |
| Renderer unittest | PASS | 114 tests, 0 failures/errors/skips; set `TEMP` and `TMP` to ignored `.analysis/python-temp` because the sandbox's system temp path rejected writes |
| Interface generator | PASS | `test_generation_is_deterministic` passes after integrating buffer wrappers into the generator |
| Compileall | PASS | `modernization/renderer/tools` and `modernization/renderer/tests` |
| Proxy verification | PASS | PE32/I386 DLL; SHA-256 `2726e51fd5dc3d1caa82a17ce6ecb021ea985a6c1b0bcf2f8786597a3c81a3db` |
| Pytest | NOT AVAILABLE | Attempted `python -m pytest modernization/renderer/tests -q`; active Python has no `pytest` module. No install attempted. |

The first unrestricted unittest attempt had Windows `PermissionError` failures under the sandbox-owned system temp path, and it ran before the full native test target had completed. It is superseded by the later complete run with workspace-local temporary storage. The supplied F10 audits were not modified or regenerated; there was no new PC runtime or PCSX2 capture. `git diff --check` is reported after final documentation and packaging changes.
