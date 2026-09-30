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

The R5V-E0.1b xref audit confirms the consumer but does not find the producer
of `Race/CarN/Colour`. The ordinary-path property is a four-component float
value, but its upstream writer and semantics remain unresolved. The earlier
runtime report that the marker stayed aquamarine after changing ID25's
SmallCarSheet selector proves independence from that selector only; it does
not identify the color source. Classification: **UNKNOWN** upstream. No
participant or vehicle-color semantics should be inferred yet.
