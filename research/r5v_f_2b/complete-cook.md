# Complete model cook gate

## Required runtime evidence

The first runtime gate is one new loose file:

```text
research-output/r5v_f_2b/runtime-cook/DataGx/Vehicles/Mercedes/complete.dx
```

Before launch, the same directory must contain `complete.gxm` and no `complete.dx`.
Capture retail debug output showing the complete resource request, cache miss,
`Reading GXM`, `Making dx model`, `Saved cached model`, and `Loaded cached model`.
The file's creation time and hash must be recorded after exit. This excludes a
cache hit or a packaged old model as the cause of success.

The isolated retail archive index has no `DataGx/Vehicles/Mercedes/` members,
and no legacy Mercedes DX was copied into the loose runtime folder. The
complete model can therefore only come from a new loose cook or a runtime
failure. The source GXM and all its root historical DXT files are present.

## Validation before Practice

Do not launch Practice before this new file passes the following checks:

- DX header identifies the retail target revision 135.
- The modern DX parser accepts geometry, bounds, draw/material records, and
  footer.
- All numeric geometry and bounds are finite; material texture references
  resolve to the staged DXT set.
- Semantic counts and AABB are compared with the legacy `complete.dx` rev127
  from the selected demo source. Explain every material or geometry difference.

No runtime output exists yet. The game step is intentionally stopped after
this complete-only gate so the offline validation can run before car/wheel
loading.
