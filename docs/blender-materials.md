# Blender vehicle material Preview V3 (R-MAT1)

**APPROXIMATE WITH DOCUMENTED LIMITATIONS.** Runtime binding/operation
annotations are backed by the executable; the node graph is an honest
approximation, not a Direct3D8 raster-equivalence claim.

Slot0 alone supplies the base texture. Slot1 stays an environment stage and is
never promoted when slot0 is NULL. All observed helpers share one generic
camera-normal path, with no filename strengths or special chrome shader.
The three NULL-base/helper-present records retain exact bindings in metadata
and suppress env preview under the separately labelled NULL-cascade inference.
The two textureless draws display vertex diffuse.

Byte2 enables source vertex diffuse modulation; byte3 enables source UV0.
Stage1's separate unlit contribution approximates
`current.rgb + current.a*env.rgb`, while alpha multiplies by env alpha.
Principled lighting/color management, Blender display normals/camera
conventions, fixed-function clamping and engine queue/depth behavior prevent
pixel parity. The unlit term is not a claim of physical emission or additive
glow blending. The Blender5.2.2 custom-normal safety workaround is unchanged.

Raw byte0 controls alpha independently from HasAlpha and image pixels. Enabled
byte1 selects a GREATER_THAN128/255 threshold node. Blender5.2 uses DITHERED;
legacy supported APIs use CLIP/BLEND when available. Integer GPU alpha test,
filtering and raster coverage remain approximation limits. Stock alphatest
count is zero; its preview is tested synthetically.

Each material keeps ordered slots, four raw flag bytes, raw mask, existing
source properties, selected family and structured `mr_material_semantics_json`.
`mr_preview_confidence` and small approximation-note codes separate exact
annotations from display behavior. Unsupported branches expose UNKNOWN plus
a reason; missing textures produce warnings. Default Reflections projection
is ON; `PreviewMaterialCache(..., reflections=False)` suppresses env without
rewriting raw metadata.

Draw-specific canonical object metadata remains the writer source of truth.
Per-draw `runtime_material_semantics` is a separate read-only annotation.
Preview node edits cannot author DX material bytes. Existing fixed-field alpha
and env edits retain their prior restrictions; no byte1/2/3 or new-material
writer was added.

Fresh loaded-texture Blender audit: 1478 draws / 78 resources, 1092 env bindings,
1089 effective previews across all eight helper names. It verifies raw fields,
nodes, slot identity, alpha choice, save/reload, 78 byte-identical zero edits
and byte identity after deleting preview nodes. The former V2 filename rule
covered only 367/1092 bindings. See
[preview details](../research/r-mat1/blender-preview.md),
[validation](../research/r-mat1/validation.md), and
[runtime model](vehicle-materials.md). R4D.1 V2/R4E historical notes are refined
by V3; no new human runtime result is claimed.
