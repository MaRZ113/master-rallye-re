# Reproducible command log

Commands below were run from `D:\Game\Master Rallye\master-rallye-re-general`. Paths to game inputs and capture logs are local external dependencies.

## Direct Ghidra EER analysis and bounded export

The Ghidra project lives under ignored `ps2-research/data/revalidation2/ghidra_ee/`. The following invocation reprocesses the existing project with full analysis and runs the included bounded script. It completed successfully; full analysis took 69 seconds, then wrote the selected assembly/decompilation/xref output. The EER overlay analyzer emitted warnings for unmapped DVP sections and skipped those sections; it did not alter the canonical ELF.

```powershell
& 'D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat' `
  'D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\revalidation2\ghidra_ee' `
  EERevalidation2 -process 'SLES_509.06' `
  -scriptPath 'D:\Game\Master Rallye\master-rallye-re-general\ps2-research\revalidation2\tools' `
  -postScript 'EERevalidation2.java' `
  'D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\revalidation2\ghidra_r5900_revalidation2.txt' `
  -max-cpu 2
```

## Independent R5900 byte verification

```powershell
& 'ps2-research\data\revalidation1\tooling-venv\Scripts\python.exe' `
  'ps2-research\revalidation2\tools\verify_r5900_revalidation2.py' `
  --elf 'D:\Game\Master Rallye PS2\SLES_509.06' `
  --ghidra-output 'ps2-research\data\revalidation2\ghidra_r5900_revalidation2.txt' `
  --frozen-evidence 'ps2-research\treeblend1\instruction-evidence.json' `
  --instruction-probes 'ps2-research\revalidation2\instruction-probes.json' `
  --output 'ps2-research\data\revalidation2\r5900-byte-check-final.json'
```

## Runtime log, F10 and screenshot audit

```powershell
& 'ps2-research\data\revalidation1\tooling-venv\Scripts\python.exe' `
  'ps2-research\revalidation2\tools\audit_pilot_runtime.py' `
  --logs-dir 'D:\Game\Master Rallye Pristine\MRRRenderer\logs' `
  --screenshots-dir 'C:\Users\MaRZ\Documents\ShareX\Screenshots\2026-10' `
  --sessions session-1.jsonl session-2.jsonl session-3.jsonl session-4.jsonl `
  --screenshots 0.jpg 1.jpg 2.jpg 3.jpg `
  --reference-frame 'D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-1.jsonl' `
  --reference-frame 'D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-2.jsonl' `
  --reference-frame 'D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-3.jsonl' `
  --reference-frame 'D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-4.jsonl' `
  --reference-frame 'D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-14704-d1-00007608.jsonl' `
  --reference-frame 'D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-29960-d1-00004311.jsonl' `
  --output 'ps2-research\data\revalidation2\runtime-correlation.json'
```

## Focused tests and syntax check

```powershell
& 'ps2-research\data\revalidation1\tooling-venv\Scripts\python.exe' -m unittest discover -s ps2-research\revalidation2\tests -v
& 'ps2-research\data\revalidation1\tooling-venv\Scripts\python.exe' -m compileall -q ps2-research\revalidation2\tools ps2-research\revalidation2\tests
& 'ps2-research\data\revalidation1\tooling-venv\Scripts\python.exe' ps2-research\revalidation2\tools\package_handoff.py
git diff --check
```

The runtime audit command above is intended to reproduce the compact JSON report. The clean handoff does not include the external sessions, screenshots, F10 files, canonical PS2 corpus, Ghidra project, or full Ghidra listing.
