# Demo DX parser boundary

`src/master_rallye/demo_dx.py` is a read-only view, not a retail `DxModel`. It bounds-checks the 16-byte header, position/normal/color/UV arrays and local indices; locates a unique `(1, local-index-count)` global-index table; retains the intervening demo draw/material region raw; and reuses the existing compatible collision tag101/tag102 and marker-1339 readers on the trailer. Ambiguous or unsupported boundaries fail closed.

The inspected Trooper car/complete/wheel DX files in both demo 8.4.1 and 9.3.1 pass this bounded layout (6/6). The car pair's raw draw region is 1,638 bytes in 9.3.1 and byte-identical across original/rebuild. This **does not decode demo material or draw semantics**. Course/test DX and other demo variants are outside this result. The comparator will report `UNRESOLVED` for changed raw draw bytes or changed unknown collision bytes; topology changes get `STRUCTURALLY_DIFFERENT` where counts/indices/triangles are actually known.
