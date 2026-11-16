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
