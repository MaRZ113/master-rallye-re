# PORT2 handoff

Read final-report.md and runtime-ab.md under ps2-research/pc-port/docs/vehicle-model-port2.

Frontend X-Trail: implemented, pending user runtime. Race CAR: deferred separate contract. Original renderer immutable; source and tests are included, original model/texture bytes excluded. DLLs are in artifacts/baseline and artifacts/ps2-enabled. SHA256SUMS.txt covers archive members; release-provenance.json identifies the commit and build inputs.

Rebuild from the original repository with its locked Git objects:
`python ps2-research/pc-port/overlay/build_overlay.py`
This reuses .build/baseline, .build/ps2-enabled and .staging, serial builds, strict patches and renderer verification. Private resource regeneration:
`python ps2-research/pc-port/docs/vehicle-model-port2/assets/convert_complete.py --ps2-root "D:/Game/Master Rallye PS2"`

See build-report.json for exact source/patch hashes, generator, CTest and export verification. Extracted handoff tests are recorded separately in handoff-validation.json. Rebuilding the proxy requires the original immutable Git objects, SDK/toolchain and local original assets for asset-dependent checks. Never install automatically.
