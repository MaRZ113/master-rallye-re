# RCX tracks (Rally Championship Xtreme, PC) -> Master Rallye

Tools: `tools/rcx_tracks/rcx_map.py` (stage `.map` + `config.cfg` reader), `rcx_tex.py` (TEX decoder),
`rcx_to_course.py` (Course Studio project + build), then `tools/course_pack.py` and the Vehicle Manager course-pack
commands, as for the Evo 2 tracks (docs/evo2-tracks/EVO2_TRACKS.md).

## Pilot: Fire Rock (kenya1)

```
PYTHONPATH=<master-rallye-re-course>/src py -3 tools/rcx_tracks/rcx_to_course.py \
    --stage <extracted Levels/kenya1.rcx> --work .research-output/rcx-tracks/pilot-11 \
    --resource-root <Data.sma_unpacked> --title "Fire Rock"
py -3 tools/course_pack.py make --name RCX --label RCX --out .research-output/rcx-tracks/packs/RCX-01 \
    --course .research-output/rcx-tracks/pilot-11/builds/RcxKenya1 --title "Fire Rock" \
    --shots .research-output/rcx-tracks/pilot-01/previews --distance-km 6.0
py -3 tools/vehicle_manager.py --game <host> course-pack-add .research-output/rcx-tracks/packs/RCX-01
py -3 tools/vehicle_manager.py --game <host> course-category "EVO RCX"
py -3 tools/vehicle_manager.py --game <host> apply
py -3 tools/vehicle_manager.py --game <host> seed-course-progress
py -3 tools/verify_course_layer.py <host>          # PASS, 31 races in the category
```

Result: build ok after 3 repair passes (31 off-road spots made drawn only), terrain 31 880 triangles, visual
119 381, 58 deck slabs, 3 634 barrier triangles dropped; native collision pools 20.4 MB (course layer sets the
model cache to 96 MB), DX 43 MB, textures 12.2 MB with mips (budget 24 MB); route 6.0 km, splits = RCX gates
obj02 / obj04 / obj06. Not yet run in the game.

## Collision findings (build iterations pilot-01 .. pilot-11)

| Attempt | Collision geometry | Result |
|---|---|---|
| all RCX ground + untextured barriers | 61 k terrain tris | pools 50.1 MB > 32 MB; 737 phantom solids (barrier walls), 190 route hits |
| corridor 60 m, faces with normal Y >= 0.35, rock/wood/metal drawn only | 26 k | finish has no support (the route finishes on flat rock under a bridge) |
| corridor 60 m, slope filter, rock solid | 32 k | 703 phantoms: the slope filter leaves floating rock plateaus without sides |
| corridor 45 m, no slope filter | 32 k | 22 MB; only 55 adaptive holes (rock tangles off the road, bridge) |
| + repair passes | | off-road holes fixed; 18 holes on the bridge deck edges (barriers, overhanging top) |
| + deck slabs, barriers / rails drawn only | 32 k | **ok** |

Course Studio's terrain BSP needs a surface without open walls: open vertical soup (RCX invisible barriers, fences,
bridge barriers, piers) makes neighbouring empty cells solid. Keep collision to the ground near the road.

## Open

* One extra Quick Race category only: Evo 2 and RCX races share it (label "EVO RCX"). Separate per-game categories
  need a second mode in `tools/course_layer.py`.
* Without the barrier walls a car can leave the RCX road where RCX blocked it; the MR limits (45 / 75 m) reset it.
* Previews are the pilot-01 Blender renders (same visuals).

## Set 3 fixes (2026-11-16, owner test of host-rcx-01)

* **Quick Race card showed the previous race's icon** (race 32 selected, icon "31", race 32 loaded). The Quick Race
  screen publishes `Frontend/QuickRace/FlagImageID` itself at 0x47A889 and 0x47B313: frame = race id, +1 from id 10
  (flagsheet frame 10 is no race icon). Retail frame 40 is no race icon either, so the appended icons (from frame 41)
  were one frame off. `course_layer` now calls a small routine there: for race id >= 39 the frame is
  `flag_frame + (id - 39)`, where `flag_frame` is the flagsheet frame count before the course icons
  (`course_frame_base`), and `install_course_resources` checks that every icon lands on that frame.
* **Race titles rendered as "C D"**: the Race Select title font has capital letters only. Titles are upper-cased in
  `course_layer.plan_catalog` (all 30 Evo 2 titles were affected the same way).
* **Atmosphere texture seams on the ground**: with no lighting package for a course, Atmosphere lights an unknown
  texture only as "automatic ground" (renderer `atmosphere_native.hpp` universal_draw: noise stage, opaque texture, no
  alpha test, CCW cull); everything else stays native. The Evo 2 terrain has `noise=True`, the RCX ground had
  `noise=False`, so RCX ground stayed native next to lit draws. Opaque RCX ground (collision corridor and far
  ground) now has `noise=True`; trees, objects and cutout ground stay native as on the Evo 2 tracks.
* **Ground snags (owner screenshots, Clashin Darroch x -854 z -1992, x -833 z -1789, start x 250 z -83)**: offline,
  the three places are clean: no two ground layers within 0.6 m at one point, no shared-edge steps, no route-crossing
  creases (all creases >= 12 deg within 4 m of the route run along the road edge), no BSP hole or solid from the
  ground up to 0.4 m on a 0.25 m grid, no solid 0.3-1.5 m above ground within 12 m of the route nearby; the land
  database covers every triangle by its bounds. Cause not found offline; next is a runtime capture (Observatory
  with `vehicle_manager.py dev-menu on`, collision overlay F11) at the exact place.

## Set 4: ground splat and solid props (pack RCX-05)

* **Ground seams.** RCX `.map` groups with flag 0x8 carry a second texture (+8). The vertex colour alpha blends
  between them (0 = texture1, 255 = texture2; verified against neighbouring groups). The importer now writes
  texture1 as the opaque ground, or texture2 when every alpha is at least 250. Partially blended faces get a ROLE_VISUAL
  overlay with texture2, the per-corner alpha and the baked light. The overlay is lifted 0.02 m and uses material `RCX blend layer`
  (alpha `blend`). The native shader honours vertex alpha (0x57FED5, material +0x22).
  Ground `noise` is back to False: noise ground mixed Atmosphere-lit and native draws (orange and green patches).
* **Solid trees and fences.** These are closed `box_proxy` boxes in the mesh "RCX prop collision" (surface rock).
  - Tree trunks are 0.5 × 3 m, clustered on a 1.5 m grid, within 25 m of the line.
  - Fence panels are near-vertical faces turned into 0.15 m slabs, at most 3 m long with 0.1 m end gaps, within 45 m.
  - Props stay more than 5 m from the dense driving line and never overlap.
  - Boxes near a reported collision spot are dropped in the repair loop.
  - At most 1800 boxes are kept, nearest the route first: 4170 boxes needed 35.7 MB of collision pools against the 32 MB cache.
* Results: Fire Rock was OK after 3 passes, with 31.5 MB of pools. Clashin Darroch was OK after 8 passes, with 29.2 MB.

## Set 5: RCX collision hulls, vertex lighting (pack RCX-06)

* **Hulls.** RCX trees are three NO_COLLIDE planes around the trunk. They are solid in RCX because of untextured
  render-flag 0x2404 geometry: a 0.9 m pyramid on each trunk, closed boxes on woodpiles, and building shells.
  Set 4 dropped these hulls and clustered tree triangles on a 1.5 m grid, which put boxes beside the trees.
  - Each hull connected component now becomes one closed box: the minimum-area oriented rectangle in xz, with the
    height capped 4 m above its base.
  - Components longer than 12 m give their vertical faces to the slab builder instead.
* **Fences.** Vertical Fence-surface faces become xz segments, de-duplicated across both sides and both rails.
  - Each segment is a run of abutting 0.15 m slabs, at most 3 m long, with 0.1 m joints.
  - 0.02 m joints made near-coplanar BSP slivers.
* **Placement rules.**
  - The route gap is measured over the whole outline (3.5 m to the 2 m dense line); reach is 35 m.
  - Boxes are placed nearest first, at most 2400. Rectangle SAT keeps them from overlapping.
  - Repair drops props within 6 m of a reported spot.
* **Lighting.** RCX vertex RGB is baked light: slopes and tree shadows, on shared corners.
  - It is now the vertex colour of every drawn mesh, scaled so the 90th percentile of ground reaches 245.
    The scale is 0.96 on Fire Rock and 1.34 on Clashin Darroch.
  - Course Studio's own bake lit each unwelded RCX face by its face normal, which made the ground faceted.
  - The set 4 blend layer used an unnormalised normal, which made dark and bright triangles.
* **Repair loop.**
  - Route distance now uses the dense line: a 2 m disc between two 10 m route points had removed road ground.
  - New last stages:
    - 1 m discs 3.5 m out;
    - unstack discs, negative radius: only the top of stacked ground layers stays solid (fords);
    - protect points, radius 0: the ground face over a spot is solid again (holes the discs opened at a cliff edge).
  - `--seed build-<stage>.json` resumes from a previous run's discs and dropped props.
* **Results.**
  - Fire Rock: OK after 3 passes, 25.1 MB of pools, 1330 boxes (122 hulls and 1208 fence slabs).
  - Clashin Darroch: OK after 14 passes plus 1 seeded pass, 25.8 MB, 2168 boxes (612 hulls and 1556 fence slabs).
* **Snag capture** (Observatory 2026-11-17 09:46, x -843 z -1445).
  - The wheels sit 0 to 13 mm above the land.
  - The terrain is smooth.
  - BSP probes at 0.02 to 1 m above the ground and 0.1 m below it are clean at all four reported spots.
  - It is not geometry. A model-cache hitch is suspected (Fire Rock pools were 31.5 of 32 MB).
