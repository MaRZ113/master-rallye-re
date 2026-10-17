# PS2-COLOR1 runtime A/B

Install: replace `d3d8.dll` only (assets unchanged from LIGHT2.1) and add to `PS2Port.ini`:

```
PS2Color=1
PS2ColorCurve=0.426,0.384,0.364
```

1. Same course/angle as a PS2 shot with `PS2Color=0` and `=1` (F12 screenshots or ShareX).
2. Check: sky/rock/road/banners closer to PS2; note the car (expected: somewhat darker than PS2).
3. `MRRRenderer/logs/session-*.jsonl` must contain `{"type":"ps2_color","reason":"graded",...}`.
   Any other reason (e.g. `fixed_function_caps_unsupported`, `copyrects_failed`) means the pass is
   off and the frame is untouched.
4. Alt-Tab / resolution change (device Reset) must keep working; after it the log shows `graded` again.
5. Optional tuning: lower values (e.g. `0.3,0.3,0.3`) soften the effect; `0,0,0` = no change.
