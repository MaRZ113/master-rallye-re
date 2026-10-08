# PS2-GRASS1 validation and completion gates

Overall **PS2-GRASS1 STATUS: PARTIAL**. The source/parser/owner/generator and
CPU resource/packet chain are executable-backed. Matching embedded VU programs
have a concrete sprite/GIF contract. Exact upload/residency and final frame
flush remain essential execution links, independently of visual parity.

## Check results

| Check | Result | Basis |
|---|---|---|
| Canonical ELF, CNF, PAK,000 | PASS | Fresh SHA/size verification before and after research; exact values in case-evidence.json and ignored final-checks.json |
| Named extraction | PASS | Existing PackFS, four fresh landscape payloads and GRASS1/BUSH1 GXIs; no duplicate container/image parser |
| Structural corpus | PASS |36/36,671,413 triangles with unique source material binding; cached payloads compared against fresh named extraction |
| Focused tests | PASS |20 unittest tests, including two optional proprietary checks enabled |
| PS2 regression unittest | PASS |150 tests,0 SKIP; PackFS/UI/UI2/CDELTA1/AMBIENT1/GRASS1 |
| Relevant pytest | PASS |150 tests and164 subtests |
| compileall | PASS |tools and tests |
| git diff --check | PASS |Before staging and final staged review |
| Seven original-source diagnostics | PASS |Repeat output SHA equality; explicit synthetic activation/camera/rounding inputs, not PS2 placement parity |
| Embedded single-sprite diagnostic | PASS |Analytic synthetic corners/STQ/FTOI4, size cap and center clip controls |
| Original files | PASS |Immutable reads; fresh four-container hashes unchanged |
| Course SDK | PASS |Same4244fa0c4d878523c9947f54816bf377cdfb2589 HEAD and clean status |
| Live PCSX2/debugger capture | SKIP |No supported active session available; no runtime PASS claimed |
| Exact MPG upload/residency | BLOCKED evidence gate |No CPU upload reference established; decoded stream linkage remains STATIC_INFERENCE |

The existing PackFS hard-link extraction fixture required host execution:
sandbox execution returned WinError5. The suite was rerun with its normal
fixture and host permission; no test was weakened. Automatic approval review
did not reject an action. Environment failure was not counted as a PASS.

## Twenty-gate acceptance matrix

| Gate | Status | Evidence / precise boundary |
|---|---|---|
|1 Repository discipline | PASS |General worktree, master, clean preflight; only intended ps2-research paths committed; SDK untouched |
|2 Corpus provenance | PASS |All four exact canonical SHA/size identities checked |
|3 Directive consumer | PASS |2d5100 substring extraction at2d7114/2d7148 and interning |
|4 Runtime material representation | PASS |Proxy+98 interner IDs, material-index lookup and owner+102c/+1030 comparisons |
|5 Material-to-geometry | PASS |Actual tag103 spatial surfaces share model vertices; France positive4 and none8; visual strip/LOD equality remains UNKNOWN |
|6 Position source | PASS |Runtime incremental generation from spatial triangles, not authored points or random barycentric samples |
|7 Surface eligibility | PASS |Category, upward normalized crossY>.975, degenerate threshold, queried/clipped activation region |
|8 Density/count | PASS |Pitch1.33 scanline lattice, half-open loops and capacity growth; separate point/record/output budgets; conditional precision documented |
|9 Randomness | PARTIAL |Original fixed seed30ff, LCG and table/call order recovered; guard lifetime and live FCSR/history stability not captured |
|10 Grass/shrub distinction | PASS |Pools1/0, name IDs, cached resource lookup, handle binding and shared record consumer |
|11 Stones | PASS |Recognized/stored but excluded by this two-pool branch; no separate stone renderer is claimed |
|12 Special directives | PARTIAL |None and singular shrub exclusion proved; no grass-off override in this path, cooker/other semantics UNKNOWN |
|13 Primitive geometry | PARTIAL |Embedded pc449 two corners/STQ/RGBA/FTOI4/cap56 proved; actual program residency and live transforms unverified |
|14 Draw path | PARTIAL |CPU→VIF→MSCAL and frame DMA CALL proved; embedded GIF/XGKICK conditional on upload and final flush |
|15 Relevant render state | PARTIAL |Actual register IDs/mode11 and state-copy code recovered; inherited PRIM flags/live texture state unobserved |
|16 Lifetime/visibility | PARTIAL |Owner/create/destroy, camera activation, pruning and radial fade proved; frame guard writer, packet latency and live VU linkage open |
|17 Independent reconstruction | PASS |Deterministic bounded diagnostic, synthetic controls, original byte/instruction checks; no invented original camera state |
|18 PC portability | PASS |Selected sidecars rehashed; missing surface/category interface identified; no port |
|19 Validation | PASS |Configured suites, compileall, diff-check, reproducibility/provenance and scoped closeout |
|20 Scope discipline | PASS |No PC renderer, SDK, asset, water, reflection, HUD or gameplay changes; pending AMBIENT1 runtime work untouched |

PASS for a bounded contract does not imply runtime visual parity or an
unrecovered universal PSM format. No essential missing execution arrow is
silently promoted to confirmed evidence. The phase is PARTIAL under the user's
overall rule, despite substantial new static contracts.

## Reproduction

Use the normal Python with Pillow and the existing local CDELTA1 LZO support;
the bridge environment is separate. On the configured local corpus:

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:\Game\Master Rallye PS2'
$env:PS2_UI_CORPUS='D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\ui1\extracted\TNG\DATAPSM\HUD'
$env:PYTHONPATH='D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\cdelta1\python'
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/tests -q
python -m compileall ps2-research/tools ps2-research/tests
git diff --check
```

Raw canonical coordinates/decompilations/logs and the fresh local archive remain
ignored under data/grass1. Committed metadata contains counts, addresses,
hashes, offsets and short material facts. The actual commit/archive SHA values
are recorded in ignored git-closeout.json and the user-facing final reply;
the report's containing commit is recoverable through Git without self-hash
substitution. No push occurs.
