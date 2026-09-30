# R5T-E GXM topology binding

Status: **MORE WORK NEEDED**. This pass is read-only. No topology parser,
Course SDK geometry model, Blender change, or writer was added because the
corner-to-position chain is not proven.

## Confirmed binary and corpus constraints

- The only course-folder GXM files in the available build corpus are Demo
  8.4.1 France1 and Italy1. Counts for Demo 9.3.1, Demo 9.10.0, and Retail are
  each 0. The paired developer Boinds GXM/TXT/DX is an additional validation
  sample.
- Existing bounded readers parse each of the three GXM/TXT pairs. Their
  16-byte counted bank, trailing float3 bank, and TXT-validated node-table
  boundaries are non-overlapping and within the file. The counted 16-byte
  bank's semantics remain **UNKNOWN**.
- Header word 3 matches the TXT `Materials(Size N)` value in all three samples:
  France1 121, Italy1 66, Boinds 36.
- Header word 4 equals three times word 6 in all three samples. Every parsed
  `moMesh` span is nonnegative, spans are gap-free, and their sizes sum to
  word 6. This strongly supports (but does not itself prove) word 6 as a
  triangle count, word 4 as corner count, and `moMesh.Index`/`Size` as triangle
  ranges.
- Header word 7 bounds a finite trailing float3 pool. Prior source/cooked
  position-set comparisons support its spatial relationship to DX; they do
  not bind an individual mesh to pool entries.

Exact identities, hashes, offsets, counts, and diagnostic windows are in
[`topology-candidates.json`](topology-candidates.json). Candidate offsets in
that file are explicitly marked exploratory; they are not accepted parser
boundaries.

## What the candidate windows show

Italy1 has a plausible 32-bit sequence of `word4` entries. It is aligned with
the sidecar mesh spans when treated as three entries per triangle, and its
first small mesh uses early values that index a compact region of the source
float3 pool. But 47,954 of 142,131 values are greater than or equal to the
float3 count. These are outside the direct-position-index range if interpreted
as position indices; their meaning is unresolved, and no established table
resolves them to positions.

Boinds has a plausible 16-bit sequence of `word4` entries, but 4,318 of 28,212
values are at or above its float3-pool count. This exceeds the direct-position
index range but does not prove the values are position references. Its offset
and width remain candidate observations, not a decoded bank.

The France1 diagnostic 16-bit window was selected only because it minimized
values at or above the float3-pool count over one bounded region. It has 600
unique values across 185,751 entries, includes 801 `0xFFFF` values, and its
first startpoint slice
does not resolve to the known box under direct float3 lookup. It is **rejected
as a proven bank boundary** and is retained only as a reproducible negative
diagnostic. No heuristic scan was promoted to a parser.

## France1 startpoint

The TXT/GXM node-table cross-check confirms `startpoint`, ordinal 1, parent 0,
`Index 0`, `Size 12`. The first eight float3 pool entries form the documented
10-unit axis-aligned point set. However, no proven 36-corner sequence currently
binds those points to the span. Consequently the 12 triangles, face ordering,
edge incidence, closed-manifold result, and source position-index mapping all
remain **UNKNOWN**. The point set must not be represented as a decoded closed
mesh yet.

## Exact blocker

The missing link is the actual version-appropriate index/vertex grammar and a
validated route from each corner entry through any intermediate vertex record
to the trailing float3 pool. The Italy and Boinds candidate values have no
proven interpretation, and the France1 startpoint span remains
unbound. Header arithmetic and complete sidecar span coverage are not enough
to implement a safe decoder.

Material assignment per triangle also remains **UNKNOWN**. No physical,
collision, gameplay, or source-name semantics are inferred here.

## Implementation boundary

No changes were made to `course_gxm.py` or the Blender add-on. The existing
prefix, TXT-validated node-table, and float3-pool readers remain the supported
read-only GXM API. The next topology attempt should establish a source-backed
bank boundary and decode position references across France1 and Italy1 before
adding parser APIs or changing the standard course import.
