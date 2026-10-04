# Five-car Quick Race — human runtime gate

**READY FOR HUMAN RUNTIME / PREPARED_RUNTIME_UNTESTED.** This tests exactly
five cars, all T1: one human and four ordinary stock AI. The extra AI uses the
stock unique pool, so its exact CarID varies. No sixth participant is enabled.

1. Use an isolated retail game copy with stock data and a fresh profile. Preserve
   its original EXE. Stage `.research-output/r-ai2/five-car/MRallye.exe` as
   **MRallye.exe**. Verify size **3,121,214** and SHA256
   `806ebedcd6d174682fcc4619fb75eaabca2a1281eda4d4d784807b3583f5f2e2`.
   If needed for Observatory, enable the existing `Menues/Enabled` in the
   isolated copy's loose `DataGame/dev.xml`, as in the previous tests.
2. From this checkout start the same audited Observatory through the adapter,
   then use **L** to launch a fresh game process:

   ```powershell
   python tools/r_ai1_observe.py --observatory '<audited Observatory directory>' --candidate '<isolated copy>/MRallye.exe'
   ```

3. Normal frontend: **Quick Race / Race, Humans1, Opponents3, T1, TOMMEK
   DIRTBEAST (ID0 / LandCruiser), Ghost OFF**. Use the same **Track10 / ItalyS4**
   course as the earlier validated test; leave its default selection unchanged.
   **Keep the visible Opponents3 choice:** the guarded research patch promotes
   its two effective reads to four AI. No T3 access or progressed save is needed.
   Optional action **3**, label **five-front**, records the setup; it is not an
   active-participant proof. A different mode/player/course leaves stock count
   unchanged and does not test this candidate.
4. After countdown, action **3**, label **five-race**. Count five real cars and
   observe that all four AI drive. Run the checker below; it reports the actual
   Car4 ID/family and established named-physics values. Watch that vehicle's
   independent wheels, collision, damage and progress. If the race is unstable,
   stop and preserve the captures/logs.
5. For FULL PASS complete the race, including an observed Car4 finish and five
   logical result entries. Check fifth driver/icon/row in Race Results, then
   action **3**, label **five-results**. This candidate includes the previously
   audited NULL-safe native Dump; keep its exact hash. Return normally to the
   frontend and report survival. Optional **five-return** records the lifecycle
   point; persistent CarN Broker paths alone do not establish teardown. Replay
   is optional; report its stability only if exercised.

From the checkout, validate the two JSON/raw pairs:

```powershell
python tools/r_ai2_capacity.py check-race '<isolated copy>/MRallye.exe' '<five-race.json>' --observatory '<audited Observatory directory>'
python tools/r_ai2_capacity.py check-results '<isolated copy>/MRallye.exe' '<five-results.json>' --observatory '<audited Observatory directory>'
```

The adapter keeps generated config/logs/captures under this checkout's ignored
`.research-output/r-ai2/observatory`. It pins all four public Observatory files
and the exact candidate. Checkers bind JSON entries to the raw Dump hash and
selected complete block. No path-by-path human inspection is required.

Expected state: NumCars5, NumPlayers1, NumNetworkPlayers0, Type2,
FinishingType0, AttractFalse, NetworkSyncFalse, GhostPlaybackFalse; Car0
ID0/class0/PlayerType1/Driver30. Car1..4 are class0/PlayerType2, four distinct
stock IDs1..6 and distinct DriverIDs0..9, with each ID's own family/wheels.
The Car4 oracle checks the already-established WheelBase, TrackWidthFront and
GearRatioDiff values; it does not invent physical constants. Results must have
five Position/Name/Time list items, five own registry image icons and three
blank tail slots. The pinned parser preserves native list-item quotes.

**P0:** five visible active cars; unique real Car4 model, physical motion and AI
driving/progress; other cars normal; no immediate corruption/crash.

**FULL PASS:** P0 plus Car4 own model/wheels/physics/controller,
collision/damage, timing/ranking/finish; five logical results with acceptable
fifth presentation; stable Results Dump and normal frontend return/cleanup.
Cosmetic clipping or missing markers can be logged separately, but broken
progress, aliasing, crash or corrupt state blocks FULL PASS. If the player ends
the event before Car4 finishes, that run does not establish the Car4 finish gate.

Automated verdicts are **BROKER_STATE_MATCH_ONLY** and
**BROKER_RESULTS_MATCH_ONLY**, with `runtime_full_pass=false`. Broker data and
static redzones do not prove five materialized actors or runtime memory safety.
Preserve both JSON/raw pairs, logs and a brief human observation report. Restore
the preserved stock EXE to remove the intervention. Stop at this five-car test;
do not test six or more cars.
