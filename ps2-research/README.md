# Master Rallye PS2 research

Active filesystem work lives in `packfs/`, tools in `tools/`, tests in `tests/`.
Canonical development branch: `master`. Historical `research/general-re` and
`research/r-*` are reference evidence; this track does not edit them.

Start with [PackFS findings](packfs/findings.md) and [validation](packfs/validation.md).
Original ISO files remain external. Extracted resources, full directory images,
Ghidra databases and raw decompilations stay under ignored `data/`.

The tools use Python 3.10+ standard library only. `elf_query.py` additionally
requires the already installed ghidra-ai-bridge/PyGhidra environment, Ghidra
12.1.4, and a compatible JDK. No external LZO library is required for `tngtool.py`.

```powershell
python ps2-research/tools/tngtool.py info 'D:\Game\Master Rallye PS2\TNG.PAK'
python ps2-research/tools/tngtool.py decompress-pak 'D:\Game\Master Rallye PS2\TNG.PAK' --output ps2-research/data/TNG-directory.bin
python ps2-research/tools/tngtool.py list 'D:\Game\Master Rallye PS2\TNG.PAK'
python ps2-research/tools/tngtool.py find 'D:\Game\Master Rallye PS2\TNG.PAK' --query HUD
python ps2-research/tools/tngtool.py verify 'D:\Game\Master Rallye PS2\TNG.PAK' 'D:\Game\Master Rallye PS2\TNG.000' --manifest ps2-research/packfs/tng-manifest.json
python ps2-research/tools/tngtool.py extract 'D:\Game\Master Rallye PS2\TNG.PAK' 'D:\Game\Master Rallye PS2\TNG.000' '\TNG\DATAPSM\HUD\HUD-TEMPLATE.PSB' --output ps2-research/data/manual-extraction
python ps2-research/tools/build_report.py --inputs 'D:\Game\Master Rallye PS2'
$env:MASTER_RALLYE_PS2_INPUT='D:\Game\Master Rallye PS2'
python -m unittest discover -s ps2-research/tests -v
```

`list`/`find` derive paths structurally from PAK. Their `gz` unpacked sizes remain
unknown until a TNG.000 header inventory is performed; the generated complete
manifest includes that inventory. Resource extraction validates the canonical
data hash, seeks to one exact range, and writes one decoded resource plus JSON
provenance. The 64 MiB default memory limit deliberately rejects very large
resources such as `0.DAT` and `1.DAT`; those are not validation targets.

Unknown hashes are rejected for directory/resource operations. Compression-only
`info`/`decompress-pak` also accept structurally valid synthetic frames without
asserting that they represent a supported game build.
