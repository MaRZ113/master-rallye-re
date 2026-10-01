# Course SDK G0 runtime results

Status: **PASS — RUNTIME AUTHORING CONFIRMED**.

The project owner reports successful in-game testing of RaceTest XML exported
through Blender's G0 authoring workflow. Each result matched the previously
established direct XML behavior. These are human runtime observations; the
closeout report did not provide a runtime build/hash, exported XML hash, or
candidate manifest, so those identifiers are not inferred here.

| Blender → RaceTest XML edit | Human-observed runtime result | Evidence |
|---|---|---|
| StartArea marker edits | Expected start-grid transformation reproduced. | `CONFIRMED_BY_RUNTIME_AUTHORING_TEST` |
| FinishArea marker edits | Completion region changed as expected; `RACE COMPLETE` behavior remained predictable. | `CONFIRMED_BY_RUNTIME_AUTHORING_TEST` |
| SplitTime0 main Egg Row3 edit | Gameplay trigger center moved as expected. | `CONFIRMED_BY_RUNTIME_AUTHORING_TEST` |
| Combined StartArea + FinishArea edit | Runtime loaded normally; no unexpected behavior observed. This is not exhaustive combinatorial validation. | `CONFIRMED_BY_RUNTIME_AUTHORING_TEST` |

No unexpected race-logic behavior or runtime anomalies were reported. G0 is
closed; the G0.1 Blender/corpus checks are documented separately and do not
claim runtime testing of the newly editable visual-companion positions.
