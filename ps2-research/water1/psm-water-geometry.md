# Targeted visual PSM geometry

WATER1 adds the selected landscape **visual scene-tree** decoder that GRASS1
deliberately did not claim. It reuses the shared vertex layout and separately
calls GRASS1's spatial decoder as an independent boundary check. It does not
turn spatial triangles into visual draw records.

| Serialized stage | Layout and ELF evidence |
|---|---|
| Header | u32 d00d,2,539; shared vertex count at0x1c |
| Vertex | 52 bytes from0x20: first16 normal/control bytes, packed color+16, four UV floats+20, XYZW+36 |
| Runtime vertex | 3900f0:48 bytes; normal/control+0, UV+10..1c, XYZ+20/+24/+28, RGBA bytes+2c..2f |
| Visual tree start | 32+52*vertex_count |
| Container tags | Selected five landscapes use1,5,6; u32 child count and recursive children |
| Mesh tag2 | u32 tag, opaque word, three map-slot records, material string, two opaque words, four byte booleans, opaque32-bit parameter, strip vector, child count |
| Map slot | one byte present; if present: three byte booleans and string |
| String | u32 length; if nonzero u16 same length, exactly that many ASCII bytes; no terminator/padding |
| Strip | u32 first vertex,u32 count,u8 flag,f32 scale =13 bytes |
| Visual termination | Tag100 immediately followed by separately validated tag103 spatial block |

`30be70` treats any nonzero serialized boolean as true; the decoder matches
that behavior. Unsupported scene tags fail closed. The mesh parameter read
into+70 includes non-finite bit patterns in original data; it is preserved as
an opaque word, not interpreted as a coordinate, radius or invalid position.
Actual source XYZ and strip scale are checked for finite values.

`391d38` creates a0xf4-byte physical mesh, adds it to model+44 and stores
strips at mesh+74. Packed strip helpers `3a5400`, `3a53d0`, `3a5458` and
`3a54b8` encode the first vertex (19 bits), count (16 bits), flag and quantized
scale. `3a5598/3a5560` retrieve the source range. The offline tool accepts only
the supported range and does not reproduce unproved overflow behavior.

| Course | Shared vertices | Visual meshes | Tree end | Spatial tag103 |
|---|---:|---:|---:|---:|
| France1 |67387|956|3717635|3717639|
| Italy_S1 |69577|930|3835287|3835291|
| Turkey3 |65446|1008|3631901|3631905|
| Turkey1 |65803|1034|3661838|3661842|
| Spain_S2 |77216|824|4209317|4209321|

A strip triple uses consecutive shared vertices. The newest vertex's control
word at disk+12 has bit0 copied by `31f4e0` into the packet. The embedded VU
contract converts it into ADC suppression for both output streams. Ignoring
that bit wrongly inflates France1's face count and area; using it gives exact
cross-platform 3,586-face agreement. Geometry metrics omit suppressed triples
and triangles with diagnostic area<=1e-7. Canonical strip winding, strip-flag
back-face behavior and all LOD choices are not reconstructed by these metrics.

Coordinates are the authored landscape/model source convention. France/Italy
face matches and ordinary Turkey3 vertex matches independently validate identity
alignment with PC source data. The ELF applies the scene instance/world and
camera matrices at rendering; the exact live Turkey3 instance matrix was not
captured. This is why reports say **VISUAL_SOURCE_STRIP**, not ACTUAL_RUNTIME_DRAW.

The selected water surfaces are explicit mesh records in the landscape tree.
No separate water entity or load-time plane synthesis is needed in the traced
chain. This bounded finding does not prohibit other scene water elsewhere.
