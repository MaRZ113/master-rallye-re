# 4x4 Evo 2 GameCube exclusives pilot (2026-11-13)

Source: `TRUCK.pod` from the GC disc (branch research/source-formats, `evo2-gc/tools/rvz.py`).

```
py -3 -c "from master_rallye.source_adapters.evo2_gc import create_scene; create_scene(<TRUCK.pod>, <scene out>, 'CFRT')"
py -3 -c "from master_rallye.evo2_gc_pilot import create_pilot; create_pilot(<scene.json>, 'CFRT', <retail Data.sma 03c2b52d>, <Data.sma_unpacked>, <out>)"
```

* `source_adapters/evo2_gc.py`: generic over the four GC-only TRK catalogs (CFRT, JWR, SMT, WDRT).
  Visible objects = BASE body set + TRK `stockPartList` (STOCK map); `Light*` light-pass sprites,
  axles, inner glass and non-stock accessories hidden (recorded in `selection.hidden_objects`);
  rear lens quads LightBL/BR/BC kept as the MR brake draw. Source wheels (`<tire>16L/R.SMF`) at
  the TRK `static_bpos` hubs. Glass gets its own atlas copy at alpha 140 (MR authoring).
* `evo2_gc_pilot.py`: MR Classic via `txr3_classic_pilot.create_pilot` with `keep_source_scale`
  (feet -> metres, no donor rescale) and `source_track`. Roles from SMF object names.

| Truck | Donor (physics/templates) | Wheelbase | Track | Wheel r | Author class / target |
|---|---|---|---|---|---|
| Calmini Nissan Frontier Race Truck | Navara | 3.16 | 1.52 | 0.37 | T2 / T5 RAID |
| Warn Dodge Dakota Race Truck | Navara | 3.53 | 1.56 | 0.47 | T2 / T5 RAID |
| Stillen Silverado Monster Truck (TRK name "Vauxhall Frontera") | Patrol | 3.93 | 2.62 | 0.84 | T2 / owner |
| Jeep Wrangler Rubicon | Pajero | 2.57 | 1.47 | 0.38 | T1 |

Monster truck: RMonster has no qualified frontend wheel correspondence and Kamaz/Navara fail the
SDK guards, so Patrol is the template; physics needs tuning for 0.84 m wheels. Native states PASS
for all four; gameplay not tested; not in the roster.
