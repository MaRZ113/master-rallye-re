# PS2-GRASS3 resource and placement contract

This inventory uses fresh named extraction from canonical PackFS, the existing
`detail_runtime.decode_landscape`, and the frozen GRASS1 source hashes. All four
canonical files were rehashed. No original asset was written or modified.

`course-inventory.json` contains 36 distinct supported landscape resources.
Every examined course contains both recognized `$detail(grass)` and
`$detail(shrubs)` material records bound to slope-eligible source triangles.
This proves source eligibility in all 36 examined landscapes, not simultaneously
visible tuft totals or admission of all 36 courses in the PC pilot.

The original parser searches the first case-sensitive `$detail` occurrence,
then interns the extracted token with ASCII lowercasing. `$DETAIL(grass)` is
not the same token; `$detail(shrub)` remains unrecognized. Turkey_S1 has a
separate singular-shrub material; it must not be silently folded into shrubs.
Stones and none do not enter either generating pool.

The static/executable resource selection is global per category:

| Category | Pool | Canonical image | SHA-256 |
|---|---:|---|---|
| grass | 1 | `particles/grass1` | `519908ac79ca57591a8a38d3629286e25ffc51539705342864a5056785427eb6` |
| shrubs | 0 | `particles/bush1` | `2e4178614fbcbb3dbc3eaf5931001d2a566e76d59ef6adf7e66cd372556d40e9` |

Both are 32x32 RGBA source resources with stored alpha 0–255: 223 distinct
grass alpha values and 213 shrub values. No per-course image variant selection
was found in the recovered two-pool consumer. A course ground texture named
GRASS-TGA is not the particle image. This is a bounded selection claim, not a
claim that other foliage textures do not exist.

Placement uses material-owned tag103 spatial triangles with shared source
positions, original winding, and strict normalized upward normal Y > .975.
The original float32 pitch is bits `3faa3d71`; both categories use the same
scanline/hash/jitter rules. Grass lift/size is .33, shrubs .4. The original
camera activation square has width60, center snapped at twice pitch, retained
point pools, and radial alpha falloff. No wind deformation or stochastic density
LOD was found in the bounded generator. Source mesh counts are not tuft counts.

The existing PC pilot deliberately reconstructs full source triangles once,
then bins the derived positions into 8-unit XZ cells. It does not reproduce
the original incremental clipping/history or live FCSR exactly. Current PC
preview uses view-space rectangles, two triangles each, reusing native
projection. Original VU screen-sprite Q scale/cap56 is not a claim of this
preview. Alpha maps GS /128 to D3D /255; inherited GS state is not fully captured.

## Independently checked expansion candidates

| Course/category | Eligible source triangles | Exact PC matches at .001 | Excluded | Reconstructed points | Private artifact SHA-256 |
|---|---:|---:|---:|---:|---|
| France1 grass | 5193 | 5192 | 1 | 197680 | `354cb84c7238e8a1a4959c95fc7e265587f32a3f26dcb29b98aa818c1096f961` |
| France1 shrubs | 1463 | 1463 | 0 | 169932 | `69e64191810c4f3ce5b9b06862e9afe8d4ea2a69940ee7d4449cb71430fc2802` |
| Italy_S1 grass | 3239 | 3239 | 0 | 125524 | `e764d52060bc87c797e43459d743ec3dc6a4cd1aff67f239a62c59e82863c1ae` |
| Italy_S1 shrubs | 1158 | 1137 | 21 | 75253 | `e2d08cfc56f7f3ea8e91b5225ba1b4a228ec40062b361c697426694c0f88234d` |

These are source-derived, whole-course reconstructions, not live PS2 population
counts. All four fit the existing 250000-point artifact budget without thinning.
No private asset was emitted by these inventory helpers: the artifact hashes
were obtained by calling the existing serializer in memory and structural
readback. Root integration can reproduce the exact byte streams privately.

France1 route anchors have zero residual. Italy_S1 has two known route outliers
(max26.8221 source units; 290/292 within one unit), retained in the report.
Both editions' authored landscape matrices are independently identity matrices;
the matched triangle coordinates are checked directly, without fitting a
transform. Do not erase Italy route outliers or claim its entire route identical.

`eligible_source_digest` hashes ordered source triangle/material IDs and their
original float32 XYZ bytes; it is explicitly not a placement digest.
`generated_xyz_sha256` hashes the reproduced original source-triangle scanline
order. Private artifact hashes also include category texture/source identity
and deterministic bin ordering. No full mesh or original image is in the JSON.

## Admission and performance recommendation

Start runtime expansion with France1 and Italy_S1, retaining Turkey3 unchanged.
Admit an exact supported course + category + PSM hash + GXI hash + PC DX hash +
complete artifact hash tuple. A valid France1 asset must never be used on another
course. Unknown course, absent/invalid asset, or unproved live world/camera/target
identity means Stock. The 36-course source inventory alone is insufficient to
admit the remaining courses without retail geometry/resource checks.

Reuse the accepted race certificate, device/reset generation, depth/target,
viewport and camera proof. Clear course-bound proof and consumed-boundary state
on restart/switch/real reset; preserve reset-echo behavior. Keep cold-menu
preflight before Broker/GPU state access. Do not perform filesystem reads or
full placement generation per UI draw. Load/verify bounded CPU data once; use
8-unit bins and the existing half-width30 camera square and radial fade.

Keep the 16384 visible-point/category guard. Current overflow rejects the batch
with `grass_visible_point_limit_no_thinning`; it does not silently discard tufts.
Do not raise it without measured native cap and performance evidence. Preserve
separate category failure so a bad shrub asset does not disable working grass.
No additional geometry mirroring or baseline change is required by the data
contract. The root alone owns any source and overlay integration.

Test Stock defaults, correct and wrong course/category tuples, hash swaps,
restart, course switching, menu preflight, HUD visible/hidden, real reset versus
echo, malformed bins/nonfinite positions and visible-limit fail-closed behavior.
User A/B should run Turkey3 → France1 → Italy_S1 → Turkey3, restart each race,
return to menus cold and warm, and toggle HUD. Native tests cannot establish
visual density, lifecycle performance or runtime parity.
