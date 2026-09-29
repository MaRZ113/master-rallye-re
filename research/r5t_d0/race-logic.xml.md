# RaceTest XML read model

## Parser structure

The canonical `master_rallye.course_xml` parser now retains a complete ordered
`CourseXmlNode` tree with each element's tag, attributes, text, and child nodes.
Typed projections preserve the old flat Marker list for existing callers while
adding:

- `CourseXmlMarkerList`: list name/order/path and ordered Marker records.
- `CourseXmlMarker`: parent list, index in list, No, Type, Pos, Dir, raw
  values, parsed vectors, XML path, and parse issues.
- `CourseXmlEgg`: parent Egg list, source index/order, name, model, all matrix
  properties, AI slots, and XML path.
- `CourseXmlMatrix`: raw matrix attributes and parsed Row0–Row3 values; Row3
  XYZ is exposed as a candidate position without interpreting matrix behavior.
- `CourseXmlAiObject` / `CourseXmlAiComponent`: AI No/name, direct AI values,
  component tag/values, unknown attributes, and source path.

Unknown XML tags and values remain present in the generic tree. Missing or
malformed optional vectors/matrix rows are retained as issues instead of
silently discarded. XML records keep the ancestry needed to distinguish an Egg
AI component from a Marker record.

## Retail France1 hierarchy

France1's XML root is `Scene`, with top-level `EggLists_Version4` followed by
`MarkerLists`. Its marker lists are Cameras, RaceLine, StartArea, FinishArea,
LeftInnerLimit, LeftOuterLimit, RightInnerLimit, and RightOuterLimit. There are
1,080 Markers total. The `SplitTimes` Egg list contains StartSplitTime,
SplitTime0 with four sibling Eggs, SplitTime1 with four, and SplitTime2 with
four. The `gaRaceSplitTimeAI` component occurs on the three main SplitTime
Eggs, not on the four same-prefix sibling Eggs.

The JSON report contains all source-ordered markers and the exact matrix/AI
data for the split visual and sibling Eggs. Nearest marker lists are ranked by
3D distance and separately by XZ distance; threshold counts are 5, 10, 20, 40,
80, and 150 source units. Distance is a search aid, not proof of a runtime
reference.

## Retail corpus scan

All 41 Retail `DataScene/RaceTest/*.xml` files parse with no errors. StartArea
is present in 41, FinishArea in 40, and `gaRaceSplitTimeAI` in 38. Component
record counts are 0:3, 3:35, and 4:3; split visual Egg counts are 0:4, 3:35,
and 4:2. `Multi.xml` contains four split AI records without split visual Eggs,
so the two counts are not conflated. Turkey3 and TurkeyS2Flip have a fourth
split Egg with repeated IDs and remain corpus outliers. The corpus has 117
Radius and 113 ExtraTime values; the observed ranges are 7–30 and 42.5–120.
These ranges do not assign gameplay meaning to ExtraTime or identify a
universal split count.

See `france1-race-logic.md` for geometry and the user-provided runtime
evidence, and `split-trigger-localization.md` for the candidate spatial test.
