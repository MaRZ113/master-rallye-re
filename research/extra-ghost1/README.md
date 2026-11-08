# EXTRA-GHOST1 — Ghost Mode and five difficulties in the Extra Options loader

GHOST1 (`master-rallye-re-ghost`, branch `research/ghost`, last change 08e18ec) proved Ghost Mode
and five Quick Race difficulty levels with patched EXE copies (`MRallye_ghost.exe`). This phase moves
the same behaviour into the `dinput8.dll` Extra Options loader so the retail `MRallye.exe`
(SHA-256 `bf8aef32…`) stays unmodified on disk.

## Why the caves moved

The GHOST1 caves lived in the `.text` slack `0x68E2A0..0x68EE20` and a `.data` slack buffer at
`0x70CC00`. The SDK33 roster extension (`native-patch-manifest.json`, `collection_delta_105..262`)
writes the whole `.text` slack `0x68E2A0..0x68F000`, so the two cannot coexist at the old addresses.
The loader now owns a fixed region at `0x70020000` (directly after the F3 code/data regions):

| Region | Protection | Contents |
|---|---|---|
| `0x70020000..0x70020FFF` | RX | progress cave `+0x2A0`, menu cave `+0x390`, strings `+0xC00` (GHOST1 layout, same offsets) |
| `0x70021100` | RW | absolute path of `MRallyeExtraOptions.ini` (0x200 bytes, replaces `.\MRallyeExtras.ini`) |
| `0x70021C00` | RW | summary text buffer (was `0x70CC00`) |

`tools/build_extra_ghost_plan.py --assemble` reassembles both GHOST1 sources (`source/`) with
`tools/ghidra/AsmCave.java` at their original bases and requires the deployed GHOST1 bytes
(SHA-256 pinned), then assembles the address-translated copies (`relocated/`). An independent model
checks that every relocated instruction has the original length and differs only in translated
literals or rel32 branches to the same retail targets (7 progress + 103 menu instructions changed).
The listings are committed, so `--check` reproduces `src/native/rmod1/extra_ghost_plan.hpp` without
Ghidra. `plan-report.json` records hashes and offsets.

## Hook table

19 retail hook sites, each with exact expected bytes from the pinned retail EXE, applied through
`rmod2_boot::apply_native_writes` (same transaction as the F3 plan: pristine `PAGE_EXECUTE_READ`
image pages, other threads suspended and no EIP inside a target, readback, full rollback):

* Ghost (15): sample FABS fix, progress hook, mode focus / right arrow / init / accept / accept IDs /
  exit-hide / first-show / ghost-type focus, race-start flags, summary mode text and ghost type,
  Alpha car/wheel name fallback.
* Difficulty (3): level = menu index, right arrow bound 4, summary text.
* Both (1): list-builder jump into the menu cave.

Not ported: G1 forced constants (replaced by the G3 menu), the `.text`/`.data` VirtualSize header
edits (file-only), and the AttractMode redirect at `0x464F69` (the D3D8 proxy's
`legacy_attract_guard` already applies it on the retail EXE).

When one feature is disabled its cave entry points stay unreferenced and the shared list-builder cave
is trimmed with NOPs (`ghost-mode-entry` 9 bytes at `+0x396`, `difficulty-list-entries` 26 bytes at
`+0x39F`), so Ghost and Difficulty are independent.

## Configuration (`MRallyeExtraOptions.ini`)

```ini
[General]
ConfigVersion=1

[Ghost]
Enabled=1
; re-read by the caves at every Quick Race start / ghost load
WithOpponents=0
RecordAllModes=0
UseAlphaModel=1

[Difficulty]
; 4 = retail list, 5 = VERY EASY..EXTREME
Levels=5
```

The strict Extra Options validator accepts both sections (all keys optional, `[Ghost]` values 0/1 only
because the caves use `GetPrivateProfileIntA`). `MRallyeRandomizer.ini` and its validator are
unchanged. `MRallyeExtras.ini` from the GHOST1 EXEs is no longer read.

Ghost additionally requires the loose `DataScene/FrontendScreens/QuickModeSelect.xml` with the GHOST
panel (`tools/ghost3_frontend.py` in the ghost checkout); without it the loader logs
`GHOST_UNAVAILABLE` and installs only the difficulty hooks. `<Car>Alpha` folders remain optional
(fallback to the normal model). Remove that XML when Ghost is disabled: retail code does not hide
panel group 5.

The module runs after the Randomizer boot regardless of its result and is disjoint from both the F3
plan (17 operations) and SDK33 (264 operations) — verified offline by range comparison.

## Evidence

* `extra_options_tests.cpp`: new accepted/rejected `[Ghost]`/`[Difficulty]` cases, PASS with
  `research/r-mod1/MRallyeRandomizer.release.ini`.
* Candidate `.research-output/extra-set1/ghost-01` (no graphics rebuild). Live smoke launch of the
  retail EXE in an isolated host: `GHOST_READY ghost=1 five_difficulties=1 hooks=19`; with Ghost off,
  difficulty on and the release Randomizer INI: `NATIVE_INSTALL_COMPLETE operations=16` and
  `GHOST_READY ghost=0 five_difficulties=1 hooks=4`. Process alive after 25 s in both runs.
* Not yet shown: menu navigation, ghost race/record/playback, summary texts through the loader,
  and the SDK33 integrated launcher combination. These are owner tests.
