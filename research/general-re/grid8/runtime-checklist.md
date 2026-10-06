# R-GRID8 human runtime checklist

UI ordering is not independently mapped in this phase. The checklist follows the canonical retail RaceTest corpus grouped by country; aliases stay attached to the physical resource.

## Prepare the isolated test copy

1. Copy the pristine retail game folder to a disposable test directory. Do not replace the corpus EXE or use a progressed save. Put `.research-output/general-re/grid8/MRallye.exe` in that copy as `MRallye.exe`.
2. Verify the staged executable is exactly `75942c0b65147b96b8b2254ee536f6aefc7f3a501c23d12be640f85a562680ac` with `Get-FileHash <staged-MRallye.exe> -Algorithm SHA256`.
3. Start that staged game and use Quick Race → Race, Humans=1, visible Opponents=Three, Class=T1, player CarID0 / TOMMEK DIRTBEAST, Ghost=OFF. Keep the local/offline mode and do not load Replay.

## Capture and classify one start

While the race is active (after all eight cars spawn), run from the `master-rallye-re-general` root:

```powershell
python tools/r_grid8_observe.py --observatory "D:\Game\Master Rallye Pristine\Observatory" --candidate "<staged-install>\MRallye.exe" grid8-<course-slug>
```

Use the snapshot JSON path printed by the tool. Its `.dump.bin` sidecar is required. Validate it with:

```powershell
python tools/grid8_audit.py check-capture --candidate "<staged-install>\MRallye.exe" --observatory "D:\Game\Master Rallye Pristine\Observatory" --snapshot "<capture>.json" --course <CanonicalCourse>
```

Observe the countdown and first 5–15 seconds: check Car0..Car7 independently, visible spacing, static objects, boundary/terrain contact, and any immediate impulse. Then exit normally to the frontend; do not enter Results and do not run native Debug→Dump after Results. Return to Quick Race and select the next course. The false-Attract fix is present; if the menu/race lifecycle changes unexpectedly, record it and restart rather than hiding it.

The checker can prove Broker state only, not visible actors or physical clearance. Record exactly one primary status in `grid8-audit.json`; for every non-clean result, add issue tags, affected CarN slots, a capture label, and a useful note. Keep screenshot references local and do not commit runtime captures/screenshots.

## France

- [ ] `France1` — scene ID(s) `0` — `grid8-france1`
- [ ] `France2` — scene ID(s) `1` — `grid8-france2`
- [ ] `France_M` — scene ID(s) `22` — `grid8-france-m`
- [ ] `France_S1` — scene ID(s) `24,36` — `grid8-france-s1`
- [ ] `France_S2` — scene ID(s) `11` — `grid8-france-s2`
- [ ] `France_W` — scene ID(s) `15` — `grid8-france-w`
- [ ] `France_W_flip` — scene ID(s) `30` — `grid8-france-w-flip`

## Italy

- [ ] `Italy1` — scene ID(s) `2` — `grid8-italy1`
- [ ] `Italy2` — scene ID(s) `3` — `grid8-italy2`
- [ ] `Italy3` — scene ID(s) `4` — `grid8-italy3`
- [ ] `Italy_M1` — scene ID(s) `29,38` — `grid8-italy-m1`
- [ ] `Italy_M1_flip` — scene ID(s) `33` — `grid8-italy-m1-flip`
- [ ] `Italy_M2` — scene ID(s) `19` — `grid8-italy-m2`
- [ ] `Italy_S1` — scene ID(s) `18` — `grid8-italy-s1`
- [ ] `Italy_S2` — scene ID(s) `12` — `grid8-italy-s2`
- [ ] `Italy_S3` — scene ID(s) `25` — `grid8-italy-s3`
- [ ] `Italy_S3_flip` — scene ID(s) `35` — `grid8-italy-s3-flip`
- [ ] `Italy_S4` — scene ID(s) `10` — `grid8-italy-s4`
- [ ] `Italy_W1` — scene ID(s) `23` — `grid8-italy-w1`
- [ ] `Italy_W2` — scene ID(s) `14` — `grid8-italy-w2`

## Spain

- [ ] `Spain1` — scene ID(s) `5` — `grid8-spain1`
- [ ] `Spain2` — scene ID(s) `6` — `grid8-spain2`
- [ ] `Spain_M` — scene ID(s) `26` — `grid8-spain-m`
- [ ] `Spain_S1` — scene ID(s) `16` — `grid8-spain-s1`
- [ ] `Spain_S1_flip` — scene ID(s) `32` — `grid8-spain-s1-flip`
- [ ] `Spain_S2` — scene ID(s) `28` — `grid8-spain-s2`
- [ ] `Spain_W` — scene ID(s) `21` — `grid8-spain-w`
- [ ] `Spain_W_flip` — scene ID(s) `34` — `grid8-spain-w-flip`

## Turkey

- [ ] `Turkey1` — scene ID(s) `7` — `grid8-turkey1`
- [ ] `Turkey2` — scene ID(s) `8` — `grid8-turkey2`
- [ ] `Turkey3` — scene ID(s) `9,37` — `grid8-turkey3`
- [ ] `Turkey_m` — scene ID(s) `20` — `grid8-turkey-m`
- [ ] `Turkey_s1` — scene ID(s) `27` — `grid8-turkey-s1`
- [ ] `Turkey_s2` — scene ID(s) `13` — `grid8-turkey-s2`
- [ ] `Turkey_s2_flip` — scene ID(s) `31` — `grid8-turkey-s2-flip`
- [ ] `Turkey_w` — scene ID(s) `17` — `grid8-turkey-w`

## Three-course smoke

1. `Italy_S4` — historical Track10 eight-car full-lifecycle reference and reported launch/geometry anomaly. Recheck the affected slot; do not presume this course is clear.
2. `France1` — first non-Italy course smoke; physical clearance remains untested.
3. `Spain1` — cross-country smoke; physical clearance remains untested.

No distinct course is documented as an eight-car `PASS_CLEAR` before R-GRID8. Italy_S4 is both the historical eight-car lifecycle reference and the reported geometry concern; this checklist preserves that ambiguity instead of inventing a known-safe course. France1 and Spain1 are prospective smoke cases, not prior passes.

After each smoke: write the result with `python tools/grid8_audit.py record --course <name> --status <STATUS> ...`; do not proceed after a severe structural/physics anomaly until reviewed.
