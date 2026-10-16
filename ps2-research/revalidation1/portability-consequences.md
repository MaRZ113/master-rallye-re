# Portability consequences

The France1 source surfaces already exist in the PC compiled course: the
selected 24 source faces have a strict 24/24 geometric correspondence. A
future restoration does not need new geometry for this selected feature.

The PS2 and PC material labels differ (`treeblend` vs `tree`) and the
associated source images differ in dimensions and stored-alpha distribution.
The port problem is therefore initially material/render-state and possibly
asset selection, not an established content-geometry gap. Exact PS2 alpha
coverage and GS blend parity remain unknown because the PS2 runtime texture
conversion and live PC texture-stage/diffuse state were not captured.

The current pilot's strict geometry identity, current resource generations,
one draw-local state request and masked native-state restoration are a useful
bounded experiment. Its mode 1 result demonstrates a visual problem according
to the user; it does not justify broad transparent sorting, geometry changes,
or extra passes. Preserve the Stock default and gather the next controlled
single-state observation before changing architecture.

Future planning labels for this one case:

- `REUSE_EXISTING_PC_MESH`
- `MATERIAL_ONLY_PORT`
- `RENDERER_ONLY_PORT`
- `PS2_TEXTURE_CONVERSION` (conditional; only after alpha/source semantics)
- `REQUIRES_DEEPER_RE` (for runtime alpha-stage and render-order cause)

No port or content change was performed by this audit.
