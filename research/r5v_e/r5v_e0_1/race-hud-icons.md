# Race HUD icons — player marker and progress marker

The HUD evidence is split into two questions because the owner's phrase
“in-race 1P icon” may refer to an object distinct from the stage progress
marker.

## Progress marker

Retail DataScene/Hud/Hud0.xml and Hud1.xml define ProgressCar0 through
ProgressCar7 with:

- model hud/hud-template;
- Image Bank Index 3;
- Use CarID = True;
- Display Car ID = 0 through 7.

The referenced hud-template_003_000.dxt is 16x8, 532 bytes, SHA-256
2485192edf007f5dc97a455be87ae8f6b18c01719da4c7b4d60f396c577ade93. Its
decoded art is a small generic white-car silhouette, not a Trooper or Astero
model illustration.

The HUD reader/updater functions are FUN_004A72A0 and FUN_004A74A0; the
component constructor is FUN_004A71B0. The updater uses the configured display
slot to query Race/CarN/Progress and Race/CarN/Colour and places the shared
template marker. It does not consult VehicleRecord, CarID, the internal vehicle
name or the Race Results selector field.

Conclusion for the progress icon: its source is the same generic frame 3 for
every display slot. The owner's “Astero” description is a visual attribution;
the code and art do not support a vehicle-specific Astero mapping.
Classification: source **PROVEN**; Astero-specific identity **not supported**.

## In-race player 1P icon candidate — R5V-E0.1a

Further retail analysis identifies `TimeDiffs` as the leading scene-object
candidate. Hud0/Hud1 define an Egg with `AI Name="gaHudTimeDiffsAi"`; the
corresponding constructor embeds that name and creates three child pointers.
The object is separate from `ProgressCar0` and has a scene position distinct
from the progress bar.

Raw function `0x004AAE70` reads a participant's `Race/CarN/CarID`, indexes the
vehicle registry, reads `VehicleRecord[CarID] + 0x1C`, then passes the value to
an embedded image selector. This strongly supports the same
`smallcarsheet_index` field driving a per-participant TimeDiffs image.

Two static joins remain open. Ghidra reports no direct caller to
`0x004AAE70`, and the inspected vtable does not establish a dispatch to it.
The TimeDiffs XML uses `en2d Model Name="Null"`; the executable's
`4BFrontend/RaceResults/SmallCarSheet` string has no direct xrefs in the
current export. The isolated `trooper-smallsheet29` candidate is documented in
`research/r5v_e/r5v_e0_1a/runtime-diagnostic.md`. The owner reported FULL PASS:
the top-left 1P icon and Race Results show Forklift frame 29; the separate
progress marker remains aquamarine and Trooper gameplay remains normal.

## Evidence classification

- generic progress marker frame and asset: **PROVEN** by scene and updater.
- progress marker tint consumer: `Race/CarN/Colour` Vector4-like value copied
  to the render object; **PROVEN** by the updater path. The property producer
  and semantic identity remain **UNKNOWN** (R5V-E0.1b).
- TimeDiffs small-image selector: **RUNTIME_CONFIRMED** by the isolated
  selector test for the owner-observed top-left 1P icon and Race Results.
- 1P icon equals ProgressCar0: **not supported**; ProgressCar0 remains the
  separate bottom progress-bar marker.
- top-left image equals a TimeDiffs child: **RUNTIME_CONFIRMED** by owner
  observation of the `0 -> 29` diagnostic.
- owner runtime visual label “Astero”: retained as owner-reported observation,
  not as a verified sprite identity.
