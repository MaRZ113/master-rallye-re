# Final Mercedes ML-320 profile — implemented; runtime acceptance pending

The final `mercedes-final` ID26 profile has been added to the hash-locked retail patcher. Its static acceptance candidate and isolated runtime package are ready. P0 frontend is waiting for a human run; P1 gameplay is gated on P0 PASS. See [R5V-F.2e findings](../r5v_f_2e/findings.md) and its [runtime-test plan](../r5v_f_2e/runtime-test-plan.md).

| Profile field | Final value | Evidence / limit |
|---|---|---|
| Physical slot / class-local | ID26 / T1 local7 | Existing R5V-F registry expansion; IDs 0–25 remain unchanged |
| Internal/resource/runtime family | `Mercedes` | Retail native cooker and family path use `DataGx/Vehicles/Mercedes` |
| Physics family | Retail `Vehicles/Mercedes` | Static schema: 144 parsed values, 6 gears, 6 torque entries; gameplay still needs P1 |
| Model package | Native retail-cooked rev135 `complete.dx`, `car.dx`, `wheel.dx` | Cook A/B byte-identical; final package statically validated |
| Display | `MERCEDES ML-320` | ID26-only direct strings for Vehicle Select and three Quick Race group-0x35 lookups; do not patch `gaLocal` globally |
| Vehicle Select art | T1_Car8 uses historic carsheet frame4 | Staged as zero-based image-bank index3; not Mercedes-exclusive art |
| Frontend stats | Speed 4, Acceleration 3, Handling 6, Endurance 5 | Historical demo initializer order |
| SmallCarSheet | donor frame9 | Controlled fallback; authentic Mercedes frame remains unproven |
| Race colour | Existing explicit red ID26 canary | Custom presentation colour, not historically authentic |
| Unlock | ID26-only test unlock | Campaign unlock/save integration remains out of scope |

Keep `donor-cleanup` and `mercedes-cook-harness` intact. Final candidate and package hashes are in `research-output/r5v_f_2e/candidate/candidate-manifest.json`. Do not call the vehicle runtime-confirmed until P0 and P1 pass on that exact candidate.
