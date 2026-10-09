# Race marker color and HUD identity

`race_colour_rgba` is a separate addon property. It is serialized in the
VehicleRecord initializer as four little-endian IEEE-754 single-precision
arguments. The R5VQualifier profile requests `[1,0,1,1]`, encoded as
`0000803f000000000000803f0000803f`. Observatory 0.2.3-beta capture
`R5VQ-quickrace-AI` confirms the live ID27 Broker `Colour` is
`[1,0,1,1]`; the active race also identifies `CarType` and `WheelType` as
`R5VQualifier`. This closes the record-colour mismatch seen in the earlier
I.1 candidate. The magenta body DXT remains an independent texture asset.

Results name, Results image selector, SmallCarSheet selector, and race/progress
marker color are distinct channels. The examples explicitly carry a fixed
display-only Results name, stock art frames, and marker RGBA. The paired
Quick Race Results capture reports `R5V TEST DRIVER` for the ID27 Results
display identity while the race's native DriverID remains 5. The capture
confirms Broker state, not a visual audit of the HUD marker or Results artwork;
those visual channels remain in the J.2 handoff.
