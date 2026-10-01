# R5T-F.0 controlled cook and runtime handoff

## Cook validation complete

Three cold cooks per cohort have been captured and validated by
`python tools\r5t_f0_cooker_runs.py compare`. All six DX files parse as
revision 135 with validated course render sections. The input manifest
confirms the only source-input hash difference is `France1.gxm`; the runtime,
TXT, and RaceTest XML are unchanged.

`tag100` repeats byte-identically within both cohorts, but differs between
baseline and modified. Sizes are 10,118,248 bytes (baseline) and 10,114,844
bytes (modified); SHA-256 values are respectively
`9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7` and
`e31f79ae9ac83db3141a631363e7f982e0fbd9d4ba281bbb5f4a4f21bdf19d07`.
The payloads differ at 3,294,483 positions in their 10,114,844-byte common
prefix, with 412,277 same-offset ranges, and the baseline has a 3,404-byte
tail. These offsets are not semantic record alignment. Full DX files still
vary within each cohort, so render-prefix differences remain subject to
cooker nondeterminism. None of these results establishes tag100's physical
meaning.

The final cooked runtime copies are retained at:

- Baseline: `research-output/r5t_f0/cooker-lab/baseline/runtime`
- Modified: `research-output/r5t_f0/cooker-lab/modified/runtime`

The exact run-03 DX identities are baseline
`b7820fe13c5ef7eb53593bcee4e54943cf97780244b47f6fe7cb549d5c5ee7f2` and
modified `01289e705750fa257037b65f55f7b469db795b4c649f74b45777da0a8d08bac2`.
The in-game visual/physical comparison has been completed and is recorded in
[`findings.md`](findings.md). R5T-F.1 now isolates whether the tested physical
state follows the render prefix or trailing tag100.

## Probe identity

| Item | Baseline | Modified |
|---|---|---|
| Source GXM SHA-256 | `56ebbf03fe681d730e796a40d455562b5f9976d794c710e73d5c9be32e4e86b2` | `2e93f6291f9b5e4b0606b218e42f7926a7d4f0d37a1eb76f359d9ccbff4dc2a2` |
| Target | `COLLIDE_finishline03`, `Index=47083`, `Size=24` | Same mesh span and topology |
| Source edit | none | 14 exclusive positions, source X `+20.0` |
| Runtime/XML centroid | `(-1471.7653, 68.4258, 352.5542)` | `(-1451.7653, 68.4258, 352.5542)` |
| Runtime/XML AABB min | `(-1472.2988, 63.6745, 352.0665)` | `(-1452.2988, 63.6745, 352.0665)` |
| Runtime/XML AABB max | `(-1471.2317, 73.1173, 353.0419)` | `(-1451.2317, 73.1173, 353.0419)` |

The same Demo 9.10 RaceTest XML is used by both clones (SHA-256
`6048ed26c78118f3f82d9ddbcaf4f75c6655b24d805189d3cf3bd772202dc0df`). The
baseline and modified course source inputs differ only by `France1.gxm`.
FinishArea and every XML field are unchanged. Exact output hashes for all six
DX files and generated DXT files are recorded in
`research/r5t_f0/cook-differential.json`.

## Human observations after cook validation

Use the run-03 runtime tree for each cohort, with the same opponents and
comparable driving approach. Observe only:

1. Is a visible object corresponding to this source mesh present at the old
   position, the new position, both, or neither? Does anything visibly move by
   the expected +20 runtime X?
2. At each position, does the car make physical contact with something (stop,
   collide, or otherwise react)? Compare baseline and modified.
3. With RaceTest XML and FinishArea unchanged, does race completion still occur
   in the ordinary FinishArea? Does its observed region change?
4. Is there obvious rendering corruption, a loading failure, disappearing
   objects/cars, or an AI/route anomaly?

Do not infer internal semantics from the object name. The following matrix was
the pre-test interpretation guide; the completed observations are recorded
after it:

| Observation | Bounded interpretation |
|---|---|
| Visible object and physical contact both move; FinishArea completion stays put | Source mesh may contribute to visible and physical representations; XML completion remains separately effective. Requires compiled-region attribution. |
| Not visible; physical contact moves; FinishArea completion stays put | Strong evidence for hidden physical behavior; a stable tag100 response would be a candidate compiled bridge, not a complete tag100 decode. |
| Visible object moves; no physical contact moves; FinishArea completion stays put | Evidence favors a render-oriented role for this source mesh. |
| FinishArea completion moves or changes | Unexpected coupling; preserve as a single-probe result for focused review. |
| Nothing observable changes | The mesh may feed another system, be unused, or the test location may be insufficient. No forced conclusion. |

## Completed human observation

Baseline collision was present at both visible finish supports. In the
modified course the visible banner/right support stayed at its original render
location, but the right support became pass-through; collision was encountered
at the predicted +20 runtime-X position in empty/non-rendered space. Race
completion remained at the unchanged RaceTest FinishArea. This is
**CONFIRMED_BY_RUNTIME_EDIT** for the tested `COLLIDE_finishline03` physical
effect and translation. The result does not identify tag100 as its carrier;
see the reciprocal swap test in `research/r5t_f1/`.
