# R-DEMO2.6 — exact demo-8.4.1 hull NULL provenance

## Executive result

**Level C: structure and immediate NULL producer closed; source-level cause OPEN.** In the exact September 2001 demo, `005C3200–005C3238` is an edge endpoint-overlap predicate, not a generic comparator. It returns true if either of one edge's two endpoint pointers equals either endpoint pointer of the other edge. The failing argument is an **edge-object pointer** stored at `+8` in a circular doubly linked list node. `005C447B` explicitly sets the candidate edge pointer to zero after an exhaustive no-match search, and `005C4496` inserts that zero into the local list. The next iteration obtains it through `005C443B–005C4441`, calls `005C3200`, and faults at `005C3212` on NULL+`0x64`.

The original baseline did not present a zero edge argument at the user's conditional breakpoint and completed model loading. Static code shows the condition for zero: a nonempty face edge list contains no edge sharing an endpoint with the current local-list edge. Which **face and endpoint set** first causes this for the edited input is not yet captured. The uniform translation is a demonstrated input difference, but a specific violated source/dependent invariant is **UNKNOWN**. No EXE patch or new model mutation was made.

## Evidence identity and limits

| Input | SHA256 / observation | Status |
|---|---|---|
| `demo-8.4.1/MRallye.exe` | `bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be` | CONFIRMED_BY_BYTES; exact static target |
| Original `demo-8.4.1` Trooper `car.gxm` | `fd08bc10c440fce261ef126e40445002fb56359d4011c1dcbf9c2f71b0e91047` | CONFIRMED_BY_BYTES |
| Crash candidate `car.gxm` | `0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699` | CONFIRMED_BY_BYTES |
| Candidate at `005C4457`, condition `EBX==0` | EBX=0; `[esp+38]=16495788`, first node `16495D28`, node `+8=0`; AV at `005C3212` reading `0x64` | USER-REPORTED CONFIRMED_BY_RUNTIME; x32dbg excerpt supplied in phase prompt, not an independently acquired raw capture |
| Baseline, same conditional breakpoint | no trigger; completed loading | USER-REPORTED CONFIRMED_BY_RUNTIME, limited to that run |

The PE32 has machine `0x14c`, preferred image base `0x400000`, and DLL characteristics `0x0` (no `DYNAMIC_BASE` flag). Addresses in this report are exact virtual addresses for this executable and the reported run. Do not transfer them to 9.3.1 or retail.

## Static NULL chain

1. `005BA290` builds `0x80`-byte intersection/edge objects for qualifying pairs of `0x40`-byte face/plane objects and calls `005C42D0` twice to append the new edge pointer to each face's `+0x28` list. The call argument is computed as the base of the edge-object array plus a `0x80` stride; this ordinary producer does not pass literal zero.
2. `005BA6B0` fills each edge `+0x64` endpoint list with pointers into the `0x20`-stride vertex-object array, using `005C3960` to reuse a vertex or `005BA930` to select the nearest existing vertex. `005C3100` writes those pointers at list-node `+8`.
3. `005BABC0` iterates face objects at hull-state `+0x24` in `0x40` strides, calling `005C4350`, which first calls `005C43A0`.
4. `005C43A0` moves the first face edge pointer to a local list and removes it from the face list. While the face list remains nonempty, `005C4451–005C4479` tests face edges against the current local edge using `005C3200`. A match chooses a real pointer. If no match exists, `005C447B XOR EDI,EDI` chooses NULL. `005C4481 MOV [ESP+1C],EDI` and `005C4496 CALL 005BC490` write it into an inserted local node's `+8`.
5. The subsequent removal scan `005C449B–005C44DE` removes matching edge pointers from the face list. With NULL chosen and normal non-NULL face edge pointers, no entry matches, so count remains nonzero. `005C44E5` loops to `005C443B`, which obtains the local first-node payload into EBX. The call at `005C4457` passes EBX as the argument; `005C3212 MOV EDX,[EAX+64]` dereferences that NULL argument.

The chain from no-match branch to fault is **CONFIRMED_BY_EXE** and consistent with the user's runtime observation. Actual execution of `005C447B` in the candidate has not yet been directly breakpoint-captured. The ordinary face-list writer makes the no-match branch the concrete static producer; memory corruption or another unexpected writer is not established and cannot be categorically excluded by static analysis alone.

## Predicate and search invariant

At `005C3200`, `ECX` is one edge pointer. Its `+0x64` points to a sentinel whose first two payloads provide endpoint pointers A/B. At `005C320B`, the stack argument becomes EAX; its `+0x64` provides endpoint pointers C/D. `005C321C–005C322D` compare A==C, A==D, B==C, B==D; `AL` becomes 1 on any equality, 0 otherwise. The caller tests `AL` at `005C445C`.

Thus the local face-reordering algorithm requires a next edge sharing at least one **vertex-object identity** with the current edge while unprocessed face edges remain. When the source positions change, plane/intersection generation and endpoint selection can change which identities exist or are shared. That causal route is **INFERRED**, not proof of a particular stale GXM field. Exact first divergent face, edge sequence and endpoint identities require the bounded runtime capture in `r-demo2.6-runtime-followup.md`.

## Exact GXM differential

`tools/scanner/r_demo2_6_hull_diff.py` pins both input hashes and rejects other build/layout/section edits. Repeatable JSON is retained at `.research-output/r-demo2/exact-841-hull-diff.json` (ignored).

- Both files are 222,749 bytes. Exactly 126 bytes differ, offsets `221585..222008`, exclusively source Vector-C X words for indices `1317..1352`. No source Y/Z words, A/B array bytes, material/record bytes, or hierarchy bytes changed. The leaf `$chull(Trooper)` still has 68 records `[1911,1979)`, 204 corners and 36 referenced C indices.
- Per-point source X delta is `0.3999999762..0.4000000358`; source hull X bounds move `[-0.94192147,0.94192177]` to `[-0.54192150,1.34192181]`; centroid X moves `-0.07185331` to `0.32814669`. Source Y/Z bounds and centroid remain equal. Hull radii from its own centroid stay `1.098078..2.978146` within binary32 rounding, while origin radii change from `1.223661..2.797270` to `0.950688..2.827110`. Minimum hull-to-other-global-C distance is `0.0588820` baseline and `0.0528134` candidate in source coordinates, both above the 9.3.1 welder tolerance `0.01`; the exact 8.4.1 welder behavior is not inferred from that comparison.
- All 68 source triangles remain nondegenerate. Triangle normals/cross magnitudes are invariant geometrically under rigid translation, with binary32 rounding residuals (maximum normalized component delta `2.23e-7`). Derived source-plane `d=-n·p` changes by up to about `±0.399924`, and the residual from the expected `-n_x*0.4` relation is at most `2.61e-7`. These are Python binary64 diagnostics on binary32 GXM values, **not** captures of native post-weld plane objects.
- A/B vectors, indices and hierarchy are unchanged bytes. Whether native face selection uses A/B, absolute plane offsets, tolerances, or another derived state to reach the no-match branch is **UNKNOWN**. A uniform translation by itself does not change the selected point set's ideal topology.

## Remaining unknowns and R4G impact

The first candidate face/edge list with no shared endpoint, the corresponding baseline edge list, and the exact geometric decision upstream of that divergence remain **UNKNOWN**. Therefore no additional field recomputation rule can yet be specified for writable `$chull` GXM tooling. R4G collision writing remains frozen at its previous evidence boundary; this phase adds a concrete guard requirement for future source-edit validation: reconstruct/validate the face edge-adjacency walk and reject a no-match case before proposing a runtime-safe hull edit. This is a research requirement, not a proven repair algorithm.

This work stays in the dedicated `research/r-demo-pipeline` branch. No merge, push, R5T, runtime mutation or raw asset commit.
