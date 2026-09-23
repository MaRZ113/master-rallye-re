# R4D draw control correlations

Counts cover 1,478 parsed physical draws in 78 vehicle resources. All fields are still named by their DX core offsets. Alpha means any referenced DXT has pixels below 255; UsesAlpha is counted from any matched sidecar candidate. This is a correlation, not proof of runtime state causality.

| Core +0x20 raw bytes | Draws | Alpha-bearing | UsesAlpha candidate | Observation |
|---|---:|---:|---:|---|
| 00000101 | 1,092 | 49 | 9 | Large general family; alpha bytes do not imply alpha shader here. |
| 01000101 | 212 | 212 | 209 | Strong glass-like alpha correlation; includes tag 2/7/8. |
| 00000001 | 147 | 2 | 1 | Includes brake-light-on and wheel families. |
| 01000001 | 25 | 25 | 24 | Mostly brake-glow family. |
| 00000100 | 2 | 0 | 0 | IceCream car/complete Null-only outlier. |

| Core +0x24 u32 | Draws |
|---|---:|
| 7 | 938 |
| 3 | 363 |
| 5 | 151 |
| 1 | 21 |
| 6 | 3 |
| 2 | 2 |

Core +0x18 is zero for 1,478/1,478 draws; +0x1c is float32 1.0 for 1,478/1,478. Core +0x14 is 1 for 1,476; two IceCream Null-only draws store 0x492F7365. The value is preserved raw; no meaning is assigned.

**HIGH_CONFIDENCE_INFERENCE:** the first byte of +0x20 participates in an alpha-related material distinction, given its complete correlation with the two major alpha families. It is not sufficient to choose alpha blend versus alpha test: 49 alpha-bearing draws have 00000101, and the direct DX-to-shader xref is absent.

**UNKNOWN:** whether +0x24 is a shader feature bitmask. Its small values resemble the material-object +0x34 mask read by executable function 00580360, but no loader copy or transformation was traced. Do not rename or write either field as a renderer flag.
