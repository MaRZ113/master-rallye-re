# Command and evidence log

Commands below were run from `D:\Game\Master Rallye\master-rallye-re-general`
unless otherwise stated. Paths are retained for reproducibility; source files
and logs containing proprietary payloads are not packaged.

## Repository preflight

```powershell
git status --short --branch
git branch --show-current
git rev-parse HEAD
git diff --exit-code -- modernization/renderer
```

Result: `master`, HEAD `61cb84d5c7f28d3bd88a3f1f9a8ce16d4c178390`, two commits
ahead of `origin/master`; pre-existing modifications/untracked work only
under `ps2-research/pc-port/`; renderer diff empty. No user changes were
staged, reset, or overwritten.

Course SDK reference:

```powershell
git -C 'D:\Game\Master Rallye\master-rallye-re-course' status --short --branch
git -C 'D:\Game\Master Rallye\master-rallye-re-course' rev-parse HEAD
```

Result: clean branch `research/r5t-course-archaeology`, HEAD
`4244fa0c4d878523c9947f54816bf377cdfb2589`.

## Canonical identities

```powershell
Get-FileHash 'D:\Game\Master Rallye PS2\SLES_509.06' -Algorithm SHA256
Get-FileHash 'D:\Game\Master Rallye PS2\SYSTEM.CNF' -Algorithm SHA256
Get-FileHash 'D:\Game\Master Rallye PS2\TNG.PAK' -Algorithm SHA256
Get-FileHash 'D:\Game\Master Rallye PS2\TNG.000' -Algorithm SHA256
Get-FileHash 'D:\Game\Master Rallye Pristine\MRallye.exe' -Algorithm SHA256
```

All hashes match [target-compatibility.md](target-compatibility.md).
Selected PSM, DX, GXI and DXT hashes are recorded in
[evidence-inventory.json](evidence-inventory.json).

The original PS2 ELF header, unique `PT_LOAD` mapping, and frozen
TREEBLEND1 instruction/data words were checked with:

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:\Game\Master Rallye PS2'
python ps2-research/revalidation1/verify_ps2_evidence.py
```

Result: PASS, zero word/anchor mismatches. This verifies byte provenance and
VA mapping only; it is not an instruction decoder.

## REA

The REA handshake/target query selected the verified original PC PE above.
REA successfully returned Ghidra 12.1.4 procedures/decompilation for
`FUN_00580360`, `FUN_00565DA0`, `FUN_0053F8B0`, and `FUN_0053F930`. Its exact
PS2 `open_binary` request returned `capability_unavailable`; that failed
request is recorded, not hidden or retried with changed architecture flags.

GNU objdump was used only to decode original PC PE bytes around `0x005867a0`
after REA reported no Ghidra-defined procedure at that address. It was not
used as a substitute PS2 R5900 provider.

## Focused tests actually run

PowerShell environment for the PS2/PC source checks:

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:\Game\Master Rallye PS2'
$env:MASTER_RALLYE_PC_INPUT='D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked'
$env:MASTER_RALLYE_COURSE_SDK='D:\Game\Master Rallye\master-rallye-re-course'
python -m unittest discover -s ps2-research/tests -p test_foliage_runtime.py -v
```

Result: **30/30 PASS**. It rechecks source hashes, PSM/DX ownership and the
24-face geometry relation, texture alpha summaries, and deterministic report
generation.

```powershell
$env:MRR_PC_PORT_RENDERER_ROOT='D:\Game\Master Rallye\master-rallye-re-general\ps2-research\pc-port\.build-overlay\ps2-enabled\modernization\renderer'
python -m unittest discover -s ps2-research/pc-port/tests -v
```

Result: **8/8 PASS**, including integration/overlay contracts.

```powershell
ctest --test-dir ps2-research/pc-port/.build-overlay/ps2-enabled/build -C Release --output-on-failure -R ps2_port_extension_contracts
```

Result: **1/1 PASS**.

```powershell
python modernization/renderer/tools/verify_proxy.py ps2-research/pc-port/.build-overlay/baseline/build/Release/d3d8.dll
python modernization/renderer/tools/verify_proxy.py ps2-research/pc-port/.build-overlay/ps2-enabled/build/Release/d3d8.dll
```

Result: both proxy verifications **PASS**; the outputs are distinct DLLs.

```powershell
python -m pytest ps2-research/tests/test_foliage_runtime.py -q -p no:cacheprovider
```

Result: unavailable because the active Python 3.15 environment has no
`pytest` module. No package was installed. This is **SKIP/UNAVAILABLE**, not a
test failure or pass.

## Build evidence

No build was run for this documentation/evidence audit. The previously
generated `ps2-research/pc-port/overlay/build-report.json` reports successful
baseline and PS2-enabled Release builds (`--parallel 1`), each CTest and proxy
verification. This audit verifies the report and output hashes but does not
claim those builds were newly rerun.

## Final checks

```powershell
python -m compileall -q ps2-research/tools ps2-research/tests
python -m py_compile ps2-research/revalidation1/verify_ps2_evidence.py ps2-research/revalidation1/package_handoff.py
git diff --check
git diff --exit-code -- modernization/renderer
```

Results and any environment limits: [validation.md](validation.md). The
documentation/package file hashes are recorded inside the deterministic
handoff archive.
