# PS2-RIGID1 validation

| Check | Result |
|---|---|
| Focused RIGID1 unittest | PASS:37 tests,0 failures,0 skips;33 synthetic/compact+4 original-data integration methods;10.267s |
| Full PS2 unittest | PASS:345 tests,0 failures,0 skips;75.105s |
| Full PS2 pytest | PASS:345 tests and290 subtests,0 failures,0 skips;76.40s |
| Compileall tools/tests | PASS |
| Canonical source and reference integrity | PASS:four full PS2 hashes and five selected PC baseline hashes; SDK clean at4244fa0c; renderer/proxy diff empty |
| Deterministic CLI | PASS:two byte-identical synthetic JSON runs, compact expected trace |
| Runtime PCSX2 | NOT_PERFORMED; precise future capture plan supplied |
| Isolated handoff unittest | PASS:301 successes;318 executed methods;26 reported skip entries including9 class-setup skips;1.969s |
| Isolated handoff pytest | PASS:301 tests and174 subtests;44 explicit external-input skips;2.45s |
| Diff-check / final scoped commit | Diff-check PASS; actual scoped commit recorded in archive manifest/receipt |

Initial restricted unittest ran345 methods with **six errors**, all Windows PermissionError in existing temporary-directory/link tests. That run is **FAIL / filesystem restriction**, not PASS or SKIP. Reviewed execution with the necessary filesystem access passed the unchanged regression suite. `unittest-restricted.log` and the successful log are both retained. No test failure was hidden, no unexpected exception became a skip, and no original asset was made writable by the diagnostic.

The full pytest includes the final additional vtable-word checks. The final focused suite also verifies those words against the canonical executable. The source/data tests are kept separate from synthetic activation/math and compact fixture checks. Passing derivative/RK4 tests does not validate a full contact solver, actual original seed/timing or visible collision parity.

## Acceptance matrix

| Gate | Status | Evidence / exact boundary |
|---|---|---|
| 1 Git discipline | PASS | requested master, scoped PS2 paths; pre-existing Observatory edits preserved; no push |
| 2 Canonical corpus | PASS | four canonical identities checked; PackFS originals read-only |
| 3 Authored inventory | PASS | 83 records,9 rigid courses,36 course controls;58 hay/25 tumble |
| 4 Resource identity | PASS | two byte-identical hay aliases and exact tumble PSM hash |
| 5 Class registration | PASS | string472360,factory15b190/call15d014,ctor19fcd0,vtable473820 |
| 6 Property parsing | PARTIAL | Mass/MOI consumed; trigger/shadow typed storage proved, later consumers not identified |
| 7 Runtime layout | PASS | owner/body/manager/shape/transform layouts and original instruction evidence |
| 8 Physics ownership | PASS |171c78 registered body in real manager vector; allocation precedes proximity |
| 9 Collision representation | PASS |model+34 convex container ->concrete backend instance ->body pointer; A/B stage choice unknown |
| 10 Activation | PASS |first two views,radius4 predicate,3D<=10000,contact wake/far resume; authored trigger excluded from selected update |
| 11 Timing | PARTIAL |two fixed halfsteps per invocation proved; scheduler wall-clock frequency/pause semantics not captured |
| 12 Linear dynamics | PASS |13-state momentum derivative and selected RK4; independent original gravity/derivative oracles |
| 13 Angular dynamics | PASS |qdot,local/world inertia,normalization,R and omega/L route; exact PS2 numerical edges bounded |
| 14 Car contact | PARTIAL |dispatch,wake,selected impulse application and state commitment proved; magnitude/full material mix unknown |
| 15 Terrain contact | PARTIAL |convex/BSP dispatch and initial correction plus contact route; full narrowphase/settling unknown |
| 16 Physics-to-visual | PASS |267f60 ->Broker Transform ->265d18 ->same entity en3d all16 words |
| 17 ItalyS1 | PASS |primary hay source/properties/shape/body/visual chain |
| 18 Turkey1 | PASS |primary tumble source/properties/convex shape; no invented wind |
| 19 Duplicate control | PASS |14 distinct source records retained at13 matrix hashes |
| 20 Cross-course | PASS |Italy2 MOI/shadow/list contrast plus all36 authored scans |
| 21 PC hay counterpart | PASS |standalone visual/convex positive control; baked draw/name leads kept separate from instances |
| 22 PC tumble counterpart | PASS |7595-name/270-text bounded negative; no universal absence claim |
| 23 Portability | PASS |reuse/instance mapping/contact/runtime/renderer interfaces distinguished; no implementation |
| 24 Offline diagnostics | PASS |bounded reproducible inspection/math/pose; unsupported contact simulation omitted |
| 25 Runtime honesty | PASS |NOT_PERFORMED; selected original physical update differs from live collision observation |
| 26 Regressions | PASS |full and focused tests,compileall,determinism,source integrity; handoff/diff closeout below |
| 27 Scope | PASS |no PC physics,assets,renderer,SDK,next phase or universal engine reverse |

The PARTIAL gates are explicit boundaries of the bounded contract, not missing physical integration or visual pose ownership. The user status rule permits static COMPLETE without a complete general contact solver. Runtime remains NOT_PERFORMED.

## Independent handoff and closeout

The isolated copy removes all original corpus/SDK/HUD environment variables. Its unittest requires no additional runner packages. Pytest first reported `No module named pytest` after clearing PYTHONPATH (**BLOCKED: runner dependency**, no tests ran); rerun used only the existing public pytest dependency directory and passed. Both logs are retained. An initial incorrect relative log destination also prevented invocation; absolute destinations corrected it before these reported runs. Neither setup result is counted as a test PASS.

Unittest reports class-setup skips differently from pytest:301 successful methods plus17 method skips yield318 executed methods, while9 class-setup skip entries produce26 reported skips. Pytest enumerates345 methods:301 successes+44 missing-external-input skips. No missing compact JSON dependency or unexpected failure occurs. Full original-data regression has0 skips.

The final ZIP is built from the scoped commit. Its source commit, CRC, file-level SHA/size and archive SHA are recorded in MANIFEST.json and the external receipt, avoiding a self-referential committed hash. The tested independent copy has the same tools/tests/compact oracles as the final handoff; later narrative/log updates do not change those tested inputs.

Six unrelated Observatory paths were present at preflight and are excluded from staging/commit. Original-source verification is exact for allfour PS2 files and five inspected PC assets, with clean same-HEAD SDK and empty renderer/proxy diff; it is not a fresh hash inventory of every unrelated PC file. No game writer was introduced or invoked.
