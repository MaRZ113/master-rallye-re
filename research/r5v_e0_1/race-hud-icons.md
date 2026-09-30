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

## In-race player 1P icon

ProgressCar0 is the configured marker for race display slot 0 and is a
plausible object behind the owner's 1P observation. However, no screenshot was
provided and the inspected Hud0/Hud1 scenes contain no separate object
explicitly named for an Astero/1P vehicle image. The raw HUD updater above
does not select a per-vehicle icon.

Therefore the exact graphic that the owner describes as “the icon next to
1P” remains **UNKNOWN**. If it is ProgressCar0, it uses the generic frame 3;
if it is a separate HUD element, its producer and selector are not yet
identified. Do not carry an Astero-specific race_player_icon into a generic
profile based on this evidence.

## Evidence classification

- generic progress marker frame and asset: **PROVEN** by scene and updater.
- per-vehicle HUD icon selection: **not present in this path**.
- 1P icon equals ProgressCar0: **UNKNOWN**, plausible but not directly matched.
- owner runtime visual label “Astero”: retained as owner-reported observation,
  not as a verified sprite identity.
