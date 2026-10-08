# Reproduction commands and scopes

Working directory: D:/Game/Master Rallye/master-rallye-re-general. Every writable
research artifact is under ps2-research. Source corpus and SDK are read-only.

```powershell
git -c safe.directory='D:/Game/Master Rallye/master-rallye-re-general' status --short --branch
git -c safe.directory='D:/Game/Master Rallye/master-rallye-re-general' branch --show-current
git -c safe.directory='D:/Game/Master Rallye/master-rallye-re-general' rev-parse HEAD
```

Fresh ELF queries use tools/elf_ui_query.py --track refl1 --elf canonical ELF
--install D:/Game/Master Rallye/_reverse-tools/ghidra-bridge-main/ghidra_12.1.4_PUBLIC.
The existing ignored project/profile/temp wrapper selects that installed
ghidra-ai-bridge environment. All temporary R5900 stack/scalar substitutions are
rolled back. Instruction probes always read original canonical bytes.

Representative fresh query windows/entries:

| Window | Entries | Relevant verification |
|---|---|---|
|3ade58..3adfe8|3ade58|Full carshiny handler, including original epilogue|
|3adfe8..3ae2e0|3adfe8,3ae250|caralpha/carflat controls|
|3ae040..3ae250|3ae040,3ae0c8,3ae150|Glass/glow handlers|
|330780..332628|330780|Guarded target writer and model draw wrapper|
|31a518..31af50|31a518|GS sprite packet and complete EE argument ABI|
|32f988..32fce0|32f988|Reset flag, split-screen gate|
|3387c8..338db0|3387c8,338ab8|Race/alternate camera inputs|
|343458..343c00|343458|Camera/view globals; full return window|
|3628c0..362dd8|3628c0|Object current/retained orientation rule|
|36fc18..370080|36fc18, --ee-scalar|Camera basis/epsilon/SQRT; original instructions checked|
|322220..3223f8|322220, --ee-scalar|Color equation; MULT rd surrogate and original store order|

The raw outputs remain ignored. Exact bounds, fresh/reused provenance, callsites,
fields, constants and short original-word probes are in elf-functions.json.
No full decompilation or Ghidra project is needed in the handoff.

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:/Game/Master Rallye PS2'
$env:MASTER_RALLYE_PC_INPUT='D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked'
$env:MASTER_RALLYE_COURSE_SDK='D:/Game/Master Rallye/master-rallye-re-course'
$env:PS2_UI_CORPUS='D:/Game/Master Rallye/master-rallye-re-general/ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD'
python -m unittest discover -s ps2-research/tests -v
$env:PYTHONPATH=(Resolve-Path 'ps2-research/data/cdelta1/python').Path
python -m pytest ps2-research/tests -q -p no:cacheprovider
python -m compileall -q ps2-research/tools ps2-research/tests
git -c safe.directory='D:/Game/Master Rallye/master-rallye-re-general' diff --check
```

Initial sandbox full unittest:196run,6environment errors (WinError5 temporary
directory/hard-link operations), explicitly retained in the ignored log. Permitted
host rerun:196 PASS,0skip. Pytest:196 PASS,259subtests PASS,0skip. No test was
weakened. Focused REFL1:20 PASS including three external original-corpus methods.

See offline-validation.md for diagnostic CLI commands. Before final commit,
all four canonical size/SHA checks were repeated; read-only renderer paths had
no diff; SDK retained HEAD4244fa0c4d878523c9947f54816bf377cdfb2589 and clean status.

```powershell
python ps2-research/tools/package_reflection_handoff.py --check-dir ps2-research/data/refl1/bundle-check
python ps2-research/tools/package_reflection_handoff.py --archive ps2-research/data/refl1/PS2-REFL1-handoff.zip
```

The archive is created after the phase commit and records that actual SHA.
Bundle-only runs unset the four external-input variables; runtime and original
integration evidence are not manufactured by shipping proprietary files.

The isolated check directory was tested with all four external-input variables
unset and without the original SDK/corpus PYTHONPATH: unittest184run,16skip,OK;
pytest171 PASS,25skip,160subtests PASS. Class versus per-test skip reporting explains
the different counts. Both subprocess exit codes were0. Local logs and
package-checks.json retain the actual result tails. The final archive contains
the committed documentation and metadata; tests used the same source/fixtures.
