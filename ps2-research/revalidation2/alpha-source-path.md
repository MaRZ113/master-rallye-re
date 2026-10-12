# Source alpha to GS: strongest proved chain

The final per-pixel GS blend coefficient cannot yet be stated as one value.
It depends on both the vertex color and the sampled texture alpha, plus
runtime texture conversion and inherited GS state.

## Vertex channel path

The selected France1 material binds the authored `bush01` visual strips and
their source vertex records. The executable path is:

```text
packed source color 0xRRGGBBAA
  -> 0x003a7f10 extracts bytes at shifts 24/16/8/0 and divides by 255
  -> channel setters multiply by 255, convert to integer and clamp 2..254
  -> 0x0031f4e0 reads runtime RGBA bytes with LBU and scales each by 0.5
  -> selected VU color route converts to integer RGBAQ (FTOI0)
  -> TEX0 TCC=1 / TFX=MODULATE combines texture and vertex color
  -> GS source alpha As enters the ALPHA equation if the live descriptor/state matches
```

Addresses `0x003a7f10`, `0x003401f0`, and `0x0031f4e0` were independently
rechecked against original words with the exact R5900 language and
Rabbitizer. At `0x0031f8ac`, `LBU` zero-extends an alpha byte; the following
`BLTZ` alternative is unreachable for that value. The positive path converts
the channel to float and multiplies by 0.5. This is byte-backed executable
behavior, not an assumption that texture alpha is rescaled the same way.

The source channel clamp means fully transparent and fully opaque source
bytes do not pass through unchanged: values are clamped to 2..254 before the
cache half-scale. A rough resulting channel interval is 1..127 before the
VU conversion. Exact final per-vertex integer behavior still depends on the
VU conversion and source route; it is not a captured final packet value.

## Texture alpha

The canonical France1 PS2 `BUSH01-TGA.GXI` payload is 64x64 RGBA-like data
with stored alpha 0..255, 89 unique alpha values, and 1,673 nonzero pixels.
The stored payload SHA-256 is
`76b2f5c72e119716506e39b8bfdc1125082ebc3c02bd096d401b26bd3db57e89`; decoded
RGBA payload SHA-256 is
`4c82e76360e2266d0cc4acac2c5d1688e750d454dd1e947e2707e5efa1b1cd29`.
These identities are confirmed by source bytes and PackFS provenance.

The PC France1 `bush01-tga.dxt` source is 128x128 BGRA, with alpha 0..255,
15 unique values, 11,671 zero-alpha pixels and 4,168 fully opaque pixels.
Its file SHA-256 is
`24beae6fbd549a62939e56b3c83655fb10f487f04d00441ea7667d3729972396`.
For both row policies, zero-alpha RGB averages are approximately
`(93.35, 104.90, 76.06)`, not white. That makes the white cards in mode 2
inconsistent with a simple claim that the stored alpha-zero pixels themselves
are white. It does not identify the runtime cause: the bound resource's
format/alpha interpretation and the sampled texels are not captured.

## Unknown conversion stages

The PS2 loader resolves the material texture name to a cached handle and
descriptor, and the shared GS producer selects MODULATE. The resource loader
has an option that differs for `treeblend`, but filename cache hits can reuse
an already-created descriptor. The exact cache-option effect, selected live
TEX0 format/palette, CLUT, TEXA and mip sample are still unknown. Therefore
the final source alpha `As` cannot be reconstructed from the GXI bytes alone.

## Blend scale comparison

PS2's blend uses `As/128`. D3D8's conventional `SRCALPHA`/`INVSRCALPHA` path
uses its own normalized alpha convention. Those contracts are not numerically
equivalent by simply assigning the same 8-bit alpha value. PILOT1.3 is a
behavioral approximation and has no alpha remapping.
