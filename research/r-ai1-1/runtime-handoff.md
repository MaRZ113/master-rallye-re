# Hardened randomized Quick Race — human handoff

Status: **COMPLETED / CONFIRMED_BY_RUNTIME**. This is the historical protocol;
[final closeout](runtime-closeout.md) records the actual four fresh generations
plus one Restart capture, hardened Results Dump survival and loading pass. [Older handoff](runtime-handoff-unhardened.md) is **SUPERSEDED / DO NOT
USE** for this smoke. The new guard permission applies only to the exact new
candidate; pristine/old candidates remain unsafe for post-results Dump.

1. Preserve the original EXE in an isolated retail copy. Stage
   `.research-output/r-ai1-1/hardening/randomized-hardened/MRallye.exe`
   as **MRallye.exe**. Verify SHA256
   `603f0c06ca2a502367baa7e49fcaeab9e2ab9a7d6c47dd46ed82ca27cb9840a1`
   and size3,121,214. Fresh PlayerState/profile, stock data; existing
   Menues/Enabled in loose DataGame/dev.xml may be enabled for Observatory.
2. Start the research adapter from the main checkout with the same audited
   Observatory directory, then use **L** to launch a fresh process:

   ```powershell
   python tools/r_ai1_observe.py --observatory '<audited Observatory directory>' --candidate '<isolated copy>/MRallye.exe'
   ```

3. Normal UI: **Quick Race / Race, Humans1, Opponents3, T1, TOMMEK DIRTBEAST
   (ID0), Ghost OFF**. Keep one course/difficulty/rules throughout. No progressed
   save or T3 frontend access. After countdown capture via action **3**,
   label **mixed-random-race-1**. Observe normal player/three AI motion.
4. **Finish this first race**, enter Race Results, then action **3** with label
   **mixed-hardened-results**: this invokes the original native Broker Dump.
   Required: game stays alive, complete Dump, empty PointsList representation
   and later entries. Observe result driver names/icons and normal result UI.
5. Leave Results and generate another normal Quick Race in the **same process**.
   Required: loading starts the race normally, with no unintended AttractMode.
   A Restart can additionally exercise loading but does not count as new AI
   generation if it merely restores the same participants. Stop on crash or
   unexpected Attract and preserve the log/raw artifacts.
6. If both smoke checks pass, collect active-race labels
   **mixed-random-race-2** through **mixed-random-race-5** from four newly
   generated races in this same process. These can be short; return to Quick
   Race frontend to generate each. Race1 already counts toward five.
   Preserve all JSON/raw pairs and a brief record of models/AI movement,
   successful post-results Dump, later loading and stable frontend return.

Car0 must remain ID0/class0/human1/driver30. Each Car1..3 is AI2 with stock
class0/1/2 and its own valid distinct ID/family/wheels/physics; AI drivers are
distinct0..9. NumCars4/NumPlayers1, Type2/AttractFalse. A single homogeneous
sample is allowed; MIXED does not guarantee all classes in every race.
Ordinary AI T1 pools include IDs beyond the three initial frontend cars.

From the main checkout, verify the Results pair and then the five active pairs:

```powershell
python tools/r_ai1_hardening.py check-results '<isolated copy>/MRallye.exe' '<mixed-hardened-results.json>' --observatory '<audited Observatory directory>'
python tools/r_ai1_mixed_class.py summarize-general '<isolated copy>/MRallye.exe' '<race-1.json>' '<race-2.json>' '<race-3.json>' '<race-4.json>' '<race-5.json>' --observatory '<audited Observatory directory>'
```

No manual path-by-path inspection is needed: the research checker verifies
exact candidate, pinned implementation, source metadata/freshness, JSON/raw
binding, RACE TIME/PointsList and continuation. The active oracle checks
counts/identity/physics, same course and observed class/ID variation.
Native empty PointsList cannot distinguish NULL from an allocated empty list.
Automated verdicts remain state/sampling matches; human liveness and lifecycle
are necessary. Generated logs/captures stay ignored in the main checkout.

**HARDENED RUNTIME PASS**: post-results Dump completes while game lives and
subsequent normal loading/restart works. Separate idle-main-menu Attract logic
is preserved statically; a long idle test is optional.

**R-AI1.1 RANDOMIZED MIXED-CLASS CONFIRMED_BY_RUNTIME** additionally needs five
newly generated races with varying valid AI class/ID arrangements, non-player
classes, four participants, normal AI/models/physics/progress and no loading
Attract contamination. If five samples show insufficient variation, retain
that result and collect more short samples; do not claim uniform probabilities.
Stop here. Opponent Capacity requires a separate later instruction.
