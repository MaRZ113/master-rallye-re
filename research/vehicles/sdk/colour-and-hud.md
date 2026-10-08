# Race marker color and HUD identity

`race_colour_rgba` is a separate addon property. It is serialized in the
VehicleRecord initializer as four little-endian IEEE-754 single-precision
arguments. The R5VQualifier profile requests `[1,0,1,1]`, encoded as
`0000803f000000000000803f0000803f`. The existing I.1 candidate/captures use
white `[1,1,1,1]`; the magenta body DXT is an independent texture asset. J0
does not call the new color runtime-confirmed.

Results name, Results image selector, SmallCarSheet selector, and race/progress
marker color are distinct channels. The examples explicitly carry a fixed
display-only Results name, stock art frames, and marker RGBA. Native DriverID
selection is not modified by a fixed Results label. No ID27 color update has
been applied to the live executable.
