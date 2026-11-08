# GHOST1 G1 — forced-flag runtime test

Goal: prove that the retail Ghost Mode chain (see [FINDINGS.md](FINDINGS.md)) works when its Broker flags are
set, before any menu work.

## Build

`tools/ghost1_build.py` writes a kit to a new directory:

```
python tools/ghost1_build.py --retail-exe <game>/MRallye.exe \
  --alpha-source <game>/Data.sma_unpacked/DataGx/Vehicles \
  --ghosts "<Nov 2001>/Ghosts/Italy1.bestever.t2.ghost" \
  --output .research-output/ghost1/kit-g1
```

Kit G1 (2026-11-08): `MRallye_ghost1.exe` SHA256 `32551ba71225da2357ecbc941e664bac13b4d842a43e0da53051cecff21676a2`,
25 `<Car>Alpha` folders, one seed ghost. Installed into `D:\Game\Master Rallye` as new files only
(`MRallye_ghost1.exe`, `DataGx\Vehicles\*Alpha`, `Ghosts\`); the retail EXE is untouched.

### EXE patches (retail SHA256 bf8aef32…)

| VA | Old | New | Effect |
|---|---|---|---|
| `0x449245` | `6A 00` | `6A 01` | frontend ctor sets `Race/GhostPlayback` = 1 instead of 0 |
| `0x44926A` | `6A 00` | `6A 01` | frontend ctor sets `Race/Car0/RecordSpline` = 1 instead of 0 |
| `0x48EB14` | `6A 00` | `6A 01` | race start keeps `Race/GhostPlayback` = 1 when no ghost record is found |
| `0x4AE0F0` | `51 68 B4 58 6E 00` | `B8 01 00 00 00 C3` | `Frontend/QuickRace/Ghost` reader returns 1 (= best ever; 0 = session best) |

### Alpha cars

The demo Alpha `car.dx` files (rev 131) are rejected by the R-DEMO DX Upgrader ("global-table boundary
ambiguous"), so G1 uses `--alpha-mode retail-copy`: `<Car>Alpha` = the retail `car.dx`, `wheel.dx` and `.dxt` of the
same car. The ghost code applies its own translucency flag (`0x4BFE00`). Faithful demo Alpha models are G2.

## Test procedure

1. Start `MRallye_ghost1.exe`. Quick Race, **Italy1**, a **T2** car, **no opponents**.
   The seed file `Ghosts\Italy1.bestever.t2.ghost` (Jump, 173.56 s) should appear as a translucent Jump.
2. Finish the race. Expected: the game logs `SplineManager: …` and writes/updates ghost files
   (`*.bestever.t2.ghost`, `*.sessionbest.t2.ghost`) if the time is better. Note where the files appear (game root
   `Ghosts\` or the user folder used by `0x5417D0`).
3. Restart / next race on the same course: the ghost should replay your own best run.
4. A course with no ghost file (e.g. France1): no ghost; after finishing a file should be created.
5. Optional: same with 1–3 AI opponents (watch grid order, `Race/Ghost/StartPosition`).

Record: ghost visible (Y/N), translucency look, file names and folder, crashes. The PS2 port proxy rejects ghost
races (`network_attract_ghost_or_replay`), so PS2 effects are expected to be Stock while a ghost is active.

## Rollback

Delete `MRallye_ghost1.exe`, `Ghosts\` and `DataGx\Vehicles\*Alpha` from the game folder.
