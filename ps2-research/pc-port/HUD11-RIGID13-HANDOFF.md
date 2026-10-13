# HUD-PORT1.1 / RIGID-PORT1.3 independent bounded decisions

Repository: `master-rallye-re-general`, branch `master`.
Starting/ending HEAD: `0bddf7c7bc5e95831f98714ff6231da05ab073ea`.
Frozen renderer tree: `e33386bcf682db6983380c499e4928726c758fe0`.
Existing unrelated tracked/untracked port work was preserved.

## Separate results

HUD: **BLOCKED_ON_CURRENT_PLATE_TO_NATIVE_RESOURCE_LIFETIME_JOIN**.
The original consumer's source subimage layout, key selection, triangle data
and texture-wrapper path are documented in `docs/hud-port1.1/`. A bounded
read-only collector and explicit user debugger recipe replace reliance on old
F10 pointers. The next observation must connect the current SpeedDial key0
plate and native resource generation in the same session. No replacement is
implemented or enabled; needle, speed, gear and HUD cache remain untouched.

Physics: **NO-GO / PRIVATE_NATIVE_ADMISSION_BLOCKED**.
`docs/rigid-port1.3/` independently establishes that the original cache loader
requires PC DX revision135 and that the hay initializer overwrites the selected
model before body registration. A native private prototype owner, compatible
container, consuming initializer, rollback, admission boundary and teardown
are still required. No private object, test-copy course or fake collision was
created. No repeated broad vehicle sampler or 99-file XML census was used.

## Current verification, not runtime acceptance

Executed from the repository root:

```powershell
python ps2-research/pc-port/docs/hud-port1/live-semantic-tests.py
python ps2-research/pc-port/docs/hud-port1.1/plate-contract-tests.py
$env:MRR_ORIGINAL_EXE='D:\Game\Master Rallye\MRallye.exe'
python ps2-research/pc-port/docs/rigid-port1.3/test_admission_evidence.py
git diff --check
ctest --test-dir ps2-research/pc-port/.build/ps2-enabled -C Release --output-on-failure -R '^(hud_visibility_contracts|ps2_.*)$'
```

These checks passed: existing HUD13, new plate16 and physics6 tests. Additional
collector tests and byte probes are recorded in the HUD phase validation.
Physics original-EXE probes were verified against SHA-256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Without that external EXE, its one integration test explicitly skips.
No synthetic check establishes resource lifetime, safe spawning or visual parity.
The existing native HUD-cache and PS2 state/feature contract subset also passed
**7/7 CTest**, using the already-built canonical binaries. This is regression
verification, not a new build or a runtime plate/physics test.

`build_overlay.verify_baseline()` passed again, including frozen Git-object
source identity, working-tree integrity and exact patch hashes. No native
implementation or integration patch changed, so no new build was performed.
The existing canonical DLLs were rehashed and remain:

| Variant | SHA-256 |
|---|---|
| Baseline | `011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138` |
| PS2-enabled | `6edc2426e2602545121f16959cdbb2055fb205a907b36173cb85a447b7051deb` |

Only `.build/baseline`, `.build/ps2-enabled` and existing `.staging` are used;
no new CMake tree was created. No deployment, push or commit was performed.

## One next user runtime test

Follow `docs/hud-port1.1/runtime-recipe.md`: one original SpeedDial consumer
pause, bounded read-only plate observation, then resume and one same-session
F10 capture. Use current debugger registers and current PID, never the old
session's addresses. This is a mapping control, not stock-vs-PS2 visual A/B:
an A/B pilot must wait until its resource/lifetime gates pass.

## Compact archive

`overlay/package_hud11_rigid13_handoff.py` packages both reports, compact
instruction evidence, diagnostic sources, synthetic tests and their explicit
dependency closure. It verifies CRC, all member SHA-256 values and deterministic
regeneration. It excludes DLLs, original assets and full process dumps.
An isolated extraction under ignored `data/hud-port1.1/handoff-review` also
passed all three included suites without the private corpus: **34 PASS,
1 explicit SKIP** for original-EXE byte integration. No missing import or
fixture was found.
