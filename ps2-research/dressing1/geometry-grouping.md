# Deterministic geometric decomposition

The diagnostic offers three independent adjacency definitions: original shared
vertex indices; coordinate-welded vertices; complete coordinate-welded edges.
Whole edges use three ordered source corners converted into unsigned edge keys.
Coordinates are rounded to four decimals, matching GEOM1's diagnostic convention;
decimals3/4/5 are checked independently. All four whole-edge component counts
are stable across those three precisions.

Index splitting reflects compiled strips, so it produces64/53/51/28 components.
Welding produces16/11/7/3 vertex-connected and16/12/7/4 edge-connected groups.
The hut and pinus differences expose point-only contact and disconnected
subparts; none supplies a reliable placed-instance population. Degenerate
zero-length edges are not allowed to join unrelated records.

The matcher retains every source face and stable original group/node/strip ID.
Component IDs hash the minimum original face identity plus method/precision;
union-find roots or set iteration are not report identities. Duplicate triangles,
coincident LOD/helper groups and repeated references remain separate source facts.

Hut/boat shape search chooses the largest-area anchor, tries six target corner
permutations and constructs a proper rotation from triangle bases. Default scale
is fixed1. Translation is fitted; all unique source corners and every original
triangle must match the target family within0.001. A declared hypothesis budget
fails closed. No affine/shear, screenshot fitting, partial-shape acceptance or
new placement is created. Symmetric matches are hypotheses, never instance counts.

Synthetic tests distinguish touching corners/whole edges, duplicate faces,
disconnected subparts, changed grouping, transforms, malformed paths and partial
shape fits. Known source bytes and frozen GEOM1 anchors provide separate original
data checks. Complete coordinates and all transform hypotheses stay ignored.
