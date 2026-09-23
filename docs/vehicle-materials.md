# Vehicle material semantics (R4D)

The canonical R4D inventory is research/r4d/material-corpus.json. It covers 1,478 physical draws in 78 vehicle DX resources. Every draw stores three ordered texture slots, with slot 2 always Null in this corpus. Slot 0 is populated in 1,473 draws; three draws have Null in slot 0 but a texture in slot 1; two have no texture. Slot 1 contains shared helper families in many draws.

## Evidence-based model

A material binding should retain ordered DX slots, raw core/prefix control words, sidecar candidates and nullable HasAlpha/UsesAlpha/IsNoise values, per-texture DXT alpha statistics, source vertex colors, and distinct confidence/evidence labels. A derived preview_base_texture may be chosen independently. UNKNOWN is a valid semantic category.

**CONFIRMED_BY_EXECUTABLE:** this is a Direct3D 8 program with registered base, environment, alpha and alpha-test shader variants. A runtime selector uses material-object fields and global Reflections/DetailPasses options. The mapping of parsed DX draw fields to that object has not yet been proven.

**CONFIRMED_BY_CORPUS:** 18 neutral signatures cover all draws. The main alpha-bearing glass/glow families share raw flag patterns, but multiple material names can occur under one signature. HasAlpha, UsesAlpha, and actual pixel alpha differ in some bindings.

## Material families

- Opaque body/paint: first-slot body art and slot-1 whitepaint/silverpaint recur. Tint, vertex-color use, and stage equation remain UNKNOWN.
- Decals: sticker/body tuples recur. A second-stage decal equation remains UNKNOWN.
- Glass: windscreen+glass tuples have alpha pixels and flag 01000101 in many draws. Exact alpha blend/test, render order, depth-write, and breakable glass linkage remain UNKNOWN.
- Chrome/envmap: chrome helper and executable env shader variants exist. Coordinates and combine equation remain UNKNOWN.
- Light/glow: brake families use distinctive 00000001/01000001 flags and unknown_0x24 values 5/1. Additive blending and scene-light emission remain UNKNOWN.

No production material writer exists. See research/r4d/runtime-renderer.md and runtime-test-matrix.md for exact evidence and next tests.
