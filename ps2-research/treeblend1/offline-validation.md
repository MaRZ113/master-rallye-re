# Offline evaluator and independent evidence

`ps2-research/tools/foliage_runtime.py` is a bounded diagnostic, not a renderer. It reuses `tngtool`, WATER1 visual strips, `psbtool` GXI, DRESSING1 extraction, GEOM1 matching and read-only SDK DX/DXT readers.

## Supported modes

```powershell
python ps2-research/tools/foliage_runtime.py states

python ps2-research/tools/foliage_runtime.py cases `
  --input-root 'D:/Game/Master Rallye PS2' `
  --pc-root 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' `
  --sdk 'D:/Game/Master Rallye/master-rallye-re-course' `
  --output ps2-research/data/treeblend1/my-cases.json
```

Output destinations must be new paths under ignored `data/treeblend1`; existing files are preserved. States can print to stdout without any game corpus. Cases require canonical identity and reject an unexpected node/material, unsupported GXI/PSM, non-finite vertex or incomplete source path. PC comparison requires both PC root and SDK, with frozen selected DX/TXT SHA checks.

No coordinates are generated. Source attributes are read locally, then reduced to counts/bounds/hashes/strip provenance and compact histograms. No runtime texture handle, inherited GS bit or live hierarchy set is invented. Explicit inherited state supplied through the Python evaluator is labeled **EXPLICIT_SYNTHETIC_INHERITED_WORDS**; absent state remains INHERITED.

## Precision and scope

* Token/mode selection, GS mask operations: **EXACT_ELF_OPERATION**, using recovered integer behavior.
* Byte-derived color load/clamp/half-scale/FTOI0 diagnostic: **FLOAT32_RECONSTRUCTION**. All256 normalized source bytes are checked; arbitrary FCSR conversion and VU edge behavior are not emulated.
* GEOM1 exact unsigned triangle equality under a declared profile: geometric diagnostic with original source identities; live culling/winding remains separate.
* Surface-overlap/modified-region results: **STATIC_INFERENCE**, with explicit profile/residuals.
* Billboard/wind/LOD absence: bounded negative evidence in handler/cache/selector0, not a synthetic camera/time experiment.

## Independent checks

1. Canonical ELF SHA plus620 original CPU words, selected original VU pairs and ten original string/vtable/jump-table anchors are independently read and compared to the compact probes. Surrogate disassembly is annotated, never substituted for original words.
2. Original PSM material offsets/strips and GXI payload hashes are freshly extracted via PackFS, with earlier DRESSING/GEOM case offsets/counts as separate anchors.
3. Original PC compiled DX complete-disjoint coverage and frozen WATER1 SHA identities are enforced. GEOM1 supplies exact/coverage matching; no second foliage matcher is invented.
4. PC selected alpha flags/mask are read directly from original DX core+20/+24 as a second path beside the SDK parser.
5. Independent GXI RGBA bytes and SDK DXT row/channel conversion establish pinus2/pinetree image equality. Equal texture names were not used as the pixel oracle.
6. Explicit negative object material shows that the shared geometry/cache path alone does not enable alpha blending or alpha testing.

The committed case matrix adds review annotations to the diagnostic's compact core: packet producer, queue bucket, LOD unknowns and portability categories. Regenerating `cases` reproduces core original-data facts; it need not reproduce editorial fields. The function inventory/probe metadata derives from bounded Ghidra queries and prior verified function evidence, not from a decompiled universal renderer.

## Runtime capture plan — NOT_PERFORMED

No trusted selected-mesh PCSX2 capture was available in this phase. No emulator automation stack or ELF patch was built.

For a later read-only capture, use Turkey3 A and then ItalyS1 B:

1. Record canonical ELF/disc identity, PCSX2 version/configuration and exact course/frame/camera.
2. Break/read at391690/3ae618 or3ae710; identify the mesh pointer, original source node/material, +28/+2c/+3c/+44 and +dc/+e0.
3. Read the original texture descriptor/cache option and selected upload/CLUT/TEXA representation. This resolves file-alpha-to-sampled-alpha rather than assuming equality.
4. Capture at3bca80/31d250 and queue drain31cd98. Record the selected cache, bucket/key, complete state after312610/311c50, especially TEST/ZTE,ALPHA,ZBUF,TEX0/TEX1/CLAMP,FRAME/PABE/TEXA.
5. Capture the actual VIF chain after31d7c8/31e010 and micro-RAM/MSCAL entry. Correlate STQ/RGBAQ/XYZF2 and source indices with the mesh and visible frame.
6. Repeat with changed camera and fixed source mesh; inspect cached/world/output positions and selected hierarchy. Repeat at a second time to separate parent selection/projection from true deformation.
7. Record two frames' texture/image/state and VU residency. Compare against the static contract; do not call a changing silhouette proof of billboarding or wind.

The capture would validate runtime state and visual coverage. It is not required to invent new architecture before this bounded static pass can close.
