# Original vehicle material contract

The visual loader parses the readable source name during model loading.
`390d98` searches case-sensitively for `$shader`, then the first following `(`
and `)`. The extracted name is interned; ASCII capitals and slash direction are
folded by the shared interner. `391690 ->3a6c58` resolves the registered handler
and calls virtual slot+14 with the real mesh. These operations were established
in WATER1 and linked afresh to the vehicle tag2 stream.

| Token | Registration | Handler | mesh+28 | Secondary result |
|---|---|---|---:|---|
| carshiny |3a6ea8/vtable487ee8|3ade58|3|CommonTextures\\rendertarget64x64, unless resolved old name contains `rubber`|
| caralpha |3a6f98/487ec8|3adfe8|2|No environment override in handler|
| carglass |3a7008/487ea8|3ae040|20|CommonTextures/windscreen-reflect|
| carsglass |3a7078/487e88|3ae0c8|20|Same static highlight|
| carglow |3a70e8/487e68|3ae150|21|CommonTextures\\rendertarget64x64|
| carflat |3a7158/487e48|3ae250|1|Single-texture default control|

All rows are CONFIRMED_BY_EXE. Only carshiny/carglass/carflat are associated in
depth with selected original vehicle meshes. Mode21 is a bounded lead, not a
complete lamp/light reverse. carbrakelights and the survey's `crashiny` are not
silently mapped to one of these contracts.

carshiny additionally writes mesh+2c/+3c/+40=0, +44=0.3 and +24=an auxiliary
allocated by327f30. carglass/carsglass write +2c/+3c=1,+40=0,+44=0.3.
carflat writes the same scalar defaults as carshiny and the same color auxiliary,
but retains mode1. Serialized booleans and runtime shader-written fields must
not be treated as identical by position alone.

The secondary map is a runtime override. Kia root.20 originally references
`chrome-tga`, but the handler replaces mesh+38 before `3714e0` binds mesh+e4.
That source image's existence is not evidence that its pixels reach this draw.
The `rubber` test is a literal substring search on the **resolved** secondary
name returned by3a4718; no special material enum is introduced. Diagnostic tests
of an uppercase resolved input do not establish raw authored-case behavior
before interning. No unknown token is repaired or trimmed.

`3b2190(handle,2)` is a deletion/release epilogue: it frees only when argument
bit0 is set. It does **not** set a texture format or dynamic-reflection flag.
The GS target format is established from actual31a518 call arguments instead.
