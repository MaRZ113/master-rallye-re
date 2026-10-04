# R-AI1.2 validation

Baseline 316 synthetic passed,0 failed,0 skipped; compileall/diff-check PASS.
Legacy generalized native94 cases and five-car native44 cases PASS; existing
general/hardened-base/randomized-hardened/five-car exact verifiers PASS.

Final checks, 2026-10-05:

| Check | Passed | Failed | Skipped | Scope |
|---|---:|---:|---:|---|
| Synthetic unittest suite | 334 | 0 | 0 | prior316 plus18 new tests |
| Compiled native C++ checks | 2534 | 0 | 0 | real parser/policy, five modes, count0..4, masks1..7, Stock0 RNG, byte-return ABI, DLL unsupported-host rejection |
| New native x86 emulation | 824 | 0 | 0 | 810 builder cases + Master transfer +7 loader cases +3 stage transitions +3 full five-car compositions |
| Legacy generalized x86 | 94 | 0 | 0 | original policies/native chooser regression |
| Legacy five-car x86 | 44 | 0 | 0 | original R-AI2 setup/allocation/progress/results/cleanup regression |
| Oracle CLI smoke | 4 | 0 | 0 | synthetic native-format JSON/raw, tampered JSON rejection, changed DLL/version rejection |

compileall src/tools/tests and diff-check PASS. Both new EXE inverse verifiers,
module verifier, and existing general/base/randomized-hardened/five verifiers
PASS. No missing test fixture. The four audited Observatory implementation
pins are unchanged; both exact new profile help smokes pass. The CLI oracle
smoke uses fabricated state, not a human runtime capture.

Native builder cases include QuickRace750, Master18, Cup18, Invitation18,
Challenge6. Quick covers every class plan for count1..4, three representative
human classes and rewards on/off, plus count0; campaign builders exercise
Stock and two three-class plans. Challenge uses synthetic fixed event table
entries, not a claim to have completed every retail Challenge.

Stock native writes, selected participants and game range calls match pristine
controls exactly. ABI/stack/SEH, callee-saved registers, bounded heap guards,
no inactive participant writes and no duplicate IDs are checked. Native range
outputs/DLL callbacks and Broker/TLS/heap insertion have explicit synthetic
boundaries. Compiled C++ tests separately exercise the real policy/parser;
the game DLL callbacks in Ghidra return controlled plans. This is not an
end-to-end execution of the game and Windows DLL in one emulator.

Actual Cup/Invitation/Master stage control flow keeps mixed identity tuples
without policy callbacks. Scoring/bests/conditions and XML/OS writer calls are
bounded interfaces in those cases. Master real452640 and452FE0 transfer typed
identity state into a fresh emulator instance; real disk serialization/process
restart remains human pending. Native stock saved tail fields are not active
six-car tests. Full composed47B780 -> existing capacity shim ->458090 tests
produce exactly five cars with Stock, Mixed-plan and Diverse-plan callbacks.

Absent DLL/export, already loaded DLL, truncated/long/baseless paths and export
ABI are exercised by the real loader bytes. Final DLL PE32/x86 exports and
two-directory byte equality are recorded in [build summary](build-summary.json).
Generated exact patch manifests contain original/replacement bytes and inverse
commands; checked-in metadata stores range hashes without proprietary payload.
Ghidra domain object is read-only, transactions rolled back, project not saved.

Ignored reports/logs are in `.research-output/r-ai1-2/`: synthetic-tests.log,
emulation.json/log, package/native-policy-tests.json, legacy-*-regression.json,
oracle-smoke/summary.json and build/repro logs. Safe summary is
[validation-summary.json](validation-summary.json).

No R-AI1.2 human game run has been performed. All automated/native-emulation
results are static evidence and cannot certify vehicles, racing, Challenge
completion, Cup progression or fresh-process Master save/load.
