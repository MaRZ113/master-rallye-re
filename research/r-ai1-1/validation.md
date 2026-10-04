# R-AI1.1 validation — 2026-10-04

Baseline: **270 passed, 0 failed, 0 skipped** before research edits. Starting
branch research/r-ai1, HEAD73ccb37, tracked tree clean. Latest on-disk Ghidra
12.1.4 with installed ghidra-bridge/pyghidra was used read-only; temporary
analysis/disassembly/emulation transactions are rolled back, project not saved.
Raw outputs stay under this checkout's ignored `.research-output/r-ai1-1`.

Final synthetic suite: **285 passed, 0 failed, 0 skipped**. R-AI1-specific:
**31 passed**, including all previous16 tests, one live-offline-key correction
test and14 generalization tests. Compileall and diff-check PASS.

## Native x86 emulation

**94 cases passed, 0 failed, 0 skipped**:3 STOCK,3 DIVERSE,81 MIXED
(all27 class sequences for player IDs0/7/14),7 paired setup/mode guards.
The7 guards also run pristine controls:101 native chooser executions total.
Actual class pool cases, vector erase/clear, vehicle shuffle, driver helper,
driver shuffle, CRT srand/rand and publication/control flow execute. Tests
check independent three class-range requests, unchanged human, distinct valid
IDs/drivers, stock-equivalent guard outputs/RNG calls, RET/ESP/SEH and callee-saved
register restoration. No fifth slot is read/written. Legacy selector emulator
also passes **248/248** unchanged.

Boundaries: synthetic Broker, vector insert heap/free and TLS pointer; scripted
class range outputs and synthetic seed stimuli at game range helper. Native
floating RNG computation, actors, physics/collision, renderer and game timing
are not emulated. Therefore generalized game runtime remains **UNKNOWN**.

Reproduce with the installed bridge Python/latest Ghidra:

```powershell
& '<ghidra-bridge Python>' tools/scanner/r_ai1_emulate.py --general-source '<pristine MRallye.exe>' --install '<latest Ghidra>' --project _ghidra_project --output .research-output/r-ai1-1/native-emulation.json
python -m unittest discover -s tests/synthetic -v
python -m compileall src tools tests
git diff --check
```

## Deterministic build and integrity

Candidate SHA `f9e8e556842602252ec39b2174e796f6cb67651d8f573f2565f9d2e5569bd9ac`.
Two in-memory builds reproduce identical EXE/manifest; emitted file matches.
Inverse verification restores exact pristine SHA. Source/profile/size/layout/
original-byte gates and modified-ranges-only check PASS. STOCK returns exact
original bytes. Patched source, legacy candidate as source, unknown image and
unrelated-byte mutation reject. Manifest emits five ranges, hashes and purposes;
proprietary EXE remains ignored. No image/page/raw/participant allocation growth.

External Observatory scripts remain pinned and hash-identical. New and legacy
exact adapters verify; unknown executable and modified implementation tests
reject. All three supplied JSON/raw pairs (attractmode, mixed-front, mixed-race)
reparse identically. Fixed live oracle now returns BROKER_STATE_MATCH_ONLY
using actual offline keys. No randomized runtime captures yet.

The [canary table](vehicle-physics-canaries.json) reuses `r5v_a_inventory.xml_values`
and canonical registry. It is reproduced from exact vehicles.xml SHA
`a6762bb20999c7224c71b9f5d1d7edca55bcea147ff9f973300a8cf8d350aee0`:
three named numeric values per25 stock families, not invented physics semantics.

Ignored reports: `native-emulation.json`, `legacy-emulation.json`,
`integration.json`, `fixed-runtime-oracle.json`, `candidate-build.json`,
`candidate-verify.json`, `synthetic.log`, `compileall.log` and candidate manifest.
No additional subsystem test is required because those implementations were
not changed. Human randomized sampling/lifecycle is the next gate only.
