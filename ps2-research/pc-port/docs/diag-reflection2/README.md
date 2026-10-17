# DIAG-REFLECTION2 — env target view + PS2MotionBlur keys/time scale

## ReflectionDebug=1 result (user screenshots, Turkey, SeatBuggy, 2026-10-17)

Rear, front, side and top-down shots: left flank blue/red, right flank cyan/yellow, roof/upper
blue/cyan, lower bumper red/yellow — the same layout as `ps2-env-quadrant-reference.png`.
**The PC env UV/orientation equals the PS2 one.** The framebuffer term is drawn flipped
(`reflection_capture_quad(...,true,...)`: target top = frame bottom = ground), as on PS2.
So the "chrome on PC / metal on PS2" difference is in the *content* of the 64x64 target at runtime.
The PS2 target is known from the SW dump (findings section 9: top rows warm 35..51/30..43/19..26,
bottom rows bluish 64..67/72..75/80..81); the PC target needs a runtime view.

## ReflectionDebug=2 (diagnostic)

Normal reflection, plus the last composed PC 64x64 env target drawn unblended, point-sampled, 4x
(256x256) at the top centre of the screen before Present (after PS2Color/PS2Output/blur).
Screenshot it next to the PS2 values above.

## PS2MotionBlur

* `PS2MotionBlur=0/1` switches it; `PS2MotionBlurStrength` (default 0.195 = PS2 chase camera,
  GS dump FIX 103; 0..0.9, unparsable -> default).
* PS2 SLES-50906 renders a full frame every 50 Hz vsync (all four GS dumps: equal GIF traffic per
  vsync), so b is the weight per 20 ms. PC frame weight = b^(dt*50) (dt = time since the previous
  Present, QPC); dt > 0.1 s restarts the history. At ~97 fps (user's session) weight 0.43 per frame.
* First run used `PS2MotionBlur=1` + a duplicate `PS2MotionBlur=0.010`: GetPrivateProfileString takes
  the first key, so the old parser clamped 1 to 0.9 (log `"blur":0.900`) — the "too strong, viscous" trail.
* Log: `{"type":"ps2_motion_blur","reason":"blended",...,"frame_weight":..,"dt_ms":..}`.
