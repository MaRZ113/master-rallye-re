# R5V-E0.1d.2 — VehicleRecord colour producer

## Status

**FULL PASS by user-reported runtime result.** The static source-to-property path is confirmed in retail Ghidra assembly/P-code; the corpus contains 25/25 plausible normalized RGBA vectors. The isolated red-tail A/B changed ID25's marker to red while Trooper model/physics/collision, Astero's marker, and opponent colours remained unchanged. This phase's runtime result is user-reported, not independently reproduced in this workspace.

The best eventual semantic name is `race_colour_rgba`: the same four floats feed the `Race/CarN/Colour` property through multiple race setup paths, and the progress-marker HUD reads that property. The authoring/profile API remains unchanged until the red-tail diagnostic is reported.

## Main evidence

- `FUN_00458E70` contains 25 direct calls to the retail full record initializer at `0x0045A0B0`. Their receiver displacements resolve to IDs 0–24 with `base + 4 + ID * 0x34`. Each call site supplies four float words which the initializer stores at `VehicleRecord +0x24..+0x30`. Source is ignored raw Ghidra Bridge output at `research-output/r5v_e0_1d_2/ghidra/458e70.asm`.
- The table in [corpus-colours.tsv](corpus-colours.tsv) has 25 distinct RGB triples. All RGB components are finite and within `[0,1]`; all alpha values are exactly `1.0`. ID25 is a synthetic test record and inherits Astero's vector in the already runtime-confirmed Trooper/SmallCarSheet29 baseline.
- `FUN_0044A320` iterates race participant slots. In the ordinary path, `FUN_0044A510` reads the participant's `/CarID` through `FUN_004AC660`, resolves the registry record, reads four contiguous dwords from `base + ID*0x34 + 0x28` (equivalent to record `+0x24`), and passes them to `FUN_004ACDD0` with the participant slot.
- In the alternate race-mode path, `FUN_0044A710` resolves its participant vehicle ID through `FUN_004B0630`, reads the same four-dword tail, and calls the same setter. `FUN_0044A8E0` has additional setup call sites that read the same vector and call that setter.
- `FUN_004ABCE0` initializes the setter schema: `[this+0x8C]` is the literal `/Colour` member of the `Race/Car` schema. `FUN_004ACDD0` selects the requested `Race/CarN` path and copies the four dwords as a vector property.
- The existing HUD consumer `FUN_004A74A0` forms `Race/Car%d/Colour` from its display slot, calls the property getter, then copies the four components into its HUD colour state. The prior ABI-safe bypass test already showed at runtime that this property overrides the XML fallback and affects the Player1 marker.

## R5V-E0.1d.1 runtime results supplied by the user

These are owner-reported runtime observations, not independently reproduced in this session:

| Consumer | HUD XML | Player1 marker | Opponents |
|---|---|---|---|
| Normal | Normal | Aquamarine | Normal colours |
| Normal | Red fallback | Aquamarine | Normal colours |
| ABI-safe Car0 override bypass | Normal | Grey/white fallback | Normal colours |
| ABI-safe Car0 override bypass | Red fallback | Red | Normal colours |

With the bypass, all player-selected cars used the same XML fallback, while opponent colours stayed normal. This demonstrates that the normal Player1 override is vehicle-dependent and that the XML value is a fallback.

## ID25 red-tail diagnostic

Tested candidate: `research-output/r5v_e0_1d_2/runtime-test/MRallye_slot25_trooper_redrecordcolour_test.exe`, SHA-256 `9d56c1ef0682224d3254db0e5e49cb4ecb11076467321f073f15d60526f60e46`.

It was derived from the P0 Trooper / SmallCarSheet29 candidate, SHA-256 `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`. Exactly three 4-byte RGB immediate words in the existing ID25 initializer stub changed. Alpha stayed `1.0`. HUD XML, the bypass, class capacity, name, stats, Trooper family, and SmallCarSheet29 index were untouched. The user reports that the candidate produced the predicted red ID25 marker; the original Astero marker and opponent colours stayed normal, and Trooper model/physics/collision were unchanged.

See [race-colour-dataflow.md](race-colour-dataflow.md), [vehicle-record-colour.md](vehicle-record-colour.md), and [runtime-diagnostic.md](runtime-diagnostic.md).

## Gate

Static mapping plus the isolated user-reported runtime A/B establish this vector as the per-vehicle race-marker colour source. E0.1d.2 is closed. No executable or runtime candidate was changed by this documentation closeout. R5V-F remains gated on the separate Vehicle Select icon issue and other stated readiness criteria.
