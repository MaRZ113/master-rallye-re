# PS2-VEHICLE-MODEL-PORT1 handoff

Status: **PARTIAL**. Race shiny-subset pilot implemented, not yet game-tested.
COMPLETE conversion29/29, replacement blocked on the one current native owner join.
Brake lights are research only. No models, textures, physics, course files or
original EXEs were changed/deployed. Frozen renderer source/tree is unchanged.

Use `runtime-ab.md` for one Xtrail A/B, then the six-family/Reset control. New
options default Stock. There is no enabled frontend replacement in this DLL.
`FrontendGeometryDiagnostics` is read-only and independently opt-in, bounded128
attempts/17 records. Do not infer frontend suppression permission from F10 ordinals.

The archive includes exact successful-build extension sources/tests, the two staged
patches, renderer Git-object lock, pure source readers/preparation scripts, compact
PS2/PC/R5900/x86 metadata, synthetic tests, original command list, build report and
both proxy DLLs. Original PSM/DX/GXI, prepared `.ps2vehicle`, grass/water resources,
raw F10 logs, ELF/Ghidra projects and screenshots are excluded. Required historical
small JSON fixtures are included. SHA256SUMS covers every archive member.

Corpus-independent checks (actually executed after extraction):

```
python -m unittest discover -s ps2-research/pc-port/tests -p test_vehicle_model_port.py -v
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights -p "test_*.py" -v
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port1/frontend-identity -p "test_*.py" -v
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port1/race-partitions -p "test_*.py" -v
```

Rebuilding the DLLs requires the original repository Git objects for pinned commit
`0bddf7c7bc5e95831f98714ff6231da05ab073ea`, exact renderer tree
`e33386bcf682db6983380c499e4928726c758fe0`, Win32 MSVC/Windows SDK/CMake.
There is no full renderer copy in this archive. Run:

```
python ps2-research/pc-port/overlay/build_overlay.py
```

This serially reuses `.build/baseline`, `.build/ps2-enabled`, `.staging` with exact
patch/generator verification. Optional private asset integration tests require the
asset environment variables listed in `command-log.md`; they do not affect build
source authority. Without those resources their availability must be reported.

Reproducing the source corpus joins requires canonical PS2 PackFS at
`D:/Game/Master Rallye PS2`, protected PC78DX vehicle corpus at
`D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles`, and the
read-only Course SDK source at `D:/Game/Master Rallye/master-rallye-re-course/src`.
Native byte probes require the canonical PC EXE or PS2 ELF plus installed EER12.1.4
and RabbitizerR5900 as specified in the source evidence. No Blender is required.

Private model preparation (actually executed locally for all29):

```
python ps2-research/pc-port/tools/prepare_vehicle_models.py --ps2-root "D:/Game/Master Rallye PS2"
```

Output is confined to ignored `.assets/vehicles/`; do not distribute those files.
They retain original strips/control/attributes; they are not a render-ready
frontend replacement. `private-model-preparation.json` contains only counts/hashes.

Manual installation only: back up the accepted proxy; use
`artifacts/ps2-enabled/d3d8.dll` with your existing local PS2 resources/config. The
baseline artifact is a stock rollback/reference. Preserve the existing working
grass/water/reflection settings. No code automatically installs anything.
