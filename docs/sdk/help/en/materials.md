# Surfaces, native texture bindings and reflection weights

The hierarchy identifies variant, physical draw, native material and exact texture
slot. Select a draw to highlight its source surface. Shared vertices reject
independent RGB/reflection-weight changes. Wheel draws affect all instances.

Selected-surface RGB modulates vertex colors; it is not semantic paint. Baked
lettering may change too. Existing environment passes can be disabled. Reflection
weight × source (0..2) is qualified only for independent **opaque** environment
vertices. It preserves the original weight pattern and clamps to a byte; weights
already at 255 cannot brighten further. A source zero stays zero. Restore returns
the baseline. Native damage may subsequently lower the weight. Blended/cutout
alpha and unknown shader families stay read-only: opacity is not a universal
reflection-intensity knob.

Assign Existing Texture changes one existing owned diffuse slot 0 or existing
opaque environment slot 1. Compatible textures appear first, with search, an
optional incompatible list, counts and a large independent image preview.
Select a texture for dimensions, memory, alpha range and compatibility details.
This changes a native descriptor, **not** the pixels of any shared image.

Names may have different lengths. The structural writer reconstructs one
length-prefixed string and verifies geometry, UVs, other material records and
collision/suffix bytes. Different dimensions retain normalized UVs without
resampling. Blended opacity classes must remain compatible; cutouts retain
visible/discarded coverage at native threshold 128. Opaque environment texture
alpha is reflection weight; warnings expose that distinction. Native switch-owned
lamp/glass variants, Null activation, unowned/missing resources, aliases and
unknown special shaders reject. Effects are never silently classified by names.

An assignment affects only the selected model variant. Inspect race/frontend
explicitly. Save/reopen, candidate build and Undo/Redo/Restore use shared SDK Core.
