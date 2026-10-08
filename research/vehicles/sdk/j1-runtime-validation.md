# R5V-J.1 static validation record — 2026-10-08

## Status boundary

**READY FOR HUMAN RUNTIME.** The exact retail image, runtime operation bundle,
243-file resource root, and native x64 launcher are statically verified. The
launcher was not used to start the game in this task. Bootstrap behavior,
process-memory installation in a real game process, resource-root resolution,
and addon gameplay therefore remain unconfirmed.

Starting repository state was branch `research/vehicles`, HEAD
`792ab88` (`research: archive J0 implementation review package`), with a clean
tracked tree. No other worktree was used.

## Build identities

* Retail input at `D:\Game\Master Rallye\MRallye.exe`: SHA256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
  3,121,214 bytes. The corpus retail input matched this identity.
* I.1 reference candidate verified from its deterministic builder:
  `90abfbf9825f1cc7acebb3a1a2811a179e6474f2406433854e1ffdbc60bdd955`,
  3,121,214 bytes. It remains ignored research output and is not used as the
  launched executable.
* Two-addon J.0 plan: SHA256
  `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`;
  `runtime_installable=false` remains unchanged.
* Native patch manifest: SHA256
  `78c1070f2e656677f02d22f5d4fdff457e43c7ba74c67bb4e5a5c1488ca53179`.
* RVP1 operation table: SHA256
  `f4938b1a997364e371af6b1aee4798ca1865d67b22752bead9849c5d216a34ce`.
  It has 246 records: 244 changing process-memory ranges, one identical-byte
  `.rdata` canary, and one `.text` PE-header-only record excluded from process
  writes. The reconstructed reference file hash is
  `dd03adbd9f45c679e59d09e0a9f09337bd99c787d81f4ce018edb654c1cec881`; no
  reconstructed or patched EXE is emitted.
* Verified resource inventory: 243 files; index SHA256
  `2fc7121c3d4f66c407cedbcb47dc223c580301971e3d12d16aa197c7a70a3384`.
  Resource-manifest SHA256
  `b7e0fd4f785ed3f7a94dc6a0632cd8c16d7311478470087ad42bd73c0b871948`.
* ID27's generated registry initializer uses the manifest's independent
  `[1,0,1,1]` race-marker RGBA. This is separate from its magenta body texture;
  no live Broker confirmation is claimed.
* Native launcher: MSVC x64, 141,312 bytes, SHA256
  `9d4a98d01166362933974f8c376f3a42323feecfdfd021af7df0a3b1aceb31b5`.
  Two clean builds with `/Brepro` produced byte-identical executables.
  Build metadata intentionally remains
  `STATIC_BUILD_ONLY_NOT_RUNTIME_QUALIFIED`.

## Exact checks and results

Commands were run from the repository root:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -v
python -m unittest tests.synthetic.test_addon_sdk_runtime -v
python -m compileall src tools tests
python tools/build_vehicle_multislot_i1.py verify
python tools/addon_runtime.py verify .research-output/vehicles/sdk/j1/reference-runtime-final
.research-output/vehicles/sdk/j1/launcher-release-final/mr-runtime-launcher.exe --verify 'D:\Game\Master Rallye\MRallye.exe' .research-output/vehicles/sdk/j1/reference-runtime-final
```

Results:

* Complete synthetic suite: **393 passed, 0 failed, 0 skipped**.
  Full output: [`j1/unittest-output.txt`](j1/unittest-output.txt).
* Focused J.1 runtime-planning/launcher tests: **11 passed, 0 failed,
  0 skipped**. Output: [`j1/focused-output.txt`](j1/focused-output.txt).
* `compileall`: **PASS**.
* I.1 candidate verifier: **VERIFIED**, exact retail source and expected ID27
  family/pool mapping.
* J.1 Python bundle verifier: **PASS_STATIC_RUNTIME_BUNDLE**; 246 native plan
  records, 243 resources, no executable emitted, runtime not qualified.
* Native launcher `--verify`: **PASS**; it reported
  `RESOURCE_ROOT_VERIFIED files=243` and
  `RUNTIME_BUNDLE_VERIFIED patch_operations=246`.
* Wrong-image negative check with `C:\Windows\System32\notepad.exe`:
  **FAIL_CLOSED** with `retail executable SHA256 mismatch` before child-process
  creation.
* Missing-resource negative check: **FAIL_CLOSED** with
  `indexed resource is missing or linked: Data.sma` before any target process
  is created.
* Offline two-addon `mrtool addon build` followed by `addon verify`: **PASS**;
  plan SHA remained `357d3cf1...170989`,
  `runtime_installable=false`.
* Native launcher reproducibility: **PASS**, two independent `/Brepro` builds
  had the exact SHA above.
* `git diff --check`: **PASS**.

Captured verifier outputs and the two non-binary build metadata records are in
[`j1/`](j1/): the manifest validation, I.1 candidate check, Python runtime
bundle check, native bundle check, both fail-closed cases, and launcher build
metadata A/B. No generated executable is included in this evidence directory.
The compact source/evidence review package is
[`archive/r5v-j1-implementation-review-2026-10-08.zip`](archive/r5v-j1-implementation-review-2026-10-08.zip);
its internal `archive-index.json` covers every payload entry except itself.

The Windows test runner's default temporary directory denied strict path
resolution in legacy tests. The full and focused commands were rerun with
`TEMP` and `TMP` pointed to the ignored checkout-local J.1 temporary directory;
the source tests were not weakened or edited for that environment issue.

## Human runtime gates

The reproducible candidate and exact steps are in
[`j1-runtime-handoff.md`](j1-runtime-handoff.md). Still required:

1. Ordinary retail startup and on-disk EXE hash before/after.
2. External `--bootstrap-only` startup and normal frontend confirmation.
3. No-op in-memory canary startup.
4. Observatory confirmation that the child image is the retail path and the
   effective resource root is the external root.
5. Integrated Mercedes selection/race, Broker identity, and human model,
   wheels, controls, and movement observations.
6. On-disk retail EXE hash after the integrated game exits.

No game launch, Broker capture, rendered model inspection, or human gameplay
observation was performed for J.1. Do not describe J.1 as bootstrap-pass or
unchanged-EXE gameplay-pass until those gates are returned.
