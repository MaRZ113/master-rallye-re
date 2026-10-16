# Kia wheel/OFF validation and required damage trio

Close the game. Manually install this d3d8.dll and copy the ONE new file assets/KIASPORTAGE-WHEEL-FLEET.ps2model into the existing PS2Vehicles directory. Retain all other assets/settings. Ensure:

```ini
RacePS2ModelMode=1
RacePS2FleetMode=1
RacePS2WheelMode=1
RacePS2ModelAssetDirectory=PS2Vehicles
RacePS2FleetCapture=1
RacePS2FleetDamageCapture=1
ReflectionMode=4
```

Do not change successful COMPLETE/grass/water/MSAA4x/glow settings. Use ONE fresh KiaSportage practice race, same process; no restart/car switch/windowReset before the three F10s:

1. BEFORE any impact: allow wheel warmup, drive/steer and inspect authentic wheel shape/rim/tread. Inspect rear lamps with brake OFF. FirstF10 healthy.
2. Damage body once, release brake, secondF10. The current build still intentionally uses Stock damage fallback; this file is required to prove the replacement delta map safely.
3. Damage again, release brake, thirdF10. Do not substitute a menu F10 or a new race.

After the trio, optional: hold/release brake and inspect separate glow; Reset window with existingMSAA4x, inspect menu/FPS, then exit normally. Report wheel appearance/steering/tread/reflection, OFFlamp reflection and FPS. Exactly three `fleet-damage-PID-dDEVICE-fFRAME.bin` files should be in the ordinary MRRRenderer/logs. Additional F10s do not create more rawdamage files after the cap.

Expected bounded F10metadata: fleet_ps2_wheel_submission, four current wheel slots, each252privatefaces and successful draw/restore; fleet_car_private_submission for healthyKia; fleet_glow_identity onbrake. There must be no doubled wheels or frozen steering. Missing source/material/device capabilities remain Stock. The native game continues all physics/damage.

Turn RacePS2FleetDamageCapture=0 after successful trio collection. Assets are unchanged except the newKiawheel file. Do not test the whole fleet until this current contract is accepted.
