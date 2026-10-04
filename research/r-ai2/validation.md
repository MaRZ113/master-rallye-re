# R-AI2 validation boundary

## Baseline

Before research edits: branch `research/r-ai1-1-hardening`, HEAD `6b30a48`,
tracked tree clean; existing local Ghidra/archive artifacts excluded. Synthetic
suite **302 passed, 0 failed, 0 skipped**; compileall and diff-check passed.
Fixed, generalized, base-only hardening and randomized-hardened EXE verifiers
passed. Previous four-car runtime results remain closed and unchanged.

## Deterministic preparation evidence (retained chronology)

The new synthetic suite has **316 passed, 0 failed, 0 skipped**, including
14 R-AI2 tests for guarded policy, stock pool, source/output hash rejection,
size/original-byte/range checks, deterministic inversion, disjoint patches,
manifest scope, Broker identity/provenance, own Car4 physics, five results and
the capacity matrix. Results fixtures retain the pinned native parser's quoted
StringList representation, verified against the existing hardened four-car
capture. These are fixtures, not a fabricated five-car capture.

Actual native x86 emulation: **44 passed, 0 failed, 0 skipped**:

- 16 full stock chooser runs: eight seeds, each four/five-car control; exact
  indices0..4, no Car5 publication, distinct vehicles/drivers, preserved player
  and first three vehicle draws, normal pool/shuffle/driver bookkeeping.
- 11 direct shim cases: original read, accepted configuration and rejected
  opponent/mode/human/ghost/player/course guards; registers/flags/stack retained.
- 10 ordinary setup cases: both reads, NumCars increment, first AI index/count.
- 7 storage cases: native pointer-vector growth through five entries, five
  physics-handle destructions, four AI destructions, progress initialization
  and destructor at N4/N5, result allocation/append/rank publication at N4/N5.

Bounded allocations have untouched redzones. The result test runs native
47D6D0/47C6C0/47DBE0 and publishes rank5 for participant4. Finish-time sorting
is an explicit boundary; UI lists are checked by the separate synthetic oracle.
Heap, Broker, scene and OS boundaries are explicit. These emulation tests do not exercise game rendering, collision simulation, a completed fifth finish or Results UI; the later human validation establishes that separate evidence.
The Ghidra transaction is rolled back and the project is not saved. Newest
installed Ghidra12.1.4 is used; [derived evidence index](static-evidence-index.json)
records function addresses and assembly-listing hashes without raw disassembly.

The shared chooser emulator's original generalized four-car suite passes
**94/94**; native hardening passes **52/52** (40 Loading, 12 Dump), with no
failures or skips. See [emulation summary](emulation-summary.json). The new candidate is verified by source-size/hash,
every original/replacement byte, PE mapping, non-overlap, inverse-to-pristine
and exact regeneration. A second independent build is byte-identical, output
SHA256 `806ebedcd6d174682fcc4619fb75eaabca2a1281eda4d4d784807b3583f5f2e2`,
size3,121,214. All five current/legacy verifier profiles pass.

The Observatory adapter loads the audited distribution in a fresh Python
process and accepts this exact profile with `-- --help`; the game is not
launched. File pinning, unknown-image rejection, read-only capture behavior and
JSON/raw integrity remain in force. Existing Loading and NULL-Dump hardening
are reproduced unchanged, not reimplemented or weakened.

Stock ownership caveats remain explicit: two progress key arrays are retained
by stock destruction, and full result-record reclamation is not established.
This is not a fixed-four cleanup limit, but long-run heap stability is unproven.

## Reproduction

From the checkout:

```powershell
python -m unittest discover -s tests/synthetic -v
python -m compileall src tools tests
git diff --check
python tools/r_ai2_capacity.py verify .research-output/r-ai2/five-car/MRallye.exe
```

With the existing read-only pristine Ghidra project and latest installation:

```powershell
& '<bridge Python>' tools/scanner/r_ai2_emulate.py --install '<Ghidra12.1.4>' --project _ghidra_project --source ../corpora/retail/MRallye.exe --candidate .research-output/r-ai2/five-car/MRallye.exe --output .research-output/r-ai2/emulation.json
```

Builder reproduction and exact ranges are in [intervention](five-car-intervention.md).
Logs, emulation details, proprietary EXEs and all future captures stay ignored.
**Five-car runtime status: CLOSED / CONFIRMED_BY_RUNTIME.** Both bound captures pass the original checkers, whose runtime_full_pass remains false by design. Human FULL PASS is recorded separately in [closeout](runtime-closeout.md). Closeout reruns the 316-test suite, 44-case native five-car emulation, compileall, candidate/base verifiers and diff-check. No missing fixture was encountered.
