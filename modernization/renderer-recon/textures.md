# Decoded image to texture and material binding

**CONFIRMED_BY_EXISTING_RESEARCH:** external sibling
`master-rallye-re-general/research/r-exe1/findings.md`, retail opener VA
`0x0064D530`, tries loose CreateFile before Data.sma archive fallback. Shared
GXI/GXM resource loading and cache diagnostics precede renderer-specific work.
Exact precedence among ambiguous roots/archive names is still bounded.

**CONFIRMED_BY_EXE:** `UploadTexture_005587E0` owns decoded source image and prior
D3D texture. It releases/replaces old resources; decoded image exposes pixels+8,
width+0xC, height+0x10. TextureQuality maps 1->divide dimensions by2, 2->divide1,
other selected values->divide4; dimensions clamp to at least1. TextureDepth and
source-alpha detection choose format preference lists checked by `0x0055A430`.

The data at VA `0x006E9398` contains counted format lists: opaque 22/20
(X8R8G8B8/R8G8B8), alpha 21 (A8R8G8B8), low-depth opaque 23/24/30
(R5G6B5/X1R5G5B5/X4R4G4B4), low-depth alpha 26/25 (A4R4G4B4/A1R5G5B5).
The selected format depends on option, source and caps; not one fixed format.

CreateTexture call VA `0x005589CD` (RVA `0x001589CD`): requested width/height,
Levels=0 (full chain), Usage=0, selected D3DFORMAT, pool1 MANAGED. GetSurfaceLevel
0 at `0x005589E5` obtains upload surface. Linked helper `0x005D8982` receives
decoded A8R8G8B8 source (format21), source pitch width*4, zero color-key parameter;
the surface is released. `0x005D9281` filters/generates texture mip levels.
This is an observed upload path, not proof that every DXT/source path uses it.

Handle lookup `0x0054ACD0` connects cache/resource handles to D3D texture pointers.
Compiled binding `0x00577620` preserves slot positions; emission uses `0x00564EE0`
and inline SetTexture calls. R-MAT1 [ordered slot evidence](../../research/r-mat1/texture-stage-binding.md)
is authoritative: Null slot0 does not promote slot1 into base color.

Cubemap, volume and render-target texture creation are not observed in the reviewed
game upload paths. Environment reflection here is a 2D texture stage, not evidence
of dynamic cubemap rendering. Full cache eviction/reset texture-reload ownership,
all source image decoder formats and linked D3DX indirect methods remain open.
No resource was changed or committed.
