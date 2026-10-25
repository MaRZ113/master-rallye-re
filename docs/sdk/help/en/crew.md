# Crew Inspector

This edits an EXISTING qualified stock MR seated pair. It does not create a rig,
replace animated people or invent cockpit attachment points. Previously imported
static crew remains static; native control/animation records stay byte-identical.

Use Qualify crew from conversion report to choose the exact original GT4 converter
report containing MR stock crew records. Full output SHA256 must match each model;
every component must uniquely match its texture tuple, vertex/triangle counts and
all six bounds. This recovers source-confirmed identities, including harness and
helmet components. Other model revisions fail closed. Alternatively import a local
crew preset with exact model hash and explicit draw/vertex selectors.

Select Race or Frontend and a driver/co-driver. The panel displays source evidence,
component draw IDs, bounds and vertex count. XYZ are metres; yaw is degrees about
the recorded rest-pose pivot. Corrections are bounded to 0.5 m and 45 degrees and
must remain within the original model bounds. These are conservative SDK authoring
limits, not measured engine capabilities. Apply changes actual compiled positions
and normals, not the physics profile or preview-only wheel configuration.

Reset person rest pose returns that person's correction to zero. Save/reopen,
Undo/Redo, comparison and isolated Build share the same recipes as SDK Core.
Highlight crew component selects its first draw; use the existing Previewer's
focus and layer-isolation controls to inspect it. Body/seats remain visible in
the normal assembled view. Runtime visibility toggles and skeletal editing are
unsupported. Definitions sharing vertices with unrelated draws are rejected.

An optional qualified cockpit envelope reports vertices outside it. This is only
an envelope warning; no automatic seat/roof/dashboard triangle intersection test
is claimed. Without an envelope, inspect clipping manually from several views.
New crew positions require actual game testing even when resource validation and
GPU captures pass. No bundled retail crew meshes or textures are supplied.
