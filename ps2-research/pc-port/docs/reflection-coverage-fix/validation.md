# Validation

Final DLL and exact source/test/patch hashes: `build-report.json`.
Build log: ignored `.build/logs/reflection-coverage-fix-release-build.log`.

| Check | Result |
|---|---|
| Baseline Win32 Release, serial incremental build | PASS |
| PS2-enabled Win32 Release, serial incremental build | PASS |
| Baseline CTest | 24/24 PASS |
| PS2-enabled CTest | 30/30 PASS |
| Both proxy export verification | PASS |
| Interface generator repeated twice for both variants | deterministic, no initial file rewrite |
| Port unittest | 115/115 PASS |
| Port pytest | 115 PASS,470 subtests PASS |
| Source-panel metadata tests | 5/5 PASS |
| WOOLDAND/Forester independent tests | 5/5 PASS |
| Modified-material metadata tests | 3/3 PASS |
| Final compileall and diff-check | PASS |
| Frozen renderer source/tree and exact patch hashes | unchanged, PASS |
| Original corpus hashes | verified by read-only source audits |
| Course SDK status/HEAD | clean,4244fa0c4d878523c9947f54816bf377cdfb2589 |
| Post-fix game run / visual parity | NOT_PERFORMED / NOT_ESTABLISHED |

The native tests exercise all212 signatures with synthetic native state, old
identity compatibility, rejected unknown digests, wrong current resources,
FVF0x142 rejection, world/native context checks, affected-family-only admission,
Mode4-only additions, exactly one draw, original HRESULT, state transactions,
resource retention and Reset. These are code-side checks, not live car identity.
Verified local GXI Reset/upload and all36 grass/shrub file pairs were available
to the native suite. Missing external fixtures must be reported explicitly.

No new capture/resolve code was added. Existing MSAA/capture native tests passed;
the earlier standalone real D3D8 resolve result is not relabeled as a new game
test. Broad unrelated legacy research suites were not rerun. The known missing
`pefile` dependency of the wider renderer Python environment was not repaired
or concealed as a passing test.

The .001 exact geometry baseline remains unchanged. Eight new source-material
relations use a separately documented .005 displacement threshold. These are
neither identical triangles nor UV parity. Four position-only joins remain
explicitly distinguishable from complete emitted-face matches.

Final handoff integrity, isolated corpus-independent tests and modified-material
metadata checks are recorded in `handoff-validation.json` and command-log.
The first new metadata assertion incorrectly equated raw Navara face counts
with nondegenerate counts; it failed on3/1 suppressed zero-area source records.
The assertion was corrected to retain both original count categories. Production
geometry, registry and already built DLL were not changed by this test repair.
