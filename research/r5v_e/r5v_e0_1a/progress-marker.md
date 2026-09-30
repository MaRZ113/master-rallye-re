# Race progress marker — frame and color

This is separate from the top-left TimeDiffs image candidate and from the Race
Results player icon.

## Frame source

Retail `Hud0.xml` / `Hud1.xml` define `ProgressCar0` through `ProgressCar7` as
`hud\hud-template`, image bank index 3. The referenced frame is the shared
generic marker. The updater at `0x004A74A0` handles progress and color values;
it does not read `VehicleRecord` or `smallcarsheet_index`.

## Color source

`0x004A74A0` references `Race/Car%d/Colour` at `0x006E51A8`. Its decompilation
reads the returned four-float color into state fields `+0x3C..+0x48`, then
writes those components into the marker render object at `+0x14..+0x20`.
The ghost path has an explicit white/half-alpha override. The scene's
`ObjectColour` default is white with alpha `0.50`.

Classification: **PARTICIPANT_COLOR**, applied as a UI object tint. The art
frame is shared; the ordinary marker tint is obtained from the race
participant color property. No color patch or second diagnostic candidate
was created.
