# GXM to DX correspondence: Trooper case study

This document compares build-qualified sources; it does not reuse a missing file from another build.

`demo-8.4.1:DataGx/Vehicles/Trooper/{car,complete,wheel}.gxm` has parsed material tables, three float3 arrays, and indexed records. The same-build DX files all start with magic `0xD00D` and a readable position array, but the current retail DX parser rejects their draw-table grammar (`unreasonable texture slot count`). This prevents a full source-to-tag mapping in this phase.

| Role | GXM vector C count | Demo DX leading position count | GXM C vectors matching any DX position after `(x,y,z)→(x,z,-y)`, rounded to 4 decimals | Non-Null GXM texture stems literally present in DX bytes |
|---|---:|---:|---:|---:|
| car | 1,353 | 2,310 | 1,305 | 24/24 |
| complete | 1,564 | 2,500 | 1,552 | 19/24 |
| wheel | 146 | 220 | 146 | 6/6 |

This is strong coordinate and texture-name correspondence, but the count expansion and 8.4.1 complete omissions show that a simple byte copy is not the compiler. The five complete-only absent texture stems are `black-tga`, `dcambell-tga`, `drichard-tga`, `trhelmet32-tga`, and `whitesuit-tga`; they remain source-side material references in GXM.

The DX header version/control word differs: among 49 demo-8.4.1 DX files, 39 have word_0x04=127 (other values 125/123/126/5); among 30 demo-9.3.1 DX files, 27 have 131 (others 130/128); all 160 supplied retail DX files have 135. All have `0xD00D` magic and word_0x08=1337. The retail DX grammar must not be asserted for demo draw/collision tails.

## Collision and material boundaries

`demo-8.4.1:DataGx/Vehicles/Trooper/car.gxm` contains the length-prefixed string `$chull(Trooper)`; complete and wheel resources have different source directives. This is **SOURCE_SIDE_EVIDENCE**. The retail full-DX draw parser is incompatible with the demo draw grammar, but the new conservative demo DX inspector can parse tag101 in the 9.3.1 Trooper tail. A separate Jump comparison now establishes close cross-build numeric correspondence of `$chull` geometry with retail tag101 Representation B/A and the radius; see `collision-source-map.md`. `$cylinder` source numbers are not directly equal to the parsed demo/retail tag102 values, so their transformation remains **UNKNOWN**.

Likewise, `$paint`, `$glass`, `$perspex`, and `$rubber` are source-side labels. The retail material renderer semantics in R4D/R4D.1 still come from runtime/executable evidence. Demo material flags and effects need a version-aware DX parser or targeted executable trace before promotion.
