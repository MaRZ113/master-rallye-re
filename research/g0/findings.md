# Course SDK G0 — Race Logic Authoring v0

Status: **PASS — RUNTIME AUTHORING CONFIRMED**.

G0 adds the first user-facing authoring workflow for existing RaceTest logic.
The output is a new RaceTest XML file; no compiled course resource or game
archive is written. The project owner has since tested G0-generated exports in
the runtime: StartArea, FinishArea, and SplitTime0 center authoring all passed;
combined StartArea + FinishArea editing loaded normally. See
[`runtime-results.md`](runtime-results.md). This replaces the earlier
runtime-pending status without changing the original structural test results.

## Implementation

- Core model: `CourseRaceLogicAuthoring` in
  `src/master_rallye/course_race_authoring.py`.
- Allowlisted setters: `set_start_marker`, `set_finish_marker`,
  `set_split_center`, `set_split_radius`, `set_split_id`, and
  `set_split_visual_companion_position`.
- Blender client: **Load Course Race Logic** creates source-identified helpers;
  **Export Race Logic XML** invokes the core transaction.
- Position export reads helper world locations and uses the canonical
  Blender/runtime inverse transform `(x, y, z) -> (x, z, -y)`.
- The source-span patcher preserves original bytes outside changed allowlisted
  attribute values. No-op output is byte-identical.
- A parsed-tree semantic guard permits only the changed allowlist fields.
  Source hash mismatch, ambiguous structure, missing helper inventory, edits to
  read-only helpers, and in-place/overwrite output paths are rejected.
- Export manifest: `<output>.mr-race-edit.json`, with source/output hashes,
  changed paths and values, and warnings; no XML payload is embedded.

## Supported fields and preserved data

Editable: all four ordered `Marker Pos` values in an unambiguous StartArea or
FinishArea, plus main SplitTime Egg Row3 XYZ, `Radius`, `Split Time ID`, and
G0.1 exact sibling visual-companion Egg Row3 XYZ.
The writer preserves marker direction and other marker properties, Egg matrix
rows 0–2, Row3 W, `ExtraTime`, model references, hierarchy, object order, other
attributes, unknown properties, and unrelated XML content. Visual companion
edits are independently allowlisted by exact source Egg identity. It exposes
no generic XML setter.

StartArea and FinishArea accept point deformations. Validation reports
coincident points, near-zero X/Z area, self-crossing point order, and extreme
extent as warnings without reordering or correcting points. Split Radius must
be positive and finite; unusually large values and duplicate IDs are warnings.
The exact `ExtraTime` semantics remain `UNKNOWN`.

Two current Retail FinishAreas have five markers: ItalyS4 and TurkeyS1. G0
refuses authoring for those FinishAreas rather than dropping a point. A moved
unsupported helper is now an export error rather than a silent no-op.

## Corpus and static edit evidence

The curated Retail `CourseProject` inventory contains 36 principal course
projects. All 36 XML files parse, and 36/36 no-op exports are byte-identical.
All 36 StartAreas are authorable, 34/36 FinishAreas are authorable, and all
110 discovered SplitTime records pass the authoring gate. Split distribution:
34 courses have three records; two courses have four. Radius observed range is
7–30 in this corpus; that range is an inventory, not a supported limit.

`tools/validate_course_race_logic_authoring.py` exercises these four France1
in-memory scenarios and verifies the allowlist paths:

| Scenario | Fields changed | Result |
|---|---:|---|
| StartArea rigid runtime X +3 | 4 | PASS |
| FinishArea runtime X/Z scale 2 around centroid | 4 | PASS |
| SplitTime0 main Egg center move | 1 | PASS |
| SplitTime0 Radius edit | 1 | PASS |

Generated scenario bytes were checked in memory only; proprietary XML files
were not modified or committed. Results are in
[`retail-race-logic-validation.json`](retail-race-logic-validation.json),
[`retail-race-logic-validation.md`](retail-race-logic-validation.md), and
[`france1-edit-validation.json`](france1-edit-validation.json).

## Blender validation

Blender 5.2.2 smoke tests passed against both repository sources and the built
installable ZIP. The test imports France1, checks hierarchy/helper counts,
performs a byte-identical no-op export, edits one StartArea point, one
FinishArea point, one SplitTime center, Radius, and ID, exports, and reparses
the result. Existing Retail France1 course XML hash used by the smoke is
`beaa2180912ffd54f313a149962e295f9894239014481d2c7ba2db84fb1e08e1`.

G0's original Blender validation was structural/UI-pipeline testing. The later
human runtime result is recorded separately. G0.1's additional Blender 5.2.2
smoke executes the Master Rallye Course and Course Race Logic panel draw
callbacks with icon enum validation, then checks byte-identical no-op export,
area scale warning behavior, whole split-group translation, independent visual
companion translation, explicit Radius behavior, and semantic manifest roles.
G0.1 is **PASS — BLENDER/CORPUS VALIDATED**. Visual-companion edits have not
been separately runtime-tested.

## G0 runtime closeout

Human runtime tests through Blender export passed for StartArea, FinishArea,
and SplitTime0 center. Combined StartArea + FinishArea editing also loaded
normally with no unexpected behavior reported. The runtime build/hash and
exported XML hashes were not included in the closeout report and are left
unspecified. The earlier [`runtime-handoff.md`](runtime-handoff.md) is retained
as the preparation plan and marked completed.

## Scope boundary

No DX, GXM, tag100, tag1400, physical, RaceLine, SFL, surface, or general course
writer was added. No executable patch or archive modification was made. The
existing Vehicle SDK remains unchanged.
