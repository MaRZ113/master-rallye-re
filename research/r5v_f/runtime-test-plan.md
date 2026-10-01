# R5V-F runtime plan

## Current gate

**P0 candidate ready; human frontend test pending. No race yet.** Use the
ignored package in `research-output/r5v_f/runtime-test/` and a disposable copy
of the already working R5V-E0 Trooper test installation. Preserve its Trooper
loose override and disposable profile. Do not use the main game installation.

## P0 — frontend only

1. Install the staged `MRallye_id26_t1_test.exe` and `Data.sma` in the isolated
   test copy.
2. Launch and confirm the game boots.
3. Enter T1 Vehicle Select and move from local6 to local7.
4. Confirm local7 is ID26, displays `TOMMEK DIRTBEAST`, shows stats `4/2/4/6`,
   shows carsheet frame3 at Button7XPos, and previews Landcruiser
   `complete.dx`.
5. Move backward and forward repeatedly across local6/local7.
6. Switch T1→T2→T3→T1. Confirm T2 has seven entries, T3 has twelve, and ID25
   Trooper remains selectable with T3_Car12 visible.
7. Leave and re-enter Vehicle Select; repeat navigation; exit normally.

Do not start a race during P0. Stop on any crash, remapped old vehicle,
missing preview, wrong widget identity, or class navigation corruption.

### P0 classification

- **FULL PASS:** boot, T1 eighth entry, donor identity/stats/icon/preview,
  stable navigation, unchanged T2/T3 and ID25.
- **PARTIAL:** only a cosmetic placement or label issue, with ID26 selection
  and no structural fault.
- **FAIL:** crash, old-ID remap, class corruption, or unusable ID26 selection.

P1 must not start until the owner reports P0 FULL PASS.

## P1 — offline Quick Race, after P0 only

Use the same candidate and disposable profile. Select T1 local7/ID26 and run
offline Practice/Quick Race. Check Landcruiser `car.dx`, `wheel.dx`, physics,
collision, damage and camera; top-left SmallCarSheet icon; progress-marker
colour; meaningful driving; full-stage completion; Race Results; return to
menu; then verify donor ID0 and Trooper ID25 still work. Capture debug output
for resource lookup. Do not use campaign persistence or multiplayer.

## Candidate identity

The executable and Data.sma hashes are `DFF9…48ABC` and `D21E…70FA`. Exact
values, source hashes, archive-member diff, and operation manifest are in
`research-output/r5v_f/runtime-test/VALIDATION.json` and
`patch-manifest.json`.
