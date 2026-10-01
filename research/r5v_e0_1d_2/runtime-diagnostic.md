# ID25 red record-colour diagnostic

## Candidate

- File: `research-output/r5v_e0_1d_2/runtime-test/MRallye_slot25_trooper_redrecordcolour_test.exe`
- Candidate SHA-256: `9d56c1ef0682224d3254db0e5e49cb4ecb11076467321f073f15d60526f60e46`
- Input: runtime-confirmed P0 Trooper / SmallCarSheet29 candidate, SHA-256 `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`
- Patcher: [prepare_r5v_e0_1d_2_record_colour.py](../../tools/prepare_r5v_e0_1d_2_record_colour.py)
- Package metadata: ignored `research-output/r5v_e0_1d_2/runtime-test/patch-manifest.json`, `binary-diff.txt`, and `TEST_INSTRUCTIONS.txt`.

The generator pins the source executable SHA, prior manifest, ID25 profile, initializer stub address/size, and all four source words. It refuses an unexpected input or an existing output. It emits a separate candidate and never opens the retail executable for writing.

## Exactly changed values

ID25's existing initializer stub begins at file offset `0x28E2A0` / VA `0x68E2A0`. The patch changes its three RGB immediates:

| Stub immediate offset | Record field | Original bits (Astero) | Diagnostic bits |
|---:|---:|---|---|
| `+0x0A` | `VehicleRecord +0x24` | `3D8B1C04` | `3F800000` |
| `+0x12` | `VehicleRecord +0x28` | `3F092D67` | `00000000` |
| `+0x1A` | `VehicleRecord +0x2C` | `3EF74E40` | `00000000` |
| `+0x22` | `VehicleRecord +0x30` | `3F800000` | `3F800000` unchanged |

The three changed 4-byte file windows are `0x28E2AA..0x28E2AD`, `0x28E2B2..0x28E2B5`, and `0x28E2BA..0x28E2BD`. No other byte differs from the P0 input. The candidate retains the original initializer call and its owned-string behavior.

## Controlled run

Use a disposable copy of the same retail installation/data used for the P0 runtime result. Use normal HUD XML and the normal colour consumer. Do not pair with XML-red data or a Car0 bypass executable. Select ID25 in Quick Race.

Expected result if the direct vector is the visible source: only the Player1 bottom progress marker changes from aquamarine to red. Verify Trooper preview/race model, physics and collision behavior, SmallCarSheet29 Forklift icons, frontend stats, and opponent marker colours remain the same. Do not use campaign saves.

The candidate is **prepared but not runtime-tested**. Return observations, including any unexpected changes or crash, before changing profile field names.
