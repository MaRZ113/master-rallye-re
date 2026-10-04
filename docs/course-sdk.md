# Course SDK: read model and bounded RaceTest authoring

R5T-SDK1 composes the existing format readers into a typed course read model.
G0 adds a deliberately narrow RaceTest XML authoring transaction for runtime-
confirmed race-logic fields. This is not a general course authoring SDK: no DX,
GXM, RaceLine, SFL, surface, physical-data, or course-geometry writer is
provided.

## Public entry point

The Python package exports `CourseProject`, the race-logic and render model
types, `CourseRaceLogicAuthoring`, and the existing `parse_course_dx`,
`parse_course_xml`, `parse_hnt`, and `parse_sfl` readers. To discover exact-stem
resources from a directory or a given course resource path:

```python
from pathlib import Path
from master_rallye import load_course_project

course = load_course_project(
    Path("DataScene/RaceTest/France1.xml"),
    search_roots=(Path("DataGx/Course/France1"), Path("DataScene/ICont")),
)
```

`discover_course_resources()` returns candidate paths and diagnostics before
parsing. A file path pins that resource. Folder discovery uses exact normalized
stems, with a unique-model fallback only for an explicitly supplied course
folder. When HNT files are available, an exact resolved `Model` path links the
selected DX to its HNT and that HNT's exact stem to RaceTest XML and SFL.
TXT/GXM sidecars may use the selected DX's exact stem. Multiple matches or an
unlinked model candidate are reported; no basename-only HNT guess is made.
`load_course_project()` keeps successfully parsed resources if an optional
sibling is absent or malformed. DX-only, XML-only, and TXT-only projects are
representable.

The curated Retail corpus at `corpora/retail/Data.sma_unpacked` resolves all 36
course folders into DX, TXT, HNT, principal RaceTest XML, and SFL projects. Of
2,843 HNT references, 2,842 resolve by exact path, one texture reference
remains unresolved, and none are ambiguous. Its runtime necessity is unknown.
All 41 RaceTest XML files in the curated corpus parse: 36 principal
HNT-matched course files and five other RaceTest files. The repository-parent
live unpack used for runtime probes is excluded because its France1 DX/XML
differ from the curated baseline; its probe copies are not counted as Retail
corpus files.
See [`research/r5t_sdk1/retail-corpus-validation.md`](../research/r5t_sdk1/retail-corpus-validation.md).

The Blender interface remains incremental: import the course DX, then select
its RaceTest XML. The core SDK discovery/loading path is ready for scripts and
later package-folder UI work.

## Unified Blender add-on

Course workflows and vehicle workflows share one maintained source tree:
`blender/master_rallye_io/`, with the reusable parser library in
`src/master_rallye/`. The install candidate is
`dist/master_rallye_io.zip`; `tools/build_blender_addon.py` verifies every
packaged Python source against its canonical source, including the vendored
library. R-MAT1 Preview V3 is selected only for `resource_kind="vehicle"`.
Course DX keeps the existing unscoped material preview because equivalent
course-material semantics have not been established.

SplitTime companion cards remain editor-only: their pole base begins at the
unchanged Row3 export anchor, the billboard previews the source-facing `+Row2`
basis, and the separate arrow previews `-Row2` as a local RaceLine travel
correlation. The latter is a high-confidence geometric correlation, not
runtime gameplay proof. Neither diagnostic object expands the RaceTest writer.

## Model layers

Raw readers remain loss-preserving and independently available:

- `CourseXmlDocument` retains the generic XML tree, ordering, attributes,
  matrices, markers, Eggs, AI components, raw values, and XML paths.
- `CourseDxModel` continues to parse the shared DX prefix and revision-135
  course draws with the established range validation.
- HNT, SFL, TXT, and GXM prefix readers retain their existing behavior.

`CourseRaceLogic` is a semantic projection over `CourseXmlDocument`. It keeps
references to the original marker lists, Eggs, and `gaRaceSplitTimeAI` component
so callers can inspect provenance without reparsing XML. `CourseStartArea` and
`CourseFinishArea` preserve source-order markers, parsed positions/directions,
centroids and X/Z bounds when all positions are valid. StartArea is a geometric
frame for physical starting-grid placement and heading. FinishArea contributes
to race completion; it is not claimed to be the only finish subsystem.

Each `CourseSplitTime` exposes the parsed ID, Egg Row3 center, Radius, raw and
numeric ExtraTime, the source Egg/component, issues, and exact-name visual
companions. Its trigger shape is `sphere`. A missing/invalid ID, center, or
nonnegative Radius keeps `trigger_complete` false; no values are fabricated.
`ExtraTime` semantics remain `UNKNOWN`.

Evidence fields distinguish semantic-rule evidence from record-specific
evidence. The generic XML parser reports the executable/shared-structure basis
for interpreting split centers and radii; it leaves `record_evidence` empty
rather than treating a filename such as `France1.xml` as proof that the loaded
file is the runtime-tested original. StartArea/FinishArea runtime findings are
likewise rule evidence, not proof that every list instance was directly tested.
The specific France1 SplitTime0 debugger and moved-on-road results remain in
[`research/r5t_d1`](../research/r5t_d1/), separate from generic parsed-record
provenance. SplitTimeN-index companions remain separate visual objects and
are not trigger-center sources.

## Package resources

`CourseProject` may contain any subset of:

- `render`: a frozen `CourseRenderResource` view of positions, normals, colors,
  UV sets, local indices, draw groups and texture-slot summaries.
- `race_logic`: typed RaceTest semantics plus its raw XML document.
- `dependencies`: HNT keyword/value/raw line, resolution status, exact relative
  result, and ambiguity candidates. `Model`, `Texture`, and `FSTexture` remain
  distinct keywords.
- `sfl`: dimensions, header, payload statistics and `semantics="UNKNOWN"`.
- `source_txt` and `source_gxm`: parsed hierarchy and bounded GXM prefix.
- `source_geometry` and `source_meshes`: read-only topology for paired version-7
  `moModel` resources. Meshes preserve literal names, hierarchy, `Index`/`Size`,
  source position indices, bounds, and evidence while leaving gameplay role
  `UNKNOWN`.
- `resources` and `diagnostics`: selected paths, candidate sets, and parse or
  ambiguity information.

The public course render view represents the trailing tag-100 region as
`CourseTag100Region` with presence, offsets, size, hash, boundary status, and
`semantics="UNKNOWN"`. It does not call the region collision BSP. The current
low-level course parser still reuses the historical shared trailing-section
parser internally; vehicle collision APIs are unchanged. The low-level parser
object used by Blender is held behind a private adapter field, while the public
Course SDK surface uses neutral names.

## Blender helpers

The existing add-on consumes `CourseRaceLogic` for RaceTest helper creation.
It creates source-ordered StartArea and FinishArea marker-point collections,
a separate three-ring wire sphere for each complete split, and a
`Visual Checkpoint Objects` collection for associated sibling Eggs. The main
SplitTime center stays visually simple; the procedural sign cards and direction
rays are attached to each sibling visual companion and use that companion's own
source matrix. A translation-only checkpoint group parents the main Egg helper
and visual companions while preserving their initial world transforms. Center
and radius use the established course-to-Blender transform and scale. The sphere
stores ID, radius, source XML paths, semantic-rule evidence, record-evidence
metadata, raw ExtraTime, and `ExtraTime` semantic status.
`CourseRaceLogicAuthoring` provides setters for four-marker StartArea and
FinishArea positions, main SplitTime Row3 XYZ/Radius/ID, and exact visual
companion Egg Row3 XYZ. Its source-span writer preserves original bytes outside
changed attributes, returns source bytes unchanged on no-op, applies a
semantic diff guard, and refuses in-place overwrite. ExtraTime, matrix rows
0–2, Row3 W, and all unallowlisted properties remain unchanged.

RaceLine remains an ordered marker list. Retail executable analysis confirms
that `gaRaceLineAI` consumes its `Marker Pos` sequence for nearest per-car
sample, normalized Progress and Rank updates. A controlled runtime edit to
France1 samples 265–268 produced a localized visible progress-indicator change
as the player passed that region (`CONFIRMED_BY_RUNTIME_EDIT`). No obvious AI
steering change was observed in that probe; AI use is not ruled out globally.
The separate SplitTime path still runs from split center to nearest RaceLine
sample/percentage; no RaceLine marker is treated as a split trigger center.
The source-order corpus median spacing is about 20 world units, with variation;
this is guidance for a future bounded authoring phase, not a format constant.
RaceLine remains read-only in the stable writer. The add-on package is version
4.6.0 and retains its Blender 4.3 minimum.

G1 adds read-only Blender source-order polylines and marker helpers for
RaceLine and the four exact limit lists. Retail executable analysis confirms
`gaLimitsAI` loads `LeftInnerLimit`, `RightInnerLimit`, `LeftOuterLimit`, and
`RightOuterLimit` and publishes per-car `LimitState`; it does not establish all
downstream reset behavior. The first LeftInnerLimit edit was inconclusive; an
isolated LeftOuterLimit probe is prepared but not runtime-tested. `Marker Dir`
is preserved and visualized as an optional diagnostic ray, not promoted to
gameplay semantics. The XML `Cameras` list remains read-only; its linkage to
camera parameters is unknown. See [`research/g1`](../research/g1/findings.md)
for executable anchors, corpus geometry, and runtime results. None of these G1
fields were added to the stable G0 XML writer.

Tracked corpus reports and findings live under repository `research/`.
Hash-guarded human runtime probe XML/manifests default to the untracked runtime
root `D:\Game\Master Rallye\research-output\g1\probes`; the probe tool prints
the resolved absolute paths and accepts `--output-root <path>` to select
another destination.

## Authoring boundary and open questions

Supported reads include revision-135 course render geometry, RaceTest
hierarchy and the proven StartArea/FinishArea/SplitTime interpretations, HNT
dependencies, structural SFL data, TXT hierarchy, version-7 GXM source
topology, and raw tag100 metadata. A standalone read-only tag100 parser now
decodes the loader-confirmed recursive wire shape; a separate probe correlates
some optional float4/code records with the tested source planes. The higher-level
`CourseProject` physical API remains unimplemented. G0 does not support course
geometry writing, physical/collision authoring, arbitrary layouts, RaceLine AI
steering authoring, limit authoring, camera authoring, or surface authoring.

Still unknown are ExtraTime's exact meaning, StartArea interpolation, the exact
FinishArea algorithm, RaceLine steering/route semantics beyond executable
progress/rank tracking, limit downstream reset behavior, Cameras XML linkage,
SFL meaning, most tag100
semantics, `$bsp -> tag100`, and source-node gameplay semantics. For the one
tested France1 source mesh, face-plane records in the tag100 tree correlate
with the moved physical state, but F.1 swapped the complete tag100-starting
suffix and did not isolate later tag1400 bytes at runtime. R5T-E.1 closes the
version-7 `moMesh` triangle-to-position binding; it does not infer gameplay
meaning from names such as `COLLIDE_finishline`, `_raceline`, `$boinds`, or
`$bsp`.

## G0 RaceTest authoring v0

`CourseRaceLogicAuthoring` exposes semantic setters rather than generic XML
mutation. Export changes only allowlisted values after resolving each target
against the canonical `CourseRaceLogic` projection. Ambiguous or unsupported
records remain readable and are refused for authoring. The Blender add-on edits
helper world positions and supported SplitTime properties, then calls this core
transaction to write a new XML copy and a `.mr-race-edit.json` manifest. It
does not alter a source archive or any compiled course resource.

G0 runtime authoring passed for StartArea, FinishArea, and SplitTime0 center;
combined StartArea + FinishArea editing loaded normally. G0 is **PASS —
RUNTIME AUTHORING CONFIRMED**. Runtime hashes were not included with the human
result. G0.1 is **PASS — BLENDER/CORPUS VALIDATED** and additionally allows
exact visual-companion Row3 XYZ positions and adds a translation-only
checkpoint group. Those newly editable visual-companion fields have
corpus/Blender validation but no separate human runtime authoring test.

The SplitTime viewport keeps the main trigger center and 3D Radius sphere
visually simple. Procedural sign cards and direction rays sit at each
`SplitTimeN-i` visual companion and follow that companion's own imported
matrix. They are editor-only diagnostics, not new gameplay semantics or writer
fields. The generic visualization helpers are intended for future read-only
RaceLine, Camera, and limit-marker views.

The curated Retail validation passes no-op export for 36/36 principal course
projects. StartArea authoring is supported in 36/36; FinishArea in 34/36; 110
main SplitTime records and 440/440 visual companions are structurally
supported. ItalyS4 and TurkeyS1 have five FinishArea markers, so those two
lists are preserved and shown read-only rather than truncated to four. See
[`docs/course-race-logic-authoring.md`](course-race-logic-authoring.md),
[`research/g0/findings.md`](../research/g0/findings.md), and
[`research/g0/runtime-results.md`](../research/g0/runtime-results.md).
