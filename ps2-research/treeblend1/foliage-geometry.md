# Visual geometry and vertex attributes

The five cases use the already validated WATER1 visual PSM reader, with DRESSING1 ancestry and GEOM1 matching. They are **PS2_VISUAL_SOURCE_MESH**, not tag103 spatial/collision triangles. No new PackFS, GXI or universal PSM parser is introduced.

Supported selected paths use tags1/6/5/2. Tag2 owns the exact material/texture names, source strips and flags. Original source positions are in course/game coordinates; no local matrix is serialized in the selected leaf paths. The identity-frame comparison is anchored independently by GEOM1 route and ordinary-ground correspondence. Live parent state still requires a runtime capture.

## Vertex chain

| Layout | Offset | Meaning / consumer |
|---|---|---|
| PSM source,52bytes | +0,+4,+8 | Normal XYZ |
| | +12 | Control; newest strip vertex bit0 suppresses triangle emission |
| | +16 | Packed `0xRRGGBBAA` |
| | +20..+32 | Four UV floats |
| | +36..+48 | Position XYZW |
| Loaded vertex,48bytes | +0..+12 | Normal/control |
| | +16..+28 | UV4 |
| | +32..+40 | XYZ |
| | +44..+47 | RGBA bytes |
| Cached vertex,64bytes | qword0 | NormalXYZ; first vertex carries strip length, later vertices original control bit0 |
| | qword1 | RGBA float, each byte×0.5 |
| | qword2 | UV4 |
| | qword3 | XYZ,W=1 |

`3900f0` loads source vertices. `3a7f10` shifts the source color by24/16/8/0 and divides each channel by255. `3a4fd8` calls setters `3401f0/340230/340270/3402b0`, multiplying by255, converting to integer and clamping **every channel to2..254**. This includes black RGB and fully opaque alpha.

`31f4e0` makes the 64-byte cache. The original `MTLO` at31f868 initializes the source base; original SPECIAL2 word `70623000` at31f86c is `MADD a2,v1,v0`, adding index×48. A generic Ghidra SPECIAL2 pseudo-expression is not an independent pointer-address oracle.

Example, original color `0x211a00ff`:

```text
source RGBA    (33,26,0,255)
runtime bytes  (33,26,2,254)
cache floats   (16.5,13,1,127)
VU FTOI0       (16,13,1,127)
```

The offline evaluator preserves float32 multiplication order for this byte-derived domain. It is **FLOAT32_RECONSTRUCTION**, not a general FCSR or bit-exact R5900/VU emulator. All256 original channel values independently round-trip through /255 then×255 in the focused test; arbitrary material float conversion edge cases are outside that claim.

## Geometry and attribute consumption

The source positions and original strip order are copied to the cache. Selector0 transforms qword3 through the common object/view/projection input and Q=1/W; UVxy becomes perspective STQ. RGBA becomes RGBAQ through FTOI0, and projected position becomes XYZF2 through FTOI4. Control/ADC participates in strip emission and common clipping.

NormalXYZ is copied, but the selector0 coordinate/color path does not read it. No tree-specific diffuse/specular normal calculation, billboard pivot, normal-to-camera basis or wind weight was recovered. UVzw remains in the shared cache layout; the second geometry stream is NOP in these modes. This is not permission to interpret unused UV values as foliage animation metadata.

Common clipping may create clipped vertices. That is ordinary clipping of authored strips, not plant generation or replacement by camera-facing quads. Winding and ADC suppression are preserved; unsigned cross-platform matching does not prove live culling behavior.

The case matrix contains strip ranges/flags/scales, source offsets, compact normal/UV ranges and color histograms. It omits full proprietary coordinates. Component counts refer to explicitly documented shared-edge geometry; they do not establish independently transformed trees/shrubs or alternative LOD instances.
