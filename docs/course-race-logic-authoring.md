# Course Race Logic Authoring v0

G0 adds a small Blender-to-RaceTest XML authoring path for runtime-confirmed
race logic. It does not write course render geometry, GXM, tag100, tag1400,
physical data, RaceLine, or any other compiled resource. Newly exported XML has
not yet been tested in-game through this G0 UI path.

## Supported fields

| RaceTest item | Editable fields | Limits |
|---|---|---|
| `MarkerLists/StartArea` | The ordered `Marker Pos` Vector3 for markers 0–3 | Export requires exactly four unambiguous markers. Runtime semantics support a physical grid frame; exact slot interpolation is unknown. |
| `MarkerLists/FinishArea` | The ordered `Marker Pos` Vector3 for markers 0–3 | Export requires exactly four unambiguous markers. The list contributes to completion; it is not claimed to be the only finish subsystem. |
| Each main `SplitTime` Egg | `en3d Matrix/@Row3` X/Y/Z, `gaRaceSplitTimeAI/Split Time ID`, and `Radius` | Row3 W, matrix rows 0–2, `ExtraTime`, components, sibling Eggs and all other properties are preserved. |

StartArea and FinishArea positions are accepted as arbitrary four-point shapes;
the writer does not reorder or force a rectangle. It reports warnings for
coincident points, nearly zero projected area, a self-crossing X/Z perimeter,
and unusually large extents. Duplicate Split Time IDs are warned about, not
renumbered. Radius must be finite and greater than zero; a large value warns
without asserting a game limit. ExtraTime's exact meaning remains `UNKNOWN`.

Authoring is refused when the target's source structure is missing, duplicated,
or ambiguous. In the current Retail corpus, all 36 StartAreas and all 110 main
SplitTime records pass the structural gate. Two FinishAreas have five markers:
ItalyS4 and TurkeyS1. They remain visible/read-only; export refuses if one of
those unsupported helper points was moved.

## Blender workflow

1. Import the course DX through **File → Import → Master Rallye Course (.dx)**.
2. In the 3D Viewport sidebar, open **Master Rallye → Master Rallye Course**,
   choose **Load Course Race Logic**, and select the matching
   `DataScene/RaceTest/<course>.xml`.
3. Edit the ordered marker empties in the `Race Logic/StartArea` and
   `Race Logic/FinishArea` collections. Move one point for deformation, or
   multi-select all four and transform around the median point for a group
   translation, rotation, or scale. Export uses each helper's final world
   position; it does not export a parent transform.
4. Move a main SplitTime sign helper to move the sign and trigger center
   together. Select it and edit **Radius** or **Split Time ID** in the
   **Course Race Logic** panel. Its wire sphere follows Radius. Rotation and
   scale are locked by default and are not written to the XML.
5. Do not move the separate `SplitTimeN-0..3` visual checkpoint objects to
   position a trigger. They are informational visuals. ExtraTime is shown as
   preserved metadata and is not editable.
6. Select a helper from the imported Race Logic hierarchy and click
   **Export Race Logic XML**. Choose a new output filename.

The coordinate conversion is shared with the course importer:

```text
RaceTest/runtime (x, y, z) -> Blender (x, -z, y)
Blender (x, y, z)          -> RaceTest/runtime (x, z, -y)
```

Thus a runtime X edit is Blender X; a runtime X/Z plane transform maps to
Blender X/Y. The exported points are computed from world positions, so Blender
object parenting and multi-object transforms are folded into the four points.

## Export safeguards

The exporter checks the source XML SHA-256 captured at import. If that file
changed, reload the helpers before exporting. The core writer edits only the
allowlisted source attribute spans and then compares the parsed XML trees with
only those values masked. Any other semantic difference rejects the export.
An unchanged document returns the original bytes exactly. The writer refuses
the source path and refuses an already-existing output or manifest; it never
modifies `Data.sma`, the source XML, or compiled course resources.

Alongside the new XML it writes `<output>.mr-race-edit.json`, containing course
identity, source and output SHA-256 values, changed paths and old/new values,
unknown-content preservation status, and warnings. It does not embed the source
XML contents.

## Evidence limits

StartArea translation/orientation/spacing, FinishArea's completion-region
effect, SplitTime Egg Row3 center, and the spherical Radius behavior have
runtime evidence documented in the R5T-D closeouts. G0's corpus and Blender
tests validate source preservation, allowlist enforcement, coordinate handling,
and operator behavior. They do not establish in-game behavior for a G0 export.
See [`research/g0/findings.md`](../research/g0/findings.md) and the optional
[`research/g0/runtime-handoff.md`](../research/g0/runtime-handoff.md).
