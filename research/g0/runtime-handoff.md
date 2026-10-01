# G0 optional Retail runtime handoff

This is a review handoff, not an executed test. The G0 export path has only
been tested structurally and in Blender 5.2.2. Do not modify the user's
original game installation or `Data.sma`; generate each XML in Blender, keep
its `.mr-race-edit.json` manifest, and test one candidate at a time in a
separate Retail runtime copy using the existing known RaceTest override method.
Restore that copy to baseline between candidates.

Use Retail France1 and its principal source:

```text
DataScene/RaceTest/France1.xml
```

The exported file must be installed under the runtime's expected France1 XML
identity/path in the isolated copy. Preserve the original copy and record the
candidate manifest hash. Do not infer success from the Blender preview alone.

## Test A — StartArea group translation

1. Load baseline France1 Race Logic.
2. Select the four `StartArea` marker helpers and translate all by **+3.0 on
   Blender X**. This is runtime X +3 under the shared axis mapping.
3. Export a new XML and confirm the manifest lists only the four
   `/MarkerLists/StartArea/Marker[i]/...Marker Pos...` fields.
4. Test in the isolated Retail copy.

Expected discriminating result: the physical starting grid translates
laterally as a coherent group, matching the already established direct
RaceTest runtime effect. If the participant order changes, record it separately
from marker geometry.

## Test B — FinishArea expansion

1. Reload baseline France1 Race Logic.
2. Select the four `FinishArea` marker helpers, use the median pivot, and scale
   **Blender X and Y by 2.0**, leaving Blender Z unchanged. Runtime X/Z map to
   Blender X/Y.
3. Export a new XML and confirm only the four FinishArea marker positions
   changed.
4. Test in a fresh baseline copy.

Expected discriminating result: the completion region expands and `RACE
COMPLETE` occurs earlier than at the baseline boundary, consistent with the
prior direct XML runtime edit.

## Test C — SplitTime0 center move

1. Reload baseline France1 Race Logic.
2. Select the main `SplitTime0` sign helper and set its world position to the
   Blender conversion of runtime `(-2415.42, 72.10, -124.94)`, which is
   `(-2415.42, 124.94, 72.10)`.
3. Keep **Radius = 21**, **Split Time ID = 0**, and all other values unchanged.
   In particular, do not move sibling checkpoint objects, RaceLine, StartArea,
   or FinishArea.
4. Export a new XML. Confirm the manifest has only the main SplitTime0 Row3
   XYZ path and that ID, Radius, and ExtraTime are absent from the changes.
5. Test in a fresh baseline copy and observe the relocated on-road point and
   the old split location.

Expected discriminating result: the SplitTime0 event is awarded at the moved
on-road sphere before reaching its ordinary location; the visible sign follows
the same Egg center. This target reproduces the earlier direct runtime edit
through the new authoring/export path. Do not place it near StartArea: a sphere
there previously activated all four per-car one-shot flags during startup.

For every test capture the game build, source XML hash, exported XML hash,
manifest, selected course, and observed result. Report missing triggers,
startup activation, unrelated split/finish changes, or load failures without
changing multiple candidate files in the same run.
