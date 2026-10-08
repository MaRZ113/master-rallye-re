# Read-only spatial diagnostics

The executed three baseline comparisons generated TURKEY3.svg,FRANCE1.svg and
ITALY_S1.svg under ignored data/geom1. SVG IDs separate shared, coverage-equivalent,
partial, near-modified, PS2/PC unmatched candidates and degenerates. Water outlines
are independently highlighted. Full source IDs remain polygon tooltips.
TURKEY3-preview.png is a locally generated Pillow preview, visually inspected.
No original texture is used. X is right,Z is up; Y is collapsed. Overlapping2D
polygons do not prove3D equivalence. Diagnostic layering is not game draw order.

geometry_delta_visualize.write_svg/write_png accept decoded source geometry and
relation tables; both enforce ignored output paths. SVG uses only stdlib; PNG
optionally requires Pillow. No Blender/add-on installation or project changes.
A future Blender diagnostic would use(X,-Z,Y),scale1 and preserve source IDs,
but no Blender scene was created here. These local rich derivative views are
excluded from the handoff, which ships reproducible tools and compact metadata.
