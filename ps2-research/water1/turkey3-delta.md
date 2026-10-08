# Turkey3 platform delta

**Conclusion:** additional authored PS2 visual landscape surfaces, together
with PS2 `puddle` material behavior. This is a content difference in the
compared compiled landscapes; the complete difference in live presentation
still needs a controlled capture. User gameplay comparison remains
**USER_RUNTIME_OBSERVATION**, independently of this static result.

The canonical resource is `\TNG\DATAPSM\COURSE\TURKEY3\TURKEY3.PSM`,
decoded size 4,086,061 and SHA256
`dd274ac1cb56c16d35410fbe2e8e3771a750b47710b747fddc70604fdb3d59fc`.
Its first matching material starts at decimal **3,429,472**, reproducing
CDELTA1's source-byte lead. The owning node-2 record starts at **3,429,418**.
This record contains map `Course\turkey3\water-tga` and
`water $surfacetype(water) $shader(puddle)`. Its strips reference real model
vertices; the binding is in the render tree, not inferred from tag-103 cells.

| Authored visual source metric | Turkey3 PS2 |
|---|---:|
| Puddle mesh records / strips | 17 / 51 |
| Non-suppressed nondegenerate triangles | 745 |
| Distinct XYZ positions | 537 |
| Edge-connected components | 11 |
| Component triangle counts | 207,101,77,77,63,62,61,30,26,23,18 |
| X bounds | 1957.5634765625 .. 3436.294921875 |
| Y bounds | 19.0061817169 .. 37.9566268921 |
| Z bounds | -818.287353515625 .. 534.1873168945312 |
| Unsigned surface area | 38112.91549169407 source units squared |
| Horizontal faces | 745/745 with abs(normal.Y)>0.99999 |
| Absolute slope range | 0 .. 0.000030914 degrees |

Components share complete edges after XYZ coordinates are rounded to four
decimal places. Point-only contact does not join components. This is a
diagnostic topological grouping, not a count of separately visible puddles.
LOD membership and runtime back-face decisions can change submitted coverage.

The original PC `.dx` baseline is reproduced: **939 physical draw records,
54,589 vertices, 42,237 triangles**, SHA256
`724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8`.
The read-only SDK validates complete draw coverage before comparison.
The name-based water/puddle candidate scan again returns zero draws.

The stronger comparison searches **all** PC draws, regardless of texture or
material name. At maximum per-coordinate corner error 0.001, allowing all
six triangle permutations, **0/745** PS2 faces match PC. **0/537** distinct
puddle positions match any PC vertex. The identity coordinate convention is
independently supported by **22,679/26,125** distinct model positions matching
the PC vertex array; no screenshot fit or per-puddle transform is applied.

A different tessellation could have the same surface without matching corners.
The second test therefore projects each of the 745 PS2 triangle centroids
vertically onto **every PC triangle covering its X/Z point**. All have PC
footprint coverage, but none is coplanar within 0.001. Nearest signed height
differences range from **-6.68201155 to +9.58656543**; minimum absolute gap is
**0.00140479**. There are 405 centroids above and 340 below the nearest PC
surface. These are double-precision diagnostic measurements of original
float32 positions, not bit-exact PS2 calculations.

This test rejects a straightforward "same PC ground face, renamed material"
explanation for the recovered surfaces. It does **not** establish that every
face is an overlay above the road: some are below nearby PC terrain, the
terrain itself differs, and the smallest gap is close to the declared tolerance.
Nor does it exclude water produced by an unexamined PC entity or runtime path.
The defensible scope is **extra PS2 visual source geometry relative to the
validated compiled PC landscape**, not universal absence of all PC water.

The ELF classifier attaches mode9 and a puddle auxiliary to these records.
`320938` changes vertex color according to nearby spatial ground height;
`320c78` changes cached UVs. Neither produces their XYZ or triangle topology.
Thus the recovered puddles are authored surfaces processed at runtime,
not planes synthesized from a shader-name string.

Future faithful Turkey3 work needs course surface/material delivery as well as
the renderer behavior. Adding `WATERSURFACE2` or changing alpha state on existing
PC water draws alone cannot supply these missing compiled surface records.
Actual conversion, collision decisions and final visible subsets are deferred.
