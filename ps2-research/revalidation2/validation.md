# Validation

## Static byte and architecture checks

The canonical PS2 ELF is SHA-256 `b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`. The explicit Ghidra language is `r5900:LE:32:default`; Rabbitizer is 1.16.2 with `InstrCategory.R5900`.

Latest independent verifier result:

```text
frozen TREEBLEND1 words: 620 checked, 0 mismatches
fresh Ghidra instruction words: 6,633 checked, 0 source-byte mismatches
invalid Rabbitizer R5900 instructions: 0
mnemonic spelling/alias differences: 1,218
compact phase probes: 576 valid original instruction words
```

The name/alias differences are not byte differences. The verifier rejects unsupported ELF class/endianness and ambiguous or non-file-backed VA mapping. `instruction-probes.json` retains a compact reproducible sample, not the full ELF disassembly.

The saved Ghidra project was reprocessed through `analyzeHeadless.bat` with
full analysis and the included bounded script. Auto-analysis completed in
69 seconds and the script exported the same bounded listing. The EER DVP
overlay analyzer warned that several overlay blocks were not byte-mapped and
skipped them. The ELF `PT_LOAD` mapping and functions discussed in this audit
are file-backed; no conclusion relies on those skipped DVP sections.

## Runtime evidence audit

`audit_pilot_runtime.py` consumes the four supplied session JSONL files, four matching frame captures, and four screenshots. It outputs hashes and selected fields only. It does not include screenshot pixels, full frame traces, or raw session logs.

For the four target frames, the tool verifies one target draw per frame, successful draw result, state write sets around the call, and restoration of each modified state to the pre-draw frame snapshot. In particular Mode 2 has no ZWRITE write and Mode 3 has no alpha-state write. The four session logs have 27/27/15/22 malformed lines; the relevant selected-mode and target-identity rows parse. Screenshot pairing remains ordinal/timestamp correlation because mode is not embedded in JPEGs.

## Focused tests and checks

Run from the repository root:

```powershell
& 'ps2-research\data\revalidation1\tooling-venv\Scripts\python.exe' -m unittest discover -s ps2-research\revalidation2\tests -v
& 'ps2-research\data\revalidation1\tooling-venv\Scripts\python.exe' -m compileall -q ps2-research\revalidation2\tools ps2-research\revalidation2\tests
```

The revalidation-specific suite has 14 tests covering ELF mapping, invalid headers, R5900 `MULT`, byte mismatch rejection, screenshot JPEG dimensions, session mode extraction, capture suffix pairing, target/state restoration audit, the four-mode contract, the frozen runtime correlation, probe identity/uniqueness, and deterministic handoff packaging. Runtime integration depends on the user's original local F10 logs/screenshots; those are intentionally not embedded in the clean handoff.

Independent R5900 verifier command and runtime audit command are recorded in [command-log.md](command-log.md). `git diff --check` is required at closeout. No live PCSX2 capture was performed, and static checks do not establish PS2 visual parity.
