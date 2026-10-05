# R5V-F.2e P0/P1 runtime handoff

> Historical handoff. The owner later tested the F.2e candidate and found the independent Race Options writer still emitted `GALOCAL UNKNOWN`. Use the F.2f handoff for the corrected Race Options identity candidate; this document is retained as chronology.

## Exact isolated build

Run only the isolated copy:

```text
D:\Game\Master Rallye\master-rallye-re-e0.1\research-output\r5v_f_2e\runtime\MRallye.exe
```

Set the working directory to:

```text
D:\Game\Master Rallye\master-rallye-re-e0.1\research-output\r5v_f_2e\runtime
```

Candidate executable SHA-256: `1fb0a1f1ba02cd05fa25f0c94558cf1b281fd12affcdc37bb3c1ca538e6c65af`.

Start DebugView before launching. Save evidence only under `research-output/r5v_f_2e/logs/`; do not put captures or logs in Git. The test runtime is a disposable offline copy. Do not use the installed game directory or test online.

## P0 — frontend acceptance

Run through the pre-race screen and stop before starting the race. Record the result for every item:

- [ ] Candidate launches and reaches Vehicle Select.
- [ ] T1 shows exactly 8 entries; its final local7 entry maps to ID26.
- [ ] T2 remains exactly 7 entries; T3 remains exactly 12.
- [ ] T1 local7 displays `MERCEDES ML-320` and the Mercedes complete model.
- [ ] Mercedes textures/materials render with no missing-texture artifacts.
- [ ] T1_Car8 shows the historic Mercedes-slot frame4 art.
- [ ] Stats are Speed 4, Acceleration 3, Handling 6, Endurance 5.
- [ ] Left/right navigation through the end of T1 and back remains stable.
- [ ] Stock ID0 remains separately selectable.
- [ ] ID25/Trooper remains separately selectable and unchanged.
- [ ] Quick Race pre-race still displays `MERCEDES ML-320` for ID26.
- [ ] No `GALOCAL UNKNOWN` appears in the tested flow.

P0 passes only when all identity, class/capacity, preview, art, stats, navigation, and stock-regression checks pass. If any item fails, stop without changing files and classify the failure as mapping, display, art, package, stats, navigation, or stock regression. Save the DebugView capture as `research-output/r5v_f_2e/logs/mercedes-final-p0-debugview.log` and report the first failing item.

## P1 — gameplay acceptance (only after P0 passes)

Run offline Practice or Quick Race. Capture DebugView from setup through return to menu. A Broker Observatory snapshot is optional; do not modify Broker Observatory.

- [ ] Mercedes `car.dx` and `wheel.dx` are loaded from the cache.
- [ ] Required Mercedes DXT resources load.
- [ ] No Mercedes GXM/GXI read, authoring Junction lookup, or `D:\projects\MRallyeTNG` access occurs. Ignore unrelated source/cache lookups for other game assets.
- [ ] Steering, acceleration/braking, suspension, and grip feel coherent under ordinary driving.
- [ ] Normal obstacle collision works; external and internal damage occur.
- [ ] Camera and HUD work; the red custom ID26 race marker appears where expected.
- [ ] Complete a meaningful stage section; if stable, finish the stage and reach Results.
- [ ] Return to menu; verify ID0 and ID25/Trooper still remain.
- [ ] Glass breakage is not required for this old Mercedes model.

Do not perform extreme crash tests. Save the capture as `research-output/r5v_f_2e/logs/mercedes-final-p1-debugview.log`. Keep the `PeakMu` warning unclassified until observed handling and, if useful, a Broker snapshot show what happens.

## Result record

```text
P0: WAITING_FOR_HUMAN
P0 first failure / notes:
P0 DebugView path:
P1: BLOCKED_UNTIL_P0_PASS
P1 DebugView path:
Broker snapshots:
PeakMu classification:
```

Do not call the Mercedes a runtime-confirmed 27th vehicle until both P0 and P1 pass on the exact candidate hash above.
