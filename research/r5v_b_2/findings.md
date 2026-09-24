# R5V-B.2 findings (retail)

Read-only investigation of the selected vehicle path. Addresses are retail virtual addresses. Raw instruction windows and bridge exports are retained outside Git in `.research-output/r5v_b_2/`. No game binary or asset was changed.

## Correction to the entering hypothesis

`MasterRallye/PlayerT3Car0` receives an **absolute ID**, not class-local 11. `0x4819B0` converts class 2/local 11 to ID25, writes ID25 to `Frontend/VehicleSelect/CarModel`; `0x47BB00` reads that value and writes the same integer to `PlayerT3Car0`. The shipped `MasterRallye.xml` default of 14 supports absolute-ID semantics. Quick Race uses its own direct selection path (`0x481340` and `0x47B780`), not this campaign persistence key.

## Established edges

| Edge | Evidence | Status |
|---|---|---|
| class 2/local 11 → absolute ID25 | `0x481E20`, `0x481391` | RAW_GHIDRA_ONLY |
| selected ID → `Race/CarN/CarID` | `0x481410` → `0x4ACAF0`; Quick Race restore `0x47B780` | RAW_GHIDRA_ONLY |
| `Race/CarN/CarID` → record owned name → `Race/CarN/CarType` and `WheelType` | `0x44A320` → `0x44A510`, registry indexing `ID*0x34 +0x20` | RAW_GHIDRA_ONLY |
| ID25 → preview `Vehicles/Astero/complete` if initialized | scene `CarModel` binding; `0x44C4C0` path builder | RAW_GHIDRA_ONLY |
| named Astero physics → runtime `Vehicles/Car0/...` | `0x44ED50` → `0x493E30` → `0x4938C0` | RAW_GHIDRA_ONLY |
| `CarType` → race `vehicles/<name>/car` and `/wheel` | conditional branch at `0x4B6B17` to `0x4AC610`, then `0x4B6FF7`/`0x4B7100` | RAW_GHIDRA_ONLY, conditional |

The race actor takes `Race/CarN/CarType` only while `Frontend/Active` is true. Otherwise it retains a separate scene `Car Name` property. The value of `Frontend/Active` at the intended Quick Race actor creation point was not proven. This remains a precise missing edge for a safe R5V-C gate. The shipped scene XML often contains `Car Name="Jump"`, so the fallback is materially different from donor Astero.

`0x481950` computes twelve X-position config keys, but the retail VehicleSelect scene has widgets through `Button10XPos` only. This loop itself uses local strings rather than a twelve-element button array; keyboard/controller focus and visibility for entry 11 remain unproven. ID25 also uses unlock flag 15 at `0x45A150`.

**Decision:** R5V-C BLOCKED pending proof of the live race actor branch and the final frontend visibility/selection path. ReAgent actual reversal was attempted but rejected by automatic approval review because it would send retail decompilation to the external Codex provider; no generated C++ is available for independent comparison.
