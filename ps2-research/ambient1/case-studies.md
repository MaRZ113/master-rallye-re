# Controlled cases

Resources are exact named `\TNG\DATASCENE\RACETEST\*.XML` payloads read by
the existing PackFS reader. Payload/route hashes, selected normalized settings,
structural applicability and deterministic artifact hashes are recorded in
`case-evidence.json`; full parameter types, coordinates and complete source
properties remain in ignored `data/ambient1/diagnostics/`.

| Course / Egg / route | Controls and code implications | Last knot / total time, nominal units |
|---|---|---|
| ITALY3 / barge / barge, 11 | Const, open, triggered 400/1000, speed 3, no rest/bank. Init inactive; resume on proximity. Final-marker hold includes 265.108429 closing time. | 267.583557 / 532.692017 |
| TURKEYW / barge / bargelist, 10 | Same owner/model and speed 3, open, trigger disabled. Starts active once observer exists. Closing hold 207.958206. | 253.097794 / 461.056000 |
| FRANCE1 / boat1 / boatlist1, 6 | Const, loop, speed 2.5, no trigger/bank. Rest=True, 300 sec -> 9000 invocations, ignored in closed advance branch. | 185.869019 / 211.049942 |
| FRANCEM / zeppelin / zeppelin, 4 | **Const=False**, loop, speed 12, no trigger/bank. Four equal spans of 64.707542. Same evaluator/publisher as barges. | 194.122620 / 258.830170 |
| SPAINS2 / boat1 / boat1, 7 | Const, loop, trigger 300/600, speed 8, banking 1, samples 30. Own ring, active flag, time and route. | 160.212021 / 230.856689 |
| SPAINS2 / boat5 / boat5, 5 | Const, loop, trigger 300/600, speed 6, banking .6, samples 30. Independent of boat1 with shared Car0 observer. | 112.029892 / 133.665512 |

The first four cases have identity authored model matrices. Both SPAINS2
boats have nonzero authored translations, overwritten by the same initial
and tick publisher. Route position is absolute in that carrier's world
matrix; it is not an offset from those authored translations.

All six routes have constant authored Y. Therefore FRANCEM does **not** itself
prove a vertically varying flight route. Small float32 Y differences in a
cubic sum are arithmetic, not a discovered airship altitude behavior.
Synthetic XYZ-varying controls constrain vertical evaluation; the ELF carries
all three components with no model-family branch. Optional ITALYS4 airship
has nine controls, Const=True, loop, speed 9, also constant Y; structurally
checked with the remaining selection, not promoted to a seventh runtime case.

Each mandatory case has 360 explicit controller invocations using a synthetic
fixed observer at its first route point, plus a **separately labeled** 601-time
full-domain curve sweep for SVG. Sweep points are not successive simulation
ticks. Trigger, rest and boundary transitions additionally use controlled
synthetic tests; the full 24-object structural pass does not simulate gameplay.

Cross-instance conclusion: the factory/clone and per-instance vectors support
the same control contract for all three model families. No boat-specific
water height, barge-specific physics or airship-specific altitude/yaw branch
is present in this owner. Visibility, successful loading and true motion of
these exact objects remain `UNKNOWN` until observed. Six offline cases are
`FLOAT32_RECONSTRUCTION`; authored/executable linkage is
`CONFIRMED_BY_BOTH`, never `CONFIRMED_BY_RUNTIME`.
