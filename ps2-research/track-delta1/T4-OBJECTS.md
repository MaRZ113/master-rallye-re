# T4b: Turkey3 house and caravans as loose PC models with collision

Script `ps2_course_objects.py` (uses `ps2_obj_to_dx.py` and `tag100_patch.py`); mesh selection by `mesh_pc_presence.py` (share of a PS2 mesh's vertices that exist in the PC course DX, output `turkey3-meshes-low-pc-share.json`). Output (untracked): `D:\Game\Master Rallye\research-output\t4-objects`.
T4a result (user, 2026-10-19): the house draws with PS2 lighting and blocks the car correctly after the plane-code fix (`T4-HOUSE1.md`).

## Objects
| Model | Instances (Egg, mesh, centroid) | Texture | Notes |
|---|---|---|---|
| house1 | ps2_house11 (root.0.65.1) 1971.4, 39.1, -113.0 | brickhouse 64x64 | as T4a |
| caravan | ps2_caravan1 (root.0.9.7), ps2_caravan2 (root.0.56.1) | caravan 64x64 | second instance is a rigid copy, residual 0.0002, yaw about 180 degrees with a small tilt |
| redcaravan | ps2_redcaravan1..4 (root.0.0.1, 0.8.15, 0.56.2, 0.65.9) | newtex 64x64 | rigid copies, residual below 0.001 |
One DX per model (template `haybaletest.dx`, same texture-slot rule as T4a), one Egg per instance with the fitted rotation (Egg rows = columns of the fitted R, row-vector convention) and the centroid as translation, one collision brush per instance (convex hull of the instance, plane code taken from the ground plane below it).
Instance pairing: the vertex order of the instances differs, so the rotation is fitted by distance-from-centroid pairing followed by nearest-neighbour refinement (set residual in the report).

## Collision cost
Hull planes: house 33 (82 cells), caravans 48 and 53, red caravans 96, 130, 111, 100 (3 to 262 cells). Tag100 tree 5.41 MB to 9.18 MB (the patched DX is 11,918,469 bytes), nodes 235,089 to 316,083, invariants hold. The hulls are convex fills (an open door or awning is solid), not the PS2 polygon collision.

## Not converted
CARAVAN_ALPHA (2 meshes x 16 vertices, alpha-test material: the DX material flags for alpha test are not understood yet), huts, shrubs, boats, fences (PLACEMENT_DIFFERS: the PC course has these models elsewhere, adding PS2 placements would duplicate them, moving PC ones needs course-DX edits), puddles (own overlay channel), tyres (DIFFERENT_MATERIAL).

## Run
Copy from `research-output\t4-objects` into the test install keeping paths: `DataGx\Misc\PS2Port` (3 model folders), `DataScene\RaceTest\Turkey3.xml`, `DataGx\Course\Turkey3\turkey3.dx` (replaces the house-only one). Teleport points (ground + 1.5, 14 units from each object):
```
Point1=1985.4,34.9,-113.0,0   ; house
Point2=2379.1,32.9,-854.0,0   ; caravan 1
Point3=3405.2,52.5,-711.0,0   ; caravan 2
Point4=3007.7,44.6,-435.2,0   ; red caravan 1
Point5=2369.6,31.4,-843.6,0   ; red caravan 2
Point6=3414.4,52.8,-716.2,0   ; red caravan 3
Point7=1955.9,35.3,-160.6,0   ; red caravan 4
```
Check: each object is drawn at the right place and orientation (compare with PS2), lit like its surroundings, solid, no crash on load or after three race restarts. Remove `PS2Port`, the XML and `DataGx\Course` to return to stock.

## Update 1 (user run, 2026-10-19)
Result: all objects load, all have collision. Two findings.
1. Textures are mapped upside down. The GXI rows are top-down (`BRICKHOUSE-TGA` has the door and windows in the lower half), the PC DXT is stored bottom-up (`dxt.py` flips rows for PNG), so copying the rows unchanged turned the images over. The converters now flip V by default (`--no-flip-v` restores the old behaviour); to be confirmed by the next run.
2. Red caravans 1 and 4 stood crooked: their lowest vertices are +1.35 and -3.33 units away from the PC ground (the other instances are within 0.6). The PS2 terrain differs from the PC terrain at those two places (the PS2 screenshot of the house shows a fence and a different ground texture around it, the registry lists 1,242 non-exact ground triangles). The converter now shifts an instance vertically when its lowest vertices are more than 0.75 away from the PC ground (red caravan 1 by -1.35, red caravan 4 by +3.33; collision brush shifted the same). This hides the symptom; the real fix is the PS2 terrain and fence placements, next step.
New teleport points are unchanged except the two shifted objects (about 1 to 3 units in height only).
