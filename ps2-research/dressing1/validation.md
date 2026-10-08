# Validation and acceptance

PS2-DRESSING1 STATUS: COMPLETE within the bounded static ownership contract.
RUNTIME_VALIDATION: NOT_PERFORMED. COMPLETE does not mean live visibility,
pixel parity, recovered scenery populations or implementation readiness.

| Check | Result | Evidence |
|---|---|---|
| Canonical PS2 provenance | PASS | Fresh preflight/postflight four-file size/SHA checks |
| PC integrity | PASS |87 distinct inspected files rehashed;90 check records include path aliases |
| SDK reference | PASS |4244fa0c4d878523c9947f54816bf377cdfb2589; clean before/after |
| PC renderer/proxy | PASS | No HEAD diffs or writes in readonly paths |
| GEOM1 preservation | PASS | Three original full-report SHAs unchanged; fresh targeted source/water/ground anchors |
| Complete four candidate records | PASS | Source/material offsets, full paths, bounds, strip controls, ancestors and PC evidence |
| Boat independent check | PASS |113 unique source faces ->113 unique of125 PC draw825 records;0 ambiguous |
| Full unittest | PASS |240 tests,0 failures/errors/skips;61.704 s |
| Full pytest | PASS |240 tests and282 subtests;0 skips;62.26 s |
| Isolated bundle unittest | PASS with declared SKIP |209 successful methods;222 testsRun,18 skip entries;0 failures/errors;0.195 s |
| Isolated bundle pytest | PASS with declared SKIP |209 passed,31 dependency skips,166 subtests passed;0.47 s |
| Compileall | PASS | Current tools/tests including packaging helper |
| Diff-check | PASS | Working and final staged whitespace checks |
| Reproducibility | PASS | Both final original-corpus diagnostic SHAs289a7d23...632802; byte-identical |
| Private maps | PASS | Turkey/Italy source SVG generated; Turkey PNG inspected; excluded from Git/archive |
| Handoff | PASS | Isolated code/fixtures tested; post-commit archive CRC and per-payload SHA/size verification |
| Optional haybale EOF probe | NOT_DECODED | Explicit strict-format refusal, preserved in evidence; not a false PASS or silent SKIP |
| Live selected group/frame | NOT_PERFORMED | Deferred controlled plan; no synthetic/runtime promotion |

The isolated unittest denominator includes13 individual skipped methods plus
five setup-class skip entries; setup-class entries do not all increment testsRun.
Thus222 testsRun/18 skip entries corresponds to209 successful methods. Pytest
expands class dependency skips into individual methods, yielding31 skips.
Dependencies are the external SDK, canonical ELF/PackFS/PC/HUD and original UI2
XML. They are documented in HANDOFF.md; no unexpected failures are hidden.

The first full unittest attempt was FAIL:239 testsRun with two missing GXI
subtest errors because PS2_UI_CORPUS pointed at incomplete data/validation.
The existing complete ui1/extracted corpus resolved both errors; tests were
unchanged. The final run also includes the subsequently added whole-boat control.
An --ee-scalar Ghidra attempt was explicitly rejected for HI/LO consumers;
--ee-sqrt-only preserved those instructions. Incomplete EE predicates remain
UNKNOWN instead of being rewritten into an invented selector.

Full suites ran concurrently, so wall times are not isolated performance
benchmarks. Public bounded diagnostics process only the selected source groups
and family targets; existing all-course matching is not rerun. No arbitrary
all-pairs whole-corpus search, hidden geometry skip or external heavy dependency
was introduced. Complete source diagnostics/maps stay ignored.

## Acceptance matrix

| Gate | Status | Proof boundary |
|---|---|---|
|1 Git discipline | PASS |master, no branch/worktree/reset/push; user ZIP preserved |
|2 Corpus provenance | PASS |Canonical PS2 and inspected PC identities |
|3 GEOM1 preservation | PASS |40,832/36,001;41,817/41,620;40,479/39,682 source/exact anchors |
|4 PSM hierarchy | PASS |All four complete ancestor/child paths with source offsets |
|5 Node interpretation | PASS |Generic group/mesh/selector/bound roles grounded in original ELF |
|6 Transform ownership | PASS |No local matrix in selected source groups; landscape and spline carrier distinguished |
|7 Instance model | PASS |Source/component/reference/carrier/live levels; unknown populations explicit |
|8 LOD/conditional model | PARTIAL |Culling and child dispatch proved; full directional/membership predicates and live alternatives unresolved |
|9 Runtime visibility honesty | PASS |No source count promoted to live budget |
|10 Turkey shrub | PASS |Grouping, material/hierarchy, PC scope and foliage consumer limit |
|11 Turkey hut | PASS |Multiple subparts;126 source faces with fitted PC counterparts; whole group unresolved |
|12 Turkey boat | PASS |Whole113-face group has one proper rigid correspondence to PC draw825 subset |
|13 Italy pine | PASS |Multiple grouping methods, PC pinus family, final tree representation bounded UNKNOWN |
|14 Broader PC search | PASS |Paths/TXT/XML/shared/standalone identities plus selected geometry fits |
|15 Static/dynamic dinghy | PARTIAL |Owner/model/baked distinction proved; exact instance/pose/safe replacement remains NOT_READY |
|16 Instance counts | PASS |No invented tree/boat/hut counts; duplicate haybale references preserved |
|17 Diagnostic visualization | PASS |Source-region maps/ancestor labels/material components inspectable |
|18 Structured inventory | PASS |All four complete compact cards and versioned ownership inventory |
|19 Portability assessment | PASS |Reuse/replacement/addition limits; no PC implementation |
|20 Regression | PASS |Full/isolated suites, source integrity, compileall and diff checks |
|21 Scope discipline | PASS |No asset, SDK, renderer, physics or subsequent-phase change |

The two PARTIAL gates are explicit sub-contracts, not disguised runtime claims.
The phase closes because the principal source->hierarchy/transform->bounded
instance/selection->PC counterpart chain is useful and reproducible, and all
four investigations plus the dinghy control reach their strongest supported
conclusions. Tree rendering and dynamic/static instance correspondence are
separate unresolved dependencies; no implementation-ready population is claimed.

The committed report cannot recursively include its own commit/archive hashes.
The final archive MANIFEST.json records actual post-commit HEAD and every payload;
ignored data/dressing1/ZIP_SHA256.json records archive SHA/size/CRC result. Final
reply reports the exact commit and archive location. The pre-existing user
ps2-research.zip hash27230b7e...55367 remains unchanged and is never packaged.
