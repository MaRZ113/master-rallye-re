# Route, bounds, and XML helper inventory (R5T-B)

Source `moMesh` names and spans are now confirmed between old France1/Italy1
GXM node tables and paired TXT. France1 provides `startpoint`, `_raceline`,
`$boinds`, `$ps2cells`; Italy1 provides `raceline`, `_boinds`, `_limits`,
`_bsplitX`, `$ps2cells`. `$bsp`, `$draw $landdb`, and `$nodraw` are `moUnknown`
hierarchy records; their TXT nesting and child counts are checked. Literal
names/directives are retained exactly and are not treated as runtime meanings.

The GXM object table gives spans, not source transforms or usable point arrays.
Therefore the R5T-B Blender source-helper collection remains empty. The
currently understood spatial overlay is RaceTest XML markers only.

## RaceTest XML observations

Demo 9.10.0 France1 has 583 `Marker` records and Italy1 has 277. Every record
has parseable `Marker Pos` and `Marker Dir` Vector3 values in these two files.
All France and Italy marker positions lie inside the corresponding DX vertex
AABB. The addon can import them as neutral Empty markers into a separate
`XML Markers - <course>` collection using the established Blender coordinate
conversion and preserving raw XML values.

France1 and Italy1 each contain three `gaRaceSplitTimeAI` records and one
`gaRacePostFirstSplitTimeAI`; neither contains `gaLimitBuilderAI` in the
available Demo 9.10 XML. The split IDs, radii, and extra-time values are
retained as literal XML fields. The parser does not call them checkpoints or
infer a route order. Details are in `xml-marker-correlation.json`.

No `startline`, `finishline`, or `splittime*` developer GXM assets were present
in the current `inputs/` set. Their generated-resource destination is still
unknown.
