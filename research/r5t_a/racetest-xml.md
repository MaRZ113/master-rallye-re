# RaceTest XML inventory (R5T-A)

The report records XML tree shape and source attribute values. Names and values are retained as corpus evidence; gameplay semantics are not inferred.

| Build | RaceTest XML files | Exact course-folder matches | Root |
|---|---:|---:|---|
| Demo 8.4.1 | 11 | 2 | `{'Scene': 11}` |
| Demo 9.3.1 | 2 | 2 | `{'Scene': 2}` |
| Demo 9.10.0 | 33 | 2 | `{'Scene': 33}` |
| Retail | 41 | 36 | `{'Scene': 41}` |

## Repeating structure

- Most common element names across the scanned RaceTest XML: `[('Value', 338020), ('Marker', 61956), ('AI', 22184), ('AI_List', 5546), ('Egg', 5546), ('List', 1569), ('gaRacePaceNoteAI', 1472), ('gaBootAICar', 704), ('enAiSoundSource', 444), ('gaRaceSplitTimeAI', 253), ('gaLimitBuilderAI', 204), ('gaAiCloudSetUp', 174), ('gaCameraManagerAI', 162), ('MarkerLists', 87), ('Scene', 87), ('aiShadowBoot', 87)]`.
- Most common attribute names: `[('Name', 345135), ('Type', 338020), ('Value', 326928), ('No', 84140), ('Row0', 11092), ('Row1', 11092), ('Row2', 11092), ('Row3', 11092), ('SaveOptions', 41), ('SavePlayerState', 41)]`.
- For each XML, JSON preserves root attributes, all element/attribute counts, exact-stem resource-like attributes, literal track/course identifier attributes, and bounded samples of transform rows and position-like values.
- Developer/test-name XML matches: 41; these are separately listed in JSON and remain inventory-only.

## France1 / Italy1 and variants

See per-file structures in `racetest-xml.json`; course names are paired to `DataGx/Course` by exact case-insensitive normalized stem.
