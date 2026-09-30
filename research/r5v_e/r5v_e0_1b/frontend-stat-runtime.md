# Frontend stat fields and isolated runtime candidate

## Direct record reads

Retail `FUN_004819B0` obtains the selected absolute vehicle ID through `FUN_00481E20`, gets the registry base from `FUN_0045A3C0`, and performs four loads with stride `0x34`:

| UI property | Registry-base load | VehicleRecord field |
|---|---:|---:|
| Speed | `base + 0x10 + id*0x34` | `+0x0C` |
| Acceleration | `base + 0x14 + id*0x34` | `+0x10` |
| Handling | `base + 0x18 + id*0x34` | `+0x14` |
| Endurance | `base + 0x1C + id*0x34` | `+0x18` |

The registry accessor's first record begins at `base+4`, accounting for the four-byte adjustment in the expressions above. The four results are written to separate frontend properties. `VehicleSelect.xml` maps SpeedBar, AccelerationBar, HandlingBar, and EnduranceBar to their matching properties. No Astero ID16 redirect appears in these loads.

The stats integers present in the retail registry fall within 2..10 for these fields. The Vehicle Select gradient box bank includes numbered frames 0 through 10. The diagnostic values `(3,4,6,10)` are each observed in the corresponding field among retail records and remain inside that frame range.

## Candidate and exact diff

Candidate:

```text
.research-output/r5v_e0_1b/runtime-test/stats/MRallye_slot25_trooper_stats_test.exe
SHA-256 feb1b072a22bd77312b8f36f39c80dca85893d8b41645a6ee563831014b70976
```

The source is the unmodified retail executable, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. The comparison baseline is the runtime-confirmed Trooper + SmallCarSheet 29 candidate, regenerated from the same source and matching SHA-256 `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`. This preserves the known Forklift participant and Results icons during the independent stats test.

Relative to that Trooper + frame-29 baseline, executable length is unchanged and only these four immediate bytes differ:

| File offset | VA | Baseline | Diagnostic | Initializer argument |
|---:|---:|---:|---:|---|
| `0x28E2D7` | `0x68E2D7` | 8 | 10 | Endurance |
| `0x28E2D9` | `0x68E2D9` | 8 | 6 | Handling |
| `0x28E2DB` | `0x68E2DB` | 6 | 4 | Acceleration |
| `0x28E2DD` | `0x68E2DD` | 6 | 3 | Speed |

These are the four independent integer arguments passed to the original record initializer in reverse stack order. All other patch operations, including slot, class, Trooper name, SmallCarSheet selector 29, four tail floats, unlock test override, class-2 capacity, registry hook, and stub structure, match the baseline. Patcher `--verify-existing` rebuilt the file in memory and verified both the candidate and manifest.

## Human check

Inspect T3 Vehicle Select ID25 using the stats candidate. Record the four bar lengths independently and compare with `(3,4,6,10)`. The candidate retains SmallCarSheet selector 29, so the previously confirmed Forklift frame-29 top-left and Results icons should remain. Vehicle Setup may be opened as a crash check; a race is not required. The candidate does not change Trooper physics or assets. Runtime result remains **WAITING FOR HUMAN**.
