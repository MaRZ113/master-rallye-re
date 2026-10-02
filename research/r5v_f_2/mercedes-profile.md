# Final Mercedes ML-320 profile — values fixed, implementation gated

The final profile values are defined by R5V-F.2d. **Do not generate the profile or its executable until the cache-only preview and race car/wheel loads pass in the isolated runtime.** At the current checkpoint, only the `mercedes-cook-harness` profile exists in the patcher; the profile below has not been applied.

| Profile field | Final value | Evidence / limit |
|---|---|---|
| Physical slot / class-local | ID26 / T1 local7 | Existing R5V-F registry expansion; IDs 0–25 remain unchanged |
| Internal/resource/runtime family | `Mercedes` | Retail native cooker and family path use `DataGx/Vehicles/Mercedes` |
| Physics family | Retail `Vehicles/Mercedes` | Static schema: 144 parsed values, 6 gears, 6 torque entries; gameplay still needs P1 |
| Model package | Native retail-cooked rev135 `complete.dx`, `car.dx`, `wheel.dx` | Cook A/B byte-identical; cache-only human test still pending |
| Display | `MERCEDES ML-320` | Historic demo spelling; ID26-only overrides for groups 0x33, 0x34, and 0x35; do not patch `gaLocal` globally |
| Vehicle Select art | T1_Car8 uses historic carsheet frame4 | Historic Mercedes-slot mapping, not Mercedes-exclusive art |
| Frontend stats | Speed 4, Acceleration 3, Handling 6, Endurance 5 | Historical demo initializer order |
| SmallCarSheet | donor frame9 | Controlled fallback; authentic Mercedes frame remains unproven |
| Race colour | Existing explicit red ID26 canary | Custom presentation colour, not historically authentic |
| Unlock | ID26-only test unlock | Campaign unlock/save integration remains out of scope |

Keep `donor-cleanup` and `mercedes-cook-harness` intact. The final profile should be a separate semantic profile in the profile-driven patcher. Cache-only PASS is the hard prerequisite for that change. The profile's first human gate is P0 identity/preview; P1 gameplay remains a separate test.
