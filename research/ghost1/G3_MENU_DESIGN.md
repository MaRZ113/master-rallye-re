# GHOST1 G3 — native Ghost mode in the Quick Race menu (design)

Status 2026-11-08: research done, not implemented. G2 owner result: translucency looks like the demo (odd see-through
spots are original behaviour), Attract Mode no longer appears after restarts, replays no longer crash.

## Demo 9.3.1 flow (reference)

* `QuickModeSelect.xml` has four mode panels: `GhostMode`, `SingleRaceMode`, `CountdownMode`, `SoloMode`. The
  `GhostMode` panel holds a generic list widget `GhostType` (`StringList* = Frontend/QuickModeSelect/GhostList`,
  `Value* = Frontend/QuickModeSelect/Ghost`, `CurrentText* = Frontend/QuickModeSelect/GhostText`).
* Init `0x463260` builds the lists from the text table (`0x468EC0` vtable+0xC, group 0x3E = 4 mode names incl.
  the ghost mode; ghost type names are the existing STEEL MONKEYS BEST / BEST THIS SESSION / BEST EVER strings).
* Accept `0x463D60`: QuickRace mode = Mode + 1; when Mode == 1 it copies `Frontend/QuickModeSelect/Ghost` into the
  QuickRace ghost setting (`0x48BB00`).
* Race setup `0x447AD0`: race mode 2 (ghost) sets `Race/GhostPlayback = 1` and `Race/Car0/RecordSpline = 1`
  (`Car1` too for two players); other modes leave the frontend defaults (0).
* Race start `0x4703E0` = retail `0x48E9C0` (same GhostCar creation).

## Retail state

* `QuickModeSelect.xml` keeps `SingleRaceMode`, `CountdownMode`, `SoloMode` only; `GhostMode` and the
  `GhostList`/`Ghost`/`GhostText` keys are gone. `QuickRace.xml` still shows `GhostText`
  (`Frontend/QuickRace/GhostTypeString`).
* Mode handling, renumbered without the ghost mode: update `0x47A120` (panel = list `mode + 2`, focus states
  1/4/7 per mode via `0x525A80`/`0x525970`, right arrow enabled while `mode < 2`), init `0x47A540`, accept
  `0x47A8C0` (QuickRace mode = Mode + 1; mode 1 copies opponents/difficulty, mode 3 countdown difficulty), list
  builder `0x479BB0` (`Frontend/QuickModeSelect/ModeList`).
* Race-side code for QuickRace modes 1/2/3 is everywhere (`0x47D4C0` commit cases 1/2/3, AI generation, HUD,
  results). A brand-new QuickRace mode 4 would touch all of them.

## Proposed design (demo-faithful UI, retail-safe race logic)

1. **Menu**: append a fourth mode "GHOST" (Mode index 3) so retail indices 0..2 keep their meaning. Add a
   `GhostMode` panel (copied from the demo XML, adapted to retail layout) with the `GhostType` list widget:
   OFF is not needed in this mode; entries = BEST THIS SESSION (0), BEST EVER (1), STEEL MONKEYS BEST (2), matching
   the retail file-type indices (`0x4BC170` reads 0, `0x4BC030` reads 1).
2. **EXE (frontend)**: `0x479BB0` adds the 4th ModeList entry and builds `GhostList`; `0x47A120` accepts mode 3
   (arrow bound `< 3`, panel index, focus state for the new widget); accept `0x47A8C0` maps Mode 3 → QuickRace mode 1
   (solo/time trial, so all race-side code stays on a known path) and stores the ghost type in
   `Frontend/QuickRace/Ghost` plus a "ghost requested" flag.
3. **EXE (race)**: replace the G1 constant patches. At race setup, set `Race/GhostPlayback` and
   `Race/Car0/RecordSpline` from the ghost-requested flag (demo `0x447AD0` behaviour); restore the original
   `0x4AE0F0` reader. Recording in other modes stays optional (owner liked ghosts with AI opponents; that can be a
   setting).
4. **Loader**: every change stays a (VA, old, new) entry or a cave, for the final dinput8-style loader.

## Ghost model questions (owner, 2026-11-08)

* **Fallback when `<Car>Alpha` is missing**: `0x4BFE00` formats `Vehicles/%sAlpha/car` and `/wheel` and loads them
  via `0x4D1010`; behaviour on a missing resource is not yet traced. Options: (a) cave that checks the result and
  retries with `Vehicles/%s/car` (opaque fallback); (b) always generate Alpha folders (SDK/Workshop step for new
  cars). A config switch "translucent ghost on/off" is then just choosing the Alpha or normal path.
* **Translucency without a separate model**: the ghost entity's render object (`entity+0x50`) only gets flag
  `+0x70 |= 1` and `+0x6C = 0` from `0x4BFE00`; no per-object alpha/tint was found yet. HUD render objects do carry
  an RGBA tint (`+0x14..+0x20`, used by `0x4A74A0`), so the 3D object class must be checked for an equivalent
  field consumed by the vehicle draw path (`0x576970 → 0x561A40`). If none exists, runtime translucency needs either
  an engine hook in the vehicle draw (force blend + TFACTOR alpha for the ghost instance) or the d3d8 proxy.

## G3 implementation (2026-11-08)

Owner decisions: a separate fourth mode with a ghost type selector, exactly as in the demo; ghost-with-opponents,
record-in-all-modes and class filtering go to the INI config; Alpha models generated for all cars, with an INI
switch to use them or not.

Text table facts (retail EXE, records `(group, index, char*)`, all languages present): group 0x3E = mode names
(0 PRACTICE, **1 GHOST**, 2 RACE, 3 CHECKPOINT; retail ModeList uses 0, 2, 3), group 0x3F = ghost types (0 BEST
THIS SESSION, 1 BEST EVER, 2 STEEL MONKEYS BEST — identical to the `.ghost` file type index), group 28 index 2 =
"GHOST TYPE" label. Panels are `Egg Group = mode + 2`; widgets are `gaFrontendMultistateAI` with XML-defined
Button ID / Up Path / Down Path and Broker StringList/Value/CurrentText keys.

### Data

`tools/ghost3_frontend.py` writes a loose `DataScene/FrontendScreens/QuickModeSelect.xml`: retail file plus a
`GhostMode` list (Egg Group 5) cloned from the retail SingleRaceMode widgets — `GhostType` (button 11, label 28:2,
GhostList/Ghost/GhostText keys), `GhostTypeText`, `Mode` (button 10), `ModeText`.

### EXE (`research/ghost1/ghost3_menu_cave.asm`, cave at `0x68E390`, strings at `0x68E800`)

| Site | Change |
|---|---|
| `0x479FC0` | JMP cave `modes`: append GHOST (0x3E:1) to ModeList, build and publish `Frontend/QuickModeSelect/GhostList` (0x3F:0..2), replay `LEA ECX,[ESP+0x14]; PUSH 0x6B68A8`, JMP back |
| `0x47A1C2` | focus = `3*mode+1` (same-size rewrite of the 1/4/7 switch; GHOST = button 10) |
| `0x47A286` | right mode arrow while `mode < 3` |
| `0x47A560` | CALL cave `init`: QuickRace mode 1 with `Frontend/QuickRace/GhostMode` → report 4 (menu reopens on GHOST) |
| `0x47A8EE` | CALL cave `accept`: GHOST → QuickRace mode 1, `GhostMode = 1`, `Frontend/QuickRace/Ghost` = selected type; other modes `GhostMode = 0` |
| `0x47B871` | CALL cave `start`: `Race/GhostPlayback` = `Race/Car0/RecordSpline` = GhostMode, then the original ghost-type getter |

The G1 force patches (`0x449245`, `0x44926A`, `0x4AE0F0`) are dropped; NaN fix, progress cave, Attract redirect,
`0x48EB14` (keep playback flag without a record) and translucent Alpha stay. GHOST runs as QuickRace mode 1
(solo), so every race-side switch stays on a known path.

`tools/ghidra/AsmCave.java` now picks the shortest encoding without 0x66/0x67 prefixes (Ghidra otherwise emits
`66 E8 rel16` / `67 66 E8` for near local calls, which truncate EIP); the progress cave re-assembles byte-identical.

Kit G3: `MRallye_ghost3.exe` SHA256 `dc2ef19f4507adf6550c3e7d3bedfc3cd4b0728324264aef153c2c42b384f866`, loose
`DataScene\FrontendScreens\QuickModeSelect.xml` (read by every EXE in the folder; the retail EXE never selects
mode 3, so the extra panel stays hidden there).

### Runtime test

1. Quick Race → mode select: the mode selector cycles PRACTICE / RACE / CHECKPOINT / GHOST (localised).
2. On GHOST the panel shows GHOST TYPE with BEST THIS SESSION / BEST EVER / STEEL MONKEYS BEST; up/down moves
   between the two rows.
3. Accept, start: the ghost of the chosen type appears (Italy1 T2 has best-ever and session-best files); the
   QuickRace summary may still label the mode PRACTICE (not handled yet).
4. Back to the menu: it reopens on GHOST. Choose PRACTICE/RACE: no ghost, no recording.
5. Regression: RACE with opponents, CHECKPOINT, restarts, replays.

## INI options (next: loader phase)

Planned `[Ghost]` section in the Randomizer & Extender config (`MRallyeRandomizer.ini`, ConfigVersion 2 style,
validated by the loader):

```ini
[Ghost]
; 1 = ghost also in Quick Race RACE mode with AI opponents (uses the GHOST TYPE last chosen).
WithOpponents = 0
; 1 = record ghost files in every Quick Race mode, not only GHOST.
RecordAllModes = 0
; Which recordings may play: 0 = Any, 1 = Same class (file class = player class, current behaviour),
; 2 = Same car (also matches the recorded CarType). Later also a native menu selector.
Match = 1
; 1 = translucent <Car>Alpha ghost model; 0 = ghost uses the normal car model.
UseAlphaModel = 1
```

Notes: files are already per class (`<course>.<type>.t<class>.ghost`); `Same car` needs either the CarType check
against the loaded record (`0x4BCEB0` reads CarType) or per-car file names. `UseAlphaModel = 0` / missing Alpha
folder = redirect the two format strings at `0x4BFE00` (`Vehicles/%sAlpha/car`, `/wheel`) to `Vehicles/%s/car`,
`/wheel`; the generator in `tools/ghost1_build.py --translucent` already builds Alpha folders for every retail car
and can run for Vehicle SDK cars at install time.

## G4 — five difficulty levels, MRallyeExtras.ini, Alpha fallback (2026-11-08)

G3 has not been game-tested yet; G4 builds on it (same cave file, strings moved to `0x68EC00`).

### Five difficulty levels

ICont has five AI levels and `0x42DF50` selects `ICont/<level>/Min|Max` by `Race/DifficultyLevel` 0..4
(VEasy, Easy, Medium, Hard, Extream; absent key = 3). Quick Race wrote `level = menu index + 1`
(`INC EAX` at `0x47B8C8`), so the 3-entry menu (EASY/MEDIUM/HARD, text group 0x41) only reached levels 1..3.

| Site | Change |
|---|---|
| cave `modes` | RaceDifficultyList (EDI in `0x479BB0`) gets "VERY EASY" in front and "EXTREME" at the end (English strings; the EXE has no localised texts for them) |
| `0x47B8C8` | `INC EAX` → `NOP`: `Race/DifficultyLevel` = menu index (0 VERY EASY … 4 EXTREME) |
| `0x47A2CD` | `CMP EDI,2` → `CMP EDI,4`: difficulty right arrow up to the fifth entry |
| `0x47B70D` | summary text `text(0x41, index)` → `PUSH EBP; CALL diff` (level 0/4 → own strings, 1..3 → 0x41:level-1) |

CHECKPOINT keeps its own CountdownDifficulty list and mapping. Note: the menu value is saved in the player
profile; an old saved index now means one level lower (old MEDIUM = 1 → EASY).

### MRallyeExtras.ini

The Randomizer & Extender validator rejects unknown sections/keys (`CONFIG_UNKNOWN_SECTION`,
`CONFIG_UNKNOWN_KEY` in `dinput8.dll`), so `[Ghost]` cannot live in `MRallyeRandomizer.ini` until the loader is
extended. The EXE has no `GetPrivateProfileIntA` import; cave `ini` resolves it through the IAT
(`GetModuleHandleA` `[0x68F238]`, `GetProcAddress` `[0x68F0C0]`) and reads `.\MRallyeExtras.ini` on every call,
so edits apply without restarting. Keys (template written by the builder):

* `WithOpponents` (0): ghost also in Quick Race RACE (mode 2) with AI, type = last GHOST TYPE;
* `RecordAllModes` (0): record in every Quick Race mode (PRACTICE/RACE/CHECKPOINT). Other game modes (Cup,
  Master Rallye…) never reach `SplineManager::Commit` (`0x47D4C0` saves only for race types 1/2/3), so they would need
  a separate hook;
* `UseAlphaModel` (1): translucent Alpha model.

Start cave logic: `playback = GhostMode || (WithOpponents && mode == 2)`, `record = playback || RecordAllModes`.

### Alpha fallback

Both sprintf calls of `0x4BFE00` (`0x4BFE9C` car, `0x4BFEEE` wheel) call cave `fmt`: when `UseAlphaModel = 0`, or
`GetFileAttributesA("DataGx\Vehicles\<Car>Alpha\car.dx"/"wheel.dx")` fails, the format becomes `Vehicles/%s/car` /
`Vehicles/%s/wheel` (normal, opaque model). Alpha folders are loose-only, so the check matches what the game can
load; SDK cars without an Alpha folder fall back automatically.

### Not done yet

`Match = Any / Same Class / Same Car` (files are per class; Same Car needs a CarType check of the loaded record,
Any needs class-independent lookup) and a native selector for it; localised VERY EASY / EXTREME texts.

Kit G4: `MRallye_ghost4.exe` SHA256 `aa1908e1edcf0a4fedd7fd61c5a72bd0ae96e97daeb33bd290bc2bc5f5024de0`, 34 patch
entries, `MRallyeExtras.ini`, same XML and Alpha folders as G3/G2. `tools/ghidra/check_cave.py` validates every
branch/call of an AsmCave listing (0 errors for this cave, end `0x68E6EE`).

### Runtime test (G3 + G4 together)

1. Mode select: PRACTICE / RACE / CHECKPOINT / GHOST; GHOST panel with GHOST TYPE (see G3 steps).
2. RACE: difficulty cycles VERY EASY / EASY / MEDIUM / HARD / EXTREME; the summary shows the same text; AI pace
   visibly differs at the extremes.
3. INI: `WithOpponents = 1` → ghost in RACE with AI; `RecordAllModes = 1` → files after PRACTICE/RACE;
   `UseAlphaModel = 0` → opaque ghost; renaming one `<Car>Alpha` folder → that car's ghost is opaque, no crash.

## G4.1 — GHOST panel fixes after the first owner run (2026-11-08)

Owner run of G4: five difficulty levels work (Broker `Race/DifficultyLevel = 4` for EXTREME). GHOST panel problems:
(1) after selecting GHOST its widgets stayed drawn over other screens (also after Esc); (2) no arrows on the GHOST
rows; (3) Enter did nothing, so GHOST could not be confirmed.

Causes in the QuickModeSelect update `0x47A070`/`0x47A120`:

1. the first update shows/hides only panel groups 2..4 (`0x47A12E..0x47A164`) and the exit path hides only groups
   2..4 (`0x47A0C5..0x47A0EE`); group 5 was never hidden;
2. arrows are separate `gaFrontendArrowAI` eggs: status from `Frontend/QuickModeSelect/<Left|Right>Arrow…` keys,
   highlight from `Arrow1/2/3`, set by a jump-table switch over focus IDs 1..8 (`0x47A3CE`, `CALL 0x525800`);
3. the button result `0x45D930` is accepted only for IDs 1..8 (`CMP EAX,8; JG` at `0x47A0A9`).

| Site | Change |
|---|---|
| `0x47A0A9` | `CMP EAX,8` → `CMP EAX,0xB` (accept GHOST rows 10/11) |
| `0x47A0E1` | 14 bytes → `CALL exithide` (hide groups 4 and 5) |
| `0x47A152` | 18 bytes → `CALL initshow` (reset groups 4 and 5) |
| `0x47A3CE` | `CALL 0x525800` → `CALL focus`: sets `LeftArrowGhost` (mode 3 && ghost > 0) and `RightArrowGhost` (mode 3 && ghost < 2), maps focus 10 → 1 and 11 → 3 for the highlight switch |
| XML | `GhostLeftArrow2-2` / `GhostRightArrow2-2` (group 5, clones of the difficulty-row arrows) bound to the new keys |

Builder now refuses overlapping patch ranges (a string overlap was caught this way). Kit G4.1:
`MRallye_ghost4_1.exe` SHA256 `ce9d7a2679393edc4f374cebf4974abfe5d5320e466f351fff67f2cf310aa275` + updated XML.
