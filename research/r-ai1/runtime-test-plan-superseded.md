# SUPERSEDED / DO NOT USE

Historical plan only; current R-AI1/R-AI1.1 are CLOSED / CONFIRMED_BY_RUNTIME.
See the final runtime closeout; historical readiness text below is retained.

Historical handoff from babbb25. Its fresh-profile T3 selection assumption is incorrect.
Use [corrected runtime plan](runtime-test-plan.md); see [correction](correction.md).

# Human runtime handoff — one experiment

Status: **READY FOR HUMAN RUNTIME**, not runtime PASS. Use only the final
`.research-output/r-ai1/human-candidate/MRallye.exe`.

1. Use an isolated retail game copy with a fresh stock profile, without bonus
   vehicle unlocks. Stage this generated EXE there as `MRallye.exe`. Preserve
   the original. Its SHA256 must be
   `985cef18ada36dd4f17979e671c6ef1dd9647fa82903cee886156ecac4ed73f3`.
2. If the isolated copy does not already expose native developer tools, enable
   the existing `Menues/Enabled=True` in its loose `DataGame/dev.xml`, preserving
   other values. Do not edit the corpus, archives or participant values.
3. From the main checkout start the exact Observatory adapter (replace the two
   example directory placeholders with the supplied tool and isolated copy):

   ```powershell
   python tools/r_ai1_observe.py --observatory "<Observatory directory>" --candidate "<isolated copy>/MRallye.exe"
   ```

   Use its **L** action to launch. Capture through **3** (capture with label).
   Existing settings and captures go under
   `.research-output/r-ai1/observatory/observatory-data/`.
4. Select **Quick Race / Race**, one human, **T3 / BOWLER WILDCAT** (ID14),
   **three opponents**. Keep ordinary rules/difficulty and ghost off. Leave the
   fresh profile's stock default course (Frontend/QuickRace/Track10). Capture
   **mixed-front** at the configured frontend before starting.
5. Start the race. After the countdown, with all four participants active,
   capture **mixed-race**. The distinct T1 SUV must be an AI opponent; player
   remains the T3 Wildcat and the other two AI remain ordinary T3 vehicles.
6. Drive for a meaningful interval and finish normally if practical. Observe
   SUV movement, ordinary wheel/model identity, contacts/collision, race progress,
   HUD/markers and result identity as exercised. Check the two control AI too.
   Return from results/end to frontend; capture **mixed-return** once there.
7. Preserve the three JSON + `.dump.bin` pairs and a short observation record:
   target identified/drives/progresses; contacts and recovery if exercised;
   results/end and frontend return stable; any inert actor, alias or crash.

No manual inspection of dozens of Broker paths is needed. Run the oracle on
the fresh race JSON from the main checkout:

```powershell
python tools/r_ai1_mixed_class.py check "<isolated copy>/MRallye.exe" "<mixed-race.json>" --observatory "<Observatory directory>"
```

It checks exact image hash, command-proven freshness, raw-sidecar integrity,
latest complete Dump selection and raw/JSON equality using the original
Observatory parser. Recovery-only, frontend or altered captures fail closed.
The race checker requires:

| State | Expected |
|---|---|
| Race | NumCars4, NumPlayers1, Type2, Networked=False, Frontend/Active=True; frontend Track10 |
| Car0 | ID14, class2, PlayerType1, DriverID30, Wildcat car/wheels |
| Car1 | ID0, class0, PlayerType2, DriverID0..9, Landcruiser car/wheels |
| Car2/3 | Distinct IDs15..20, class2, PlayerType2, DriverID0..9, correct own families |
| Target physics | Vehicles/Car1 wheelbase2.45, front track1.50, diff ratio3.95 |

It also reports Vehicles/Physics/Controller/Network path counts for each Car0..3
and available Finished/lifecycle values. **BROKER_STATE_MATCH_ONLY** is the
maximum automatic verdict. Paths may persist after exiting; mixed-return is
not evidence that those actors remain instantiated.

## Runtime levels

P0 requires the distinct target materializing and driving during a short stable
race, with four participants. FULL PASS additionally needs meaningful driving,
progress, normal result/end path and stable return, plus intended own
model/wheels/physics/collision identity. State which checks were actually
exercised; leave unobserved damage/recovery behavior unclaimed. Screenshots alone
or Broker values alone cannot prove actual physical identity.

A matched unmodified control is optional only if the target's distinction is
unclear: same player/course/mode/count, then compare all-T3 vs one-T1 behavior.
Random control IDs need not match across launches. No diagnostic canary is
currently necessary. Stop after this proof; do not start capacity or other phases.
