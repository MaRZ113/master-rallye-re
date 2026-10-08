# Reflection resource inventory

All rows below are named PackFS resources freshly decoded using tngtool and the
existing psbtool GXI decoder. Exact stored/decoded SHA256, offsets and dimensions
are in [resource-evidence.json](resource-evidence.json). A data-level alpha statistic
does not determine GS alpha testing or blending.

| CommonTextures resource | Dimensions | Stored alpha | Proved role / boundary |
|---|---:|---|---|
|ENVSOURCE64X64.GXI|64x64|0..255,2values|Static GXI source loaded by330780 into49b388; first target-generation source|
|RENDERTARGET64X64.GXI|64x64|0..255,2values|Initialization image and mutable target49b380; FRAME writer and body secondary TEX0 consumer proved|
|STATICRENDERTARGET64X64.GXI|64x64|110 constant|Exists; UNUSED_IN_TRACED_PATH; other ownership UNKNOWN|
|WINDSCREEN-REFLECT.GXI|32x32|255 constant|Static normal-coordinate glass highlight selected by3ae040/3ae0c8|
|CHROME-TGA.GXI|32x32|255 constant|Kia authored secondary; replaced in selected carshiny mesh before binding|
|REAR128-TGA.GXI|128x128|255 constant|Name/material survey lead; active renderer role UNKNOWN|
|RUBBER-TGA.GXI|32x32|255 constant|Kia retained secondary via literal resolved-name exception|
|WINDSCREEN32-TGA.GXI|16x16|7..138,56values|Tata primary glass source; filename number is not dimensions|
|WINDSCREENC32-TGA.GXI|32x32|31..255,172values|Tata primary glass source|

Simple GXI is the already supported13039 format: eight-byte header then RGBA
candidate bytes. Channel-order evidence is inherited from UI1's visual
reconstruction; original stored bytes/hashes are preserved. Unsupported variants
are not decoded by assuming this layout. GXI source RGBA and the producer's GS
PSMCT16 interpretation are distinct stages; exact live converted VRAM contents
have not been captured.

String anchors485900 and485928 are exact NUL-terminated backslash names for
target/source.4874d0 is the slash-form windscreen name. These are independently
connected to handler/producer code, not grouped merely by adjacency. Resource
lookup uses the shared2fd7d0 suffix/root/cache path. No missing resource is
silently substituted in the diagnostic.

`vehicle-name-survey.json` scans29 genuine CAR.PSM byte-name sets. It establishes
candidate shader/resource spelling and broader chrome/rear leads, not active
mesh count. Target/source names need not occur in a CAR.PSM: the shader handler
injects the target at load. The selected target/source handle containers are
different; cached body meshes share the target name. There is no proof that
STATICRENDERTARGET aliases it, or that a similarly named texture is its fallback.

Evidence distinctions remain explicit: archive existence and authored reference
are CONFIRMED_BY_BYTES; selected loader/binding operations are CONFIRMED_BY_EXE;
the original selected material reaching those handlers is CONFIRMED_BY_BOTH.
TEXTURE_VISIBLE_IN_RUNTIME is not established for any row in this phase.
