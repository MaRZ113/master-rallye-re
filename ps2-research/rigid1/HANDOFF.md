# PS2-RIGID1 independent-review handoff

This archive contains RIGID1 reports, diagnostic/packaging sources, focused and historical PS2 tests, all required small JSON oracles, short original instruction windows, synthetic traces and validation logs. Proprietary binaries, original XML/matrices/meshes/textures, raw Ghidra projects and memory dumps are excluded.

Start with ps2-research/rigid1/final-report.md. `elf-functions.json` gives75 grounded function entries, bounds or explicit UNKNOWN ends, direct original JAL edges, field roles and register-offset evidence. `instruction-probes.json` gives canonical hashes/words, including complete bounded straight-line derivative/gravity windows. `vtable-evidence.json` joins virtual callbacks to original function targets. Contract, layout, shape and authored JSON preserve the original-to-runtime chain without full proprietary coordinates.

Without private inputs, run from archive root:

```powershell
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/tests -q
python ps2-research/tools/rigid_runtime.py contract
python ps2-research/tools/rigid_runtime.py evaluate --input ps2-research/rigid1/synthetic-input.json
```

Unittest uses Python's standard library. The pytest command requires pytest and its public dependencies; this machine used the existing ignored pytest9.1.1 dependency directory. Those third-party packages are not bundled. Environment-dependent integration checks skip using existing explicit test conventions; unexpected failures are not hidden. No Blender is needed.

For original-data integration set MASTER_RALLYE_PS2_INPUT to the immutable directory containing SLES_509.06,SYSTEM.CNF,TNG.PAK,TNG.000. Set MASTER_RALLYE_PC_INPUT to the unpacked retail Data.sma root and MASTER_RALLYE_COURSE_SDK to the clean external Course SDK checkout at4244fa0c. Historical UI1 uses PS2_UI_CORPUS for original extracted HUD PSB/GXI. The local PYTHONPATH directory under data/cdelta1/python contains public pytest dependencies, not a game-data adapter. Original game inputs, SDK and third-party packages are external. Exact roots and commands actually executed are in command-log.md and source-provenance.json.

Review questions: constructor/factory/class-registration.md; Mass/MOI authored-properties.md +mass_inertia original words; trigger activation-and-triggers.md; shapes collision-shapes.md +physics-registration.md; movement physics-integration.md; actual displayed pose world-transform.md; contact proof boundaries vehicle-contact.md; baked PC candidates pc-haybale-correspondence.md; test/input distinctions validation.md. Follow UNKNOWN links rather than assuming a complete general solver.

MANIFEST.json hashes every included payload and records its actual source commit. The external ZIP receipt covers the archive and manifest, avoiding recursive self-hashes. Archive-only validation logs were executed in an isolated copy with original corpus environment variables removed. No canonical game data is silently bundled.
