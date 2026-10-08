# Master Rallye PS2 research

Active filesystem work lives in `packfs/`, static content/UI work in `ui/`,
HUD runtime reverse in `ui2/`, PC/PS2 course-content survey in `cdelta1/`, tools in
`tools/`, tests in `tests/`.
Canonical development branch: `master`. Historical `research/general-re` and
`research/r-*` are reference evidence; this track does not edit them.

Start with [PackFS findings](packfs/findings.md) and [validation](packfs/validation.md).
The first content pass is [PS2-UI1](ui/findings.md), with a
[byte-accurate PSB map](ui/psb-format.md) and [closeout report](ui/final-report.md).
The runtime continuation is [PS2-UI2](ui2/findings.md), including
[dynamic minimap data flow and offline reconstruction](ui2/minimap.md).
Original ISO files remain external. Extracted resources, full directory images,
Ghidra databases and raw decompilations stay under ignored `data/`.

PackFS and PSB readers use Python 3.10+ standard library only. Diagnostic
images and screenshot inspection additionally use Pillow. `elf_query.py` and
`elf_ui_query.py` additionally
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

```powershell
python ps2-research/tools/build_ui_report.py --inputs 'D:\Game\Master Rallye PS2' --screens 'D:\Game\Master Rallye PS2\PS2-userscreens'
python ps2-research/tools/psbtool.py verify ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD/HUD-TEMPLATE.PSB --texture-dir ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD
python ps2-research/tools/psbtool.py glyphs ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD/HUD-NUMS.PSB
python ps2-research/tools/ui_visuals.py ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD/NEWHUD.PSB --texture-dir ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD --output-dir ps2-research/data/ui1/visuals/NEWHUD
$env:PS2_UI_CORPUS='D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\ui1\extracted\TNG\DATAPSM\HUD'
python -m unittest discover -s ps2-research/tests -v
```

`psbtool.py` supports `info`, `dump`, `strings`, `sprites`, `glyphs`, `verify`.
Unknown signature/version and malformed bounds fail closed. `dump` preserves
unknown trailing bytes; `verify` refuses them. Diagnostic assembly stays in
ignored `data/` and does not implement or replay the PS2 HUD renderer.

`hudruntime.py` reads a named RaceTest XML through PackFS, a decoded XML or
an explicitly bounded marker array in a memory image. It emits route bounds,
world/map points, clipped centerlines and optional SVG under ignored data.
Player position/heading/marker state must be supplied explicitly; the output
does not claim a live captured frame or bit-exact PS2 rasterization.
See [UI2 validation](ui2/validation.md) and [remaining coordinate proof](ui2/next.md).

The [CDELTA1 survey](cdelta1/final-report.md) compares all 36 paired retail
courses, authored ambient/prop ownership and material interfaces. Its
[novel candidates](cdelta1/novel-candidates.md) and [single next phase](cdelta1/next.md)
retain static/runtime boundaries. The PC Course SDK is a read-only parser reference.

```powershell
python ps2-research/tools/course_delta.py --inputs 'D:\Game\Master Rallye PS2' --pc 'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked' --sdk 'D:\Game\Master Rallye\master-rallye-re-course' --screens 'D:\Game\Master Rallye PS2\PS2-userscreens' --screen-archive 'D:\Game\Master Rallye\!backup\PS2\PS2.zip'
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/tests/test_course_delta.py -q -p no:cacheprovider
```

Survey generation uses canonical PS2 hashes, `tngtool` and the SDK scene,
sidecar and course DX readers. SDK imports disable bytecode writes. Outputs
stay in `cdelta1/` or ignored `data/cdelta1/`; diagnostic caches are independently
checked by re-decoding the original archive on every use. PSM string occurrences
are never counted as visible objects.
Compiled PC water samples and paired route spatial checks are reproducible.
The selected `ambient-evidence.json` / `materials-evidence.json` are frozen
probe metadata; the tool regenerates their broader source inventories and
delta records. Screenshots are provenance/correlation only.

On this workstation pytest is local to ignored `data/cdelta1/python`; set
`$env:PYTHONPATH=(Resolve-Path 'ps2-research/data/cdelta1/python').Path`
before the pytest command. For a fresh checkout install pytest in your normal
test environment or that ignored directory. The survey itself uses the
standard library and the existing read-only SDK; no external decoder is needed.
