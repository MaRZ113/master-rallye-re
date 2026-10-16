# Kia FIX1 runtime test

Manually replace only d3d8.dll from this release while the game is closed. Assets are unchanged. Keep the existing successful ini, including BrakeGlowMode=1, ReflectionMode=4, RacePS2FleetMode=1, RacePS2ModelMode=1, RacePS2FleetCapture=1. Do not change damage, assets or lighting.

1. Restart, select KiaSportage and enter one-car practice. Before any collision, inspect FPS; F10 at rest and after driving/steering.
2. Hold brake until a new rendered frame, F10 while still holding it, then release. Inspect glow separately from OFF/ON lamp texture.
3. Collide once and F10. New-family unsupported damage may deliberately show full Stock chassis; check for duplicates. Do not classify this as a new damage-aware CAR implementation.
4. Exit normally and report FPS before collision, body appearance and glow. Existing race-fleet-PID-d1-fFRAME.jsonl now contains exact certificate failure and compact-glow identity details even if session one-shot diagnostics are exhausted.

If healthy Kia remains Stock, the new certificate row should identify the one remaining gate; do not bypass it. No need to test the whole fleet yet.
