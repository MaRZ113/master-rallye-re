# R5T-B.1 GXM geometry probe

Status: **partial**. The float3 pool is bounded and spatially correlated. Node-to-point topology is not decoded.

## Source to compiled comparisons

| Pair | Nodes | Points | DX rev | Exact | 1-unit | 0.1-unit | Best transform | Runner-up 0.1-unit |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| Demo 8.4.1 France1 | 2322 | 49278 | 127 | 6366 | 36081 | 34904 | (x, z, -y) | 63 |
| Demo 8.4.1 Italy1 | 1117 | 34048 | 127 | 6517 | 28568 | 27033 | (x, z, -y) | 6 |
| Demo 8.4.1 developer Boinds | 17 | 4933 | 125 | 38 | 4749 | 4749 | (x, z, -y) | 0 |

Counts are source points matching the compiled DX position set. All 48 signed axis permutations were evaluated. This validates a coordinate relation, not per-node geometry.

## Current conclusions

- **float3_pool:** Header word 7 bounds a finite trailing float3 bank immediately before the TXT-validated node table. The full pool correlates with old compiled DX vertices in the three measured source/cooked pairs.
- **node_mesh_link:** UNKNOWN. TXT/GXM mesh Index/Size spans validate, but their mapping to the float3 pool and raw index streams is not proven.
- **startpoint:** HIGH_CONFIDENCE_INFERENCE: France1 has a startpoint node at Index 0 / Size 12 and the first eight pool points are eight corners of a 10-unit axis-aligned box. Face connectivity and exact pool-to-node indices are still unknown.
- **startpoint_xml:** The mapped center of that France1 point cluster is within the reported distance of Demo 9.10 France1 XML Marker 0; this is spatial correlation, not a direct XML-to-GXM binding.
- **source_to_dx:** HIGH_CONFIDENCE_INFERENCE: (x, z, -y) is the strongest match among all 48 signed axis permutations in France1, Italy1, and Boinds.
- **source_to_blender:** HIGH_CONFIDENCE_INFERENCE: identity, composed from source-to-DX (x, z, -y) and the established DX-to-Blender (x, -z, y).
- **bsp:** UNKNOWN. France1's $bsp hierarchy and mesh spans are inventoried, but the source point pool has not been mapped to individual BSP meshes.

## France1 startpoint and XML marker

The candidate startpoint box center maps to DX `[-982.0555419921875, 53.5390510559082, 468.6667175292969]`. Nearest Demo 9.10 XML marker: ordinal `0`, no `0`, distance `1.559` source units. Spatial proximity only; no record binding is claimed.

## Small developer oracle files

| Oracle | GXM | TXT | DX | GXI files in folder |
|---|---|---|---|---:|
| gordonTrack/flatTrack | True | False | False | 1 |
| gordonTrack/track | True | False | False | 1 |
| RussiaTurkey1/RussiaTurkey1 | True | False | False | 76 |
| boinds/track01 | True | True | True | 37 |
| collisiontests/crack | True | False | False | 25 |
| collisiontests/crack2 | True | False | False | 25 |

Only Boinds currently has the complete small source/TXT/cooked-DX pair. Missing companions are not synthesized.
