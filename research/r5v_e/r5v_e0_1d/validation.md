# R5V-E0.1d validation

## Ghidra setup

- Used the existing `ghidra-bridge-main` and installed Ghidra 12.0.4.
- The saved Bridge YAML pointed at an unavailable `C:\Useful\ghidra_12.0.4_PUBLIC` installation and a moved project path. A task-local YAML under ignored `research-output/r5v_e0_1d/ghidra/` pointed at the actual installation and existing retail project copy. Isolated AppData/LocalAppData paths also stayed under ignored output.
- The installed Bridge YAML was not edited. A post-query comparison of the two existing project copies found their common files hash-identical; each has two differently named internal `.gbf` fragments. No pre-query project hash inventory exists, so that difference cannot be attributed to this phase. Both copies and all raw function exports remain under ignored `research-output/` and are excluded from Git.

## XML archive checks

- Locked the original source archive SHA-256 before and after generation: `9bdf132cfde6e443e32f937b99289b07e9527457ae48fa9c7e0a373b52a28f30`.
- Confirmed the archive's `DataScene/Hud/Hud0.xml` payload matches the unpacked source hash before editing.
- Changed exactly one `ObjectColour` value inside `ProgressCar0`; reverse substitution reproduced the source XML byte-for-byte.
- Reopened the candidate archive and passed `ZipFile.testzip()`. Member count and order match; no duplicate names exist; all 8,142 other logical member payloads hash-identically.
- Candidate archive SHA-256: `10f69fde8c9110abb69bb0c004904697af4e2ca024d4e38a24f97bbd04861072`.

## Executable bypass checks

- The source E0 baseline hash matched `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df` before and after generation.
- Source call bytes at VA `0x004A7661` matched `E8 0A FE 02 00`; the 15-byte helper area at VA `0x0068E300` was zero-filled and file-backed.
- Verified the helper call displacement to `0x004D7470`, the slot-0 compare against `[ESI+0x18]`, and `.text` growth from `0x28D300` to `0x28D310`. `.rdata` starts at `0x0068F000`.
- The fail-closed generator passed its real-source `--dry-run`; the candidate has the predicted SHA-256 `2d78b8b990ca1e7fa10171352cc95af3ff8e9d2bcdfac54310b4c28c642aaf7f`, retains file length, and differs only in the approved call, helper, and section-size field ranges.
- Five synthetic tests passed: deterministic bytes and range confinement, bad source hash rejection, hook/cave mismatch rejection, PE layout rejection, and an output-path guard that confines generated files to the ignored phase directory.
- Retail source `MRallye.exe` and `Data.sma` hashes remained unchanged.

## Runtime and full tests

- XML-only game test: **NOT RUN**.
- Slot-0 bypass game test: **NOT RUN**.
- Dynamic producer trace: **NOT RUN**.
- Full `tests/synthetic` suite: **PASS**, 205 tests in 12.153 seconds.
- `git diff --check`: **PASS** after the final documentation update.

## Runtime package safety

`research-output/r5v_e0_1d/` is ignored. Use its two executables and candidate archive only in a separate game test copy. Do not stage these files into Git or replace the original retail installation files.
