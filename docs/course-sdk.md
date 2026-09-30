# Read-only Course SDK foundation

R5T-SDK1 composes the existing format readers into a typed, read-only course
model. It is a foundation for inspection and Blender visualization, not a
complete authoring SDK. No XML, DX, GXM, RaceLine, SFL, surface, or course writer
is provided.

## Public entry point

The Python package exports `CourseProject`, the race-logic and render model
types, and the existing `parse_course_dx`, `parse_course_xml`, `parse_hnt`, and
`parse_sfl` readers. To discover exact-stem resources from a directory or a
given course resource path:

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
- `source_txt` and `source_gxm`: existing parsed hierarchy and bounded GXM
  prefix probe, without assigning source directive semantics.
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
It creates source-ordered StartArea and FinishArea point/outline collections,
the procedural split sign, a separate three-ring wire sphere for each complete
split, and a `Visual Checkpoint Objects` collection for associated sibling
Eggs. Center and radius use the established course-to-Blender transform and
scale. The sphere stores ID, radius, source XML paths, semantic-rule evidence,
record-evidence metadata, raw ExtraTime, and `ExtraTime` semantic status. No
gameplay data is edited.

RaceLine remains an ordered marker list. The executable-supported direction is
split center to nearest RaceLine sample/percentage; no marker is relabeled as a
special trigger center. The add-on package version is 4.5.1 and retains its
Blender 4.3 minimum.

## Read-only boundary and open questions

Supported reads include revision-135 course render geometry, RaceTest
hierarchy and the proven StartArea/FinishArea/SplitTime interpretations, HNT
dependencies, structural SFL data, TXT hierarchy, GXM prefix metadata, and
opaque tag100 metadata. The read model does not support course writing,
physical/collision authoring, arbitrary layouts, full RaceLine or AI semantics,
surface authoring, or named GXM topology binding.

Still unknown are ExtraTime's exact meaning, StartArea interpolation, the exact
FinishArea algorithm, broad RaceLine semantics, SFL meaning, tag100 meaning,
`$bsp -> tag100`, and the GXM triangle-corner/index-bank binding. The next
research blocker is the source triangle-corner/index bank and proof that
`moMesh` triangle spans bind to the source float3 pool. That work is deferred to
R5T-E and is not part of this SDK foundation.
