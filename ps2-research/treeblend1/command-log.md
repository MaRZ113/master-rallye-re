# Executed commands and reproducibility

Date:2026-10-08. Working directory: `D:/Game/Master Rallye/master-rallye-re-general`, master. The reference SDK was inspected read-only. No new branch/worktree or game deployment was used.

## Preflight/source identity

Executed `git status --short --branch`, `git branch --show-current`, `git rev-parse HEAD` in the restored active checkout, separately in the Course SDK. Starting active HEAD:b87d7cf43ed6ab6dd3ef8ace9c268593c4cc2332; active/reference statuses CLEAN. Four canonical PS2 inputs were freshly SHA-256 checked, and every `cases` run verifies them again. Three selected PC DX/TXT pairs are freshly checked against frozen WATER1 identities.

## Executable analysis

Used latest installed Ghidra12.1.4 with the installed ghidra-bridge exporter and existing ignored read-only canonical project. Existing `data/refl1/query.ps1` orchestration was used with **`--track treeblend1`**, windows/addresses for the callbacks, registrations, mode blocks, cache, queue, texture lookup and common vertex helpers. For example, the final upload-initialization probe was:

```powershell
& ps2-research/data/refl1/query.ps1 --track treeblend1 --window 0x00311370 0x00311680 --addresses 0x00311370 --refs 0x00317208
```

This workstation helper/project is an external analysis dependency, not a promised bundle-only command. The portable evidence is the compact original-word JSON. CLI probes with hex strings lacking `0x` were rejected and rerun correctly; no rejected probe is evidence. Temporary LQ/SQ surrogates were rolled back in the analysis transaction. R5900-specific MADD/MULT were checked from original words rather than generic decompilation.

## Diagnostics

Executed production `foliage_runtime.py cases` for all five cases with canonical PS2 root, paired PC root and read-only SDK. Final outputs: ignored `cases-v4.json` and `cases-repeat.json`. Both SHA-256:

```text
f9c100752acf2f9542ba34f3e88464859a0a0e885add37d21af11093bc871c80
```

The same command with a new ignored output path is documented in `offline-validation.md`. `states` works without corpus data. The committed matrix additionally records editorial proof/portability annotations. Private source/format probes were reduced to compact metadata; full payloads remain ignored.

## Regression environment and commands

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:/Game/Master Rallye PS2'
$env:MASTER_RALLYE_PC_INPUT='D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked'
$env:MASTER_RALLYE_COURSE_SDK='D:/Game/Master Rallye/master-rallye-re-course'
$env:PS2_UI_CORPUS=(Resolve-Path ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD).Path
$env:PYTHONPATH=(Resolve-Path ps2-research/data/cdelta1/python).Path
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/tests -q -p no:cacheprovider
python -m compileall ps2-research/tools ps2-research/tests
git -c safe.directory='D:/Game/Master Rallye/master-rallye-re-general' diff --check
```

The initial sandbox baseline had six PermissionErrors in existing temporary-file/hardlink/rename tests. It was **not PASS**. The full suite was rerun with reviewed permission for those synthetic temporary files;270 unittest methods passed in60.380s,0 errors/failures/skips. Final pytest:270 passed,286 subtests passed in61.04s,0 failures/skips. Source game files were only read. This was an environment restriction, not a weakened test or hidden skip.

After the small cross-platform source-path separator fix, the focused `test_foliage_runtime.py` suite was rerun:30/30 PASS in17.359s. A subsequent bounded anchor addition checked the three original name strings, four vtable slots and three mode-table entries directly against the ELF; its CanonicalElf method passed separately. Compileall/diff-check were repeated. No diagnostic algorithm or original-data result was changed.

## Handoff and closeout

Executed check-dir packaging, then corpus-independent unittest/pytest in that copied tree with external roots unset. Actual results and integrity checks are in `validation.md`; full test-name logs are included under `validation-logs/`. Executed compileall, repeated source integrity and SDK status checks, Git changed-path review and diff-check before committing.

Final archive command: `python ps2-research/tools/package_foliage_handoff.py --archive ps2-research/data/treeblend1/PS2-TREEBLEND1-handoff.zip`, after the local phase commit. ZIP CRC/per-file SHA and the external receipt establish integrity. No push. These closeout commands are actual executed steps, with exact commit/archive identity in the final output/manifest.
