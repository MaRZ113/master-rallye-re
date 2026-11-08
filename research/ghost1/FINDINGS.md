# GHOST1 — Ghost Mode: what survives in retail and how to restore it

Date: 2026-11-08. Status: **static analysis only, not yet tested in game.**
Retail EXE SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` (Ghidra 12.1.4 headless
decompilation; addresses are VAs with image base 0x400000).

## 1. Owner-provided facts

- Ghost Mode worked in demo 8.4.1 and 9.3.1 with three modes: **Steel Monkeys Best**, **Best This Session**,
  **Best Ever**.
- The ghost car uses dedicated `*Alpha` vehicle resources, so any car can be adapted.
- After a run the game writes `Ghosts/<course>.<mode>.<class>.ghost`. Sample:
  `D:\Game\Master Rallye Nov 2001\Ghosts\Italy1.bestever.t2.ghost` (20637 bytes, Jump, Italy1).

## 2. Main result

**Ghost Mode was not removed from retail; only its entry points were cut.** The EXE still contains the complete
record, save, load and playback chain, the file-name strings and the menu strings. Missing pieces:

1. nothing sets the Broker flags `Race/Car0/RecordSpline` and `Race/GhostPlayback` to 1 (retail only resets them
   to 0);
2. no menu item sets `Frontend/QuickRace/Ghost` (ghost type);
3. no `DataGx/Vehicles/<Car>Alpha/` resources exist in retail (neither in Data.sma nor in the unpacked data). Demo
   9.3.1 ships them as GXM sources and the owner's Nov 2001 build as cooked DX, for Forester, Jump, Trooper,
   Wildcat, newRav and rav4.

## 3. Retail code map

| Address | What | Role |
|---|---|---|
| `0x449100` | `gaFrontendAI` constructor | resets `Race/GhostPlayback`, `Race/Car0/RecordSpline`, `Race/Car1/RecordSpline` to 0. No other retail code writes these keys |
| `0x48EB40` | start-grid generator | per car: if `Race/Car%d/RecordSpline` is true, creates entity `SplineRecorder%d` with AI `gaVehicleSplineRecordAI` (ctor `0x4C0B20`, vtable `0x691220`) |
| `0x4C0B20` | `gaVehicleSplineRecordAI` | reads `Race/Car%d/CarType`, `Race/RaceName`, registers a record in SplineManager (`0x4BC590`); observes `Car%d`, `Controller/Car%d`, `Race/Car%d/Time`, `Race/Car%d/Finished` |
| `0x4BCA30` | **SplineManager** singleton (`DAT_006F69E0`, 0x30 bytes) | two collections of 0x7C-byte records: loaded (+4/+8) and in-progress recordings (+0x14/+0x18) |
| `0x48E9C0` | ghost creation at race start | if `Race/GhostPlayback`: `SplineManager::Load` (`0x4BD750`), `Race/Ghost/StartPosition`, entity `GhostCar` with `gaVehicleSplinePlaybackAI`. If the start position stays -1, GhostPlayback is cleared |
| `0x4BFA10` | `gaVehicleSplinePlaybackAI` (vtable `0x6911E8`) | finds the record by `Race/RaceName`; step 0x3DCCCCCD = **0.1 s** |
| `0x4BFE00` | playback method (vtable+0x14) | loads `Vehicles/%sAlpha/car` + 4 × `Vehicles/%sAlpha/wheel` (`0x4BFFA0` = wheels), sets a translucency flag; writes `Race/Ghost/StartPosition` from the record |
| `0x4BD750` | ghost load | file name via `0x4BDA70` → `0x4BBD10` (course + type from `Frontend/QuickRace/Ghost` (`0x4AE0F0`) + class); read `0x4BBA00`; parse `0x4BCEB0` |
| `0x4BBA00` | file reader | `fopen`, checks magic **0xAB59D02E** and version **3**, payload size, then payload |
| `0x47D4C0`, `0x4CF3D0` | race end (modes 1/2/3 and 7) / attract exit | call `SplineManager::Commit` (`0x4BC3C0`) |
| `0x4BC3C0` | Commit | for each recording of a finished car: `Race/Car%d/Time`, split times (`0x4BC2B0`, `Race/SplitTime%d/Car%d`), log `SplineManager: %d %f`; unless split screen (`0x4AE2D0`) → `0x4BD1B0`. Then clears recordings |
| `0x4BD1B0` | compare and write | compares with best ever (`0x4BC030`) and session best (`0x4BC170`); writes improved file(s) via `0x4BBD10` + `0x4BB8E0` |
| `0x4A74A0` | HUD progress marker | ghost branch: colour (1,1,1,0.5), `Race/Ghost/Progress` |
| `0x4ABCE0` | Race key registration | includes `Race/GhostType` |

Retail strings (no direct code references; likely reached through text tables/formatting): `steelmonkeys`
`0x6DF348`, `bestever` `0x6DF358`, `sessionbest` `0x6DF364`, `STEEL MONKEYS BEST` `0x6CDCAC`, `BEST EVER`
`0x6CDCC0`, `BEST THIS SESSION` `0x6CDCCC`, `GHOST TYPE` `0x6CEEFC`, `GHOST`; global std::strings `.ghost`
(`0x6F6994`) and `Ghosts` (`0x6F69D4`), initialised by `0x4BB3B0` and `0x4BB500`. When saving, `0x4BD5F0` calls
`SetCurrentDirectoryA` on the game user folder (`0x5417D0`).

Retail frontend leftovers: `DataScene/FrontendScreens/QuickRace.xml` (also QuickRace2, PS2QuickRace, NetworkHost)
contains egg `GhostText` bound to `Frontend/QuickRace/GhostTypeString`. The menu strings
`Frontend/QuickModeSelect/Ghost` and `GhostList` are **absent** in retail (present in 8.4.1 and 9.3.1).

## 4. `.ghost` format (preliminary, from Italy1.bestever.t2)

Header (read by `0x4BBA00`):

| Offset | Sample | Meaning |
|---|---|---|
| 0x00 | `2E D0 59 AB` | magic 0xAB59D02E |
| 0x04 | 3 | version |
| 0x08 | 0x5091 (20625) | payload size = file size − 12 |

Payload (order from parser `0x4BCEB0`, values from the sample):

| Field | Sample | Note |
|---|---|---|
| float time (record +0x10) | 173.56 | finish time used for best ever / session comparison |
| block `0x4BCB00` | `03 00 00 00 | 00 32 24 AD 42 00 24 DF 42` | not decoded (3 + two floats ≈ 86.6 / 111.6?) |
| string (u32 len + bytes) | `Jump` | CarType → ghost loads `Vehicles/JumpAlpha` |
| string | `RaceTest/Italy1` | RaceName, record lookup key |
| 8 × 4-byte fields | 0, 1, 2.5f, 0, 0, 1.7f, 1.7f, 0.1f | +2,+3,+5..+10; last = 0.1 s sample step (matches playback) |
| u32 sample count + samples | 0x3B8 = 952 | key frame = 3 float position (e.g. −2457.1, 163.2, −913.4), then 13-byte delta frames; a key frame roughly every 10 samples |
| u32 N + N × float | file tail | monotonic floats (~178…183) — probably per-sample progress/time or splits (`+0x40`) |
| 1 + 4 + 16 + 4 + 1 + 1 bytes | tail | flags/colour/parameters (+0x13…+0x69) |

The exact sample layout and the `0x4BCB00` block still need `0x4BB160`, `0x4BF560`, `0x4BCB00` and writer `0x4BB8E0`.

## 5. Demo vs retail (known so far)

- `Frontend/QuickModeSelect/Ghost` / `GhostList` exist in 8.4.1 and 9.3.1 and are missing in retail → the mode
  selector was removed from the menu. `master.steelmonkeys.com` exists in 9.3.1 — probably the source of
  "Steel Monkeys Best" (no `*.steelmonkeys.*.ghost` file ships in any build).
- 9.3.1 and retail share `.ghost`, `Ghosts`, `bestever`, `sessionbest`, `steelmonkeys` and the file magic/version,
  so the format most likely did not change. **Compatibility check:** retail should load `Italy1.bestever.t2.ghost`
  from Nov 2001.

## 6. Restoration plan

**G1 — enable without a menu (minimal, cheap).** Set `Race/Car0/RecordSpline=1`, `Race/GhostPlayback=1`,
`Frontend/QuickRace/Ghost=<type>` before a Quick Race (proxy/Broker setters as in PAUSE-MENU1, or constant patches in
`0x449100`). Put `JumpAlpha` (DX from Nov 2001) and `Ghosts\Italy1.bestever.t2.ghost` next to the game. Expected:
a ghost Jump on Italy1, and `Ghosts\Italy1.bestever.t2.ghost` / `sessionbest` written after the finish.
Risks: index mapping of `Frontend/QuickRace/Ghost` (0/1/2 → steelmonkeys/sessionbest/bestever is unconfirmed);
`Race/Ghost/StartPosition` = -1 disables the ghost.

**G2 — Alpha cars for the whole roster.** Six cars exist in the demos; for the rest (and SDK cars) build a
`<Car>Alpha` generator from `car.dx`/`wheel.dx` (demo pattern: reduced model without crew and with simplified
materials; translucency is set by code, flag in `0x4BFE00`). Compare JumpAlpha with Jump in Nov 2001 to replicate
the recipe.

**G3 — native menu.** Restore the Quick Race ghost selector (OFF / Steel Monkeys Best / Best This Session / Best
Ever) following 9.3.1 `QuickModeSelect.xml` and the demo EXE handler (find who writes `Race/GhostPlayback` and
`RecordSpline` there).

**G4 — Steel Monkeys Best.** Ship our own reference `*.steelmonkeys.*.ghost` files (or load them from a mod folder).

## 7. Open questions

- Who sets `Race/GhostPlayback`, `Race/Car0/RecordSpline`, `Race/Ghost/StartPosition` in the demos (demo EXE not
  decompiled yet).
- Exact file name: `0x4BBD10` takes text IDs 0x5A (type) and 0x4F (class) from text table `0x485CF0` and separator
  `DAT_006DD600`; `<RaceName without RaceTest/>.<type>.<class>.ghost` is inferred from the sample, not yet confirmed
  in code.
- Which race modes record: Commit runs for modes 1/2/3 and 7 in `0x47D4C0`.
- PS2 port coexistence: the proxy race certificates reject ghost races (`network_attract_ghost_or_replay`), so PS2
  effects stay Stock while a ghost is active until the certificate admits GhostPlayback.
