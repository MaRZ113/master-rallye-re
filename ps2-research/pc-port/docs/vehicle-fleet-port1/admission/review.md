# Independent fleet admission review

Scope: existing pinned CAR source profiles and Kia session 11316. No native memory mutation, source renderer edits, builds or new binary research. The source inventory supports implementing conditional runtime admission for all 25 playable families; it does not prove all 25 render correctly in the game.

## Decision

KiaSportage is GO for the first live whole-chassis replacement: the existing three same-session frames verify all 26 native source records under one chassis owner/WORLD, 30 selected native roots, and four independently moving wheel owners. Its 22 original unconditional PS2 CAR roots contain 2,197 triangles. The current runtime gate must additionally validate ordered positions and native UV/winding; the earlier metadata capture alone did not validate those streams.

All other prepared families are GO only for fail-closed dynamic certification, not unconditional suppression. Exact selected-list ownership, complete source set, matching WORLD, current mirror generation/revision and supported material transactions are mandatory. X-Trail keeps its separately accepted damage-aware path.

The independent source checks pass for all 25 profiles: suppression/exclusion sets are disjoint and exhaust every native physical record; no suppressed record has original conditional-face overlap or an ON/glow guard; each selected source has a family-unique complete geometry certificate. All private models contain crew exactly once and exclude independent wheels and conditional native alternatives. Zero unresolved material blocks remain in these source conversions.

## Integration hazards

- Preflight all current sources before the first suppressed draw. Discovering damage halfway through submission cannot safely select whole-frame Stock after private geometry has already rendered. Never carry a healthy certificate across changed native mirrors merely to hide a transition.
- Require every suppressed source WORLD to match the exact current chassis WORLD. Current root membership alone does not authorize attaching a detached native part to the chassis.
- Native conditional windows/OFF/ON/glow remain native. Do not widen suppression to all tag-2 records: some native glow siblings also have tag 2.
- Damage on any unproved family must select complete native chassis fallback before suppression. No generic deformation transfer is justified by the X-Trail map.
- Mode 3 has both mixed framebuffer/environment and authored generic-secondary cases. Preserve this distinction. WOOLDAND mode 5 requires both accepted layers; Mattserati and Simmbugghini require mode 2 alpha treatment. Preserve source modes 0 and 20 where present.
- Native wheels retained is a safe initial limit. Most wheel resources have five records; only X-Trail, Kia, Navara and Tata have four. UFO has no paired WHEEL resource. Do not impose any wheel-record count on chassis admission.
- WOOLDAND maps to PC Forester. Original PS2 FORESTER remains a distinct unpaired model. Forklift is excluded by user request.

## Source coverage and special cases

| PC family | Candidate native roots | Exact suppression sources | Kept conditional records | Special private modes |
|---|---:|---:|---:|---|
| Astero |27|23|9|20|
| Bruno |19|18|3|20|
| ChevyBlazer |31|27|9|20|
| Frontera |28|23|11|20|
| IceCream |24|20|9|20; source DEFAULT primary case|
| Jump |25|21|9|20|
| Kamaz |28|24|9|20|
| Kangoo |24|20|9|20|
| KiaSportage |30|26|9|20; current owner/WORLD observed|
| LandCruiser |28|24|9|20|
| Mattserati |23|20|6|2,20|
| megane |28|24|9|20|
| Navara |31|26|11|20|
| NewRav |29|24|11|20|
| Pajero |28|24|9|20|
| Patrol |29|25|9|20|
| RMonster |27|22|11|20|
| SeatBuggy |28|24|9|ordinary 1,3 only|
| Simmbugghini |23|21|5|2|
| Tata |34|30|9|20; source DEFAULT primary case|
| Terrano |28|24|9|20|
| Ufo |9|7|5|ordinary 1,3; native wheel retention|
| WildCat |24|20|9|20|
| Forester / WOOLDAND |21|16|11|5,20|
| Xtrail |27|23|9|0,20; retain proven pipeline|

Root counts are source-derived candidates except current observed Kia and accepted X-Trail. They are never sufficient identities and must fail closed when the actual selected native tree differs.

Validation: `python ps2-research/pc-port/docs/vehicle-fleet-port1/admission/test_source_contracts.py` passes 4/4 source-only tests. This report makes no new runtime visibility, reset, damage or lamp-transition claim.
