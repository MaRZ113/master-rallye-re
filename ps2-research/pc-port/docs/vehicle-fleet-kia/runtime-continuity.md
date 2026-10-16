# Kia continuity runtime A/B

Kia CAR, FPS, brake glow, OFF lamp reflection and PS2 wheels were user confirmed on the previous capture DLL after the missing wheel asset was installed. This DLL adds exact Kia native damage correspondence and 21 source-verified native reflective OFF profiles. Damage continuity and the additional families need game validation.

Close the game; manually replace only d3d8.dll. Keep the existing PS2Vehicles assets (including KIASPORTAGE-WHEEL-FLEET.ps2model) and successful COMPLETE/grass/water/MSAA/glow settings.

```ini
[PS2Port]
RacePS2ModelMode=1
RacePS2FleetMode=1
RacePS2WheelMode=1
RacePS2ModelAssetDirectory=PS2Vehicles
RacePS2FleetCapture=1
RacePS2FleetDamageCapture=0
ReflectionMode=4
```

In one fresh KiaSportage race: F10 healthy; drive/steer and brake; collide and F10; collide again and F10. Inspect chassis, helmets, front/rear lamps and all wheel poses. Then Reset the window with MSAA4x and F10 again; restart the race. Exit normally to flush JSONL. Expected: PS2 chassis and materials remain through the measured damage branches, with no duplicate people/body, detached parts, lost lamp reflection or FPS regression. Compare Stock with RacePS2FleetMode=0 in a separate run.

Bounded F10 sidecar events: fleet_car_private_submission includes frame/family/instance/packet/asset SHA/source_records/private_damage_tree/kia_damage_map_complete/world_le_hex/draw_hresult/restore_hresult. Rejection is fleet_car_certificate_failure plus exact reason. Draw ordinals are diagnostic only. HRESULTs should be zero; private damaged Kia should report both damage flags true.

Cold entry into an already damaged owner without a healthy reference, changed ambiguous UV-identical parts, unproved wheel trees and other families' damage branches retain Stock. No damage/physics state is changed. New 21-family OFF profiles affect only exact original native OFF geometry, not all tail lights; private CAR meshes retain their own source material transaction.
