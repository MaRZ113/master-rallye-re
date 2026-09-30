# R5V-E0.1a — HUD SmallCarSheet selector

Date: 2026-09-30
Build: retail PC executable and retail `Data.sma` extraction.

## Result

The existing `VehicleRecord[25] + 0x1C` value is named
`smallcarsheet_index` for the examined selector consumers. A profile-driven
diagnostic candidate was generated from the retail source and the existing
Trooper profile. It changes that selector from 0 to 29. The original retail
executable and game data were not modified.

The Race Results path is statically proven by R5V-E0.1. A second HUD helper at
`0x004AAE70` reads a participant's `Race/CarN/CarID`, indexes the vehicle
registry, reads the same `+0x1C` field and passes it to an embedded image
object. Its code and the `TimeDiffs` HUD scene object strongly support the
reported top-left-icon hypothesis. The remaining static gap is the dispatch
edge: Ghidra reports no direct caller for `0x004AAE70`, and the visible `1P`
object is not named explicitly in the scene XML. The generated runtime test
is intended to settle that edge.

**Runtime status: WAITING FOR HUMAN TEST.** No runtime result is claimed.

## Static identity findings

- `Hud0.xml` and `Hud1.xml` each define `Egg Name="TimeDiffs"` with
  `AI Name="gaHudTimeDiffsAi"`. Their 2D positions are `(20, 380)` and
  `(20, 150)` respectively. The same scenes separately define `ProgressCar0`
  through `ProgressCar7` with `hud\hud-template`, image bank index 3.
- `0x004AAA30` constructs a `gaHudTimeDiffsAi` object and stores vtable
  pointer `0x00691058`; its factory allocates `0x9C` bytes. It initializes
  child slots at `+0x0C`, `+0x10`, `+0x14` and selector state at `+0x8C` to
  `+0x94`.
- Raw assembly at `0x004AAE70` uses those child slots. Its final path resolves
  a participant CarID, calls registry accessor `0x0045A3C0`, calculates
  `registry_base + CarID * 0x34 + 0x20`, and calls `0x004E1FF0` on an embedded
  image object. Given the registry's first-record offset `+4`, that read is
  `VehicleRecord[CarID] + 0x1C`.
- The `Race/Car%d/CarID` key is composed through the race-state path helper;
  `0x004ABCE0` registers `/CarID` alongside `/CarType`, `/WheelType`,
  `/CarClass`, and `/Colour`.
- The scene gives `TimeDiffs` an `en2d Model Name` of `Null`, so the exact
  child image resource binding is not declared in that XML. The executable
  string `4BFrontend/RaceResults/SmallCarSheet` at `0x006E545E` has no direct
  string xrefs in the current Ghidra export; it is not treated as proof of
  this HUD object's binding.
- The separate Race Results producer/consumer path is already proven:
  participant CarID -> record `+0x1C` -> `Frontend/RaceResults/CarN` -> image
  selector.

Detailed instruction and confidence notes are in
[hud-smallsheet-dataflow.md](hud-smallsheet-dataflow.md).

## Selector and art inventory

Retail has 30 `smallcarsheet_NNN_000.dxt` files, indexed 0 through 29. Each is
2,068 bytes and 32x16. Cross-checking the first initializer argument for all
25 normal retail records against the newly identified `+0x1C` consumer gives
these selector values in registry order: `[9,17,22,15,1,16,20,13,4,7,24,19,14,26,3,25,0,5,11,10,2,27,6,8,28]`. Frames 12, 18, 23 and 29 are not selected by any normal retail record. Frame 29 visibly matches Forklift art, strongly supporting dormant Forklift frontend art, but it does not establish the historical ID25 value. Frame 12 appears blank; frames 18 and 23 remain visually unidentified. See [validation.md](validation.md).

The existing Trooper profile keeps selector 0 and remains byte-identical to
the previously generated E0 candidate. The new `trooper-smallsheet29` profile
is otherwise identical: its only executable-byte difference is the original
initializer's selector argument, 0 to 29.

## Progress marker

The bottom progress marker remains a separate path. It uses shared
`hud-template` frame 3. Its updater reads `Race/CarN/Colour` and applies that
RGBA to the marker object's color fields; this is a participant-color tint,
not a per-vehicle art selector. No color diagnostic was made. See
[progress-marker.md](progress-marker.md).

## Next gate

Run the instructions in the ignored candidate directory and return exact
observations for the 1P icon, bottom progress marker and Race Results icon.
The candidate stays isolated under
`.research-output/r5v_e0_1a/runtime-test/`. Do not begin R5V-F until that
runtime result is known.
