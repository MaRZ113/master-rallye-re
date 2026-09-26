# R-DEMO2.7 — candidate failing-face reconstruction

## What the supplied capture proves

The user-provided x32dbg screenshot set shows the exact pinned demo-8.4.1 crash candidate stopped at `005C447B` before `XOR EDI,EDI`. The full machine-specific transcription and source screenshot hashes are kept in ignored `.research-output/r-demo2/r-demo2.7-runtime-capture.json`.

The saved caller frame gives the face-vector byte offset `0x940`. In exact 8.4.1 `005BABC0`, `ESI` is the byte offset into the face vector and each face has stride `0x40`; therefore the captured `ESI` is face index 37. The address arithmetic derives that run's face-vector base from `ESI-0x940`; the independent face `+0x20` dword also reads `0x25`, but its semantics are left unknown.

The captured face has one edge left in its circular face list. The local list count is three. The `005C43A0` loop reads the current local edge into `EBX`, compares each remaining face edge through `005C3200`, and reaches `005C447B` after the search exhausts. In the capture, `EDI` holds the last-tested face-edge pointer immediately before the no-match instruction clears it. This proves the compared current/remaining pair failed the shared-endpoint predicate. The original baseline breakpoint was not observed in the user's controlled run, and the user reports successful race loading.

## Source-plane mapping

The runtime face plane is anchored to the translated GXM triple `C[1317], C[1335], C[1337]`, which is triangle record 1950 in the `$chull(Trooper)` range. Source replay predicts that plane as candidate face 37. Runtime and predicted transformed normals differ by at most `1.4891e-7`; the plane-offset residual is `-3.28e-12`. This mapping is `INFERRED_BY_BINARY64_REPLAY` and strongly supported by the runtime face index and fields; it is not a raw native input-point capture.

The source-level first divergence is the `005C3E10` plane-equivalence decision: baseline deduplicates this plane to face 25; the translated candidate inserts it as face 37 under the executable's static default plane thickness. See [the main first-divergence report](r-demo2.7-first-divergence.md) for operands and the runtime-config limitation.

## Values deliberately left unknown

The screenshots show the current edge's endpoint sentinel and its two linked node addresses, but not those nodes' `+8` vertex payloads. They do not show the remaining edge's endpoint sentinel, its node payloads, any local-list edge payload, or the hull-state edge/vertex vector bounds. Consequently:

- current and remaining edge-vector indices: `UNKNOWN_FROM_CAPTURE`;
- endpoint vertex-object pointers and vertex-vector indices: `UNKNOWN_FROM_CAPTURE`;
- endpoint coordinates: `UNKNOWN_FROM_CAPTURE`;
- complete four-edge pointer graph and connected components: `UNKNOWN_FROM_CAPTURE`;
- configured runtime plane thickness: `UNKNOWN_FROM_CAPTURE`.

No stable index is inferred from an unverified heap base, and no vertex payload nibble is guessed from the screenshots. The next capture request is one stop at the same breakpoint, with only the exact missing vector bounds, list payloads, endpoint payloads, and tolerance value.
