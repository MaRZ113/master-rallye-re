# TXR3 Isuzu VehiCROSS — MR Classic pilot (2026-11-13)

Status: **native build PASS offline; not in a roster yet; gameplay NOT TESTED.**

Source: Tokyo Xtreme Racer 3 / Shutokou Battle 01 (PS2, SLPM-65308), BUILD.DAT entry 355
(car table record 53, `ISUZU VehiCROSS UGS250`). Format research lives on
`research/source-formats` (`source-formats/txr3/`).

## Pipeline

```
py -3 -c "from master_rallye.source_adapters.txr3 import create_scene; create_scene(<entry 355>, <scene out>, donor_wheel=<retail Pajero>/wheel.dx, donor_textures=<retail Pajero>, scale=2.385/2.327)"
py -3 -c "from master_rallye.txr3_classic_pilot import create_pilot; create_pilot(<scene.json>, 'VEHICROSS', <retail Data.sma 03c2b52d>, <Data.sma_unpacked>, <out>)"
```

* `source_adapters/txr3.py`: TXR3 container -> Universal Vehicle Scene. Untextured TXR3
  materials (header byte0 without 0x20) become 2x2 solid textures from the material diffuse;
  flare sprites (TIM 5/8/16/20/35/49/55) and the drop-shadow material (70) are excluded.
  Source frame +X front, +Z left, mirrored; normalization `(-z, y, -x)` (det -1).
* TXR3 keeps wheels in a separate library (not decoded), so the scene carries **retail
  Pajero wheel.dx** meshes as explicit MR authoring on hubs at the fitted arch centres
  (front 1.135, rear -1.192, y 0.259; wheelbase 2.327 m = real 2330 mm).
* `txr3_classic_pilot.py`: Dakar 2 MR Classic policy (source diffuse, stock MR material by
  role). Body scaled x1.025 to the Pajero wheelbase, Pajero track. Glass (material 1) split
  into front/rear/left/right breakable panes; brake = tail lamps (TIM 43) + roof stop (TIM 39).

## Result

Length 4.23 m, width 2.00 m (mirrors), height 1.51 m, wheel radius 0.391 m.
Native states: `PASS_SOURCE_OFF_STATE_EQUIVALENCE`, panes 78/60/55/56 triangles,
collision = affine fit of the Pajero hull on the paint draws. Author + Workshop projects
are generated (`CarID 29` workshop default).

## Known issues

* Dark speckle on the front wing/cladding: atlas pixels with alpha 0 flattened to opaque.
* Lower cladding colour, interior and underbody are flat colours (TXR3 untextured materials).
* No roster record yet: needs the V-CAP registry rebuild (36 records) and the Roster V4
  transform; T1 placement proposed.

## Look fixes (2026-11-13)

* **CLUT order.** TXR3 stores the 8-bit body atlas (TIM 0) CLUT in linear order. The standard
  CSM1 unswizzle scrambled it into dithered speckle (the "dark front wing"). `tim2.read(...,
  csm1_unswizzle=False)` is used for TXR3; the atlas then has clean gradients.
* **Material tint.** The game modulates the shared atlas by the material diffuse: TIM 0 is the
  painted body at 0.9 and the unpainted lower cladding at 0.5 (also TIM 9 hood insert, TIM 11/36
  bumpers, TIM 42 mirrors, TIM 38 roof rails). MR has no per-material tint, so the adapter bakes
  `diffuse / 0.9` (clamped to 1) into a per-material texture copy (`tim-NNN-kXXX`). Cladding
  materials (records 0, 10, 43) use the MR trim role instead of paint.
