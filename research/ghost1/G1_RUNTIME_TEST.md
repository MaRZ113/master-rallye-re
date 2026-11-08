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

## G1 result (owner, 2026-11-08)

Works: the ghost appears and drives (also with AI opponents; the start order sometimes changes when opponents are
set), ghost files are written and overwritten on improvement, no crashes. Files land in `<game>\Ghosts\`.
Defects: (1) at some spots the ghost hard-desyncs and flies around the map; (2) the ghost icon on the HUD progress
bar does not move (it moved in the demo).

## Defect 1 — NaN orientation samples (fixed in G1.1)

`tools/ghost_file.py` decodes `.ghost` files byte-exactly (all owner files end exactly at the declared payload size)
and audits them. Sample codec (decoder `0x4BADC0`, encoder `0x4BAA10`):

* position: key frame (3 float) every 11 samples or when any axis moves more than 10 m; otherwise int16 deltas
  (X/Z `s*10/32767`, Y `(s-0x4000)*10/16383`), closed-loop against the decoded position. Overflow is handled by
  forcing a key frame, so position coding is sound;
* orientation: forward X as int16/32767, forward Z as int16/16383 with ±0x4000 bias carrying the sign of forward Y,
  and forward Y rebuilt as `sqrt(1 - x² - z²)`; roll as a signed byte (`sign·(b/127)²·π`);
* then steering byte, 4 suspension bytes (−0.8…0.25), wheel-spin byte.

For a level car `x² + z²` quantises slightly above 1 (radicand down to −5.3e−5), `FSQRT` returns NaN, and the
Catmull-Rom playback (`0x4BFAE0`, 4-sample window) produces a NaN matrix for about 0.8 s. Owner files: Italy1 8/866
and Italy3 14/770 NaN samples; the demo-recorded `Italy1.bestever.t2.ghost` has 5 as well, so the bug is original.

G1.1 patch at `0x4BAF50`: `D9 44 24 20 D8 4C 24 20 DE E9 D9 FA` → `D9 44 24 20 D8 C8 DE E9 D9 E1 D9 FA`
(`FMUL [esp+20]` → `FMUL ST0,ST0`, freeing two bytes for `FABS` before `FSQRT`). Recomputed forward Y on the NaN
samples is 0.003–0.007, consistent with neighbours. It fixes existing files too (decode-side only).

Also seen: 20–40 m jumps in 0.2 s at key frames are real car resets after a roll (roll ≈ π just before). Playback
interpolates across them with Catmull-Rom, so the ghost briefly arcs to the reset point. Not fixed yet.

G1.1 kit: `MRallye_ghost1_1.exe` SHA256 `969dc0a464dd04f826629c68100fd1eb085729c57c1541cdfcdc39238e9a86fd`
(G1 patches + the FABS patch), installed next to `MRallye_ghost1.exe`; Alpha folders and ghosts unchanged.

## Defect 2 — static HUD ghost icon (open)

HUD marker `0x4A74A0` reads `Race/Ghost/Progress` for the ghost slot. No retail code writes that key; the playback
only publishes `Race/Ghost/Position` (`0x4BFDC9`). Car progress (`Race/Car%d/Progress`, `Rank`, `LastMarker`) is
produced by `gaRaceLineAI`. Next: compare with demo 9.3.1 to find the original ghost progress producer.

G1.1 owner result (2026-11-08): the ghost no longer flies.

## Defect 2 fix — G1.2 ghost progress cave

Demo 9.3.1 `gaRaceLineAI` (ctor/init `0x46DB40`, update `0x46D890`) interned `Race/GhostPlayback`,
`Race/Ghost/Position`, `Race/Ghost/Progress` and, while GhostPlayback was set, wrote
`Progress = nearest RaceLine point index / (count - 1)` (brute-force over 0x48-byte RaceLine records, position at
+0x38). Retail rewrote the car branch (windowed search + interpolation, `0x48AE30`) and dropped the ghost branch.

G1.2 restores it without touching `gaRaceLineAI`:

| Patch | Bytes | Effect |
|---|---|---|
| file offset `0x218` | `.text` VirtualSize `0x28D294` → `0x28E000` | code cave inside the section |
| `0x68E2A0` | 231-byte cave (`research/ghost1/ghost_progress_cave.asm`, assembled by `tools/ghidra/AsmCave.java`) | calls the original Position setter, then computes and sets `Race/Ghost/Progress` |
| `0x4BFDE8` | `E8 F3 8C 01 00` → `E8 B3 E4 1C 00` | playback update calls the cave instead of `0x4D8AE0` |

Helper ABI verified from callee returns: `0x4D8AE0`/`0x4D7ED0` thiscall RET 8, `0x4D0580`/`0x4E4D20` RET 4,
`0x4D8EC0`/`0x4E51C0` plain RET. All cave branches are short (a 66-prefixed rel16 Jcc chosen by the assembler for
long branches would truncate EIP; the cave duplicates the epilogue to stay short).

G1.2 kit: `MRallye_ghost1_2.exe` SHA256 `dbf7c7acf5fdfb55109c5ebaadd6ec785f2cd811b9a53c8209c47fd70a62ce54`
(G1.1 + progress cave). Test: the ghost icon on the progress bar should move with the ghost.

## Translucency (G2, open)

The ghost is opaque in G1.x because `<Car>Alpha` = retail resources. Demo Alpha folders differ from the normal car:
every GXI texture has alpha 0x7F instead of 0xFF (e.g. `JumpAlpha/Black-tga.gxi`), and the Alpha models are cooked
separately (different `car.gxm`). `0x4BFE00` itself only sets a flag (`+0x50 → +0x70 |= 1`) and clears `+0x6C`;
it does not make the model translucent. G2 = build Alpha DX with half-alpha BGRA `.dxt` textures and alpha-blended
draw materials (retail `.dxt` is a 20-byte header + uncompressed BGRA).

G1.2 owner result (2026-11-08): the ghost icon on the progress bar moves.

## G2 — translucent ghost + no forced AttractMode

### Forced AttractMode after restarts

The legacy Loading media check (`0x464E40`, see R-ATTR1 in
`modernization/renderer/docs/r-attr1/exact-retail-guard.md`) sets `Race/AttractMode` on every odd loading when the
CD check fails. The d3d8 renderer's `legacy_attract_guard` applies the fix in memory **only on the exact retail
EXE**, so it never ran on the patched ghost EXEs and Attract Mode came back after restarts. G2 adds the same
5-byte redirect to the file: `0x464F69` `68 84 1F 6B 00` → `E9 D8 FF FF FF` (JMP `0x464F46`, stock `Race/Starter`
path). The idle MainMenu Attract timer is untouched.

### Translucent Alpha cars

Demo Alpha folders differ from the normal cars by texture alpha 0x7F and blended materials. `tools/ghost1_build.py
--translucent --vehicles-src <research/vehicles>/src` applies the same recipe to the retail-copy Alpha folders:

* every physical draw of `car.dx` and `wheel.dx`: draw core `+0x20` byte0 = 1 (alpha on), byte1 = 0 (alpha test
  off) → SRCALPHA/INVSRCALPHA blending (`master_rallye.material_semantics`); depth-write bit (`+0x24` bit 2) kept;
* every `.dxt` (20-byte header + BGRA): alpha × 127/255 (0xFF → 0x7F, cut-outs stay 0).

Jump: 26 of 30 draws switched to blend (4 were already blended glass), 29 textures. 25 cars total.

G2 kit: `MRallye_ghost2.exe` SHA256 `f1e6b77624dfc8f4973ff999e00c7b4bc88cfb49e9c5b7ea72c0dca7361232a9`
(G1.2 + AttractMode redirect), translucent `DataGx\Vehicles\*Alpha` replacing the G1 copies (shared by all ghost
EXEs). Test: translucency look, sorting artefacts against the world/own car, Restart several times (no Attract
Mode), replays.

Loader note ([release plan](FINDINGS.md)): every EXE change here is a (VA, old bytes, new bytes) table entry; the
cave and the VirtualSize edit become an allocated executable block plus a CALL rewrite in the final loader DLL.
