# R5V-J.2 validation record

> Current root-cause candidate and its validation are recorded in
> [`root-cause/validation.md`](root-cause/validation.md). Earlier tables below
> are historical validations of the supplied-capture baseline and the
> intermediate stack-ABI repair; they do not validate the latest mapper fix.

> The first re-entry candidate below was later `FAILED_BY_HUMAN_RUNTIME` due
> to a Vehicle Select crash. The authoritative critical-hotfix validation and
> repaired-candidate hashes are recorded in the addendum at the end and under
> [`critical-hotfix/`](critical-hotfix/).

## Starting state and scope

Canonical worktree: `master-rallye-re-vehicles`; branch: `research/vehicles`;
starting HEAD: `86f5ac8b1e6038615540665a73305547fbaf2f15`. The tracked tree was
clean before these J.2 closeout edits. The original retail executable remains
at `D:\Game\Master Rallye\MRallye.exe` and was checked after candidate
verification. No game EXE, original runtime launcher source, stock resource,
or save was modified. Generated candidate output is ignored under
`.research-output`.

## Automated validation

| Check | Command | Result |
|---|---|---|
| Full synthetic suite | `PYTHONPATH=src python -m unittest discover -s tests/synthetic -v` | **407 passed, 0 failed, 0 skipped**. The suite was run with temporary files rooted under the worktree's ignored `.research-output` directory and the approved test execution context, because the default sandbox temp directory caused child-process `WinError 5`. No test or assertion was changed. |
| Focused J.2 tests | `PYTHONPATH=src python -m unittest tests.synthetic.test_j2_frontend_reentry -v` | **10 passed, 0 failed, 0 skipped** |
| Bytecode syntax | `python -m compileall src tools tests` | **PASS** |
| Whitespace | `git diff --check` | **PASS** |
| Capture archive | `python tools/verify_j2_runtime_archive.py --write` | **PASS**, 19/19 JSON/raw pairs, actual raw SHA256 and length verified |
| J.0 plan | `python tools/mrtool.py addon verify .research-output/vehicles/sdk/j2/reference-plan` | **PASS**, 3 artifacts; pinned plan SHA unchanged; `runtime_installable=false` |
| J.1 parent bundle | `python tools/addon_runtime.py verify .research-output/vehicles/sdk/j1/reference-runtime-final` | **PASS_STATIC_RUNTIME_BUNDLE**, 246 operations, 243 resources, retail EXE exact |
| J.2 candidate | `python tools/j2_frontend_reentry.py verify .research-output/vehicles/sdk/j2-reentry/runtime-candidate/bundle` | **PASS_STATIC_J2_REENTRY_BUNDLE**, 248 operations; J.0 plan preserved; physical ID/commit state not changed by hook |
| Native Windows launcher preflight | `mr-runtime-launcher.exe --verify MRallye.exe <J.2 bundle>` | **PASS**, 243 resources and 248 operations; resource index SHA verified |
| Deterministic patch planning | J.2 focused deterministic-plan test | **PASS**, repeated manifest/operation generation matched; J.1 parent operation set and J.0 plan hash preserved |

Full console output is in
[`tests-full-output.txt`](tests-full-output.txt); focused results in
[`tests-focused-output.txt`](tests-focused-output.txt); compile output in
[`compileall-output.txt`](compileall-output.txt); capture and candidate
verification records are in the corresponding `*-output.txt` files in this
folder. J.2 repeated-generation hashes are summarized in
[`j2-determinism-output.txt`](j2-determinism-output.txt). The native launcher's complete metadata is in the ignored candidate
`launcher-build.json` and its verified hashes are summarized in
[`human-qualification-handoff.md`](human-qualification-handoff.md).

## Runtime status

The supplied 2026-10-09 evidence confirms the prior two-addon runtime results:
SplitScreen ID26+ID27, Rallye Cup roster reuse, and Master Rallye roster
restoration across a fresh process. Every capture reports the verified
J.1-hardened live Dump variant. The owner's stock-without-loader observation
is recorded as `HUMAN_CONFIRMED_UNINSTRUMENTED`, not as a new instrumented
capture.

The new constructor convergence hook is only statically verified. It has not
been run in-game. Therefore current status is **READY FOR HUMAN RUNTIME** for
the re-entry regression, not J.2 FULL PASS. Close J.2 only after the ID27,
ID26, stock ID7, SplitScreen independence, and locked-ID27 checks in the human
handoff pass. J.3 and ID28 are not started.

## Critical stack hotfix validation — 2026-10-09

The failed candidate is preserved unchanged at
`.research-output/vehicles/sdk/j2-reentry/runtime-candidate/` (launcher SHA256
`c10c27a72387004a3696a1eab3d25f24e777ea2c566bf0a5f642f68e1085765c`). The
new candidate is separate at
`.research-output/vehicles/sdk/j2-reentry/repaired-candidate/`; it remains
`READY_FOR_HUMAN_RUNTIME`, not runtime-qualified.

| Check | Result |
|---|---|
| Full synthetic suite | **409 passed, 0 failed, 0 skipped** |
| Focused J.2 suite | **12 passed, 0 failed, 0 skipped** |
| Negative old-offset regression | Exact old stub SHA `f0485557df0654c21a48b0acfed4639e0bb36591b8f80f16963c315981e857e1` rejected |
| `python -m compileall src tools tests` | **PASS** |
| `git diff --check` | **PASS**, only Git LF-to-CRLF working-copy notices |
| J.0 reference plan verify | **PASS**, plan SHA preserved |
| J.1 parent bundle verify | **PASS_STATIC_RUNTIME_BUNDLE**, 246 operations |
| Repaired J.2 bundle verify | **PASS_STATIC_J2_REENTRY_BUNDLE**, 248 operations, 243 indexed resources |
| Native launcher `--verify` | **PASS**, 243 resources / 248 operations |
| J.1 parent operation bytes | Exact 246-operation binary body remains the prefix |
| Retail EXE on disk | SHA256 remains the pristine retail hash |

The J.2 hotfix logs, machine-readable ABI audit and bundle provenance are in
[`critical-hotfix/`](critical-hotfix/). The repaired bundle contains two
optional runtime-state files inherited from the J.1 package root
(`DataGame/PlayerState.xml` and `DataGame/PlayerState.xml#`); the 243 indexed
resource files and hashes are unchanged. These files are in the isolated
repaired candidate root; the J.1 parent and retail installation were not
modified.

The repaired 86-byte stub SHA256 is
`f39f33838e0e7d3d276fbec03af0439c6c36a4807224ebe8cfc7ce14e70324ee`. The
patch manifest SHA256 is
`09d2852ff8c439bb102d5b6a351860101fc7094175ab79bd2faeefe79c9b891c`, operation
table SHA256 is
`aac0f887227c64ca4a591f542d9eda8a170b8b76f16687145c23e33664d57c17`,
reconstructed reference image SHA256 is
`a2170bdbdd1bc951862bc9fd6c93fc9a26d9eeba2b4b014810fc85474055dc2f`, and
launcher SHA256 is
`4a91217c7fcb1e78f2165d12634ee7fd1746ae28a5855c9698f10b8904a0afd4`.
The derived runtime-candidate identity SHA256 is
`22c8f428b8e1508091e3b447b1f4d9c5851aca64ca4475b0d70abf9d9c545eb7`; its
canonical component record is [`critical-hotfix/runtime-candidate-identity.json`](critical-hotfix/runtime-candidate-identity.json).

The owner subsequently tested the stack-fixed candidate: Vehicle Select opens
and ID26 restores, but ID27 still resolves to Navara. That intermediate
candidate is superseded. Run the current minimal fresh-process retest in
[`root-cause/human-retest.md`](root-cause/human-retest.md). J.2 remains open
until ID27 restores as T2/local7 and the stock ID7 and ID26 controls pass.
# Historical validation snapshot. For final J.2 status and the later owner
# runtime report, see [final closeout](closeout-2026-10-09.md). The test output
# below is retained as generated and is not retroactively changed.
