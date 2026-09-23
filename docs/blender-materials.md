# Blender vehicle material previews

The R2 Blender material is an approximation: first non-Null DX texture as Principled Base Color, decoded texture alpha connected to Principled Alpha, and a provisional transparency setting when the DXT has non-opaque pixels. It is not a reconstruction of Direct3D 8 texture-stage operations.

R4D has not yet established a direct mapping from DX slots/control fields to stage 0/1, blend equations, or alpha-test thresholds. Therefore the preview shader remains conservative. A two-texture node graph, chrome mapping, and glow emission would imply unsupported runtime behavior at this checkpoint.

Canonical source evidence is the object metadata JSON: draw identity, all ordered slots, sidecar material candidates and nullable flags, raw control words, and source provenance. Blender nodes are not the authoritative representation. The R4D corpus adds external analysis of per-texture alpha and neutral signatures; it does not mutate imported DX bytes.

Preview status: **PARTIAL**. The base image is useful for geometry review; glass/chrome/body layering/glow fidelity is not yet validated. See docs/vehicle-materials.md.
