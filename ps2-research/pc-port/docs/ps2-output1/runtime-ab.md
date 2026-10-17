# PS2-OUTPUT1 runtime A/B

Install: replace `d3d8.dll` only, then in `PS2Port.ini`:

```
PS2Output=1
```

1. Same view with `PS2Output=0` and `=1` (race and Vehicle Select): expected a soft picture close to
   PCSX2 native resolution — highlights and white banners bleed slightly into dark neighbours, HUD
   softened too.
2. `MRRRenderer/logs/session-*.jsonl`: `{"type":"ps2_output","reason":"filtered",...,"draws":3 or 4}`.
   Other reasons (`private_target_allocation_failed` at very large windows, `msaa_resolve_copy_failed`)
   mean the filter is off for that device — send the log.
3. Frame time: note FPS with 0 and 1.
4. Alt-Tab / resolution change keeps working (targets are recreated).
