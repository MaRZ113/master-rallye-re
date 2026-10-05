# Human capacity validation - SIX, then SEVEN, then EIGHT

Use an isolated retail copy and preserved original EXE. Stage ONLY the chosen
capacity EXE; no randomizer DLL is needed. Candidates are in ignored
`.research-output/r-ai2-1/six`, `seven`, `eight`. Verify exact hashes against
[manifest](patch-manifest.json). Dev native Dump and audited Observatory are required.

For each candidate: Quick Race -> Race, Humans1, stock T1 ID0 TOMMEK DIRTBEAST,
Track10/ItalyS4, GhostOFF, Opponents visibly Three. This is a deliberate hidden
research count; UI extension is independently tested on another branch.

1. SIX: after all actors spawn capture `six-race`; observe six visible independent
   cars including Car5 Forester. All five AI must drive/progress/collide/take damage.
   Finish; capture `six-results`, check six rows/times/ranks/icons. Exercise Replay
   and frontend return. Stop on crash, aliasing, missing actor, bad HUD/results or cleanup.
2. Only after SIX passes, SEVEN: repeat as `seven-race`, `seven-results`, including
   Car6 Simmbugghini, six AI and seven results; Replay/return.
3. Only after SEVEN passes, EIGHT: repeat as `eight-race`, `eight-results`, including
   Car7 Kangoo, seven AI, eight HUD entries and results; Replay/return.

Do not jump directly to8. Highest actor proof requires visible model/wheels and
independent driving/physics/collision/damage plus normal lifecycle; paths alone
are insufficient. Preserve JSON/raw pairs and observations locally, do not commit them.

Capture: `python tools/r_ai1_observe.py --observatory <audited-directory>
--candidate <staged-MRallye.exe> -- capture <label>`.
Check: `python tools/r_ai2_1_capacity.py check-race <candidate> <snapshot.json>
--expected-cars N --observatory <audited-directory>`; use `check-results` similarly.
JSON/raw integrity and exact profiles are enforced; raw sidecar must accompany JSON.
Checker verifies deterministic IDs/classes/drivers, own named physical canaries,
highest Vehicles/Physics/Network state and N result lists/images/Competitor records.
Verdicts remain BROKER_STATE_MATCH_ONLY / BROKER_RESULTS_MATCH_ONLY.

No randomizer, R-UI1 integration,9-car test or general-N claim. Other courses
have static template/grid coverage but are not promoted to eight-car runtime PASS.
