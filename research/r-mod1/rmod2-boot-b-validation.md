# R-MOD2 BOOT-B validation

Candidate builder: `tools/build_rmod2_boot_b.py`.

The builder records complete command output in `validation-results.txt` inside
the source-only review archive. It runs the focused BOOT-A/BOOT-B tests, the
full synthetic suite, `compileall`, `git diff --check`, F3 product
reconstruction, x86 compilation, export audit, and Windows harnesses for
DirectInput forwarding, concurrent fail-closed initialization, and mapped
image-difference classification.

Reference profile identities: retail `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, F3 runtime `cf743e356e3198cadd68ce750ff9f8c2cce5cb7caa965a4ee64d40c75f442da3`, F3 plan template `3c760a475b854fd1435584f04450eada4dd90647ed7bbb7144fbf101e375d89d`. The reference plan has 17 records including OEP; sample ConfigVersion 2 selects 13 Randomizer operations and the in-process installer excludes OEP.

The forwarding harness checks names/ordinals and system-forwarded return values.
The BOOT-B concurrency harness launches eight simultaneous first calls from a
wrong-host test process, expects exactly one `BOOT_B_FAILED`, confirms that no
native install was claimed, and verifies DirectInput forwarding for all eight
calls. This is Windows process-level testing but not a Master Rallye game test.

The image-difference harness verifies that file-alignment padding outside
`VirtualSize` is ignored, non-hook differences are reported without being
misclassified as selected-hook conflicts, selected-hook differences are
classified as conflicts, and virtual zero-fill is checked. The production
installer still performs complete exact preimage checks for every operation
selected by the initial INI and repeats them after thread quiescence.

The corrected BOOT-B pass additionally runs
`tests/rmod1/rmod2_host_qualified_preflight_harness.cpp` after checking the
actual pinned retail file. It tests the production template-preparation,
allocation-address translation, selected-range/overlap, and preimage helpers;
it parses an empty/default configuration, the packaged ConfigVersion 2 INI,
and an accepted 4096-byte INI. It also confirms a mutated preimage is rejected.

Automated evidence is limited to exact-build planning, x86 compilation,
export-contract inspection, synthetic checks, wrong-host fail-closed behavior
and pure mapped-image difference tests. Human game startup, keyboard/gamepad
input, tests in separate copies with and without the existing renderer proxy,
randomized race behavior, live INI reload, Results, shutdown and repeated launch
remain `PENDING`. Preserve both renderer-configuration logs; neither one is
assumed to explain the original mismatch. The ZIP is a test candidate, not a
supported drop-in release.

The Practice/Checkpoint Start correction adds callback-path core tests for
opaque non-mode-2 pass-through, zeroed Quick Race selection diagnostics, the
unchanged three-AI path, four-to-seven AI, invalid counts, and MaxOpponents=3.
The exported callback delegates to the tested evaluator. Independent
native-plan byte tests still assert the exact one-call setup path, original
call-site preimage, register/flag stack preservation, denial epilogue and
`0x0047AD11` continuation. Actual Practice and Checkpoint startup remain a
human runtime gate.
