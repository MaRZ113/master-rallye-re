# PC-VISUAL-PILOT1 source/test handoff

**BLOCKED_ON_DRAW_IDENTITY.** A read-only diagnostic checkpoint;Mode1 remains Stock. The 2026-10-09 code-only continuation adds bounded CPU Lock/Unlock upload provenance for WRITEONLY buffers. It does not add a foliage override or texture. Actual commit is in MANIFEST.json;SHA256SUMS covers payload+manifest. ZIP has no DLL,originalEXE,DX,PSM,GXI,DXT,RAM/VRAM dump or game screenshot.

Included: current renderer source, vendor headers, tools, tests and compact research fixtures; F10 probe, CPU-write mirror and identity auditor; selected renderer-recon JSON dependencies; shared PS2 parser tools; frozen WATER1 course-source identities; and the unchanged small Python package from the general checkout's src/master_rallye. The separate Course SDK checkout is not embedded or modified. Historical metadata is reference material, not new runtime proof. Complete original meshes and textures remain external.

Without game data:Python3.11+ can run the identity algorithm/config-independent synthetic tests,inspect source-signatures.json and audit a supplied JSONL. Example:

```powershell
python -m unittest discover -s modernization/renderer/tests -p test_foliage_identity.py -v
```

The production-native capture test explicitly skips until a local native build exists. The CPU upload mirror is tested synthetically; a new game capture is still required to show it observes the real France1 uploads. To run all renderer native and Python coverage:on Windows use MSVCx86/VisualStudio18 2026,CMake3.21+,and:

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -v
```

Build outputs and synthetic native captures remain local. The focused production-native capture test skips without a build, but several older full-suite tests require native executables and fail if they are absent. Build first for the full suite; do not interpret the unbuilt suite as a regression or a PASS. No PC retail data is needed for mocks. The archive creates the empty renderer/.analysis scratch directory used by these tests. A Ghidra Java runtime is not required by the offline auditor or native build.

Source regeneration requires the user's canonical PC Retail Data.sma_unpacked tree, read-only Course SDK checkout and included shared PS2 tools. Optional --ps2-root needs canonical SLES_509.06, SYSTEM.CNF, TNG.PAK and TNG.000. Corpora are not embedded. The included general-checkout Python library serves existing tests; source regeneration still takes the explicit read-only SDK path. Real F10 requires a manually launched supported PC build and manual proxy selection; no deployment was performed. Blender and PCSX2 are unnecessary for this diagnostic; the PCSX2 reference remains a later visual acceptance task.

See command-log.md for commands executed in the main workspace;runtime-test-plan.md commands with frame placeholders are instructions only. Isolated handoff test results are recorded in validation.md after verification. No arbitrary geometry/RNG/texture substitute is included.
