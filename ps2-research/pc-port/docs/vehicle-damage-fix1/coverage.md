# DAMAGE-FIX1 exact coverage

Coverage refers to opt-in code/resource admission and separately identified runtime evidence. It is not a claim of pixel parity or complete visual acceptance. Original renderer remains frozen.

## COMPLETE: 24 admitted profiles

PID21808 used proxy `ac0e0ddd779264ce7cbc990d7534c10e9bba13a75630fa751478374c44afb3fc`; inherited evidence has 18 successful families. PID14520 used diagnostic proxy `ec383668b403b8bd42761cb2f1544b891eef1f1569e364e81e8c38bbb19a6110`; it logs 23 of the current 24 admitted profiles. A later release DLL must retain its own hash and needs its normal smoke test. PASS here means exact source/current owner admission plus draw/restore HRESULT 0, not a screenshot judgment.

| PC family | Original PS2 family | Admission | Inherited PID21808 | New PID14520 first PASS frame |
|---|---|---|---|---|
| Astero | ASTERO | Admitted | PASS | 5417 |
| Bruno | BRUNO | Admitted | PASS | 6868 |
| ChevyBlazer | CHEVYBLAZER | Admitted | PASS | 826 |
| forklift | FORKLIFT | Admitted | No PASS | NOT OBSERVED |
| Frontera | FRONTERA | Admitted | PASS | 721 |
| IceCream | ICECREAM | Admitted | No PASS | 7937 |
| Jump | JUMP | Admitted | PASS | 2287 |
| Kamaz | KAMAZ | Admitted | PASS | 7863 |
| Kangoo | KANGOO | Admitted | PASS | 6475 |
| LandCruiser | LANDCRUISER | Admitted | PASS | 1520 |
| megane | MEGANE | Admitted | PASS | 6550 |
| Navara | NAVARA | Admitted | PASS | 1790 |
| NewRav | NEWRAV | Admitted | PASS | 2472 |
| Pajero | PAJERO | Admitted | PASS | 1006 |
| Patrol | PATROL | Admitted | PASS | 2412 |
| RMonster | RMONSTER | Admitted | PASS | 2351 |
| SeatBuggy | SEATBUGGY | Admitted | PASS | 7801 |
| Terrano | TERRANO | Admitted | PASS | 876 |
| WildCat | WILDCAT | Admitted | PASS | 5229 |
| Xtrail | XTRAIL | Admitted | PASS | 166 |
| KiaSportage | KIASPORTAGE | Admitted | No PASS | 2522 |
| Mattserati | MATTSERATI | Admitted | No PASS | 6671 |
| Simmbugghini | SIMMBUGGHINI | Admitted | No PASS | 5336 |
| Tata | TATA | Admitted | No PASS | 945 |

**Forklift is admitted but has no live selection/PASS evidence in these sessions. Do not describe all 24 as runtime passed.** Menu rotation, Reset and visible material quality have not been individually certified for all 24.

## Five remaining PS2-family exclusions

| PS2 family | PC target / reason | State |
|---|---|---|
| WOOLDAND | PC Forester; original `$shader(crashiny)` dynamic-registration/fallback contract remains unproved | Stock fallback; do not alias to PS2 FORESTER |
| UFO | PC Ufo; `$shader(carbrakelight)` contract plus distinct mode21 GS/material requirements remain unresolved | Stock fallback; no mode20/14 substitution |
| FORESTER | No verified original PC counterpart | Excluded; distinct from WOOLDAND |
| MOONBUGGY | No verified original PC counterpart | Excluded |
| TANK | No verified original PC counterpart | Excluded |

## Seven reported frontend failures

| Family | Fix / exact blocker | Current evidence |
|---|---|---|
| Tata | Exact missing-primary original DEFAULT.GXI rule for explicit mode3; no arbitrary slot substitution | Native PASS 945; user reports new model displays |
| KiaSportage | Same original missing-primary rule independently verified for its exact source node | Native PASS 2522; user reports new model displays |
| IceCream | Exact PC source3 FVF0x42/stride16 untextured record now admitted; full geometry/owner checks retained | Native PASS 7937; prior gate2/missing bit3 resolved |
| Mattserati | Original caralpha mode2 and authored mnet alpha; separate local transparent bucket | Native PASS 6671; user reports new model displays; D3D8 alpha approximation remains |
| Simmbugghini | Same independently verified mode2 source contract | Native PASS 5336; user reports new model displays; D3D8 alpha approximation remains |
| Forester / WOOLDAND | Unknown shader registration/fallback proof missing | FALLBACK, not silently renamed carshiny |
| Ufo | Unknown shader plus separate mode21 requirements | FALLBACK; no invented glow/glass substitution |

## X-Trail race, damage and feature boundaries

- **Damage continuity:** user confirms reflections now persist after impact. PID14520 logs healthy admission13446 and private-damage admissions14554,15780,15783: all13records, ordered UV/winding verified,1330private faces, draw/restore HRESULT0. Healthy/damaged/further-damaged F10 trio14178/16180/18446 retains current owner and certified records. This is positive continuity evidence, not proof of every future damage state.
- **Transient impact blink:** user observed a short blink. Exact failure/transition gate remains unresolved because existing gate events are once-claim bounded and F10 samples are separated in time. Transition-only instrumentation is the smallest next measurement. No lighting or identity weakening is justified.
- **Crew:** static PS2 face/body/helmet/visor source submissions pass in PID21808 and PID14520. Two occupants, correct appearance, absence of duplicates/floating parts and window occlusion remain explicit visual checks; no character-animation claim is involved.
- **Lamps:** exact OFF reflective base remains separate from brake ON and additive glow. These sessions contain no dedicated rear-lamp/glow success events, so new damage-related lamp coverage is not declared runtime confirmed. Obtain rear OFF/held-ON images on the same car/camera.
- **Decal/headlights/wheels:** existing accepted paths preserved. PID14520 decal override13445 and source partition apply/restore succeed; native independent wheel transforms are preserved. These facts do not independently certify every damaged lamp/wheel surface.
- **MSAA/Reset:** inherited PID21808 Reset16188 succeeds with4x retained and replacement resumes16189; F10s23999/32683 report4x. New phase release must repeat one damaged4x Reset smoke test.
- **Menu performance:** lazy per-family resources retained; no FPS benchmark follows from native admission logs. User menu responsiveness and switching remain smoke-test checks.

## CAR fleet boundary

X-Trail remains the only admitted CAR replacement family. All other original PC vehicles retain Stock CAR geometry until separate current owner, full crew/interior suppression, conditional materials, wheel WORLD and damage certificates are established. COMPLETE admission does not authorize CAR replacement through tags or shared texture names.

Detailed evidence: `runtime/runtime-coverage.json`, `runtime/runtime-14520-delta.json`, `frontend/findings.md`, `damage/findings.md`.
