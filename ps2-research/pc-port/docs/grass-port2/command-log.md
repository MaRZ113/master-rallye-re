# Commands and external inputs

Preflight master HEAD0bddf7c7bc5e95831f98714ff6231da05ab073ea;
Git status/branch/HEAD read, pre-existing port changes retained. Frozen
renderer and CourseSDK Git state separately verified clean, SDK HEAD
4244fa0c4d878523c9947f54816bf377cdfb2589. No checkout or branch creation.

Canonical PS2 root D:/Game/Master Rallye PS2; protected PC retail root
D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked; readonly SDK
D:/Game/Master Rallye/master-rallye-re-course. Corpus/script/source hashes in
source-contract.json/source-validation.md. Named PackFS extraction reused
tngtool; no duplicate decompressor/PSM decoder. Original inputs never modified.

Actually executed prepare_shrub_pilot.py with those external roots,
.assets/grass/Turkey3Shrubs.ps2grass and docs/grass-port2/source-contract.json.
Repeated generations identical; original grass preparation script/artifact
unchanged. Example regeneration (external paths required):

```powershell
python ps2-research/pc-port/tools/prepare_shrub_pilot.py --ps2-input-root 'D:/Game/Master Rallye PS2' --pc-input-root 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' --sdk-root 'D:/Game/Master Rallye/master-rallye-re-course' --asset-out ps2-research/pc-port/.assets/grass/Turkey3Shrubs.ps2grass --report-out ps2-research/pc-port/docs/grass-port2/source-contract.json
```

Fresh ELF mapping and46instruction words independently checked with installed
Rabbitizer R5900. Existing Ghidra EER-derived GRASS1 contracts reused; no generic
MIPS substitution or broad VU residency pass. Original PC prop routines checked
through REA/Ghidra and independent objdump; see rigid-port1 native evidence.

Actually executed public build_overlay.py with all four optional original
artifact test paths configured (MRR_GRASS_TEST_ASSET/MRR_SHRUB_TEST_ASSET/
MRR_COURSE_OBJECT_TEST_ASSET/MRR_REFLECTION_TEST_GXI). Same persistent roots;
both generators twice, independent serial Win32 Release builds, CTest,
verify_proxy.py,88-case Python suite and compileall. Native tests also supply
synthetic wrong-category and two-pool/reset cases. Git diff-check PASS.

The four approved legacy roots were fully archived/readback-verified and
removed with checked literal absolute PowerShell paths. Cleanup record and
archive SHA are in build-policy/cleanup-first-pass.json. No other deletion.
No DLL automatically installed and no push. User's new grass/contact/PS2 A/B
recipe is pending, not an executed test.
