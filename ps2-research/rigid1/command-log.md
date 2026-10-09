# Commands and reproducibility

Commands below were executed during RIGID1 unless explicitly marked example. Workdir for repository commands: `D:/Game/Master Rallye/master-rallye-re-general`. PowerShell child-process environment changes affect only their respective runs.

## Preflight and references

```powershell
git status --short --branch
git branch --show-current
git rev-parse HEAD
git log --oneline -8
git -C 'D:/Game/Master Rallye/master-rallye-re-course' status --short --branch
git -C 'D:/Game/Master Rallye/master-rallye-re-course' rev-parse HEAD
```

Requested branch master, starting d34a95de2033d6b6cfc94d3b2f55bd0100198d9b. SDK clean at4244fa0c4d878523c9947f54816bf377cdfb2589. Where required, Git calls use `-c safe.directory=<exact worktree>`. Pre-existing paths preserved: root README.md; tests/synthetic/test_observatory_release.py; tools/runtime/broker_observatory.py; tools/runtime/observatory_version.py; docs/releases/observatory-0.2.3-beta.md; tests/synthetic/test_observatory_remote_anchors.py. No branch/worktree creation, reset/stash or push.

## Original source and executable analysis

The inventory/shapes/pc function modes were executed against the canonical roots; their complete compact regeneration is also repeated in the focused integration tests. PackFS and allfour original SHA/size are checked by the existing `spline_runtime.Corpus`. Exact selected PC hashes are compared with the fresh early phase counterpart baseline.

Existing Ghidra12.1.4 install at `_reverse-tools/ghidra-bridge-main/ghidra_12.1.4_PUBLIC` was used through `elf_ui_query.py --track rigid1`, the ghidra_ai_bridge/PyGhidra adapter and the existing PS2PackFS_MIPS3 project. Local ignored query wrapper assigns writable scratch profile/temp paths. Transactions roll back. EE instruction surrogates affect only analysis state; canonical originals provide every committed instruction word/hash.

Representative reproduction examples using the queried windows:

```text
--window 0x0019fcb0 0x001a1000 --addresses 0x0019fcd0 0x0019fe98 0x0019ff18 0x001a0258
--window 0x001733d0 0x00174a80 --addresses 0x00173b68 0x00173cc8 0x00173d98 0x00173df0
--window 0x00267f60 0x00268128 --addresses 0x00267f60
--window 0x00205580 0x00205c00 --addresses 0x00205628 --ee-sqrt-only
```

Per-function `analyzed_span` and address in elf-functions.json provide further valid reproduction parameters. Short original probes are directly reproducible without Ghidra using VA-file delta0xff000. Speculative/interior query entries were not promoted to function starts. The backend install is recorded as two interior VAs with function start UNKNOWN.

## Regression actually executed

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:/Game/Master Rallye PS2'
$env:MASTER_RALLYE_PC_INPUT='D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked'
$env:MASTER_RALLYE_COURSE_SDK='D:/Game/Master Rallye/master-rallye-re-course'
$env:PS2_UI_CORPUS='D:/Game/Master Rallye/master-rallye-re-general/ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD'
$env:PYTHONPATH='D:/Game/Master Rallye/master-rallye-re-general/ps2-research/data/cdelta1/python'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s ps2-research/tests -p test_rigid_runtime.py -v
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/tests -q
python -m compileall ps2-research/tools ps2-research/tests
git diff --check
```

Focused37 PASS; full345 unittest PASS; full345 pytest+290 subtests PASS. Initial restricted unittest had6 Windows PermissionErrors in unchanged temporary/link tests; reviewed filesystem access permitted the rerun. Logs retain that failure. PYTHONPATH here supplies public pytest9.1.1 dependencies, not the private game corpus.

## Independent handoff actually executed

```powershell
python ps2-research/tools/package_rigid_handoff.py --check-dir ps2-research/data/rigid1/handoff-check
```

From that independent-copy root, remove only MASTER_RALLYE_PS2_INPUT,MASTER_RALLYE_PC_INPUT,MASTER_RALLYE_COURSE_SDK,PS2_UI_CORPUS process variables and run the same unittest/pytest commands. Unittest uses empty PYTHONPATH; pytest uses the public runner dependency path above. The archive-copy scripts/fixtures do not depend on the parent original corpus. Outputs:301 unittest successes with explicit external skips;301 pytest successes/174 subtests and44 external skips. Absolute log destinations avoid working-directory ambiguity. First pytest invocation without its dependency path was BLOCKED with `No module named pytest`, retained separately.

## Read-only diagnostic examples

These CLI spellings are reproducible examples; the equivalent mode functions and synthetic evaluator were executed and tested:

```powershell
python ps2-research/tools/rigid_runtime.py inventory --ps2 'D:/Game/Master Rallye PS2'
python ps2-research/tools/rigid_runtime.py shapes --ps2 'D:/Game/Master Rallye PS2' --sdk 'D:/Game/Master Rallye/master-rallye-re-course'
python ps2-research/tools/rigid_runtime.py pc --ps2 'D:/Game/Master Rallye PS2' --sdk 'D:/Game/Master Rallye/master-rallye-re-course' --pc 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked'
python ps2-research/tools/rigid_runtime.py contract
python ps2-research/tools/rigid_runtime.py evaluate --input ps2-research/rigid1/synthetic-input.json
```

The synthetic CLI was run twice and compared byte-for-byte. New outputs containing original-data diagnostics must remain ignored under data/rigid1; existing files are refused.

## Scoped closeout

Only new rigid1 reports/JSON/logs, rigid_runtime.py, package_rigid_handoff.py, test_rigid_runtime.py, one elf_ui_query.py track entry and the PS2 index update enter the commit. Final `git status`, scoped diff checks and `git show --name-only` establish that scope. The final archive command uses `--archive ps2-research/data/rigid1/PS2-RIGID1-handoff.zip`; the receipt gives actual source commit/size/SHA/CRC. No original assets or full decompilations enter that archive.
