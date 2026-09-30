# R5T-E.1 GXM topology measurements

Current status: **PASS**. Values below are reproduced by
[`tools/r5t_e1_course_topology.py`](../../tools/r5t_e1_course_topology.py)
from actual GXM/TXT files. Full file identities and field statistics are in
[`course-gxm-v7.json`](course-gxm-v7.json).

## Version-7 bank boundaries

Offsets are hexadecimal and half-open. The raw variable-length material block
is exactly bounded by the following normal bank; its internal schema is not
decoded.

| Sample | Counts `w2..w7` | Color float4 | Material raw block | Normal float3 | Texcoord-like float3 | Triangle 52-byte | Position float3 | Mesh spans |
|---|---|---|---|---|---|---|---|---|
| France1 | `262505,121,185751,97824,61917,49278` | `[0x20,0x4016B0)` | `[0x4016B0,0x40540B)` | `[0x40540B,0x62571F)` | `[0x62571F,0x74409F)` | `[0x74409F,0xA56183)` | `[0xA56183,0xAE676B)` | 2,283; complete |
| Italy1 | `189937,66,142131,89485,47377,34048` | `[0x20,0x2E5F30)` | `[0x2E5F30,0x2E84CC)` | `[0x2E84CC,0x488B30)` | `[0x488B30,0x58EDCC)` | `[0x58EDCC,0x7E8540)` | `[0x7E8540,0x84C140)` | 1,082; complete |
| Boinds | `26750,36,28212,25745,9404,4933` | `[0x20,0x68800)` | `[0x68800,0x69D5A)` | `[0x69D5A,0xBC7CA)` | `[0xBC7CA,0x107E96)` | `[0x107E96,0x17F4C6)` | `[0x17F4C6,0x18DC02)` | 2; complete |
| Demo 9.10 AI Track | `2175,36,10584,3369,3528,2011` | `[0x20,0x8810)` | `[0x8810,0x9C6E)` | `[0x9C6E,0x28C8E)` | `[0x28C8E,0x32A7A)` | `[0x32A7A,0x5F71A)` | `[0x5F71A,0x6555E)` | 2; complete |

For each sample, the position bank ends at the TXT-validated node table. Fixed
strides back-calculate exact preceding starts, and the material block fills
the remaining gap between the end of colors and beginning of normals. The
counts and boundaries fit file EOF with the complete node table.

## Record layout and reference validation

```text
u32[0..2]  color-like index triple
u32[3]     material index
u32[4..6]  texcoord-like index triple
u32[7..9]  source position index triple
u32[10..12] normal index triple
```

The executable reader's chunks establish the 13-u32/52-byte width. Independent
pool bounds and cross-file spans verify the index-domain mapping. All four
samples report zero out-of-range references. `0xFFFFFFFF` is observed only in
color, material, or texcoord-like domains in the main France1/Italy1/Boinds
samples; those three domains permit the sentinel. Position and normal domains
require an in-range index.

In France1, word4 is 185,751 normal records and word6 is 61,917 triangle
records, so word4 equals three normal corner records per triangle. This
relation also holds in Italy1 and Boinds. It must not be described as a
separate unnamed corner-index bank.

## Mesh ranges

All source `moMesh` records validate as `[Index, Index + Size)` triangle
record ranges. Per-file span counts equal the node-table mesh count; spans are
in bounds, with zero gaps and zero overlaps, and reach the exact triangle-bank
end. `CourseGxmModelV7.mesh_triangle_indices()` returns this slice without
copying triangle records.

## Blind-scan history correction

- Italy1 `0x58EDCC`: exact triangle bank start. The initial scan's data window
  was right; treating its entries uniformly as position indices was wrong.
- Boinds `0x107E94`: two bytes early; actual start is `0x107E96`.
- France1 `0x6E956C`: within texcoord-like records, and unrelated to the
  triangle bank despite similar diagnostic counts.

The earlier report remains in `topology-candidates.json` to preserve the
chronology. New consumers must use the loader-guided version-7 parser rather
than those search windows.
