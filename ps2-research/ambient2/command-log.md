# Executed commands and reproduction boundaries

All commands used `D:/Game/Master Rallye/master-rallye-re-general`, branchmaster, no login shell. Git commands include per-checkout `-c safe.directory=D:/Game/Master Rallye/master-rallye-re-general`; no global Git configuration was changed.

Executed preflight: `git status --short --branch`, `git branch --show-current`, `git rev-parse HEAD`; separate SDK status/HEAD; fresh SHA/size of allfour canonical PS2 files. Starting master was clean, ahead14, HEAD9ace2be4384f2a052482016e5a4873758934b7b5. SDK was clean at4244fa0c4d878523c9947f54816bf377cdfb2589 onresearch/r5t-course-archaeology. One unqualified Git status was rejected as unsafe-directory; it was rerun with the explicit per-command setting.

Executed read-only Ghidra bridge queries used newest installedGhidra12.1.4, existing ignored`PS2PackFS_MIPS3`, `elf_ui_query.py --track ambient2`, bounded windows, requested original call/vtable addresses, and audited scalar surrogates. Raw exports/query-wrapper/environment scratch remain ignored. Relevant windows include manager/controller1ae870..1b19c0, clone1cec68..1cecc0, RNG1d5de0..1d5f90, marker registry1fdba8..1fde68, entity21e290..21eb70, sprite3376c0..3387c8, camera3387c8..338ab8 and cache3201b0..320700. An execution-policy block on launching a nested PowerShell script was avoided by the normal direct invocation; no execution-policy bypass was used.

Executed numerical/source checks generated compact contracts and source inventories through reused parsers, independent RNG modular calculations and original byte windows. Actual CLI inventory/resources/contract/trace repeats and manifest/hash checks are recorded in`diagnostic-checks.json`. Full original geometry/texture/XML/ELF exports remain outside Git.

Executed full regression environment:

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:/Game/Master Rallye PS2'
$env:MASTER_RALLYE_PC_INPUT='D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked'
$env:MASTER_RALLYE_COURSE_SDK='D:/Game/Master Rallye/master-rallye-re-course'
$env:PS2_UI_CORPUS='D:/Game/Master Rallye/master-rallye-re-general/ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD'
$env:PYTHONPATH='D:/Game/Master Rallye/master-rallye-re-general/ps2-research/data/cdelta1/python'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/tests -q -p no:cacheprovider
```

Initial restricted runs had six existing temporary-file/link PermissionErrors:307 unittest methods; pytest301 successes/6 failures. No failures were converted to skips. Reviewed reruns permitted those synthetic filesystem operations:308 unittest/pytest methods passed; pytest290 subtests passed. The extra method independently verifies original MPG commands versus instruction payload+4. After the final diagnostic-output/provenance adjustment a focused final Bird suite is rerun. Logs retain both outcomes.

Executed closeout: compileall, diff-check, source hashes, SDK status/HEAD, changed-path review, scoped local commit; handoff isolated tests and archive CRC/per-file SHA validation. The actual final commit is in the archive's source_commit/receipt, avoiding a self-referential hash inside its own committed report. No push.

All PCSX2 instructions in`runtime-capture-plan.md` are **examples only / NOT_PERFORMED**. No PC implementation, source modification or subsequent research phase was executed.
