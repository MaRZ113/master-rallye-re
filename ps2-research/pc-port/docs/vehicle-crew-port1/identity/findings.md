# X-Trail STATIC crew: exact native suppression ownership

The driver and codriver are static as confirmed by the user. Earlier documentation describing native character animation was unsupported and is superseded for this scope. No animation, skinning, skeleton or motion-system investigation was performed.

## Exact topology result

Original protected PC Xtrail/car.dx SHA-256: `e334085754f81d20d237a70e653b533344771e6409468e2e09252e380b3d063f`. `components.py` reuses the read-only Course SDK parser, verifies that SHA, joins only exactly equal original float32 XYZ vertices, and emits compact bounds, face hashes and component membership, never original model bytes. No tolerance or runtime bounding-box deletion rule is used.

| PC record | PC faces | Ownership | Replacement source |
|---|---:|---|---|
|16|29|negative-X occupant face; dnissanslave7|PS2 CAR root0 component123, 48 faces|
|17 faces0..37|38|two pairs of helmet/chin/visor inserts, black|PS2 CAR root7 components6/10, 48 faces|
|17 faces38..41|4|verified unrelated trim|preserve existing root15/root18 trim replacement|
|18|29|positive-X occupant face; dnissandad|PS2 CAR root0 component222, 48 faces|
|19|148|two helmet shells; xhelmet32/whitepaint|PS2 CAR root8, 148 faces|
|20|200|two occupant bodies, whitesuit32|PS2 CAR root0 components71/73, 252 faces|

All 38 PC17 native faces are crew geometry. They form four exact connected components:12+7 faces for the negative-X head and12+7 for the positive-X head. Each12-face component shares four exact vertices with the corresponding face record16/18 and six with helmet19. Each7-face component shares three face vertices and two helmet vertices. None shares exact body20 vertices. These topology seams, paired structure and head-only geometry independently distinguish them from seats, dashboard and interior trim. PC17 last four faces are two disconnected components already independently matched to PS2 trim. `runtime_hash_categories` retains each original unsigned-triangle SHA and multiplicity; validate the complete42-face multiset before choosing crew38 versus trim4. Reject missing, duplicate, unknown or changed faces.

Restored PS2 crew totals544 faces:396 previously excluded bodies/faces/inserts plus148 helmet faces. Seats/root7 component0 (six faces), dashboard, steering wheel and underbody remain in the accepted interior path. PS2 side assignment is not inferred from driver/codriver names: negative-X PC16 maps to negative-X PS2 component123; positive-X PC18 maps to component222. No fitted offset is added.

## Current-frame transform observation

Latest supplied F10 `frame-30252-d1-00134895.jsonl`, capture SHA in `current-frame-observation.json`, uses previous working DLL9ba0e326...85f0. All five crew source records were present, with native split PC17 38-face submission plus its original42-face intercepted record, giving six recorded observations. Every observation has bit-exactly equal current WORLD, including the two face draws, helmet, body and visor parts. Native buffers/generations and source index relocation+7461 agree with the accepted CAR layout. This is current captured evidence; historical draw indices and pointer values are recorded observations only.

The new implementation must still perform the existing exact current queue owner, instance↔packet, CAR model hierarchy, geometry digest, buffer generation/revision and chassis WORLD checks at interception. F10 layout association alone is not a safe persistent classifier. Match material and geometry as an owned source record, never texture-only or primitive-count-only. Conditional lamps/glow/windows are outside these records.

## Validation

`python -m unittest discover -s ps2-research/pc-port/docs/vehicle-crew-port1/identity -v`:4/4 PASS. Tests cover exact head/helmet seam closure, four trim faces retained, missing/extra/foreign hash rejection, side mapping,544PS2 versus444native crew faces, and current frame WORLD coherence. No renderer or assets were changed in this independent pass. Live acceptance of the new crew replacement remains pending.
