# Course Race Logic Authoring

## Status

**Course SDK G0: PASS — RUNTIME AUTHORING CONFIRMED.** The project owner
tested Blender → RaceTest XML export → game runtime for StartArea, FinishArea,
and the SplitTime0 trigger center. All three behaved as predicted by earlier
direct XML edits. Combined StartArea + FinishArea editing loaded normally with
no unexpected behavior reported. See [G0 runtime results](../research/g0/runtime-results.md).

**G0.1: PASS — AUTHORING UX AND CORRECTNESS VALIDATED.** It adds bounded
SplitTime visual-companion position authoring and Blender UX safeguards. The
new editor paths pass synthetic, 36-course corpus, and Blender 5.2.2 source/ZIP
smoke tests. Visual-companion XML edits have not been separately reported as a
new human runtime authoring test.

## Editable RaceTest fields

| Source object | Editable fields | Export behavior |
|---|---|---|
| `MarkerLists/StartArea` | `Marker Pos` XYZ for exactly four ordered markers | Writes each helper's final world point. Runtime authoring test confirmed the expected start-grid transformation. |
| `MarkerLists/FinishArea` | `Marker Pos` XYZ for exactly four ordered markers | Writes each helper's final world point. Runtime authoring test confirmed the expected completion-region change. |
| Main `SplitTimeN` Egg | `en3d Matrix/@Row3` XYZ, `gaRaceSplitTimeAI/Split Time ID`, `Radius` | Row3 XYZ is the trigger/sign center; Radius is explicit. Row3 W, Matrix rows 0–2, ExtraTime, model references, and other fields are preserved. |
| Exact sibling visual companion Egg | Its `en3d Matrix/@Row3` XYZ only | Preserves Row3 W, Matrix rows 0–2, model references, name, other properties, and hierarchy. Does not change the split trigger center. |

The manifest labels changes as `race.start.marker_position`,
`race.finish.marker_position`, `race.split.trigger_center`,
`race.split.visual_companion_position`, `race.split.radius`, or
`race.split.id`. Each change also retains its source XML path and old/new
values. The manifest schema remains `master-rallye-race-logic-edit-v1`; the
semantic-role field is additive.

### SplitTime model

```text
SplitTimeN_Group (translation controller)
├── SplitTimeN main Egg helper
│   └── wire Radius visualization
└── visual checkpoint companions
    ├── SplitTimeN-0
    ├── SplitTimeN-1
    ├── ...
```

The main Egg Row3 XYZ controls both the visible sign position and gameplay
trigger center. `gaRaceSplitTimeAI/Radius` controls the 3D sphere radius;
changing the helper object's scale does not change Radius. Split Time ID is a
signed 32-bit integer mapped by the supported executable. Duplicate IDs warn
but are not changed automatically. `ExtraTime` is preserved and its exact
semantics remain `UNKNOWN`.

Sibling `SplitTimeN-0..3` Eggs are separate visual checkpoint objects. Their
positions can be edited independently or translated with the group. Moving a
visual companion does not move the gameplay center. The group controller moves
all its children by one translation delta; Radius stays unchanged. Group
rotation and scale are locked in the UI and rejected by export if changed.
Main/helper rotation and scale are not written to Matrix rows 0–2.

### Transform and warning behavior

- StartArea/FinishArea marker helpers represent points. Export writes the final
  world location. Object rotation and scale are editor-only state and do not
  generate warnings when the point is representable.
- SplitTime center location authors Egg Row3 XYZ. Edit Radius through its
  explicit property. A non-unit SplitTime helper scale produces the warning:
  “SplitTime object scale does not change gameplay Radius; edit Radius
  explicitly.”
- Visual companion helpers export only final world position. Rotation and
  scale do not change source orientation rows.
- Group controllers support translation only. A rotated/scaled group is
  refused rather than baking an unsupported transform into source matrix data.

## Blender workflow

1. Import the course DX through **File → Import → Master Rallye Course (.dx)**.
2. In the 3D Viewport sidebar, open **Master Rallye → Master Rallye Course**,
   choose **Load Course Race Logic**, and select the matching
   `DataScene/RaceTest/<course>.xml`.
3. Move the four StartArea/FinishArea point helpers. Multi-select scaling or
   rotation is represented by the resulting point locations.
4. To translate a split and its visual companions together, select its
   `SplitTimeN_Group` controller and move it. To move just the trigger/sign,
   move the main `SplitTimeN` helper. To adjust only a visual object, move that
   `SplitTimeN-i` helper.
5. Set Radius and Split Time ID on the main SplitTime helper in the
   **Course Race Logic** panel. ExtraTime remains visible/preserved metadata.
6. Select a helper in the imported Race Logic hierarchy and click
   **Export Race Logic XML**. Choose a new output filename; export never
   overwrites the source XML or an existing manifest.

RaceTest/runtime coordinates convert to Blender as `(x, y, z) -> (x, -z, y)`;
export uses `(x, y, z) -> (x, z, -y)`. Marker exports use evaluated world
positions, including controller translation.

## Export safeguards and corpus status

The exporter checks the source XML SHA-256 captured at import. The core writer
patches only allowlisted XML attribute spans, then applies a semantic diff
guard. Unknown content and untouched bytes are retained; a zero-edit export is
byte-identical. Source mismatch, ambiguous identities, unsupported marker
counts, missing helpers, out-of-range Split Time IDs, or non-translation group
transforms are refused. The output manifest records source/output hashes,
semantic roles, source paths, changes, and warnings without embedding XML.

Current principal Retail validation:

- 36/36 RaceTest XML files parse and no-op export byte-identically.
- 36/36 StartAreas are structurally authorable.
- 34/36 FinishAreas are structurally authorable. Italy_S4 and Turkey_s1 have
  five markers and remain safely read-only.
- All 110 main SplitTime records and all 440 exact visual companion positions
  pass the structural authoring gate. Every split has four companions in this
  corpus; no naming/layout exception was found.
- The 36-course generic marker inventory is in
  [`course_marker_backlog.md`](../research/course_marker_backlog.md).

The add-on's headless Blender 5.2.2 smoke executes the Master Rallye Course and
Course Race Logic panel draw callbacks with icons validated against Blender's
RNA enum, then exercises import, no-op export, area point transforms, group and
individual companion movement, explicit Radius behavior, and manifest roles.

## What is not yet editable

| Source family | Current status |
|---|---|
| `RaceLine` | Imported read-only; broader runtime role remains a research target. |
| `Cameras` | Imported read-only; camera behavior is not assigned from the name. |
| `LeftInnerLimit`, `LeftOuterLimit`, `RightInnerLimit`, `RightOuterLimit` | Imported read-only; names do not prove road-edge, AI, respawn, or collision semantics. |
| `FinishAreaQuick` and other non-allowlisted marker lists | Imported read-only; no writer support. |
| Course render geometry, GXM, tag100, tag1400, physical data | Read-only; no writer support. |

No RaceLine, Camera, limit-marker, physical-course, geometry, or executable
authoring work is included in G0.1.
