# Glass and windscreen

Selected Tata root.21/root.22 and Kia carglass meshes select mode20. The source
primary windscreen texture is retained; authored secondary glass-tga is replaced
by CommonTextures/windscreen-reflect. `carsglass` has a separate registered name
but the same recovered20/static-secondary handler; no selected case requires it.

The primary uses TCC1/TFX0 MODULATE, ABE=1 and ALPHA44 (source-alpha blend):
`(Cs-Cd)*As/128+Cd`. Both primary and secondary mask depth writes. Alpha testing
is disabled by the traced template; ZTST is GEQUAL and ZTE is inherited.
The original windscreen32/c32 source images have nonconstant alpha; the effective
source coefficient also includes the prepared/cached color and GS texture combine,
so file alpha is not by itself the complete draw alpha.

The static highlight uses the **same selector1 normal-based coordinate generator**
as carshiny, rather than original UVs or a proved different windscreen projection.
Its TCC0/TFX1 DECAL plus ALPHA0000006000000068 produces
`Cs*96/128+Cd`, a0.75 additive highlight. The highlight file's constant255 alpha
does not set this FIX coefficient. This layer does not use the mixed framebuffer
target in the traced handler.

Body and glass therefore share coordinate infrastructure but differ in texture
provenance, blend coefficients, primary ABE/TCC and depth writes. Texture names
alone would not establish any of those distinctions. A full cockpit/mirror or
glass sorting reverse is out of scope. Runtime transparency/parity is NOT_PERFORMED.
