# Kia complete-model FIX2 test

Close the game and manually replace ONLY d3d8.dll. Assets and ini remain unchanged, including RacePS2FleetCapture=1, RacePS2FleetMode=1, ReflectionMode=4 and BrakeGlowMode=1.

1. Start a fresh one-car KiaSportage practice race. Before any impact, F10 at rest. Inspect front geometry, cabin/helmets and both sides; drive and steer, then F10 again. Expected: genuine PS2 CAR body and static crew, no duplicate PC body/people. Wheels are intentionally still native PC.
2. Hold brake and F10. Confirm the already-working glow and FPS remain stable. Check OFF lamp reflection separately; do not confuse it with additive glow.
3. Reset window with existing MSAA4x and recheck. Collide once and F10: unsupported Kia damage still intentionally selects Stock, without duplicate chassis.
4. Exit normally. Report front/helmets, FPS and glow. The race-fleet file should contain fleet_car_private_submission with familyKiaSportage,26 sources, original source-backed asset SHA and successful draw/restore HRESULTs. If absent, fleet_car_certificate_failure contains the exact gate/masks. No fleet-wide retesting needed yet.
