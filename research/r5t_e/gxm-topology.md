# R5T-E GXM topology evidence ledger

This ledger records only structures reproduced from the supplied Demo 8.4.1
GXM/TXT files. A count relationship is not promoted to field semantics unless
the bytes or a cross-checked source structure support it.

## Measured sample layout

All offsets are decimal plus hexadecimal. The 32-byte header is followed by a
header-word-2-counted 16-byte region. The trailing float3 pool is bounded from
the TXT-validated object table by header word 7.

| Sample | Header words 2–7 | Counted 16-byte region | Float3 pool | Node table | Mesh spans |
|---|---|---|---|---|---|
| France1 | `262505, 121, 185751, 97824, 61917, 49278` | `[32, 4,200,112)` | `[10,838,403, 11,429,739)`, 49,278 × 12 | `[11,429,739, 11,489,135)`, 2,322 nodes | 2,283 meshes; sizes sum to 61,917; gap-free `[0, 61,917)` |
| Italy1 | `189937, 66, 142131, 89485, 47377, 34048` | `[32, 3,039,024)` | `[8,291,648, 8,700,224)`, 34,048 × 12 | `[8,700,224, 8,728,347)`, 1,117 nodes | 1,082 meshes; sizes sum to 47,377; gap-free `[0, 47,377)` |
| Boinds | `26750, 36, 28212, 25745, 9404, 4933` | `[32, 428,032)` | `[1,569,990, 1,629,186)`, 4,933 × 12 | `[1,629,186, 1,629,436)`, 17 nodes | 2 meshes; sizes sum to 9,404; gap-free `[0, 9,404)` |

Full file identities and hashes are in
[`topology-candidates.json`](topology-candidates.json). The listed region
boundaries are parser bounds, not semantic interpretations of the first bank.

## Header and mesh-span cross-checks

| Field / relation | France1 | Italy1 | Boinds | Evidence status |
|---|---:|---:|---:|---|
| Header word 3 / TXT material count | 121 / 121 | 66 / 66 | 36 / 36 | **CONFIRMED_BY_BINARY_STRUCTURE** |
| Header word 4 | 185,751 | 142,131 | 28,212 | Raw value |
| 3 × header word 6 | 185,751 | 142,131 | 28,212 | Exact arithmetic relation; supports but does not prove corner count |
| Header word 6 / summed mesh sizes | 61,917 / 61,917 | 47,377 / 47,377 | 9,404 / 9,404 | **CONFIRMED_BY_BINARY_STRUCTURE** for span coverage; triangle unit remains inferred |
| Header word 7 / finite float3 count | 49,278 / 49,278 | 34,048 / 34,048 | 4,933 / 4,933 | **CONFIRMED_BY_BINARY_STRUCTURE** for pool boundary and finite records |

Header word 5 is intentionally unnamed. No triangle material association was
established.

## Candidate raw windows

These are observations from manual, read-only offset inspection. They have not
been converted into parser code.

### Italy1 — plausible 32-bit word-4-sized sequence

At `0x58EDCC`, a 32-bit sequence of 142,131 values ends at `0x619A98`. Values
range 0–69,900, with 63,653 distinct values. All fall below header word 5
(89,485), but 47,954 are greater than or equal to the source float3 count
(34,048). They cannot be direct in-range position indices; their meaning is
unresolved. The initial 42 values align with the first `moMesh` span
(`Index 0`, `Size 14`) when grouped in threes; early values produce a compact
source-pool region under direct lookup. That single local match does not
explain the remainder or prove the window start. Classify this as
**PLAUSIBLE**, not **CONFIRMED_BY_BINARY_STRUCTURE**.

### Boinds — plausible 16-bit word-4-sized sequence

At `0x107E94`, a 16-bit sequence of 28,212 values ends at `0x115AFC`. Values
range 0–24,662 and all fall below header word 5 (25,745). However, 4,318 values
are greater than or equal to the source float3 count (4,933). They cannot be
direct in-range position indices; their meaning is unresolved. The TXT/GXM
spans cover the full 9,404-triangle range, but no position resolver was
identified. Classify the sequence as **PLAUSIBLE**, not confirmed.

### France1 — diagnostic window rejected as a boundary

The diagnostic window at `0x6E956C` is 16-bit and contains 185,751 entries,
ending at `0x74409A`. It was selected only by minimizing the number of values
outside the float3 count in a bounded region. It has 600 unique values and 801
`0xFFFF` entries; `header[5]` exceeds the entire 16-bit domain, so the apparent
range fit is not discriminating. The startpoint's first 36 entries do not map
to the known box under direct float3 indexing. The window is **REJECTED as a
proven bank boundary**.

## Startpoint proof gate

The exact source-side record is France1 `startpoint` (`Index 0`, `Size 12`).
The first eight pool coordinates define an approximately 10 × 10 × 10 box,
with source-space center `(-982.055542, -468.666718, 53.539051)`. There is no
validated triangle stream for this span. Therefore this report does not assert
12 face triplets, six face pairs, edge incidence two, or a closed mesh.

## Evidence vocabulary and conclusion

- `CONFIRMED_BY_BINARY_STRUCTURE`: TXT/GXM node-table equality, exact bank
  bounds, material-count cross-check, mesh-span coverage, and finite float3
  records.
- `HIGH_CONFIDENCE_INFERENCE`: header word 6 is a triangle count and word 4 is
  the corresponding corner count because every sample satisfies the 3× count
  relation and all mesh spans cover word 6.
- `PLAUSIBLE`: Italy1 and Boinds exploratory windows may be corner references.
- `UNKNOWN`: corner-to-vertex binding, vertex-to-position mapping, France1
  startpoint connectivity, per-triangle material relation, and topology
  semantics.

Verdict: **R5T-E MORE WORK NEEDED**. No topology parser or writer was added.
