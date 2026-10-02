# R5V-F.2b ID26 cook trigger

The isolated executable at
`research-output/r5v_f_2b/runtime-cook/MRallye.exe` was built from the pinned
retail executable with the existing R5V-F.1 registry patch and a fixed
`mercedes-cook-harness` profile.

| Property | Harness value |
|---|---|
| Physical record | ID26 |
| Frontend mapping | T1 local7 |
| Internal/resource name | `Mercedes` |
| Runtime family label | `Mercedes` |
| VehicleRecord donor | ID0 / Landcruiser semantics |
| Frontend stats | 4, 2, 4, 6 (retained) |
| Race-colour fields | F.1 red canary retained |
| Display selectors | Existing F.1 selector mapping retained |
| Registry count / capacity | 27 records |
| Class capacities | T1=8, T2=7, T3=12 |
| ID25 | Trooper, unchanged |

The F.1 cleanup profile remains the patcher default. A regression test confirms
that only the code-cave payload and its derived `.text` VirtualSize differ
between the two profiles; the other 70 patch operations are identical. The
candidate's structural manifest and deterministic rebuild both pass.

The only intended runtime identity change is the ID26 owned internal name,
which should make the normal loader request `Vehicles/Mercedes/complete`, then
`car` and `wheel` in the offline race trigger. This profile is only a cooker
trigger; the retained donor stats, red canary, selection icon, localization,
physics, and race behavior are not final Mercedes acceptance.

No game launch has occurred. Runtime proof begins only after the user runs the
Junction helper and captures the complete preview cook described in
`HUMAN_COOK_INSTRUCTIONS.txt`.
