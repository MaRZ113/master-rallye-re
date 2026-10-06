# SUPERSEDED — original un-hardened handoff

Historical plan only; current R-AI1/R-AI1.1 are CLOSED / CONFIRMED_BY_RUNTIME.
See the final runtime closeout; historical readiness text below is retained.

Historical instructions for hash f9e8... ONLY. **DO NOT USE for the new hardening
smoke or same-process sampling**. Its post-results warning remains valid for
that image. Use [current handoff](runtime-handoff.md). The first full race from
this older candidate passed; repeated sampling was not completed.

# Randomized Quick Race â€” human handoff

Status: **READY FOR HUMAN RUNTIME**. Fixed R-AI1 has passed; this is its next
experiment. One candidate, five newly generated races, four participants.

1. In an isolated retail install, preserve the original EXE and stage
   `.research-output/r-ai1-1/randomized-candidate/MRallye.exe` as `MRallye.exe`.
   Verify SHA256
   `f9e8e556842602252ec39b2174e796f6cb67651d8f573f2565f9d2e5569bd9ac`.
   Use a genuinely fresh PlayerState/profile. Enable existing Menues/Enabled
   in loose DataGame/dev.xml if needed for Observatory; keep other data stock.
2. From the main checkout run the audited adapter with the supplied Observatory
   directory and isolated game EXE, then use **L** to launch:

   ```powershell
   python tools/r_ai1_observe.py --observatory "<Observatory directory>" --candidate "<isolated copy>/MRallye.exe"
   ```

3. Normal UI: **Quick Race / Race, Humans1, Opponents3, T1, TOMMEK DIRTBEAST
   (ID0), Ghost OFF**. Keep the same course/difficulty/rules for all samples.
   No T3 selection, progressed save or unlock is needed.
4. Generate a new race from the Quick Race frontend for each sample. After
   countdown, while cars are active, capture through action **3**, labels
   **mixed-random-race-1** through **mixed-random-race-5**. Observe the three AI
   models and motion; Broker summarizer supplies their classes/IDs. A restart
   that merely restores the same participants does not count as new generation.
5. The first samples can be short and return to frontend. **If Race Results is
   entered, restart the game process before any further capture**, even after
   frontend return. Do not request post-results or mixed-return native Dump.
6. Finish one representative mixed race, preferably the last sampled race.
   Observe progress, contacts/physics, finish, result driver identities/vehicle
   icons and stable frontend return. Preserve JSON+raw pairs and a brief visual
   observation record; screenshots are optional. No post-results Dump.

Expected: Car0 remains ID0/class0/human1/driver30. Each Car1..3 is AI2 with
independently selected class0/1/2 and a valid distinct stock ID from that class;
DriverIDs are distinct0..9. NumCars4 and NumPlayers1. AI may select ordinary
T1 cars outside the three frontend-visible initial vehicles. One sample can
legitimately be homogeneous; no guaranteed-diversity rule is enabled in MIXED.

Run this from the main checkout after collecting the five active captures:

```powershell
python tools/r_ai1_mixed_class.py summarize-general "<isolated copy>/MRallye.exe" "<race-1.json>" "<race-2.json>" "<race-3.json>" "<race-4.json>" "<race-5.json>" --observatory "<Observatory directory>"
```

It verifies exact EXE, pinned Observatory implementation, raw/JSON binding,
freshness, count/types/ID-class-family mapping, distinct drivers/IDs and three
corpus-derived named-physics canaries for every participant. It reports state
path counts without treating them as actor proof. Samples must use the same
course. At least five distinct labels are accepted; if variation is absent,
report that result rather than claiming randomization success.

FULL PASS requires varying AI class assignments/IDs, at least one simultaneous
mixed race and at least two non-player-class outcomes, matching actual models/
physics, normal AI motion/progression, and representative normal finish/results/
frontend return. Raw values alone do not prove physical identity or statistical
independence. Do not claim arbitrary classes, modes, IDs or participant counts.
After this test stop; R-AI2 capacity remains a separate future phase.
