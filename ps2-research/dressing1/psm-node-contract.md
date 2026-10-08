# Selected PSM node contract

WATER1's strict decoder is reused without a new PSM grammar. Header d00d/2/539,
52-byte source vertices and tag2 strip ownership remain unchanged. Source vertex
count is at+28; positions at32+52*i+36. The newest vertex control bit0 suppresses
triangle emission. Source winding/strip flags and all byte offsets remain intact.

| Source tag | Runtime interpretation | Evidence |
|---|---|---|
| 1 | Reuse supplied parent; recursive children |391d38; selected original bytes|
| 0 /5 | Allocate0x18 generic child group; ctor3a5ee0; vtable488440 |Original calls392354/392398; allocation/parser flow|
| 2 | Allocate0xf4 material mesh; ctor3ba868; append to model+44; strips+74 |Original call391e0c; WATER1 binding|
| 6 | Allocate0x38 selection group; ctor3c1038; vtable488560 |Original call392578; fresh executable query|
| 3 | Allocate0x30 bound wrapper; center+1c, radius+28, radius²+2c |391d38,3b9398; source tag3 not needed by four candidates|

Selected source tags1/6/5/2 contain no matrix payload: apart from the tag2
material/strip record, only tag and child count precede recursive children.
Tag3 carries a bound, not a16-float transform. Other parser cases exist; the
diagnostic fails closed for unsupported landscape tags. No hypothetical tag4
LOD or tag7/8 landscape instance semantics are imported from vehicle research.

At tag6 postprocessing, child virtual+2c is inspected. Base3b95d0 returns null;
bound accessor3b93e8 returns a0. A child without a bound is wrapped in a new
3b9398 node;390960 produces its descriptor,3a4990 copies it at+1c, and1df2b0
reparents the original child. Calls3929ec/392a18/392a4c/392a60/392a7c independently
ground this operation. Runtime hierarchy therefore differs from file hierarchy.

No independent transform, model lookup or new scenery Egg is created by that
wrapper. An inserted bound cannot be counted as an additional placed object.
Raw decompilations stay ignored; compact original words and bounds are in
[elf-functions.json](elf-functions.json).
