# X-Trail race A/B

Close the game before manually installing the phase DLL. Keep all existing private reflection/grass/frontend assets and configuration. Copy local .assets/vehicles/XTRAIL-CAR.ps2model beside the active root PS2Port.ini. No proprietary assets are included in the ZIP.

Add to existing [PS2Port]:
```ini
RacePS2ModelMode=0
RacePS2ModelVersion=1
RacePS2ModelAsset=XTRAIL-CAR.ps2model
RacePS2ModelDiagnostics=1
ReflectionMode=4
```

Record native X-Trail in a race, then restart the game with RacePS2ModelMode=1 and use the same car/course/camera. After one complete warmup frame, inspect body/hood/arches/bumpers/decal from front, side and rear. Drive, steer both ways and check wheel rolling/suspension. Wheels and physics remain native PC. Drivers, black trim, headlight glass, brake off/on/glow and conditional windows remain on their existing native paths. This is an authentic PS2 opaque-chassis pilot, not a full replacement of every CAR branch.

Expected bounded logs: ps2_race_model_warmup source_records_verified13; ps2_race_model_replacement verified_source_records13/current_owner_join true/private_faces from subset.json/draw_hresult0/restore_hresult0; ps2_race_model_suppression original_records_suppressed13. Gate records identify Stock fallback. Source record numbers are provenance only; actual admission uses current owner, complete geometry hashes, resource generations/revisions and WORLD.

Test braking, damage (changed source geometry must use native Stock), race restart, exit/reload and actual window Reset with MSAA4x. Compare rotation/steering and check duplicated/missing panels, floating body parts, detached wheels, nearby cars or HUD changes. Save F10 on intact moving chassis and after damage/Reset. No success is claimed until the new DLL has runtime evidence. If a gate blocks, retain the session; do not widen matching.
