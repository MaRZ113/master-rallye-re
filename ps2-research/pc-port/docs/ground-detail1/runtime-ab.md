# GROUND-DETAIL1 runtime A/B

Install: replace `d3d8.dll`, copy `PS2Grass/PS2GroundNoise.gxi` next to the other PS2Grass files,
and in `PS2Port.ini` set

```
GroundDetail=1
GroundDetailAsset=PS2Grass/PS2GroundNoise.gxi
PS2Color=0
```

(PS2Color would darken the ground twice; compare it separately if wanted.)

1. Turkey2 / France1 standing start, `GroundDetail=0` and `=1`, same view as the PS2 dumps.
2. Expected with 1: dirt road/grass ground about 10 % darker, fine dark speckle instead of the PC
   light/dark noise; car, sky, banners, objects unchanged.
3. `MRRRenderer/logs/session-*.jsonl` must show `{"type":"ps2_ground_detail","reason":"ground_detail_applied"}`.
   Any other reason means Stock ground; the most likely ones are `pc_noise_format_not_32bit` or
   `pc_noise_content_mismatch` (graphics quality converting textures) — send the log.
4. Grass and shrubs still visible; Alt-Tab/resolution change keeps working.
