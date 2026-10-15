# X-Trail COMPLETE private conversion

`convert_complete.py` consumes the existing strictly validated PS2VEH01 artifact.
It reuses the 29-model COMPLETE decoder and GXI decoder; it is not another PSM
parser. Original source SHA-256 is
`30f976c4e4e371851e8ebd45dabc1db4ea6c676f9bf99684f70a9a2932096e38`.

Converted private output `.assets/vehicles/XTRAIL-COMPLETE.ps2model`:
741114 bytes, SHA-256
`ba1cee9a21c2a2ae2935158136ae80b587eca7dc9a6701afc573e069818d772b`.
24 meshes, 6606 source vertices, 4636 nondegenerate source kicks, 28 textures
(27 authored GXI plus the verified original default texture).
No original image/model data is committed or included in handoff.

## Binary contract

All words little-endian. Header `<8s6I32s` (64 bytes): magic `PS2MDL02`, version2,
JSON length, mesh count, vertex count, index count, texture count, original PSM SHA.
Canonical UTF-8 JSON follows. Then 24 `<7I` records: node offset, PS2 material
mode (including original no-shader mode0), slot0/1/2 effective texture indices (`ffffffff` means absent), first
index and index count. Then 36-byte `<3f3fI2f` vertices: original XYZ, original
normal, source RRGGBBAA converted to D3DCOLOR AARRGGBB, original UVxy. Then uint32
indices. Each texture is width/height/byte count `<3I` and BGRA8888 bytes.

JSON retains original material strings, slot ordering, strip flags/scales,
source provenance and texture hashes. Texture rows remain in source order;
no vertical flip, resample, alpha amplification or arbitrary mip generation.
GXI RGBA bytes are swizzled to native ARGB8888 storage. PS2 `/128` versus PC
`/255` alpha/color conventions remain a material-rendering limitation.

Every mesh is a direct `root.n` child; no tag7/8 wrappers or local matrices occur
in this exact COMPLETE model. Positions/normals are not fitted, normalized or
transformed. A future consumer supplies the verified native world/view/projection
once. This does not authorize race CAR transforms or wheel animation.

ADC bit0 suppresses the newest-vertex kick. Diagnostic area cutoff1e-7 matches
the established source-face count. Ordered consecutive source triples are kept.
Strip flag, rendered parity/culling and runtime source selection are not proven;
the first diagnostic consumer must use CULL_NONE and state that limitation.

## Material and wheel boundaries

Body/lights/wheel/carflat/carglass remain separate records. Root19 is tread/rubber;
20 wheel643/rubber;21 mercwheelrim/chrome;22 jumpwheel64/rubber. Authored rubber
secondaries are explicitly preserved by the original REFL1 material contract;
carshiny does not authorize applying framebuffer reflection to all four equally.

Root17 is literal material `shit`, authored no slot0 and only slot1 silverpaint.
Bounded original R5900 byte analysis in `default-material.md` proves mode0 and
the original black `default.gxi` primary. Converter retains authored slots in
JSON, emits effective slot0=27/secondary absent for its two faces, and includes
that original 8x8 texture. It is not carflat, shiny, glass or hidden. The prior
source-only private artifact remains preserved separately; no arbitrary surface
or texture was substituted to fill this material gap.

## Reproduce

Run this directory's `convert_complete.py --ps2-root "D:/Game/Master Rallye PS2"`
on the canonical source set. This calls the existing preparation function while
preserving the full 29-model report. Then run
`python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port2/assets -v`.
Private output is ignored and manually installed only after runtime admission.
No live ownership, suppression, upload or visual acceptance is claimed here.
