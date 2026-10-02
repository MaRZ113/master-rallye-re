# Cleanup runtime plan

Use only an isolated duplicate of the existing R5V-E0 Trooper test install.
Preserve its working Trooper loose override and use a disposable profile. Copy
in only the cleanup EXE and the unchanged `Data.sma` from
`research-output/r5v_f_1/cleanup/`.

## P0 — frontend and pre-race display only

1. Launch the game and enter Vehicle Select.
2. Confirm T1 has exactly 8 entries and local7 is physical ID26.
3. Confirm ID26 shows donor display name `TOMMEK DIRTBEAST`, stats `4/2/4/6`,
   SmallCarSheet frame3 and `Button7XPos`; preview must load Landcruiser.
4. Confirm T2 has exactly 7 entries and contains no false Bowler eighth entry.
5. Confirm T3 has 12 entries and ID25/Trooper remains selectable at local11.
6. Navigate repeatedly across T1 local6/local7, switch T1/T2/T3, leave and
   re-enter Vehicle Select, and verify stable return behavior.
7. Select ID26 and reach the Quick Race pre-race display without starting the
   race. Confirm a valid donor name appears instead of `GALOCAL UNKNOWN`.

Stop for any crash, wrong old ID selection, lost Trooper, wrong class count,
missing preview or navigation fault. Do not start a race during P0.

**P0 FULL PASS** requires all seven checks. Partial cosmetic issues must be
reported separately; a structural fault is FAIL.

## P1 — independent-record canary, after P0 FULL PASS only

1. In the same isolated install, select ID26 and run one offline Quick Race.
2. Confirm the ID26 progress marker is red and the Landcruiser donor behavior
   remains stable; return to the frontend.
3. Select original donor ID0 and inspect its marker. It must remain the stock
   donor colour.
4. Recheck ID25/Trooper remains selectable.

Do not test campaign saves, multiplayer or tracks. Report P0 and P1 separately
with tested candidate hashes if available.
