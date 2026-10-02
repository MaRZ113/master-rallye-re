# Mercedes model output validation

## Inputs

The selected `Copy of Mercedes` `complete.dx`, `car.dx`, and `wheel.dx` are all
revision 127. Their source hashes and sizes are locked in
[mercedes-source-manifest.json](mercedes-source-manifest.json). The current
retail DX parser rejects the old source draw layout; the supported project
upgrader starts at revision 131 and explicitly rejects revision 127. No
converter was extended in this phase.

## Retail-cooked outputs

**None produced.** For every role, these checks are therefore pending:

- retail parser accepts output and reports revision 135;
- supported read/round-trip validation succeeds;
- expected draw/material records, bounds, hierarchy, and valid footer;
- every model texture reference resolves;
- comparison to the revision-127 reference covers vertex/triangle/draw counts,
  materials, texture names, bounds, wheel geometry, and major hierarchy roles.

No structural differences are classified because there is no output to compare.
Do not infer successful cooking from the static writer's `0x87` constant.
