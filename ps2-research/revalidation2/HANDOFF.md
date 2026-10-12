# PS2-R5900-REVALIDATION2 handoff

This is a source-and-evidence handoff for the France1 PS2 `treeblend` audit and the four-mode PC PILOT1.3 runtime correlation.

## Included

* Phase documentation and machine-readable `elf-functions.json`, `render-contract.json`, `instruction-probes.json`, and compact `runtime-correlation.json`.
* The reproducible Ghidra headless script and Python verifier/audit tools.
* Fourteen focused tests, including two Rabbitizer-dependent decoder tests and a deterministic archive test.

## External inputs

Full PS2 byte verification requires the canonical `SLES_509.06` plus prior frozen TREEBLEND1 instruction evidence, the Ghidra 12.1.4/EER v2.1.38 installation and the existing Rabbitizer 1.16.2 venv. Runtime audit reproduction requires the four `session-*.jsonl`, `frame-1..4.jsonl`, two historical reference frames, and four ShareX JPEGs at the paths in [command-log.md](command-log.md). These private local captures and binaries are not included.

The archive omits TNG archives, extracted GXI/PSM resources, screenshots, complete frame/session logs, the Ghidra database/listing, and all PC/PS2 binaries. No Course SDK source is required to run the focused unit tests; its read-only DXT parser was used during analysis.

## Run

From the repository root, install nothing and run:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q tools tests
```

With the existing Rabbitizer environment and external corpus, use the exact verifier and audit commands in [command-log.md](command-log.md). The runtime correlation JSON contains hashes and selected metadata only.

## Result

`ZWRITEENABLE=FALSE` alone is sufficient for the observed PC bush disappearance in the supplied frame. The specific occluding draw and the reason PS2's `ZMSK=1` rendering remains visible are not proved. No live PS2 runtime/parity claim is included.
