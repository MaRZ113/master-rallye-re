# Visual coverage follow-up handoff

Read final-report.md and runtime-ab.md in
ps2-research/pc-port/docs/coverage-followup. Status is partial vehicle coverage,
Reset correction implemented pending game testing, vegetation deployment
mismatch proved, Frontend source feasibility only. No new lamp or model port.

Both DLLs are under artifacts/baseline and artifacts/ps2-enabled. Source commit,
frozen renderer tree, exact patch hashes and build hashes are in
release-provenance.json and build-report.json. SHA256SUMS covers all archive
members except itself. CRC/manifest/repeated serialization and isolated tests
are verified. Earlier handoff archives remain intact.

The archive contains committed PS2-port source/test/overlay/doc files and compact
research dependencies. Original renderer sources/full copies, game binaries,
GXI/DXT textures, full models, screenshots, RAM dumps, raw sessions, private
grass/shrub assets and CMake/staging directories are excluded. No deployment.
Unrelated dirty/untracked work is excluded. Actual build source bytes are
included, with committed-content verification and explicit LF/CRLF provenance.

Full build requires the original repository/pinned renderer Git objects,
Windows MSVC/CMake Win32 toolchain. Run:

```powershell
python ps2-research/pc-port/overlay/build_overlay.py
python ps2-research/pc-port/overlay/package_coverage_followup.py
```

These reuse only the canonical .build and .staging configurations. The one-shot
docs/coverage-followup/update_reset_patch.py was an exact authoring step and
**must not** be rerun against this newer patch; normal builds apply the current
locked patch directly.

Corpus-independent tests can run from an extracted handoff:

```powershell
python -m unittest discover -s ps2-research/pc-port/tests -p test_coverage_followup.py -v
python -m unittest discover -s ps2-research/pc-port/docs/coverage-followup/vegetation -p test_deployment_inventory.py -v
python -m unittest discover -s ps2-research/pc-port/docs/coverage-followup/frontend -p test_audit.py -v
python -m unittest discover -s ps2-research/pc-port/docs/coverage-followup/body-lights -p test_audit.py -v
```

Full port integration/native tests require verified staging and the Windows
toolchain. GXI-enabled upload tests and36-course asset tests additionally need
verified local original-source files. Regenerating original source audits needs
the canonical PS2 PackFS corpus, protected PC retail corpus and separate
read-only Course SDK. R5900 byte regeneration requires Rabbitizer and the
original ELF, plus the ignored bounded EER export. None are packaged. No Blender.

The user should manually copy all72 .assets/grass/*.ps2grass into the game's
configured PS2Grass directory after closing the game. All expected hashes and
the66 missing names are included as metadata. The new DLL is tested as code;
post-fix Reset and all-course visual/FPS acceptance remain pending user runtime.
No source evidence or screenshot observation is promoted to PS2 pixel parity.
