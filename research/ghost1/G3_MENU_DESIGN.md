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
