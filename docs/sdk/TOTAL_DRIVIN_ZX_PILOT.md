# Total Drivin' Citroen ZX Rallye Raid pilot (2026-11-13)

Owner: the ZX Rallye Raid is `DAKAR1` or `DAKAR2` (same body, different livery). Both are built.
**Owner decision 2026-11-13: roster uses DAKAR1 (canonical red livery).**

```
py -3 -c "from master_rallye.source_adapters.total_drivin import create_scene; create_scene(<lvl10_obj.bin>, <lvl10_1.bin>, <scene out>, 'ZX_DAKAR1', donor_wheel=<retail Pajero>/wheel.dx, donor_textures=<retail Pajero>, scale=2.385/4.28)"
py -3 -c "from master_rallye.td_classic_pilot import create_pilot; create_pilot(<scene.json>, 'ZX_DAKAR1', <retail Data.sma 03c2b52d>, <Data.sma_unpacked>, <out>)"
```

Inputs are the decompressed LEVELS.DAT chunks of level 10 (ISLAND3): object chunk and VRAM chunk
(`source-formats/total-drivin/tools/td_lzw.py` on branch research/source-formats).

* `source_adapters/total_drivin.py`: car BODY -> Universal Vehicle Scene. Material entry types:
  0x0a glasshouse, 1 body colour (car header RGB 0x8C8C8C), 2 trim, 8 textured, 0x10 two-state
  textured (rear lamps; first buffer state = off). Textures: `page_code >> 3` = 4-bit page on the
  y = 256 VRAM row, standard CLUT word, E2 window crop (UV wraps inside the window).
  Face record normals are not consistently outward, so polygons are oriented away from the bbox centre.
* Wheels: Total Drivin' wheel nodes are parameter records (position, radius 54), not meshes; retail
  Pajero wheels at the record positions (MR authoring). Body scaled x0.557 to the Pajero wheelbase.
* `td_classic_pilot.py` reuses `txr3_classic_pilot.create_pilot` (generalised: role function,
  long axis, labels). Author project class T2 (the author SDK accepts T1/T2 only); target T5 RAID.
* Result: 4.01 x 1.82 x 0.90 m body, 3 glass panes, brake from the type 0x10 material,
  native states PASS. Gameplay not tested; not in the roster.
