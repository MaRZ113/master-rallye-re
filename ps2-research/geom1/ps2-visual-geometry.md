# Supported PS2 visual geometry

Reuse water_runtime.decode_scene, tngtool, and the already proved52-byte source
vertex layout. Header d00d/2/539; count+28; vertices+32; XYZ+36 within a vertex.
Supported landscape tags0/1/2/5/6; tag2 owns three map slots, material, flags and
13-byte strip records(first,count,flag,scale). Every mesh keeps node path/offset,
material byte offset, slots including empty slots, ancestor tag/path/offset,
source ranges, strip flags/scale and original face/vertex references.

Newest source vertex control bit0 suppresses emission. Consecutive triples are
retained in source order; render winding/backface/LOD selection is not invented.
Non-suppressed triples with area<=1e-7 remain counted and explicitly classified
DIAGNOSTIC_DEGENERATE. Unknown tags/ranges/nonfinite XYZ fail closed.
Landscape terminal100 remains the default. Spatial tag103 is never used to
invent faces. Vehicle tags7/8/terminal101 remain in reflection_runtime.

Only the selected standalone blue/red dinghy reader opts into terminalffffffff.
Both files are3420 decoded bytes,60 vertices, root1/two tag2, tree end3416 and
exact EOF sentinel. Extra trailing bytes fail. This extension is CONFIRMED_BY_BYTES
for these two original files, not a universal static-model/runtime grammar.
The existing source consumer391d38 supports shared mesh layout; the new sentinel
is not claimed as freshly executable-confirmed. Old landscape/vehicle defaults
and regressions are retained.
