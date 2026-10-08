# Texture binding and alpha provenance

The callbacks keep original primary texture names. `3714e0` walks model mesh pointers at model+44; mesh+34/+3c enters `2fd7d0`, which resolves the resource-root name plus `.gxi`. `2f84f0` looks up a filename cache and creates a descriptor when absent; `2f9c80` supplies shared VRAM/mipmap residence/upload dependencies. The result is stored at mesh+dc, with descriptor reference+e0. `311c50` consumes the selected handle for TEX0/mipmap state. Secondary names+38/options+40 and handles+e4/+e8 exist in the shared path; their geometry reglist is NOP for the selected modes.

Mesh+3c is1 for treeblend and0 for tree/object. `2fd7d0` **negates** that argument for the cache-creation option. The cache hit is filename-based, so an existing descriptor may be reused. The option's exact downstream pixel-format, palette or alpha conversion semantics are **UNKNOWN** in this bounded investigation. A differing option does not by itself prove a different live format for every draw.

## Original GXI evidence

All selected payloads satisfy the existing strict `PS2_SIMPLE_GXI_13039` reader: 8-byte header plus width×height×4 RGBA bytes. Unsupported variants fail closed.

| Resource under `\TNG\DATAPSM\` | Size | Dimensions | Stored alpha | Distinct | Decoded payload SHA-256 |
|---|---|---|---|---|---|
| COURSE\TURKEY3\SHRUBTRIG2-TGA.GXI | 16392 | 64×64 | 0..255 | 255 | e34ca0193956eca2d03217fb18929b6ec0a78cfe2d9d6e6a081b8b10c934fc4f |
| COURSE\ITALY_S1\PINUS2-TGA.GXI | 65544 | 128×128 | 0..255 | 6 | 1fd6d5d1c9910a905129f6c3289db0e2e603cde9ca67613c600d1fdefb0c97e5 |
| COURSE\FRANCE1\PINETREE-TGA.GXI | 65544 | 128×128 | 0..255 | 4 | a30758ca4e71f2f30bcfdd57346097b48ec42500da2bf3b43c81fdd2b48b1309 |
| COURSE\FRANCE1\BUSH01-TGA.GXI | 16392 | 64×64 | 0..255 | 89 | 4c82e76360e2266d0cc4acac2c5d1688e750d454dd1e947e2707e5efa1b1cd29 |
| COURSE\TURKEY3\HUT_01-TGA.GXI | 16392 | 64×64 | constant255 | 1 | 7d2bc6658eae58241d9bb3fd3c102cd1964070893536f33d7b30653dc03d94c3 |

PackFS offsets, packed sizes/hashes and decoded hashes are in `foliage-material-matrix.json`. No proprietary GXI or converted image is committed or bundled.

Evidence distinctions:

* `TEXTURE_EXISTS`: confirmed archive entry and decoded bytes.
* `TEXTURE_REFERENCED_BY_MATERIAL`: exact tag2 primary name.
* `NAME_RESOLVED_TO_RUNTIME_HANDLE_PATH`: proved3714e0→2fd7d0→mesh+dc/+e0.
* `HANDLE_CONSUMED_BY_DRAW_STATE_PRODUCER`: proved3bca80→queued key→311c50.
* `SELECTED_LIVE_TEX0/CLUT/TEXA` and `VISIBLE_RUNTIME_TEXTURE`: **UNKNOWN / NOT_CAPTURED**.

TEX0 TCC=1/TFX=MODULATE is explicitly set, so texture alpha is relevant to the traced texture-combine state. The exact sampled alpha also depends on runtime storage/palette conversion, mip generation and inherited TEXA. Therefore alpha >64 cannot be turned into a literal “stored GXI byte >64” file filter. The state equation is recovered; pixel-perfect coverage is not runtime-validated.

These course texture resources and authored source meshes are separate from GRASS1's procedural grass/shrub details and `particles/grass1` / `particles/bush1`. No shared plant-generation ownership is established by similar foliage imagery.
