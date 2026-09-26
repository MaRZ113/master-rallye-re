# R-DEMO2.7 — first divergence in demo-8.4.1 Trooper `$chull`

## Executive result

**Level B: first upstream native decision reconstructed by a source replay and anchored to the candidate runtime face. One small capture remains for the live endpoint identities and the effective tolerance.** The translated `$chull` changes a near-coplanar plane comparison: source points `C[1317], C[1335], C[1337]` deduplicate to face 25 in the original-input replay, but are inserted as face 37 after the `+0.4` X translation. The candidate's runtime face 37 has the same plane fields as that inserted plane to the recorded precision. That extra face is the face whose edge walk reaches `005C447B`.

The source-level mechanism is now strongly identified: `005C3E10` combines a loose normal-dot test with an absolute plane-offset tolerance. The planes are nearly parallel, not identical; translation changes their `d` separation by about `-1.94466e-5`, crossing the default `0.0005` threshold. The effective runtime setting was not captured, so the configured-value part remains conditional on that value lying in the computed interval. Exact endpoint payloads and the full face graph also remain uncaptured. See [the failing-face record](r-demo2.7-failing-face.md) and [the one-stop runtime follow-up](r-demo2.7-runtime-followup.md).

## Pinned evidence

| Input / observation | Identity | Status |
|---|---|---|
| Executable | `demo-8.4.1`, SHA256 `bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be` | `CONFIRMED_BY_BYTES` |
| Baseline Trooper GXM | SHA256 `fd08bc10c440fce261ef126e40445002fb56359d4011c1dcbf9c2f71b0e91047` | `CONFIRMED_BY_BYTES` |
| Translated candidate GXM | SHA256 `0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699` | `CONFIRMED_BY_BYTES`; regenerated offline to the exact hash |
| Candidate breakpoint | Ordinary breakpoint at `005C447B` fired before `XOR EDI,EDI` | `CONFIRMED_BY_RUNTIME` from supplied screenshots |
| Baseline control | Same breakpoint not observed; user reports the race loaded | `CONFIRMED_BY_RUNTIME` for that run only |
| Candidate failing face | Caller loop byte offset `0x940`, face stride `0x40`, giving face index 37; its screenshot plane matches the source replay | index `CONFIRMED_BY_EXE` + `CONFIRMED_BY_RUNTIME`; ancestry `INFERRED_BY_BINARY64_REPLAY` |
| Effective live `ConvexHull_PlaneThickness` | Not present in the screenshots | `UNKNOWN_FROM_CAPTURE` |
| Live endpoint payload pointers | Node addresses are visible, but their `+8` payloads are not | `UNKNOWN_FROM_CAPTURE` |

Machine-specific heap addresses and screenshot hashes are preserved in ignored `.research-output/r-demo2/r-demo2.7-runtime-capture.json`; raw screenshots remain under ignored `.research-output/r-demo2/user_debug_screens/`.

## Exact 8.4.1 decision path

Static evidence is from the pinned executable only; no 9.3.1 behavior is substituted.

1. `005BABC0` walks the hull state's face vector using `+0x24/+0x28`, `0x40`-byte face strides, and caller register `ESI` as the byte offset.
2. `005B9F10` enumerates point triples in nested, lexicographic order. It calls `005C3A40`, then compares each valid plane against prior faces through `005C3E10`, and checks support against every point through `005C41F0`.
3. `005B9D80` computes the AABB midpoint used to orient each plane. `005C3A40` normalizes the cross product and stores the absolute plane offset `d`.
4. `005C3E10` accepts a duplicate only when `dot(n1,n2) > 1-thickness` **and** the two absolute offsets differ by **strictly less than** `thickness`. The default global is `0.0005000000237487257`; `005B5AF0` can load an override named `ConvexHull_PlaneThickness`.
5. Later, `005C43A0` reorders each face's edges by endpoint-object identity. `005C3200` returns true only when the compared edge objects share an endpoint pointer. If the search exhausts the remaining face list, `005C447B` writes zero and the later call faults through NULL at `005C3212`.

These function roles and strict comparisons are `CONFIRMED_BY_EXE`. The runtime screenshot directly confirms the candidate reaches the no-match branch; the baseline non-hit is only the user's observation for one controlled run.

## First plane decision that differs

The deterministic analyzer is [r_demo2_7_hull_divergence.py](../../tools/scanner/r_demo2_7_hull_divergence.py). It consumes only the pinned local GXM pair and derived runtime JSON; its result is at ignored `.research-output/r-demo2/r-demo2.7-plane-divergence.json`.

The GXM source triangle is record `1950` in `$chull(Trooper)`, with corner indices `(1337, 1335, 1317)`. The face-plane enumeration order is `C[1317], C[1335], C[1337]`; their first serialized corner occurrences are records/corners `(1925,0)`, `(1943,2)`, `(1949,2)`. The candidate plane is also exactly the geometric plane of record 1950.

At the first differing source-point triple in the binary64 replay:

| Pair | Plane relationship | Offset delta | Decision at the EXE default |
|---|---|---:|---|
| Baseline | Normal dot `0.9999969607349776`; target plane deduplicates with prior face 25, whose first-plane ancestry is `C[1327], C[1317], C[1337]` | `-0.0004948211223303467` | Deduplicate |
| Translated candidate | Same normal dot to shown precision; prior corresponding face 25 has `d=0.5417067318930648` | `-0.0005142677133753715` | Insert new face 37 |

The source replay reaches this first changed decision at combination index 6,398 among the 36 referenced C positions in first-corner-occurrence order. It predicts 37 retained planes for the baseline and 38 for the candidate. It mirrors the exact 8.4.1 test order and strict inequalities but calculates with Python binary64; it is **not** an x87 bit-exact emulation and the internal 8.4.1 point buffer was not directly dumped.

The captured candidate face 37 contains native normal `(-0.9998094788806016, 0.019493582653401013, -0.0008416937794259575)` and `d=0.5411924641764101`. The replay predicts source normal `(-0.9998096277807779, 0.000841692928814299, 0.019493582274070862)` and `d=0.5411924641796895`. Under the inferred axis mapping `(x,y,z) -> (x,z,-y)`, the maximum normal component residual is `1.4891e-7` and the `d` residual is `-3.28e-12`. The saved caller loop offset independently yields face index `0x940 / 0x40 = 37`. Together, index and plane fields strongly anchor the replay plane to the runtime face.

### Why translation changes this comparison

For exactly parallel planes, translating both by the same vector changes both offsets equally and preserves their difference. Here the normal dot passes the approximate-parallel threshold, but the normals are not exactly equal. Translation adds `n·t` independently to each offset, so the comparator's absolute `d` difference changes by `(n_candidate - n_prior)·t`. The replay gives a shift of `-1.9446591045024775e-5` for this pair. Relative edge vectors, edge lengths, source triangle connectivity, and the target normal are unchanged in the serialized source values; the offset comparison is the quantity that crosses the tolerance.

The exact runtime thickness is not known. For this pair, the replay predicts the baseline/candidate split for thickness in:

```text
0.0004948211223303467 < thickness <= 0.0005142677133753715
```

The executable's static default lies inside this interval. The screenshot face index/plane match is consistent with that default, but does not reveal whether the runtime loaded an override. The small capture below requests the live global value.

## Failing face and immediate edge-walk result

At the candidate `005C447B` stop, the screenshot-derived face has one remaining face-list edge, while the local edge list count is three. The current edge is in `EBX`; `EDI` holds the last-tested face-list candidate just before the instruction zeros it. The branch itself confirms no endpoint-object pointer overlap for the current pair. The current edge endpoint list reports count two. However, the screenshots do not show the two endpoint nodes' `+8` payloads, the remaining candidate edge's endpoint list, or the local list's edge payloads. Therefore this report does **not** invent vertex indices, edge-vector indices, coordinates, or connected-component counts.

The runtime image `005C447B` establishes a failed identity comparison on face 37, not yet the complete endpoint graph. This is why the result is Level B and one bounded same-stop capture remains.

## R4G and writable-source impact

The evidence does not establish a safe `$chull` translation recipe. A future writer must not treat rigid source translation as hull-safe: it must either reproduce the exact 8.4.1 plane-equivalence sequence and validate each face edge walk, or reject edits whose plane insert/dedup decisions or pointer-identity adjacency cannot be proven. No fix to GXM fields, endpoint snapping, or the executable is proposed. R4G remains frozen; R5T and track work remain unstarted.

## Reproduction and validation

The exact candidate was rebuilt under ignored `.research-output/r-demo2/exact-841-rebuild/candidate.gxm` with the existing fail-closed offline candidate builder; it hashes to the pinned `0425e163…` value. Then:

```powershell
py -3 tools\scanner\r_demo2_7_hull_divergence.py `
  'D:\Game\Master Rallye\corpora\demo-8.4.1\DataGx\Vehicles\Trooper\car.gxm' `
  '.research-output\r-demo2\exact-841-rebuild\candidate.gxm' `
  --runtime-capture '.research-output\r-demo2\r-demo2.7-runtime-capture.json' `
  --output '.research-output\r-demo2\r-demo2.7-plane-divergence.json'
```

The new synthetic tests cover pointer normalization, circular-list integrity and count, endpoint-identity components/differentials, strict plane thresholds, build/hash rejection, and deterministic JSON. The complete suite passes: **177 tests**.
