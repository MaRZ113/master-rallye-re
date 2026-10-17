# DIAG-REFLECTION1 runtime steps

Replace `d3d8.dll` only.

## A. Reflection orientation (please do this first)

1. `PS2Port.ini`: `ReflectionDebug=1`, keep `Reflection=4`, `RaceFleet=1`, `PS2Output=0`, `PS2MotionBlur=0`.
2. Turkey, SeatBuggy, chase camera, standing or slow, car seen from behind — same view as the PS2
   dump. Take 1–2 screenshots (also one from a side if easy).
3. Set `ReflectionDebug=0` again afterwards.

Expected if PC matches PS2: like `ps2-env-quadrant-reference.png` — left flank blue/red, right
flank yellow/cyan, roof/upper rear blue/cyan, bumper/lower rear red/yellow.

## B. Motion blur

`PS2MotionBlur=0.195` (PS2 chase camera). Drive fast: a light trail on the ground/fences like on
PS2; menus and pause unaffected. Log: `{"type":"ps2_motion_blur","reason":"blended",...}`.
Try `0` vs `0.195`, and tell if you want it stronger/weaker.
