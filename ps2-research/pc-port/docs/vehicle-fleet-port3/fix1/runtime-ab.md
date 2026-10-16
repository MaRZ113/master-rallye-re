# PORT3 fix1: native damage reflections and three conditional OFF meshes

Finish any ongoing tests with the old kit first. Then manually replace d3d8.dll
and merge the three PS2Vehicles files from runtime-kit.zip. Keep all existing
CAR, wheel, COMPLETE and GXI files. No automatic installation is performed.

Keep RacePS2FleetMode=1, RacePS2ModelMode=1, RacePS2WheelMode=1,
ReflectionMode=4, ReflectionCoverage=1, BrakeGlowMode=1,
RacePS2ModelAssetDirectory=PS2Vehicles and RacePS2FleetCapture=1.
RacePS2FleetDamageCapture may remain0; no additional full raw captures needed.

1. NewRav: fresh race, F10 with brake released; drive and damage the car, then
   F10 again with brake released. Inspect the formerly flat OFF lamp region.
2. Bruno and Mattserati: one brake-released F10 each. Apply brake and release
   it to verify ON_CORE and glow remain separate. Optional damaged OFF F10.
3. In one damaged NewRav/Forester/Astero race, inspect main-body reflections
   from two camera angles. Restart, then Reset/MSAA4 as a control.

Expected new events: fleet_private_off_submission for the targeted three,
and fleet_native_damage_reflection for exact wholly reflective native records.
Both must have draw_hresult=0 and restore_hresult=0. Rejections retain Stock
and name the private OFF gate in fleet_lamp_continuity. Damage reflection events
explicitly say native_damaged_geometry_preserved=true, ps2_body_replacement=false.

The 22 unsupported complete PS2 deformation maps remain unsupported. This kit
does NOT claim to keep their PS2 chassis after damage; it restores Mode4 only
on source-verified wholly reflective native fallback records. Mixed records,
glass, rubber and unverified branches remain Stock. X-Trail/Kia/UFO retain their
existing full damage routes; UFO still has no wheels.

Report which car/surface changed, brake state, healthy/private damaged state and
F10 frame numbers. New OFF rendering and damaged native reflection continuity
remain runtime-pending until those captures and visual observations arrive.
No global lamp brightness/color correction is included.
