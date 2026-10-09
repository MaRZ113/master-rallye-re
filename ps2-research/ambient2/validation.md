# AMBIENT2 validation

**Static flying-bird chain: COMPLETE. Runtime validation: NOT_PERFORMED.**

| Check | Actual result |
|---|---|
| Full unittest, configured PS2/PC/SDK/HUD inputs | PASS:308 successful methods,0 failure/error/skip;96.132s |
| Full pytest, same inputs | PASS:308 tests,290 subtests,0 failure/skip;97.35s |
| Final focused Bird suite after output/provenance adjustment | PASS:38 methods,0 failure/error/skip;4.874s |
| Focused split | 34 synthetic/compact-evidence methods;4 original-corpus methods |
| Compileall tools/tests | PASS |
| CLI inventory/resources/contract/trace | PASS: five outputs byte-identical to committed contracts / repeat trace |
| Independent RNG oracle | PASS:1000 positive states versus modular recurrence, low24 output separately |
| Original scalar probes | PASS: original rise and updated-speed/travel FPU windows executed on synthetic state |
| Git diff-check | PASS; scoped final index check also required before commit |
| Isolated handoff unittest | PASS:268 successful methods,17 method skips plus8 class-setup skips; standard result Ran285,skipped25;0 failures/errors;0.292s |
| Isolated handoff pytest | PASS:268 tests,174 subtests;40 explicit external-input skips;0 failures;0.72s |
| Canonical/source/reference integrity | PASS: allfour fresh PS2 hashes; scanned PC texture hash unchanged; SDK clean sameHEAD; renderer/proxy diff empty |

Initial restricted full runs:307 methods, six errors in existing synthetic temporary-directory/link tests; pytest301 successes/6 failures. Status **FAIL / Windows sandbox restriction**. Reviewed reruns allowed those filesystem operations and passed; no tests were weakened or unexpected errors made into skips. Both original and final logs are retained.

One added integration method distinguishes original MPG commands from instruction payload+4 and checks each chunk/hash plus combined program hash. Tests do not count source points as birds, model a spline, invent an original per-course seed, replace the renderer or certify live visual parity. Exact detailed observations and dependencies are in `offline-validation.md` and `HANDOFF.md`.

## Acceptance matrix

| Gate | Status | Evidence / exact boundary |
|---|---|---|
| 1 Git discipline | PASS | Requested clean master checkout; scoped PS2 changes; no push |
| 2 Canonical provenance | PASS | Four canonical source SHA/size freshly verified; no source writer |
| 3 Bird source inventory | PASS | All36 pairs,36 managers,542 FlightList/55 MillList records |
| 4 Point semantics | PASS | Ordered marker loader and nearest/spawn consumers; origins, not a flight spline |
| 5 Registration | PASS | Factory15d29c/15d2a4,sizeb0,ctor1ae8b8,clone1cec68,vtable473c10 |
| 6 Runtime layout | PASS | Essential manager vectors,FlyBird,entity/carrier/visual/switcher fields |
| 7 Spawning | PASS | Flight probability/count/annulus/origin/pending conversion and pool reuse; Miller population producer explicitly unknown |
| 8 Count discipline | PASS | Source/capacity/active/submission/visible layers kept separate |
| 9 Randomness | PASS | Original global RNG,integer recurrence/output/call order; actual course state not invented |
| 10 Motion | PASS | Fly equations through carrier world-translation stores and en2d copy |
| 11 Path behavior | PASS | No spline/waypoint loop in recovered flight controller; cached origin selection distinguished |
| 12 Orientation | PASS | Translation-only Fly; proved Y-locked camera-dependent sprite basis |
| 13 Group behavior | PASS | Independent random controllers sharing burst origin; no neighbor steering in traced chain |
| 14 Animation | PASS | Three flight keys and strict counter timing,groundkey3,separate AI slot |
| 15 Visual resources | PASS | Named Burdy PSB/GXI hashes/layout and consumer chain |
| 16 Render ownership | PASS | Entity→world sprite queue→PSB→cache→texture/state→submission |
| 17 Alpha/depth/GS | PARTIAL | Mode8 known masks/blend/depth-write; final inherited ZTE/FRAME/TEXA/descriptor needs capture |
| 18 Visibility | PARTIAL | Manager distance/queue/command/generic-clip path proved; live active/visible set,initial four-key effect unknown |
| 19 Course cases | PASS | France1 ordinary,SpainW shortest,Turkey3 missing-list control |
| 20 Generality | PASS | All36 authored interpretations plus ItalyS4 sanity; no live all-course claim |
| 21 Offline diagnostics | PASS | Repeatable explicit-state flight/animation/billboard/state and inventories |
| 22 PC comparison | PASS | Bounded7595-name/122-XML scan; no universal geometry absence claim |
| 23 Portability | PASS | Source/assets/controller/renderer readiness separated; no PC implementation |
| 24 Runtime honesty | PASS | NOT_PERFORMED; live VU/frame/seed/cadence kept UNKNOWN |
| 25 Regression | PASS | Full308 tests,focused final38,compileall,reproducibility and closeout integrity |
| 26 Scope discipline | PASS | No PC/SDK/asset/EXE modification or next phase started |

PARTIAL gates concern final inherited/live state, not missing primary motion or draw producer. Ground activation and retained MarkerList registry are explicit bounded unknowns; no complete ground-bird or pixel-parity claim follows from static closure.

## Closeout

The final archive is built from the scoped local commit. Its actual commit/hash/size/per-file SHA and CRC result are in the external receipt/MANIFEST, avoiding self-referential committed commit hashes. Isolated-copy tests provide a separate proof that required compact historical JSON fixtures are included. Original proprietary inputs remain external; explicit dependency skips are reported separately from successes.

The isolated unittest counts class-setup skips differently from pytest:285 executed methods comprise268 successes and17 method skips; eight additional class-setup skips yield25 reported skip entries. Pytest enumerates all308 methods,268 successes/40 dependency skips. All included compact fixture accesses succeed; these skips are absent external corpora, not missing bundle JSON.

The primary checkout was clean initially. During closeout unrelated Observatory files changed concurrently (root README, runtime tools/tests and release documentation). They are recorded in `integrity-checks.json.parallel_changes_preserved`, preserved unstaged/unmodified by AMBIENT2 and excluded from its commit. Correct Git discipline here means the phase changes only its intended PS2 paths, not that another task's working tree remains clean.
