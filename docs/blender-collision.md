# Blender collision-hull visualization

Phase R4B adds an optional, read-only visualization of parsed vehicle tag-101
collision data. It is an inspection aid, not a collision editor or writer.

## Import option

Enable **Show collision hulls** in either vehicle DX import operator. When a
valid tag-101 section exists, the add-on creates a child collection named
`Master Rallye Collision - <resource>` containing:

- a sphere empty for the parsed base centre/radius;
- representation A `geometry_a` as an orange wire mesh;
- representation B `geometry_a` as a blue wire mesh.

Resources without tag 101 import normally and get no collision collection.
Validation-failed collision data, such as the Forklift non-finite outlier, is
retained in source metadata but is not sent to Blender mesh construction.

## Coordinate alignment

Helpers use the same shared transform as render geometry:

```text
source (X, Y, Z) -> Blender (X, -Z, Y)
```

There is no collision-only scale, origin adjustment, or guessed transform.
Headless tests compare every generated A/B vertex and base-sphere centre/radius
against this transform exactly.

## Read-only boundary

Collision objects are wire-display, hidden from renders, and non-selectable by
default. They carry `mr_collision_read_only`, owner, role, offsets, and compact
JSON metadata. They deliberately do not carry the render object's
`mr_metadata_json`, so the R3 positions-only export operator cannot mistake a
helper for an authoring mesh.

Show/hide controls in the Master Rallye panel alter viewport visibility only.
Editing or exporting collision geometry is not supported.

## Validation

Blender 5.2.2 LTS passed synthetic tag-101/tag-102 import, ZIP installation,
save/reload, and R3 writer regression. Read-only real-resource folder import
passed Astero, Pajero, Forester, Bruno, SeatBuggy, Ufo, and megane (22 DX
resources). No game-derived `.blend`, texture, or screenshot is stored in Git.
