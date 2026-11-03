# COURSE-ALIVE3 game test

## Install

1. A test installation with a PS2 course package of a prop course (`research-output\course-port-36\<Course>`: ItalyS1,
   Italy2, ItalyS4, ItalyW1, ItalyW2, Turkey1, Turkey3, TurkeyM, TurkeyS2Flip). The props need the PS2 terrain; on a stock
   PC course they stay off (`stock_pc_course_retail_dx`).
2. The kit `d3d8.dll` next to `MRallye.exe`, `PS2RigidProps.ps2rgd` in the PS2 asset folder (`GrassAssetDirectory`, or
   set `RigidPropsAsset`).
3. PS2Port.ini, `[PS2Port]`:

```ini
RigidProps=1
RigidPropsDiagnostics=1
Diagnostics=1
```

## What to check (ItalyS1 first: 14 bales near the start)

| Step | Expected |
|---|---|
| Race start | hay bales stand on the ground at the PS2 places (round bales lying on their side, axis across); no bale floats or sinks |
| Drive past without touching | bales do not move (PS2: proximity does not wake a settled prop) |
| Drive into a bale at speed | the bale is thrown ahead, rolls and tumbles, comes to rest on the ground within a few seconds; a second bale hit by the first one moves too |
| Gentle push | the bale rolls slowly along the car |
| Pause menu | props freeze, continue after resume |
| Restart race | props back at their start places |
| Turkey1 / Turkey3 | tumbleweeds (see-through shrub balls, a little above the ground as on PS2) fly away light when hit |
| Collision overlay (`CollisionDebug=1`, F9 car hulls) | the car hull touching the bale is where the bale reacts |

Known differences: the car is not slowed down by a bale (the proxy does not write the vehicle physics); no prop
shadows; props pass through BSP-only colliders (posts, banners).

## Session log records

`ps2_rigid_props_config` (asset), `ps2_rigid_props_course` (course guard, `terrain`, `terrain_records`, `terrain_ms`),
`ps2_rigid_props_draw` (first draw: draws, triangles, cars, `car_reason`, `missing_hulls`), `ps2_rigid_props_state`
(every 150 ticks: per prop state asleep/active/far, near, wakes, lift, position, speed; contacts and car contacts of the
last half step). Please send the session log with the observations.

## Round 2 (mass, PS2 shading, shadow)

| Step | Expected |
|---|---|
| Hit a hay bale at speed | the car loses speed noticeably (a 500 kg bale takes about a quarter to a third of the speed); a tumbleweed changes nothing |
| Look at a bale | darker, straw-coloured (texture at 0.45, the PS2 `dull` gray) with a faint warm sheen that moves with the camera |
| Bale on the ground | a soft dark blob under it, on the ground only (not on water), following the bale when it rolls; none on Italy2 (its bales are authored without shadow) |
| Distance | props and shadows fade into the course fog like the course |

Log: `ps2_rigid_props_car_impulse` (frame, coupled cars, velocity change) and `fog_states` / `coupled_cars` in the draw
record. `RigidPropsCarImpulse=0` switches the mass off for an A/B.
