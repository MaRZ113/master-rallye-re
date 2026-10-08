# Camera, hierarchy, LOD and animation boundaries

## Specialized billboarding

**NOT_FOUND_IN_TRACED_HANDLER_CACHE_SELECTOR0_PATH.** The material callbacks only write mode/bucket/options/mip coefficient. The cache copies authored XYZ. The selector0 coordinate path reads XYZ, UV, color and control, using ordinary object/view/projection matrices. It neither constructs a right/up camera basis nor substitutes per-plant vertices from a pivot.

The chosen pinus2, pinetree and bush01 source normals have very small Y ranges, consistent with authored upright planes. That source observation is not evidence of dynamic billboards or a count of crossed-plane plants. Turkey3's source group also contains differing normal orientations; all are preserved as source data.

Ordinary projection, frustum/range culling and potentially parent transforms are camera-dependent. Consequently the bounded result is “no specialized billboarding in these material paths”, not “the entire game has no billboards” or “camera motion cannot alter the image”. No invented camera/normal evaluator was added.

## Hierarchy and LOD

DRESSING1's inherited selection remains relevant:

* `3c1148`: model+3c and view X/Z region/child selection.
* `3c1e48`: generation-stamped child dispatch, avoiding duplicate dispatch within a generation.
* `3b9258` →`200550`: sphere/range/side-plane gate before generic child traversal.
* `3bca80`: selected material mesh draw callback.

The selected source ancestry is tags1/6/5/2, with no recovered leaf-local replacement transform or explicit tree/treeblend transition owner. Shader names do not establish paired LOD branches. Whole shared-edge components may be disconnected authored surfaces; they are not proved alternative trees.

No tree-specific distance threshold, alpha fade, density reduction or source replacement was found in the callbacks/cache/selector0. Treeblend's different depth/blend state and bucket do not prove LOD crossfade. The final selected live child set and the broader conditional predicates at26bc78/3c15d8 remain DRESSING1 boundaries. They were not reopened or filled with assumptions.

## Wind and time

No global time, periodic function, wind vector, per-vertex bend, UV scroll or animated texture selection was found in the traced material initialization, cache packing and selector0 path. Source vertices are cached/reused. This is negative evidence about these paths, not a proof that every parent/model/weather system is static.

No synthetic wind/billboard simulation was created. A runtime experiment must compare the same selected mesh's cached/world/packet vertices at two camera/time states. A changing silhouette by itself cannot distinguish ordinary perspective/culling, another selected branch and true vertex deformation.

## Grass separation

GRASS1 concerns material-detail eligibility, source spatial triangles and procedural decoration. TREEBLEND1 concerns authored visual mesh records with tree/treeblend shader modes. The texture name, disconnected component count and source material name do not join those ownership chains. Any future PC foliage restoration must retain this separation.
