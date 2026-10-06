# R5T-F.2.1 — tag100 tree ↔ tag1400 causal isolation

## Status

**R5T-F.2.1: PASS — TREE_CARRIER_CONFIRMED.** The human-tested mismatched hybrids show the tested `COLLIDE_finishline03` physical state follows T (tag100 tree), not U (tag1400). The finding is bounded to this collider and controlled pairing.

## F.1/F.2 boundary and exact section split

F.1 proved that the tested `COLLIDE_finishline03` physical state followed the selected complete suffix. It did not isolate the tag100 tree. The current baseline/modified DX files decompose at parser-derived boundaries into P/T/S/U/R; see [`section-map.json`](section-map.json) for exact offsets, sizes, and SHA256 values.

The tag1339 section S is 44 bytes and byte-identical. The parser-bounded tag1400 section U is 1,809,324 bytes in both files. A separate tag1500 region R is 15,504 bytes, byte-identical through EOF. Thus the older 1,824,828-byte ‘tag1400 region’ was the combined U+R remainder, not U alone.

## Tree-size accounting and corpus invariants

For N serialized nodes, P optional 20-byte records, Q present optional-list blocks, L list items, and N−1 one-byte link selectors, the parser-derived general wire size is `24 + 12N + 20P + 4Q + 20L + (N−1)`. Every current Retail file has Q=L=0, reducing to the requested `23 + 13N + 20P`.

France1 baseline: N=360,581, P=180,290, T=8,293,376 bytes; formula gives 8,293,376. Modified: N=360,433, P=180,216, T=8,289,972; formula gives 8,289,972.

All requested header/node relationships pass on 36/36 Retail courses. The France1 edit changes word counts by −41/−33/−74, removes 74 optional records and 148 total nodes, and changes T by −3,404 bytes: `12*(-148) + 20*(-74) + (-148 selector bytes) = -3,404`. The formerly ‘unexplained’ 148-byte remainder is exactly the change in N−1 serialized link-selector bytes; the full size equation closes with zero residual.

The hierarchy is called a **plane-bearing partition hierarchy** here. Its serialized child/sibling links and observed fanout do not prove BSP semantics.

## Header counter traversal evidence

The Retail tag100 loader at `0x0057E2D0` reads five header words and allocates its three pools; Ghidra Bridge decompilation confirmed the 0x74-byte root and 8/8/36-byte allocator roles. Separately, retained Ghidra decompilation of `FUN_0057E230` shows it initializes five counters, calls recursive `FUN_0057E190`, performs five serializer calls, then enters `FUN_0057E3A0`. The counter increments one of two fields for optional-less nodes according to a discriminator (`-1` vs other), increments two fields for every optional-record node, and adds optional-list item counts; traversal recurses through children and iterates siblings. This matches the five observed header words and corpus relationships, but exact subtype names remain UNKNOWN. The Bridge export set did not include `0x0057E190`/`0x0057E230` for a live refresh, so this counter detail is attributed to the existing F.2 decompilation artifact, not a new Bridge query.

## Optional-record code values

The 24 source triangles of `COLLIDE_finishline03` form 12 unique coplanar plane groups. Match counts by cohort: baseline 12/12, modified 12/12; matching candidate records have a code equal to at least one source triangle ordinal minus 12. Static baseline results for the other three meshes are in [`tag100-code-ordinal.json`](tag100-code-ordinal.json). This is a HIGH_CONFIDENCE_NUMERIC_CORRELATION, not proof that `code` is a triangle index or source-object owner. The possible link to startpoint Index 0 / Size 12 remains a hypothesis.

## Tag1339, tag1400, and typed differential

Retail executable SHA256 is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Tag1339 is a separate 44-byte record dispatched to handler `0x00553C80`; the France1 donor bytes are identical. Ghidra Bridge decompilation at `0x005541D0` verifies the tag1400 loader’s fixed reads and per-cell allocation path. The structural parser is in `src/master_rallye/course_tag1400.py`; it preserves unknown values and has no writer.

France1 U is 1,809,324 bytes; 64 byte positions differ over 47 ranges. The typed pass maps 47 changed float32 fields, and every changed byte is assigned to a parsed field. Changes occur in the 56-byte record family; header, cells, strings, and string references stay identical. No changed field exactly matches the known tree counters/deltas or collider AABB coordinates, and no float changes by ±20. Field meanings remain UNKNOWN.

## Retail structural validation

The current Retail corpus contains 36 course folders. Tag100 and tag1400 parse in 36/36; tag100 count invariants pass in all successful courses. Tag1400 dimensions span `[86, 263]` × `[76, 147]`; cell counts span `[8514, 36068]` and 56-byte record counts span `[21615, 35714]`. This is structural coverage only, not runtime semantic validation across courses.

## Tree-only runtime result

F.1 established that the tested physical state followed the complete suffix. F.2 bound the source face planes to records inside T with HIGH_CONFIDENCE_GEOMETRIC_BINDING. F.2.1 held P/S/R fixed: modified T + baseline U moved the collision to NEW; baseline T + modified U retained collision at OLD. Thus T determines the tested physical location in this pairing. Modified U was neither sufficient nor required for this translation; its broader runtime role remains UNKNOWN. See [`runtime-results.md`](runtime-results.md).

No physical writer, arbitrary tag100 mutation, new source mesh edit, or EXE patch was added.
