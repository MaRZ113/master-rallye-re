# R5T-SDK1 Course SDK foundation

## Result

R5T-SDK1 establishes a read-only semantic layer over the existing course
readers and integrates it with the existing Master Rallye Blender add-on. This
is a foundation, not a complete Course SDK v1. No course writer, custom layout,
or executable patch was added.

`CourseProject` composes available revision-135 render DX, RaceTest XML, HNT
dependencies, SFL structure, and optional TXT/GXM prefix data. Package
discovery uses explicit paths and exact relationships: a unique course-folder
DX fallback, exact selected-model stems for TXT/GXM, and resolved HNT `Model`
paths to link the DX with its HNT and the HNT stem with RaceTest XML/SFL.
Ambiguities remain unselected and reported.

The public course render view uses neutral `CourseTag100Region` fields. The
trailing tag100 physical meaning and `$bsp -> tag100` remain **UNKNOWN**. No
physical interpretation was added.

## RaceTest model and Blender

The SDK projects StartArea, FinishArea, and split-time records while retaining
their raw XML provenance. StartArea and FinishArea semantics retain their
runtime evidence. France1 SplitTime0's Egg Row3 is the yellow sign position and
gameplay sphere center; Radius is the 3D sphere threshold. ExtraTime remains
**UNKNOWN**. `SplitTimeN-0..3` companions remain separate visual objects.

This supersedes the early D.0 interpretation that the main SplitTime Egg Row3
only moved the visual sign. R5T-D.1 established the Row3-to-center relation by
debugger captures and a moved-on-road runtime edit. The runtime owner type for
pointer `P` remains unknown; SplitTime1/2 were not independently relocated.
The earlier StartArea probe's negative appearance is explained by one-shot
activation of all four cars during startup.

The existing Blender add-on now builds its RaceTest helpers from
`CourseRaceLogic`: ordered StartArea/FinishArea points and outlines, procedural
split signs, read-only 3D trigger spheres, and separate checkpoint companions.
Course DX importing, material previews, DXT resolution, and coordinate
conversion continue through the existing add-on and shared readers.

## Corpus and validation

The Retail corpus validation is in
[`retail-corpus-validation.md`](retail-corpus-validation.md), with machine
counts and unresolved HNT references in
[`retail-corpus-validation.json`](retail-corpus-validation.json). It confirms
36/36 course projects with validated render DX, parsed TXT, HNT, linked
RaceTest XML, and structural SFL, using the curated
`corpora/retail/Data.sma_unpacked` baseline. Of 2,843 HNT references, 2,842
resolve exactly and one remains unresolved; none are ambiguous. All 41 XML
files in that curated RaceTest folder parse: 36 HNT-matched course files and
five other RaceTest files. Runtime-probe edits in the repository-parent live
unpack are excluded because its France1 DX/XML differ from the curated
baseline.

The full synthetic suite passed **158 tests**; Python compile checks pass.
Blender 5.2.2 headless validation passed for Italy1 and France1 geometry, Retail France1
RaceTest helpers, and the packaged add-on ZIP. Blender used an isolated
`.research-output` user profile; the installed user add-on was not changed.

## Boundaries

- No course writing or export path is present.
- No EXE patching or broad route/recovery analysis was started.
- `ExtraTime`, SFL meaning, tag100 physical meaning, and `$bsp -> tag100` remain
  unknown.
- GXM triangle-corner/index-bank binding remains the deferred R5T-E topology
  question. It was not started in this phase.
