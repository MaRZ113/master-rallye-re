# Pajero source geometry and missing Master Rallye vehicles

29 October 2026. Compare decoded **PC Paris-Dakar RED #256**, **PC Silver #271**, and **Xbox Dakar 2 Pajero #205**. These are separate original assets from pinned owner-local sources, not manual OBJ adjustments or geometry traced from screenshots. Renderer status is [L2 WARN](DAKAR2_RENDERER_RESULTS.md).

## Method and exact boundary

`tools/compare_dakar_pajeros.py` reads the original UVS scenes, composes original parent/local transforms and the already documented reversible axis conversion, then measures assembled vertices and four non-spare wheel rest-node origins. Shadow geometry is excluded. A disposable preview translates the axle midpoint to the origin and **uniformly scales by measured wheelbase**. Every model uses identical orthographic camera/bounds. No nonuniform scaling, body lowering, guessed suspension settlement or modification to source JSON/geometry is performed.

Original numeric units are not independently certified as meters across games. Consequently both original numeric values and wheelbase-normalized ratios are reported; absolute cross-game physical-size claims are inappropriate. Wheel values are source rest-node origins, not recovered loaded suspension. Body-role envelopes include attachments/crew; they must not be mistaken for factory body dimensions or exact roof contours.

Private evidence: `.research-output/vehicles/dakar2-fidelity/comparison-final/measurements.json`, six `*-comparison.png` sheets and per-model six-view captures. This includes exact original scene hashes, original/normalized bounds, axle coordinates, per-part bounds, five coordinate cross-section envelopes, mesh counts and position-array hashes. Numeric source coordinates and complete geometry remain private.

## Measured differences

| Source-rest metric | PC RED | PC Silver | Xbox Pajero |
|---|---:|---:|---:|
| Wheelbase, original numerical units | 2.527780 | 2.527780 | 2.612777 |
| Front track, original rest-node distance | 1.622151 | 1.622151 | 1.710450 |
| Rear track | 1.746405 | 1.746406 | 1.751960 |
| Front overhang, body-role envelope | 0.629194 | 0.719451 | 0.651107 |
| Rear overhang, body-role envelope | 0.937437 | 0.847184 | 0.717220 |
| Body-role width / wheelbase | 0.848665 | 0.822719 | 0.786003 |
| Body-role height / wheelbase | 0.664915 | 0.681823 | 0.689874 |
| Vertices, including retained wheel/attachment meshes | 3415 | 3454 | 3689 |
| Triangles | 1956 | 2002 | 4154 |

In raw numerical values the Xbox wheelbase is 3.36% longer than either PC candidate, front track 5.44% wider, rear track 0.32% wider. These are numerical-source differences, not independently established physical dimensions. Relative to wheelbase, Xbox is 7.38% narrower than RED and 4.46% narrower than Silver by the stated envelope; its rear overhang is substantially shorter. Xbox is therefore not simply the PC RED or Silver mesh with another livery.

At six-decimal wheelbase-normalized vertex precision there are zero exact body-role vertex intersections between each pair. No original mesh-position-array hashes are shared between Xbox and either PC candidate; RED/Silver share one position-array hash. These negative comparisons establish differences in the inspected arrays; they do not disprove common earlier development ancestry, recover missing topology correspondence or establish an original MR asset. Different vertex splits/material organization can change array hashes without changing every surface.

## Feature comparison and limits

| Feature | Measured or inspectable source evidence | Interpretation |
|---|---|---|
| Body proportions / overhangs | Table above; identical camera and WB=1 sheets | Xbox is a distinct shorter-overhang/narrower-relative assembly, not a forced fit |
| Roof/cabin height | Five sampled body-role cross-sections; roof-level vertices at centre-Z reach normalized Y 0.479986 RED, 0.417495 Silver, 0.556798 Xbox within ±0.04 WB | This is a local sampled envelope above the rest axle datum, not an exact roof height or suspension-independent factory measure |
| Roof length / equipment | Top/side sheets show conspicuous raised rear roof fins on PC candidates; Xbox rear roof treatment differs | Visible geometry difference. Precise roof-only length needs a reviewed semantic triangle selection; whole-body bounds are not substituted |
| Windshield / window contours | Xbox has separately named WINDSCREEN/SIDEWINDOWS nodes; PC glass and body surfaces use a different mesh/material organization | Per-part/source bounds retained, but one-to-one A/B/C-pillar correspondence is unresolved. No arbitrary contour match asserted |
| Headlights / front bumper | RED broad clear headlamp treatment; Silver circular lamps, wide lower intake and paired bumper holes; Xbox darker rectangular lamp region and different bumper openings | Distinct original front treatments visible in fixed front views; same real-world family does not make them identical assets |
| Arches / fenders | Side/front silhouettes and source cross-sections differ | Qualitative shape comparison backed by actual geometry. No manually picked arch-radius score or hidden rescale |
| Rear body | Different overhangs, lamps, door/livery layout; none of these rest reconstructions matches the historical external central spare configuration exactly | Significant correspondence gap, especially for the historical rear image |
| Accessories / wheels | Xbox retains named axles, hubs, mudflaps, exhausts, three spare-wheel nodes and body equipment; PC detachable resources differ | All-retained rest inspection is not the original runtime equipment selection |
| Topology / materials | Xbox 4154 triangles versus PC 1956/2002; compressed multi-stage Xbox textures versus PC texture/material resources | Complexity differs. Triangle count includes source components; no historical MR polycount inferred |

The existing Silver native candidate was not used as the PC geometric source: the immutable original Silver UVS was used. No MR physics-origin rebase, material split or glass authoring is allowed to contaminate this comparison.

## Owner-local prerelease reference evidence

Original image folder: `C:/Users/MaRZ/Pictures/Master Rallye`. Reference hashes and prior observations remain in [PARIS_DAKAR_PAJERO_COMPARISON.md](PARIS_DAKAR_PAJERO_COMPARISON.md). This milestone rehashes the actual originals and creates private labeled contact sheets in `.research-output/vehicles/dakar2-fidelity/comparison-final-historical/`, with `references.json`. References include `m_rallye_05.jpg`, `m_rallye_07.jpg`, `mr4_paj.jpg`, `mr_1m.jpg`, `mr7.jpg`, `m_rallye_08.jpg`.

Publication/capture build, executable, camera projection and dates remain UNKNOWN. The owner's prerelease attribution is historical context. Perspective images are not metrically aligned to orthographic geometry and do not supply a missing MR mesh. Contact sheets uniformly resize original pixels for viewing; no generated/repainted vehicle imagery is used. Original image files remain unchanged.

| Evidence category | Finding |
|---|---|
| Exact geometry or asset evidence | Original donor streams/resources and hashes are exact for their named sources. **No exact donor-to-prerelease-MR mesh/texture identity established** |
| Measurably similar source geometry | All three have comparable short rally-raid SUV dimensions/axles after explicit WB normalization. Xbox is measurably distinct, not the PC mesh. A quantitative nearest-MR-geometry ranking is impossible without the missing MR mesh |
| Strong visual resemblance | Silver retains the strongest specific frontal design relationship to white/silver `mr4_paj.jpg`: round lamps in rectangular housings, wide low intake and paired small bumper openings. Xbox has a useful closer-looking boxy cabin/front treatment for aspects of red `m_rallye_05.jpg`, but grille/lamps/arches and rear equipment still differ |
| General real-world family similarity | Red/yellow Mitsubishi livery, upright short SUV cabin and prominent arches are shared. Number203 historical versus Xbox205 versus PC256 is a difference, not an identity bridge |
| Unresolved | Historical red rear `m_rallye_07.jpg` has central external spare and corner lights; selected Xbox/PC rest models do not match that configuration. Silver/teal263 and the partly occluded silver/red vehicle remain separate unidentified subjects. Exact MR lineage, donor model year/V20/V60 mapping and capture-build attribution remain unresolved |

## Bounded donor assessment

For the **red/yellow missing SUV**, Xbox Pajero is a useful first geometric comparison candidate: distinct compact proportions and cabin/front treatment warrant preferring it for the next owner visual review over merely recoloring PC RED. This is a feature-based donor recommendation, **not a proven closest 3D match** or a claim that MR used Dakar 2's asset. The central spare/rear-shape mismatch prevents calling it a complete restoration.

For the **white/silver frontal reference**, PC Silver remains the stronger established design match. There is no evidence to replace the accepted owner-launched Silver project with the Xbox model. For the other historical silver/teal SUV and tiny PIAA thumbnail, identity is unresolved; do not promote one donor as a universal winner.

Original MR geometry or authenticated matching build resources would be needed to establish direct asset use. Original Dakar 2 runtime captures would additionally qualify active equipment, source shader behavior and pose. Neither input was fabricated. Stop after this comparison; any new native candidate requires a separate owner decision.

## Reproduction

```powershell
python tools/compare_dakar_pajeros.py --red .research-output/vehicles/paris-dakar-source/PajeroRED/qualified/scene.json --silver .research-output/vehicles/paris-dakar-source/PajeroSilver/qualified/scene.json --xbox .research-output/vehicles/dakar2-fidelity/final/PAJERO/scene/scene.json --output .research-output/vehicles/dakar2-fidelity/owner-comparison --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe --references "C:/Users/MaRZ/Pictures/Master Rallye"
```

Outputs are private, fresh and outside supplied source projects. No screenshots, proprietary geometry or texture samples belong in source-only review archives.
