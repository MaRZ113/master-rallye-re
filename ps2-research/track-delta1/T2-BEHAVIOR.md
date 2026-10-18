# T2: static behaviour comparison, PS2 solid exterior vs PC OFF COURSE (Turkey3)

Script `gcoll_behavior.py` (output `gcoll-behavior-probes.json`), numbers from `T2-SOLID-SHELL.md`, and the first user runtime probes.

## What each platform does at the corridor edge
- PC: `LeftOuterLimit` / `RightOuterLimit` lists drive the OFF COURSE message and the stock reset. No collision stops the car before it.
- PS2: the BSP is solid outside the corridor (all 36 courses), and the lists are `LeftOuterLimit2` / `RightOuterLimit2`. The runtime softer reset still exists.

## Is the PS2 wall usually reached before OFF COURSE?
Marching from the RaceLine to each limit marker (table in `T2-SOLID-SHELL.md`), wall position relative to the limit line:
| Set | Markers with a wall | Wall beyond limit by >10 | Wall within 10 | Wall inside limit by >10 |
|---|---:|---:|---:|---:|
| PC left | 104 | 71 (68%) | 10 | 23 (22%) |
| PC right | 122 | 85 (70%) | 18 | 19 (16%) |
| PS2 left (Limit2) | 224 | 106 (47%) | 17 | 101 (45%) |
| PS2 right (Limit2) | 202 | 107 (53%) | 54 | 41 (20%) |
Reading: against the PC lists the wall lies beyond OFF COURSE at about 70% of the border, so on PC the car is reset before it could touch a PS2-style wall. At about 16 to 22% of markers the wall is inside the limit and a PS2 car would be stopped first. Against the PS2 lists the inside share is larger (20 to 45%), so on PS2 the wall is often the first thing that happens.

## The probe points (heading = degrees, atan2(dx, dz); distances to the first PS2 solid, 2-unit steps, limited to 40)
- Point 3 (probe 1 near wall): blocked at 8 to 36 units for headings 0 to 132 (a pocket on the right of the road). Consistent with the user seeing the car stop (`3ps.png`).
- Point 6 (probe 2 near wall): blocked at 8 to 34 units for headings 154 to 264, and the route heading is 270. The wall is ahead and to the left, a PS2 reset there is plausible.
- Point 9 (probe 3 near wall): blocked at 6 to 26 units for headings 242 to 264 and 286 to 44; the route heading is 205 and is open. The car in `9ps.png` ran WRONG WAY, so it probably travelled along the road, not into the wall; the probe does not contradict the data.
- Points 1, 2, 4, 5 (road and controls): no wall within 40 in any heading, matching the free controls.
The model therefore predicted the blocked and open headings of every point the user visited; what is still missing is a drive in the blocked headings of points 6 and 9.

## Verdict for the port
- Behaviour difference is real but local: PC OFF COURSE covers about 70% of the border, the PS2 wall changes the result only where it stands inside the limit.
- Porting means changing PC collision (a tag100 writer that does not exist, and risk of trapping the car), for a difference the player mostly sees as a hard stop instead of a reset.
- Decision (registry element `TURKEY3:collision:solid_exterior`): not ported now, physics and logic channels NONE, evidence USER_RUNTIME_OBSERVATION, PCSX2 verification PERFORMED. Revisit only together with a tag100 writer, or if repeat probes on points 6 and 9 along the blocked headings confirm broader blocking.

## Limit lists: PS2 border sits farther out (`limits_compare.py`, `limits-compare-turkey3.json`)
Median distance from the RaceLine: PS2 LeftOuterLimit2 88 (PC outer 61, PC inner 31), PS2 RightOuterLimit2 59 (PC outer 48, PC inner 29). Each PS2 list lies on the same side as the PC outer list of that side (median polyline distance 13 left, 6.8 right) but with a wide spread (90th percentile 75 and 37). So PS2 uses a more permissive border, matching the user's observation that the PS2 reset is softer.
Open: PC `LimitState` rules for the four lists are not reversed, and adopting the PS2 lists on PC would be a gameplay change that needs a decision (registry element `TURKEY3:trigger:marker_lists` stays UNDECIDED).
