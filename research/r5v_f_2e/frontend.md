# Final Mercedes frontend profile

| Channel | Value | Evidence/status |
|---|---|---|
| Physical slot | ID26 | Static candidate; separate from IDs0–25 |
| Class and local position | T1 local7 | Sparse map local7 → ID26 and inverse map ID26 → local7 |
| Visible Vehicle Select name | `MERCEDES ML-320` | Manufacturer/model groups overridden for ID26 only |
| Visible Quick Race name | `MERCEDES ML-320` | Three group-0x35 lookup sites wrapped for ID26 only |
| Preview model | `DataGx/Vehicles/Mercedes/complete.dx` | DX/DXT dependency inspection PASS; P0 rendering pending |
| Stats | Speed 4 / Acceleration 3 / Handling 6 / Endurance 5 | Presentation values; field order tested |
| Vehicle Select icon | T1_Car8, image-bank index3 | Historic Mercedes-slot frame4, zero-based index3; not Mercedes-exclusive |
| T3 regression | T3_Car12 remains at index5 | Existing R5V-E0.2 content preserved |
| SmallCarSheet | frame9 | Documented donor fallback; historical restoration remains partial |
| Race marker | red RGBA 1/0/0/1 | Custom ID26 presentation canary, not authentic Mercedes metadata |
| Unlock | ID26-only test unlock | Campaign/save integration excluded |

The scene overlay hash is `83006b28f88ea513c5aca768b68bf16468c834f8f9242dff18b19442eab7a756`. It appends the T1_Car8 entry and retains T3_Car12. The packed `Data.sma` diff confirms this scene is the only changed existing archive member.

The static profile does not prove that the model displays correctly, navigation is stable, or Quick Race presents the intended name. Those are explicit P0 checks in [runtime-test-plan.md](runtime-test-plan.md).
