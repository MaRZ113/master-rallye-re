# Validation and proof boundary

PS2-GEOM1 STATUS: COMPLETE at the bounded static/source-comparison level.
Runtime validation: NOT_PERFORMED. No live LOD, draw order or instance pose is
claimed. No PC geometry or renderer implementation occurred.

## Executed checks

| Check | Result | Actual scope |
|---|---|---|
| Canonical PS2 identity | PASS | Fresh preflight and postflight sizes/SHA-256 of all four canonical inputs |
| Original PC identity | PASS | Three DX, three TXT, three paired XML and two selected vehicle car.dx inputs |
| SDK reference | PASS | Clean before/after; HEAD 4244fa0c4d878523c9947f54816bf377cdfb2589 unchanged |
| PC renderer/proxy | PASS | No diff from starting HEAD; no files modified or deployed |
| Full unittest | PASS | 214 tests, zero failures/errors/skips, 30.627 s |
| Full pytest | PASS | 214 tests and 268 subtests, zero skips, 30.44 s |
| Isolated bundle unittest | PASS with declared SKIP | 187 successful methods; 200 testsRun and 17 skip entries including four setup-class entries; zero failures/errors, 0.188 s |
| Isolated bundle pytest | PASS with declared SKIP | 187 passed, 27 dependency skips, 166 subtests passed, 0.45 s |
| Compileall | PASS | Both research tools and test directories |
| Diff check | PASS | Final working and staged scoped changes |
| Reproducibility | PASS | Three fresh course loads/comparisons, core reports byte-identical |
| CLI cross-check | PASS | Turkey3 CLI report byte-identical to the independently run batch report |
| Handoff integrity | PASS | Same code/fixture selection passed isolation; final ZIP CRC and payload SHA checks performed by the packager |

Unittest adds setup-class skip entries without adding their methods to testsRun;
pytest expands those skips to individual tests. Those denominators are
intentionally not treated as equal; both runners executed 187 successful methods.
Missing SDK, original ELF/PackFS/HUD and local UI2 XML are explicit dependencies.
No missing compact JSON fixture or unexpected exception was hidden as a skip.
Windows temporary-directory/link fixtures ran on the permitted host to avoid
sandbox ACL failures; they did not modify original game files.

Full regression includes PackFS, UI1/UI2, CDELTA1, AMBIENT1, GRASS1, WATER1 and
REFL1. Eighteen new GEOM1 methods cover synthetic algorithms and selected original
integration. Synthetic inputs contain no copied proprietary triangles.

## Independent anchors

1. WATER1's frozen Turkey3 17 owners / 51 strips / 745 faces / 537 positions / 11
   shared-edge components and zero exact PC matches reproduce at 0.001.
2. France1 3,586/3,586 and ItalyS1 1,329/1,329 selected water triangle matches
   reproduce using the pre-existing WATER1 matcher, separate from new coverage.
3. Ordinary ground selection is independent of the water filter: Turkey3 node
   3502612 -> PC draw 436 (247 faces); France1 3613136 -> draw 519 (441); ItalyS1
   3758051 -> draw 530 (336). Tests separately read original tag/material/XYZ bytes
   at frozen offsets and independently verify corner residuals.
4. Course identity uses CDELTA1 internal landscape pairing, original ordered routes
   and authored identity matrices. No fitted transform makes surfaces agree.
5. Synthetic opposite diagonals, fan subdivision and T-junctions cover the same
   surface. Duplicates cannot inflate union coverage; elevated parallel surfaces
   do not become equivalent. Permutations, winding, disjoint regions, partial
   coverage, tiny/degenerate faces, nonfinite values, mirrors, budget failures,
   unsupported transforms and tolerance boundaries are explicitly exercised.
6. New dinghy EOF support is byte-confirmed by both exact original files and
   negative synthetic trailing/unsupported-wrapper cases. It is not called a
   newly executable-proved universal grammar.

## Numeric and performance limits

Host double calculations on decoded float32 inputs are geometric diagnostics,
not PS2 FPU/VU emulation. Exact triangle means six-permutation correspondence
within the named coordinate tolerance; bitwise equality is a separate metric.
Normal/plane/area/coverage tolerances are separate, with three profiles evaluated
for every course. Stable IDs do not depend on spatial hash traversal.

All supported groups participate. Runtime includes loads, comparison, SVG and the
independent water anchor in the measured batch: Turkey3 11.433 s, France1 14.817 s,
ItalyS1 11.511 s. Cumulative process peak working sets are 382,734,336,
566,882,304 and 566,882,304 bytes, respectively; these are not isolated per-case
memory peaks. Candidate counts and profile sensitivity are in committed JSON.
No all-pairs whole-course triangle scan or silently skipped large group is used.

## Acceptance matrix

| Gate | Status | Qualification |
|---|---|---|
| 1 Git discipline | PASS | Master, scoped commit, no branch/worktree/push/reset |
| 2 Input provenance | PASS | Original inputs checked before/after |
| 3 PS2 visual decoder | PASS | Selected grammar/provenance/ADC preserved; unknown tags fail |
| 4 PC visual decoder | PASS | Existing SDK complete/disjoint compiled draw validation |
| 5 Coordinate alignment | PASS | Independent routes and identity matrices, no fit |
| 6 Exact matcher | PASS | Six permutations, residuals, winding metadata and deterministic ties |
| 7 Surface equivalence | PASS | Union coverage tested for changed tessellation and overlap |
| 8 Numeric robustness | PASS | Three profiles, stacked/partial/degenerate/error cases |
| 9 Material independence | PASS | Separate axis; ambiguous TXT candidate mapping retained |
| 10 Turkey3 regression | PASS | Frozen extra-puddle result reproduced |
| 11 France1 regression | PASS | 3,586/3,586 |
| 12 ItalyS1 regression | PASS | 1,329/1,329 plus distinct water/puddle metadata |
| 13 Non-water geometry | PASS | Three ordinary ground anchors plus foliage/source candidates |
| 14 Cross-course generality | PASS | Three complete selected visual inventories, same contract |
| 15 Hierarchy/LOD | PASS | Source alternatives explicitly separated from unknown live selection |
| 16 Scene-object study | PASS | Two standalone dinghy models and PC baked candidates; placement remains UNKNOWN |
| 17 Vehicle feasibility | PASS | Optional Tata/Kia car subset; no full part/LOD claim |
| 18 Visualization | PASS | Three ignored source-coordinate SVGs and inspected Turkey3 PNG |
| 19 Delta schema | PASS | Version 1, stable source IDs and 90 compact selected records |
| 20 Portability | PASS | Research classifications only; visual/collision separation |
| 21 Regression | PASS | Full and isolated suites, compileall, diff and source checks |
| 22 Handoff | PASS | Required small fixtures included; dependencies and integrity manifest |
| 23 Scope | PASS | No game/SDK/PC-renderer modification or next-phase work |

PASS for hierarchy or objects means the required bounded investigation and honest
classification completed; it does not mean unknown live visibility or instance
correspondence was solved. See HANDOFF.md for commands/dependencies and the local
outer receipt for exact archive SHA and ending commit. Full logs, source arrays,
relation tables and visual exports remain ignored under data/geom1/.
