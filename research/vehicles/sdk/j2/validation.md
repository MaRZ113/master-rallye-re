# R5V-J.2 validation record

## Source and test state

Starting commit: `7bc85f8f1f32c1ad85c39ef501717a23df34e554` on
`research/vehicles`. The tracked tree was clean before J.2 work. No loader,
EXE patch, vehicle resource, profile, or save was modified in this closeout.
The only new test is
[`test_addon_sdk_j2_composition.py`](../../../../tests/synthetic/test_addon_sdk_j2_composition.py);
it exercises the shared reference-plan composition without claiming new
runtime behavior.

## Automated results

| Check | Command / scope | Result |
|---|---|---|
| Full synthetic suite | `PYTHONPATH=src python -m unittest discover -s tests/synthetic -v` | **397 passed, 0 failed, 0 skipped** |
| Focused SDK tests | `PYTHONPATH=src python -m unittest discover -s tests/synthetic -p 'test_addon_sdk*.py' -v` | **29 passed, 0 failed, 0 skipped** |
| Bytecode syntax | `python -m compileall src tools tests` | **PASS** |
| Whitespace | `git diff --check` | **PASS** |
| Combined native bundle | `python tools/addon_runtime.py verify .research-output/vehicles/sdk/j1/reference-runtime-final` | **PASS_STATIC_RUNTIME_BUNDLE**, 246 operations, 243 resources |
| Native launcher preflight | `mr-runtime-launcher.exe --verify MRallye.exe reference-runtime-final` | **PASS**, exact retail SHA, 243 resources, 246 operations |
| J.0 semantic plan | `python tools/mrtool.py addon verify .research-output/vehicles/sdk/j2/reference-plan` | **PASS**, plan SHA unchanged, `runtime_installable=false` |
| Deterministic rebuild | Build both manifests twice to clean output directories; compare every relative file SHA | **PASS**, all 4 output files byte-identical; plan SHA `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989` |
| Capture archive integrity | Hash archive and validate each JSON/raw association against raw bytes | **PASS**, 11/11 pairs, no unmatched entries |

The Windows synthetic tests require temporary fixture files to be resolvable by
the test process. The sandboxed first attempt returned `WinError 5` while
calling strict path resolution on its own temporary files. The unchanged full
suite was rerun with authorized fixture access and passed 397/397. No tests or
semantics were changed to obtain that result.

Exact console output is archived alongside this record in
[`tests-full-output.txt`](tests-full-output.txt),
[`tests-focused-output.txt`](tests-focused-output.txt),
[`compileall-output.txt`](compileall-output.txt),
[`candidate-verification-output.txt`](candidate-verification-output.txt),
[`capture-integrity-output.txt`](capture-integrity-output.txt), and
[`determinism-output.txt`](determinism-output.txt).

## Runtime status

The runtime archive is the human-provided 2026-10-09 Observatory capture set;
it is evidence of observed gameplay, not a test run performed by this closeout.
The captured states establish separate working ID26 and ID27 flows through the
same combined package. They do not close the remaining two-addon lifecycle
gates. Accordingly:

**R5V-J.2: PARTIAL_RUNTIME_CONFIRMED / READY FOR REMAINING HUMAN GATES.**

`R5V-J.2 TWO-ADDON EXTERNAL RUNTIME — FULL PASS` is not claimed until the
outstanding tests in [`human-qualification-handoff.md`](human-qualification-handoff.md)
have human evidence. J.3 and ID28 are not started.
