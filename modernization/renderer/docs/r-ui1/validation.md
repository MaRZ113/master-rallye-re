# R-UI1 Validation Record

## Repository and scope

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`
- Branch: `master`
- Starting HEAD: `007138f` (`research: validate camera submission ownership for R-CAM1-A2`)
- Final HEAD: recorded with the R-UI1 commit.
- The pre-existing staged Observatory files were present before R-UI1 and were left untouched.
- All R-UI1 source, test, and documentation changes are under `modernization/renderer/`.
- No proprietary executable, game asset, runtime log, generated DLL, PDB, OBJ, LIB, or EXP file is part of the tracked change.

## Automated validation

- `python modernization/renderer/tools/build.py`: passed; Win32 Release DLL and test targets built, then all CTest targets ran.
- Native CTest: 10/10 passed, including the production UI wrapper and new R-UI1 packet/draw diagnostic contract.
- `python -m unittest discover -s modernization/renderer/tests -v`: 119/119 passed.
- `python -m compileall -q modernization/renderer`: passed.
- Proxy verification: valid PE32 / I386 DLL; required D3D8 exports present; no recursive `d3d8.dll` import; evidence grade `BUILD_VERIFIED_NOT_RUNTIME`.
- `git diff --check`: passed.

The verified build output is `modernization/renderer/.build-msvc/Release/d3d8.dll`, 1,556,480 bytes, SHA256 `655510f5c74bb1ffd82f2f9d41fc7ce5106d5008315d408b40f874b4966611fe`. It remains ignored build output and is not committed.

## Runtime boundary

No game session was run as part of this validation. The synthetic test establishes that the existing retained-anchor policy can produce the supplied paired-transform displacement shape; it does not prove carousel ownership or visual correction. Race Select and Vehicle Select testing remains pending. The required short test sequence and capture fields are in [runtime-handoff.md](runtime-handoff.md).

The current R-CAM1-A2 camera submission diagnostic, GameFov behavior, foliage upload provenance, and broader D3D8 frame capture passed their existing tests and were not redirected or removed. Exclusive Fullscreen behavior and the unrelated staged Observatory changes remain outside R-UI1.

## R-UI1-D2 validation

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`; branch `master`; starting HEAD `fadc5f24190f9062e2ad268ce8045ffb1d36703e`.
- `python modernization/renderer/tools/build.py`: passed; Win32 Release proxy and all native targets built.
- Native CTest: 10/10 passed, including repeated same-device F10 capture re-arming, capture-local budgets, draw-driven promotion, adjusted/unadjusted candidate strata, deterministic bounded selection, retained anchor continuity, and exact WORLD restoration controls.
- Python suite: 120/120 passed, including the session/frame capture-ID join and the existing R-GFX/R-CAM/foliage regressions.
- `python -m compileall -q modernization/renderer`: passed.
- `python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll`: passed; PE32/I386, required D3D8 exports present, no recursive `d3d8.dll` import. Evidence grade remains `BUILD_VERIFIED_NOT_RUNTIME`.
- Current ignored candidate: `modernization/renderer/.build-msvc/Release/d3d8.dll`, 1,576,960 bytes, SHA256 `aa0495d92ccf0440aa138c19dd5531dda82567a8617f52dfed81b34273747ea2`.
- `git diff --check`: passed.

The new synthetic native session demonstrates two successful F10 captures on device 8 (`d8-f2`, `d8-f4`) with independent budgets, both adjusted and unadjusted promoted evidence, and matching Trace `frame_summary` IDs. A separate dense synthetic capture observed 343 packet consumers, including 340 without relevant draws, while promoting only drawn packets. The 80-candidate order test retained the same bounded 32/32 selection under reversed traversal. These are automated contract results, not game-session evidence.

No current production Race Select / Vehicle Select capture files were present in this checkout. No game was launched for this pass, and no carousel alignment transform was introduced. Carousel ownership and visual behavior remain pending the three captures in [runtime-handoff.md](runtime-handoff.md).

## R-UI1-D3 experimental alignment candidate

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`; branch `master`.
- Starting HEAD: `92001d277b8cdc3587c220d835409d5d3e309064`; the worktree was clean. R-UI1-D2 and R-CAM1-A2 were present in history. No unrelated modifications were present at preflight.
- `python modernization/renderer/tools/build.py`: passed with the existing Visual Studio 18 2026 Win32 generator, Release configuration, and parallel build setting; all targets built and CTest ran.
- Native CTest: 10/10 passed. `quality_tests.exe` passed the new production classifier integration, including PreserveMargins default-off parsing, explicit opt-in, invalid setting fallback, exact-profile gating, bug/control capture shapes, movement/reverse movement, negative UI controls, Reset/content-storage/scene epoch/absence handling, multiple viewport ratios, native draw count/HRESULT, packet immutability, and exact WORLD restoration.
- `python -m unittest discover -s modernization/renderer/tests -v`: 120/120 passed.
- `python -m compileall -q modernization/renderer`: passed.
- Proxy verification: valid PE32/I386 Win32 Release DLL, required D3D8 exports present, no recursive `d3d8.dll` import; evidence grade `BUILD_VERIFIED_NOT_RUNTIME`.
- DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll`, 1,584,640 bytes, SHA256 `cfa3a03c915c262ea962915f1df3679adf118c687832caf3014d7a09fd5adbe3`.
- No game session was run. In-game A/B confirmation is pending; the classifier remains off by default and the supplied D2 JSONL files were not available for independent re-parsing in this checkout.
- `git diff --check`: passed.

R-UI1-D3 is ready only for the documented **experimental** PreserveMargins test. It is not visually accepted, and no runtime claim is implied by the native suite or PE verification.

## R-UI1-D3a frontend scene-phase synchronization

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`; branch `master`; starting HEAD `030a6ce268bb2a388b7689a6e0c925257dfca081`; the worktree was clean at preflight.
- Source change: scene-family evidence is published only after a successful native Source45 projection setter, staged by `UiMargins::finish_frame()`, and considered completed only after successful native Present. Early verified UI draws may use an unambiguous same-frame observation or the immediately preceding successfully presented frontend frame (age 1); no older state is accepted.
- Transition behavior: current-frame contradictory family observations, failed/incomplete Present, race, epoch mismatch, reset, frame discontinuity, future evidence, and stale age fail closed. The existing scene-family transition continues to invalidate `MarginAnchors` epoch and carousel history.
- Native CTest: 10/10 passed, including the new real-order test that exercises UI projection/draw before late Source45 classification, Present completion, and next-frame early draw through the production wrappers. Existing D2 capture, R-CAM1-A2 camera and foliage diagnostics, renderer lifecycle, and quality contracts also passed.
- `python -m unittest discover -s modernization/renderer/tests -v`: 120/120 passed.
- `python -m compileall -q modernization/renderer`: passed.
- Proxy verification: passed; PE32/I386, required D3D8 exports present, no recursive `d3d8.dll` import; evidence grade `BUILD_VERIFIED_NOT_RUNTIME`.
- DLL output: `modernization/renderer/.build-msvc/Release/d3d8.dll`, 1,591,296 bytes, SHA256 `2abe16fb7be4aa2238c89f79d2c7d5be24f6f501db66bca0fe012d31e901238a`.
- `git diff --check`: passed before the final docs/archive/commit checks.

The automated phase contract is `CONFIRMED_BY_SYNTHETIC_TEST`; the source lifecycle is `CONFIRMED_BY_SOURCE`. The D3 runtime report is `CONFIRMED_BY_TRACE` as provided by the user, but its JSONL artifacts were not available in this checkout for independent re-parsing. No game was launched for D3a. The result is `READY_FOR_IN_GAME_VALIDATION` only; it is not evidence that Vehicle Select or Race Select is visibly corrected. Keep `CarouselAlignment` as an opt-in A/B setting until the runtime handoff passes.

## R-UI1-D3b atomic group fail-closed checkpoint

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`; branch `master`; starting HEAD `bbe41aaffbd09354e4a51be378a4bee8be2703c7`; working tree was clean at preflight.
- Source change: a proven per-packet motion track no longer sets zero margin or discards its retained anchor. Individual statuses are still recorded as evidence, while unknown group ownership selects the explicit PreserveMargins fallback. D3a scene-phase synchronization is unchanged.
- Synthetic D3b test: four production packet identities with mixed promoted/candidate states preserve all source-relative intervals at 111-unit Race Select and 100-unit Vehicle Select spacings. Group remains `GROUP_UNKNOWN`; no test-only verified group state is manufactured.
- Win32 x86 Release build: passed using `python modernization/renderer/tools/build.py` and the existing Visual Studio 18 2026 generator.
- Native CTest: 10/10 passed, including UI classifier, D3a frame timing, draw/world restoration and the new D3b atomic fail-closed regression.
- Python: `python -m unittest discover -s modernization/renderer/tests -v` passed 120/120 in 100.823s.
- Compile check: `python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization` passed.
- Proxy verification: passed; PE32/I386 DLL, required exports present, no recursive `d3d8.dll` import; evidence grade `BUILD_VERIFIED_NOT_RUNTIME`.
- Candidate DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll`, 1,595,904 bytes, SHA256 `9239753836649802f375624e3176b3f3981526ed3f1811b9c5806126e07d7fa5`.
- Runtime validation: not performed. The supplied D3b logs/JSONLs were not available for independent parsing. No in-game visual test is requested for the fallback-only candidate.
- `git diff --check`: passed after final source, test and documentation edits.

The phase result is `BLOCKED_ON_ATOMIC_GROUP_OWNERSHIP`, not `READY_FOR_EXPERIMENTAL_IN_GAME_VALIDATION`. The tests confirm the conservative fallback and retained source spacing; they do not verify a positive group policy or the visual fix. The sole unblock is verified complete pre-draw carousel membership and selection-frame relationship for both Race Select and Vehicle Select.


## R-UI1-FINAL deterministic row policy

- Repository `D:/Game/Master Rallye/master-rallye-re-general`, branch `master`; clean starting HEAD `33835ae`. No new branch/worktree; no push or deployment to the game directory.
- Read-only production input audit: the Pristine session and all three 25264 frame captures were independently parsed. 10/10/6 Y=309 card packets each have two mode-1 / caller `0x16D7C4` / FVF `0x142` / TRIANGLELIST-count-1 draws. All 192 D3b bounded render-local records report fallback; all three Present results are S_OK, frame ends complete, restore failures zero. Actual second-frame LEFT subset is -180 through 375. Prior D3a sessions confirm Y=303.891 decorations are outside the new predicate. Input hashes and source boundaries are in [final-row-policy.md](final-row-policy.md).
- Positive production change: exact-retail draw-type zero-margin policy from the first qualifying draw, without motion/roster authority. Exact-profile gating is separate from the existing feature-local modified-EXE margins capability. Anchors, D3a timing, v2 WORLD handling and camera hooks remain intact.
- `python modernization/renderer/tools/build.py`: PASS, existing Visual Studio 18 2026 generator, Win32, Release. Native CTest **10/10 PASS** (4.02s). An initial test run exposed an incorrectly expected row counter: contradictory same-frame scene evidence correctly rejected one draw, so the expectation was corrected to six; final native run passed every suite. No safety assertion was removed.
- Production Device8 tests cover both captured ten-card Race rows and six-card Vehicle row, mixed anchors, 111/100 spacing, both subdraws, first frame, forward/reverse/offscreen/new/reused packets, narrow Y bounds, material/draw/context/profile negatives, source/entity/cache immutability, single draw/HRESULT and native WORLD preservation. Motion-only tests remain diagnostic and cannot authorize a rendering correction. Existing restoration-failure/repair and D3a failed/stale/epoch cases remain active.
- `python -m unittest discover -s modernization/renderer/tests -v`: **121/121 PASS**, 107.383s. New Python contract checks actual native F10 positive LEFT/NONE decisions, zero effective margin, no WORLD set/restore, both subdraws including E_FAIL forwarding, and the unchanged selection border. Existing renderer/camera/foliage/display/vehicle suites passed.
- `python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization/renderer`: PASS (ignored pycache location).
- `python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll`: PASS. PE32 / I386; exports Direct3DCreate8 ordinal 5, ValidatePixelShader ordinal 2, ValidateVertexShader ordinal 3; imports bcrypt.dll, USER32.dll, KERNEL32.dll; no recursive d3d8 import. `BUILD_VERIFIED_NOT_RUNTIME`.
- New ignored DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll`, **1,597,952 bytes**, SHA256 **e3fa2d1d224ea667179e36da94ddf2e134470d13d1f640c813b9a4307b6c58bb**.
- No game session was launched for the new candidate. Status **READY_FOR_EXPERIMENTAL_IN_GAME_VALIDATION**, visual acceptance **PENDING**; option remains default-off. Required short Vehicle/Race run and F10 fields are in [runtime-handoff.md](runtime-handoff.md).
- `git diff --check`: PASS. All task changes are renderer source/tests/docs under modernization; raw logs, proprietary binaries and generated DLL/PDB/OBJ/LIB are excluded. Clean changed-source archive is ignored under `.analysis/archives/r-ui1-final-20261010.zip`; final commit and ending HEAD are reported in the task closeout.


## Accepted automatic closeout (2026-10-10)

Human report: Race Select and Vehicle Select passed on the R-UI1-FINAL candidate; selected cards, neighbors and scrolling were correct without missing/overlapping thumbnails. Grade `CONFIRMED_BY_RUNTIME` for these tested pristine retail scenarios only.

Starting HEAD `23941fe108f8bd4c21338736145783a5fbc15e70`, clean `master`. The public CarouselAlignment field, parser/read-table/JSON plumbing and INI switch were removed. Old keys are ignored and cannot disable the accepted policy. Device initialization automatically requests the unchanged row predicate only for PreserveMargins, separately exact-retail gated through Session::target. Stock/Centered4x3 and existing sticky anchors are preserved.

Closeout validation before camera work: canonical Win32 Release build PASS; all 10/10 native CTest suites PASS (4.80s); focused Python quality research suite 24/24 PASS (2.861s). The existing captured-row, negative, source immutability, WORLD restoration and frame-phase regressions remain active. Parser tests now check ignored old zero/malformed keys. `git diff --check` PASS. Full Python suite will also be repeated after the camera stage. No game EXE/assets, camera hook, PS2 research or unrelated files were modified in this closeout.
