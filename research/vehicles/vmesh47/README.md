# V-MESH4.7 — reflective paint masks, front cavities and coordinated wheel profile

## User runtime evidence

The user confirms that the photographed window-edge gaps disappeared in V4.6. The new captures show a too-small gold disc, mismatched tyre imagery, remaining hard/nonreflective body patches (hood and rear), and terrain visible through headlamp/front openings. The supplied GT3 appearance image is a visual comparison, not exact geometry or an instruction source.

## Pipeline changes

- Optional reflective paint masks reserve an existing environment-enabled donor atlas for alpha-tested paint islands. Previously those islands used non-environment pools next to reflective opaque panels. The new path preserves the ordered helper slot and native selector (1,1); visible texels use alpha148, clear texels zero. It is intended to remove reflection discontinuities on the hood/rear while keeping genuine cutout holes.
- An explicit solid-black-swatch policy retains classified trim with a 1x1 RGBA(0,0,0,0) texture. Within detected lamp objects these retained surfaces use the lamp helper; other constant-black trim uses the black draw. Whole-image zero alpha is not treated as coverage in that narrow case. Clear paint overlays and actual glazing remain protected. This recovers source surfaces inside lamp/vent cavities; it is a conversion policy, not a full GT3 blend reconstruction.
- `vmesh_surface_repair.py` appends separately reported black interior geometry. Lamp backs follow source triangles with a 4mm inward offset; front technical-mask backs use the same bounded policy. Small front boundary gaps are bridged only between near-parallel edges with at least 75% overlap and an endpoint separation of 0.5–20mm. Generated backs/bridges are two-sided by explicit winding pairs. Candidate edge pairs already covered by an opaque surface are skipped. Imported vertices and UVs remain unchanged. These are interior closures, not a claim of watertight body repair.
- Wheel profile mode uses an explicit configurable rim/tyre ratio of 0.80 (V4.6 was approximately0.60). This is a visual-fit heuristic guided by the supplied appearance reference, not a recovered GT3 dimension. Radius envelope, width and hub axis are inherited independently. One common procedural rubber palette now supplies tread and sidewall imagery; the gold disc uses the private source PNG. Meshes use coordinated UVs. Spoke openings remain opaque dark imagery.
- Iterative builds now inherit the previous wheel's maximum radial envelope, rather than its Y-axis extent. This avoids radius drift when the angular tessellation changes.

## Glass appearance requested by the user

The candidate additionally uses the existing native glass draw for a lightly tinted translucent layer over the lamps. Source reflection-shell triangles are selected geometrically by their vertices belonging to detected lamp objects, deduplicated, and offset outward by 1mm. This repurposes the source reflection geometry as a glass-like overlay; it is not an assertion that it was an original GT3 glass pass. A small generated constant swatch is packed into the existing glass atlas (source RGBA110/130/150/96, alpha multiplied by the existing0.7 glass scale). Ordered glass-helper binding, depth/sorting and native alpha blend state are retained. Opaque cavity backs remain inside the housing to stop terrain showing through the optical layer. Existing windscreen/window geometry and source alpha remain intact.

## Boundaries

Only the vehicles checkout/branch is used. Private input and derived assets stay ignored; no original EXE or installed graphics proxy modifications, no Randomizer changes, no push/publication. No game execution. User confirms V4.6 glazing only; all V4.7 game appearance remains pending human validation.

Candidate: `.research-output/vehicles/vmesh47/v47-exp-003`. Build with `tools/build_vmesh47_impreza_experimental.py` using the private CarModelSet input, retail root/exe and V4.6 runtime family as the before reference. Offline comparisons do not emulate environment mapping, game lighting, mipmaps or complete sorting.
