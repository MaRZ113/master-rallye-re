# R5T-B Blender validation

## Existing add-on course import

The existing Master Rallye add-on imported retail Italy1 and France1 in Blender
5.2.2 with the R5T-A course smoke script. The importer validated render indices
and created the course render scene using the shared vehicle-proven coordinate
conversion. Recorded source statistics were:

| Course | Vertices | Source triangles | Draws | Result |
|---|---:|---:|---:|---|
| Retail Italy1 | 54,612 | 41,722 | 837 | PASS |
| Retail France1 | 65,206 | 64,577 | 995 | PASS |

These are automated background-import checks; they do not claim a manual visual
review of every material or texture.

## RaceTest marker overlay

Blender 5.2.2 imported the Demo 9.10.0 France1 cooker-lab DX and its RaceTest
XML, then created 583 marker empties in a separate `XML Markers - France1`
collection. Positions use the shared axis conversion; raw marker fields remain
on the imported objects. Marker direction is metadata only and does not drive
object orientation.

The built add-on ZIP was installed in an isolated Blender user profile and
exercised through its bundled `master_rallye_io.vendor.master_rallye` package.
The packaged course operator and RaceTest marker operator both returned PASS;
the packaged XML parser and collection contained the expected 583 markers.

## Limits

The marker overlay is a location aid, not a route/checkpoint interpretation.
The test does not infer marker type semantics, race direction, SFL registration,
or physical collision. Test outputs and the add-on ZIP are under ignored
`.research-output/r5t_b/` and are not committed.
