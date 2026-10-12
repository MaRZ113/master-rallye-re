# Road Teleport forensic remediation — 2026-10-12

Status: **READY_FOR_HUMAN_RUNTIME**, not a game-runtime teleport pass.

The supplied forensic audit was checked against the current complete production sources, both omitted `.inc` files, the latest session, and the pristine retail PE. Work continued in `master-rallye-re-general`, branch `master`, starting HEAD `676ed24b2d32543c3b9356ed359e280f2b36a309`. The working tree already contained earlier modernization work; it was preserved. No branch, worktree, commit, push, retail EXE modification, direct physics write, or direct Broker write was performed.

## Audit verdicts and fixes

1. **Confirmed type error, fixed at both gates.** `manager+0x50` is a pointer to participant countdown storage, not a scalar timer. At VA `0x004CCB67` / RVA `0x000CCB67`, retail loads the pointer and then `[pointer+participant*4]`; VA `0x004CCBC3` decrements the element. VA `0x004CCBDA` calls mode-1 recovery only when that element reaches zero. VA `0x004CD166` zeros the same indexed storage at recovery completion. The shared read-only reader now validates count/index, allocation pointer, overflow, readability and a second snapshot of count/pointer/value. It reports the pointer and signed countdown separately. A live nonzero allocation address is accepted; an active positive countdown, negative value, missing storage or storage churn rejects.

2. **Confirmed second-stage veto, fixed.** Arm checks an idle participant countdown plus fresh zero `P+0x33` and no pending controller observation. Native selection is separately admitted at the verified mode-1 callsite after the legitimate stock countdown has elapsed. It checks the same manager/allocation, participant 0, current race/controller generations, zero current apply flag, no overlapping controller call, route fingerprint and native thread. Expected stock recovery is not confused with an unrelated recovery or allocation presence.

3. **Confirmed unsafe fallback, removed.** There is no post-call EAX replacement. Before argument modification, the native manager must contain exactly one participant and the request must target participant 0. The complete retail `0x004CD200..0x004CD499` helper (666 bytes) and its 40.0 distance constant are verified at setup and again before selection. Its self-skip branch at VA `0x004CD262` skips the sole participant, leaving the initial minimum distance `1e10`; the 40.0 comparison takes the unchanged-input return at VA `0x004CD48E`. Thus both original and selected ordinals are unchanged by the helper in the admitted domain. No double invocation is needed. An unexpected returned ordinal is preserved verbatim and diagnosed as `native_adjustment_invariant_failed_result_unmodified`; it is never advertised as a reconstructed stock result. Changed count, storage or code rejects before the argument write.

4. **Production wiring existed; coverage and correlation are strengthened.** `physics_transaction_capture.inc` did call `commit_matrix` and `observe_clear`; their absence from the earlier ZIP was a packaging gap. Production now uses one shared event dispatcher for native publication, completed matrix copy, physical consumption, native clear and readable settled zero. Publication candidate, controller generation, race lifetime, thread, backing and matrix are correlated. The new x86 integration test invokes the production `road_teleport_bridge.inc` and `physics_transaction_bridges.inc` with synthetic native memory/callees and reaches `Completed` through the production admission/selection/event predicates. It does not manually advance each state. Native physics and terrain placement are simulated in this test, so it is not a substitute for the next game run.

5. **Synthetic native-object model corrected.** Tests now use the actual shared manager reader with a heap-like `+0x50` pointer and indexed values. They cover idle allocation, active countdown, individual human/AI slots, missing/out-of-range storage, pointer churn, multiple human candidates, stale cached flag, pre-selection conflict, native return invariance, default-OFF stock forwarding and full completion.

## Additional defects found

- An unreadable pre-call apply flag could default to zero and later qualify settlement. Such a snapshot is now discarded; settlement explicitly requires readable native flag evidence.
- More than one active physical consumer could return false yet still later reach `Completed`. It now becomes `CommitMismatch` and cannot complete.
- Matrix completion and clear checks lacked consistent current-generation/candidate matching. Shared dispatch requires the same publication candidate and current controller/race/thread identity.
- Instance tracks survived race certificate changes and could leave stale human candidates in the gate. They are now cleared on epoch changes; native calls continue forwarding. AI tracks are also freshly inspected so a cached AI type cannot hide a new human candidate.
- Arm facts are cross-checked against their owner evidence. Native selection requires the original progress ordinal to be within the verified route extent. Changed links are not silently adopted.

The stock Reset bridges and their replayed instructions were not rewritten. Existing camera, bookmarks, Clean View, display, FOV, vehicle rendering and INI configuration behavior is preserved by the passing regression suites. The feature remains default OFF and exact-retail gated.

## Evidence and corrections to prior notes

Retail SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, 3,121,214 bytes, PE32/I386, ImageBase `0x00400000`. Complete adjustment helper SHA-256: `0d81df8f1a1af9de4d10bd3baa2ea8adf703fbe52ad9f8abb503b54c274f2688`.

The latest prior session `session-20261011-233327-12660.jsonl` matches proxy SHA `346ead0409b29d7b71897910deaa6b3f30662ae3de0d3abaa5358a168c028a72`. It contains four request sequences: three valid paused attempts rejected by the false recovery gate and one rejected by the pause requirement. All had one human track, stable links, fresh zero flag, no pending native recovery and `+0x50 == 0x119BC270`. It contains no selected-road teleport pass. The log was read without modification.

The prior owner-gate note's requirement for a “zero reset-manager timer” referred to the wrong field type. Its timer claim and the prior native-adjustment fallback description are superseded here; historical files remain unchanged. Exact byte disassembly and native graph reasoning are **CONFIRMED_BY_EXE**; bridge/dispatcher behavior is **CONFIRMED_BY_SYNTHETIC_TEST**. Actual relocation is pending human runtime.

## Validation and candidate

- Win32 x86 Release build: PASS.
- Native CTest: **22/22 PASS**, including production bridge ABI and end-to-end integration.
- Renderer Python: **190/190 PASS**; includes full retail helper hash/self-skip/countdown contracts.
- Root synthetic: **630/630 PASS**.
- `compileall`: PASS.
- Proxy verifier: PASS; PE32/I386, expected three exports, no recursive `d3d8.dll` import.
- Source archive integrity: CRC and each payload SHA-256 verified.
- `git diff --check`: PASS; only existing newline-normalization warnings.

Candidate: `modernization/renderer/.build-msvc/Release/d3d8.dll`, **2,232,320 bytes**, SHA-256 `0be98274aebdda6965a111599c68d3b70c13d7473980ddbafaf72e462d86bc47`. Generated DLLs are ignored and excluded from the source handoff.

## One-session handoff

Use that exact DLL and keep the current opt-in INI. Required settings remain `FreeCamera.Enabled=1`, `VehicleTeleportEnabled=1`, `VehicleTeleportRoadOnly=1`, `PhysicsObserver.Enabled=1`, `RoadTargetPreviewEnabled=1`. The supplied example remains OFF.

1. Start the supported offline single-human France1 race. If a live route has not yet been captured, perform one ordinary stock Reset, resume driving and let recovery finish before pausing again.
2. Pause natively, activate Freecam, and move near a clear road marker within 20 XZ units. Press T once and capture F10 before unpausing. Expected: `road_teleport_armed`, `owner_gate_reason=accepted`, readable/stable allocation, native participant count 1 and indexed countdown 0.
3. Resume manually and invoke one ordinary vehicle Reset. Confirm visibly that the car reaches the selected road point. Continue briefly and exit normally.
4. Provide the session JSONL and F10 capture. The session header must contain the candidate hash above.

Telemetry PASS requires selected input ordinal, unchanged native returned ordinal, matching publication candidate, committed matrix X/Z at the chosen marker, exactly one matching physical consumer, chassis X/Z at the committed destination, recognized native clear and a readable subsequent zero sample. Expected final state is `road_teleport_completed`. A queued/armed request or matrix copy alone is not PASS. The ground query owns Y/orientation and velocity recovery; route membership does not prove obstacle clearance.

Any rejection must show current countdown array/value and ownership reason. Any unexpected native result is retained. If the flag clears before physical consumption, status reports that causal failure rather than declaring success. Keep Freecam/display settings unchanged during this one test.

## Clean source handoff

`source-handoff.zip` contains the current source, documentation, tests and required build dependencies, including **both bridge `.inc` files**, transaction capture and the new event dispatcher. It excludes generated binaries, proprietary game assets, raw runtime logs, retained captures and ignored analysis state. `MANIFEST.json` identifies the uncommitted source snapshot with per-file hashes; the starting Git commit is not asserted to contain all these files.
