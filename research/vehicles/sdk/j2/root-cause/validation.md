# R5V-J.2 ID27 reverse-map correction — validation

**Result:** static correction verified; **READY_FOR_HUMAN_RUNTIME**. The
corrected root-cause candidate has not been run in-game. J.2 remains open.

## Source and executable identity

| Item | Result |
|---|---|
| Worktree | `master-rallye-re-vehicles` |
| Branch / starting HEAD | `research/vehicles` / `86f5ac8b1e6038615540665a73305547fbaf2f15` |
| Retail EXE | `D:\Game\Master Rallye\MRallye.exe`, 3,121,214 bytes |
| Retail SHA256 before/after candidate checks | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| Original EXE written or replaced | No |
| J.1 parent operation table | 246 ops, SHA256 `f4938b1a997364e371af6b1aee4798ca1865d67b22752bead9849c5d216a34ce`; unchanged |

## Automated checks

| Check | Command / evidence | Result |
|---|---|---|
| Full synthetic suite | `PYTHONPATH=src python -m unittest discover -s tests/synthetic -v` | **413 passed, 0 failed, 0 skipped**, 30.006 s |
| Focused J.2 re-entry | `PYTHONPATH=src python -m unittest tests.synthetic.test_j2_frontend_reentry -v` | **16 passed, 0 failed, 0 skipped**, 8.452 s |
| Bytecode compilation | `python -m compileall src tools tests` | PASS |
| Whitespace | `git diff --check` | PASS; Git emitted only its LF-to-CRLF working-copy notices |
| J.0 semantic plan | `python tools/mrtool.py addon verify .research-output/vehicles/sdk/j2/reference-plan` | PASS; pinned plan SHA unchanged and `runtime_installable=false` |
| J.1 parent bundle | `python tools/addon_runtime.py verify .research-output/vehicles/sdk/j1/reference-runtime-final` | `PASS_STATIC_RUNTIME_BUNDLE`; 246 ops, 243 resources |
| J.2 root-cause bundle | `python tools/j2_frontend_reentry.py verify .research-output/vehicles/sdk/j2-reentry/root-cause-candidate/bundle` | `PASS_STATIC_J2_REENTRY_BUNDLE`; 248 ops, 243 resources |
| Native launcher preflight | root-cause candidate `mr-runtime-launcher.exe --verify <retail-exe> <bundle>` | `RUNTIME_BUNDLE_VERIFIED`; 248 ops and 243 resources |
| Native mapper state audit | Actual reconstructed candidate bytes; reverse and forward mapping | PASS: physical ID27 -> T2/local7 -> physical ID27 |
| Old mapper negative test | Restore the inherited `[ESI+0x14]` ID27 displacement and verify | Rejected by exact-byte/native-state tests |
| ID26 and stock control | Compare effective candidate ranges for ID26 and stock reverse paths | Unchanged |

The first restricted full-suite attempt encountered Windows `WinError 5` in
unrelated tests that spawn CLI processes and write temporary files. The same
unchanged full suite was rerun with project-local ignored temporary storage in
the approved test context and passed 413/413. No test was weakened or edited
for this environment issue.

Exact console output and verifier reports are retained alongside this file:

* `tests-full-output.txt`
* `tests-focused-output.txt`
* `compileall-output.txt`
* `diff-check-output.txt`
* `j0-plan-verification-output.txt`
* `j1-parent-verification-output.json`
* `candidate-verification-output.json`
* `launcher-preflight-output.txt`

## Candidate identity

The separate ignored candidate is
`.research-output/vehicles/sdk/j2-reentry/root-cause-candidate/`.

| Artifact | SHA256 |
|---|---|
| Launcher | `1fb190ae85d2b7b119576a650e4723abb1130ef4bbdee6d353357087e3de66c7` |
| J.0 addon plan | `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989` |
| Native patch manifest | `162de9762c070fd970731da030f03150b303ecf2f8886bd4f25ca357b9129f11` |
| Native operation table | `44c139de5b211947857bcb4e70ac84a6b9f1adc23cc9b0fe2a520978a5282f5a` |
| Reconstructed reference image | `2f3b1d95d05c997bb13d6a8e235327098e344b75b46d0432c4a3a7ecf289ab64` |
| 86-byte J.2 publisher stub | `f39f33838e0e7d3d276fbec03af0439c6c36a4807224ebe8cfc7ce14e70324ee` |

The J.2 bundle retains all 243 J.1 resources. Its 248-operation table consists
of the 246-operation J.1 parent shape, with the ID27 displacement corrected
inside its inherited code-cave operation, plus the two existing constructor
publication operations. The generated profile still says
`runtime_qualified=false`; these static checks do not establish live selection
restoration.

## Human runtime gate

The owner has confirmed only the preceding stack-only candidate is crash-free;
that candidate still resets ID27 to Navara. The root-cause candidate must be
tested using [`human-retest.md`](human-retest.md). Keep the same player context
for selection/return/reopen. Required controls are ID27 T2/local7, ID26
T1/local7, and stock ID7 T2/local0. No Cup, Master Rallye, AI, or SplitScreen
rerun is needed for this fix. Do not call J.2 closed before the human confirms
the corrected candidate.
