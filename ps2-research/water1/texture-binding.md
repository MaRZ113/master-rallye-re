# Water texture selection and binding

`3ae9a0/3aea50` retain mesh+34's course map and assign mesh+38 from string
**487690**, `CommonTextures/watersurface2`. This is real shader output, not an
association inferred from adjacent names. Waterfall and waterall handlers
override **both** names with common waterfall and waterfall2 textures, so an
authored course waterfall map must not automatically be called the bound map.

`3714e0` resolves both classified names through `2fd7d0`; that existing resource
path resolves the root and `.gxi`, uses filename cache `2f84f0`, and ensures
residence through `2f9c80`. Handles land at mesh+dc/+e4, related metadata at
+e0/+e8. `3bca80 ->31d1f8` supplies both handles. During queue drain,
`311c50/312130` read the texture cache and construct first/second TEX0, TEX1 and
MIPTBP fields. Actual captured VRAM addresses are still unknown.

| Resource family, selected original files | Dimensions | Stored alpha | Distinct values | Runtime selection |
|---|---|---|---:|---|
| France1/Italy_S1/Spain_S2 WATER-TGA |64x64|255..255|1|Retained first water/puddle map|
| Turkey3 WATER-TGA |64x64|255..255|1|Retained first puddle map|
| Common WATERSURFACE2 |64x64|4..131|128|Second water/puddle map|
| Common WATERFALL-TGA |32x32|6..255|53|Overridden first waterfall map|
| Common WATERFALL2-TGA |32x32|0..67|24|Overridden second waterfall map|
| France1 course WATERFALL-TGA |64x64|0..255|71|Authored reference; classifier overrides it|
| Spain_S2 course WATERFALL-TGA |64x64|0..255|136|Authored reference; classifier overrides it|

All nine payloads were freshly extracted and accepted by existing
`psbtool.parse_gxi`, supported simple13039 layout and exact8+4*width*height
size. RGBA channel interpretation retains UI1's visual-reconstruction grade.
`texture-evidence.json` contains every path, stored/decoded size and SHA256,
alpha distribution and provenance. No new guessed GXI variant is introduced.

**TEXTURE_EXISTS** and **TEXTURE_REFERENCED_BY_MATERIAL** are original byte
facts. **TEXTURE_LOADED_BY_RENDERER** and **TEXTURE_BOUND_TO_DRAW** are supported
static consumer chains; they do not assert a live texture handle captured on
Turkey3. **TEXTURE_VISIBLE_IN_RUNTIME** is not independently confirmed.

Puddle's second pass has TCC=0, so WATERSURFACE2's stored alpha is not used by
that layer's texture combine. Water's second pass has TCC=1. The common image's
variable alpha therefore does not justify a universal transparency statement.

No ENVSOURCE64X64, RENDERTARGET64X64 or STATICRENDERTARGET64X64 pointer was
connected to these two selected mesh resource slots. That bounds the recovered
water dependency; it does not disprove a wider environment capture system.
The missing-name branch uses default handle helper2fd788. Missing/corrupt
**named** resource fallback was not traced through all general loader paths.
