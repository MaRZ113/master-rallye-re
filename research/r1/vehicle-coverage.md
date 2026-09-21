# R1 vehicle corpus coverage

All paths are relative to the external `DataGx/Vehicles` tree.

## Summary

| Metric | Count |
|---|---:|
| Total DX | 78 |
| Parsed | 78 |
| Validated | 78 |
| Fully accounted | 49 |
| Partially accounted | 29 |
| Failed | 0 |
| Exact stored-global matches | 78 |
| Unknown record tags | 0 |
| Declared/root count mismatches | 11 |

## Record variants

File frequency by encountered tag: tag 2: 78, tag 7: 25, tag 8: 25.

## Trailing layouts

| Resource type | footer56-bounds | opaque |
|---|---:|---:|
| `car` | 0 | 26 |
| `complete` | 24 | 2 |
| `sus` | 0 | 1 |
| `wheel` | 25 | 0 |

Opaque byte-count frequency: 44: 1, 152: 1, 3096: 1, 3276: 1, 3288: 1, 3300: 1, 3336: 1, 3360: 2, 3612: 1, 3804: 1, 3816: 1, 3864: 1, 3948: 1, 3984: 1, 4248: 1, 4272: 1, 4308: 2, 4512: 1, 4680: 1, 4956: 1, 5028: 1, 5076: 1, 5280: 1, 5340: 2, 5400: 1, 6600: 1.

## Material diagnostics

- Ambiguous draw matches: 132.
- Unmatched draws: 63.
- Missing referenced texture resources: 0.
- Matching uses normalized ordered texture tuples padded with `Null` to the binary tuple width.

## Interpretation

`FULLY_ACCOUNTED` is intentionally stricter than parser success. Opaque trailing data makes a file
`PARTIALLY_ACCOUNTED` even when every draw and stored global index validates exactly.

Reconstructed winding versus stored vertex normals: aligned 119454, opposed 98, near_zero 425.
