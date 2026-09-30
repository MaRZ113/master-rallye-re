# R5T-F.0 controlled cook and runtime handoff

## Current gate

The source-only mutation is prepared and audited. The isolated baseline and
modified Demo 9.10.0 runtime copies are staged, but neither has been cooked
for this probe. Runtime testing must wait until six cold cooks have been
captured and `compare` validates revision-135 DX in all six snapshots.

Use the manual sequence in
`research-output/r5t_f0/cooker-lab/COOK-INSTRUCTIONS.md`. It runs the original
Demo 9.10.0 runtime only from isolated copies. Do not launch the seed cooker
lab or Retail installation. For each cohort, perform runs 01, 02, and 03,
capturing each run before resetting caches. After run 03, leave the cooked
runtime intact. The baseline and modified run-03 runtimes are then available
for the human comparison.

From the repository root, the capture/reset commands are:

```powershell
python tools\r5t_f0_cooker_runs.py capture --cohort baseline --run-id baseline-01
python tools\r5t_f0_cooker_runs.py reset --cohort baseline
```

Use the matching cohort/run ID for each capture. Reset after runs 01 and 02
only; do not reset after run 03. After all six captures:

```powershell
python tools\r5t_f0_cooker_runs.py compare
```

The output report is `research/r5t_f0/cook-differential.json`. It must show
three validated rev135 outputs per cohort, stable tag100 bytes within each
cohort, and a baseline/modified tag100 difference before attributing any
compiled response to the source edit. Render-prefix differences are compared
across repeated cooks and must not be called causal unless they exceed natural
variance. A changed tag100 still does not prove collision or physical meaning.

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
FinishArea and every XML field are unchanged. Exact DX and DXT output hashes
remain **PENDING** until the six captures are validated.

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

Do not infer internal semantics from the object name. Record observations in
terms of what moved or what the car contacted. Interpretations remain open:

| Observation | Bounded interpretation |
|---|---|
| Visible object and physical contact both move; FinishArea completion stays put | Source mesh may contribute to visible and physical representations; XML completion remains separately effective. Requires compiled-region attribution. |
| Not visible; physical contact moves; FinishArea completion stays put | Strong evidence for hidden physical behavior; a stable tag100 response would be a candidate compiled bridge, not a complete tag100 decode. |
| Visible object moves; no physical contact moves; FinishArea completion stays put | Evidence favors a render-oriented role for this source mesh. |
| FinishArea completion moves or changes | Unexpected coupling; preserve as a single-probe result for focused review. |
| Nothing observable changes | The mesh may feed another system, be unused, or the test location may be insufficient. No forced conclusion. |

No runtime observation has been made for this mutation yet. Do not perform a
second mesh mutation or assign `COLLIDE_finishline*` a collision/trigger role
until the cook and human observations are reviewed.
