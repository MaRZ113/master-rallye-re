# Reflection coverage correction handoff

Read `final-report.md`, `vehicle-coverage.md`, `runtime-ab.md` and
`whole-model-feasibility.md` under `ps2-research/pc-port/docs/reflection-coverage-fix`.
Status: PARTIAL_COVERAGE_FIX_PENDING_RUNTIME. Full-body parity is not claimed.

The archive contains committed PS2-port sources, tests, exact overlay patches,
compact material/source/runtime evidence, the build report and two verified
independent proxy DLLs under `artifacts/baseline` and `artifacts/ps2-enabled`.
It excludes unrelated uncommitted work, original game assets, full meshes,
screenshots, raw logs, private `.assets`, staging and CMake build trees.
No renderer source copy, proxy chaining or automatic installation is involved.
`SHA256SUMS.txt` covers every member except itself. ZIP CRC, manifest and repeated
serialization are checked. Release commit/provenance is in `release-provenance.json`.

Build prerequisites: original repository and frozen renderer Git objects,
Windows MSVC/CMake Win32 toolchain. From that repository, run
`python ps2-research/pc-port/overlay/build_overlay.py`. It reuses `.build/baseline`
and `.build/ps2-enabled` and matching `.staging` roots. Source drift fails closed.
Then run `python ps2-research/pc-port/overlay/package_reflection_coverage_fix.py`.
Unrelated research commits are permitted by the exact renderer tree lock.

Corpus-independent review/tests from an extracted handoff:

```powershell
python -m unittest discover -s ps2-research/pc-port/docs/reflection-coverage-fix/source-audit -p test_audit.py -v
python -m unittest discover -s ps2-research/pc-port/docs/reflection-coverage-fix/wooldand -p test_join.py -v
python -m unittest discover -s ps2-research/pc-port/docs/reflection-coverage-fix -p test_modified_materials.py -v
python -m unittest discover -s ps2-research/pc-port/tests -p test_reflection_coverage_fix.py -v
```

Native tests and full port integration tests require verified staging headers
and Windows toolchain; they are not claimed runnable from this archive alone.
The original GXI-enabled tests require the local verified environment texture.
Grass/shrub original-source integration requires the72 local assets. None are
packaged. Synthetic native transaction tests require no original game images.
No Blender requirement.

Source audit regeneration additionally needs canonical SLES_509.06/SYSTEM.CNF/
TNG.PAK/TNG.000, protected PC retail vehicle DX and separate read-only Course
SDK. Their exact hashes/source locations are retained in compact evidence.
Original PS2 textures and runtime content must be supplied locally; never fetch
or distribute them through the handoff. The effect fails closed without the
verified environment image. Existing local asset paths/configuration remain
user-controlled.

Manual A/B first on UFO/IceCream/Tata/Forester, Mode0 versus Mode4+Coverage1,
same camera/car/paint/lighting. No new configuration key is required. Preserve
the working grass, shrubs, puddles and accepted HUD/menu fixes. Physics and HUD
implementation remain paused. Return F10 and screenshots for remaining gaps.
