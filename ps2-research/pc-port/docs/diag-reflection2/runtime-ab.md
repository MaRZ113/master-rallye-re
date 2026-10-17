# DIAG-REFLECTION2 runtime A/B

Replace only `d3d8.dll`. In `PS2Port.ini` remove any old `PS2MotionBlur=` duplicates, then:

1. Env view: `ReflectionDebug=2`, `Reflection=4`, `RaceFleet=1`, `PS2Output=0`, `PS2MotionBlur=0`.
   Turkey, SeatBuggy, chase camera, same cloud set as the PS2 shot if possible. Screenshot the
   256x256 square at the top centre (car on screen too). Put `ReflectionDebug=0` back afterwards.
2. Blur: `PS2MotionBlur=1`, `PS2MotionBlurStrength=0.195`. Expect `ps2_motion_blur` `blended` with
   `frame_weight` ~0.43 at ~100 fps (0.195 at 50 fps).
