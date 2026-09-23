# Collision hull writer (Phase R4C)

R4C provides a deliberately narrow writer for an **existing, validated vehicle
tag-101 convex hull**. It supports exact zero-edit serialization and one rigid
translation. It is not a general collision editor.

## Safety model

```text
original DX template
  -> parse exact tag101 boundary
  -> validate the normal vehicle hull relationships
  -> translate only proven positional GeometryBlock vertices
  -> serialize the unchanged topology in original order
  -> replace the same-size tag101 byte range
  -> audit every changed byte
  -> reparse the complete DX and verify preserved structures
```

The writer never searches for byte signatures or uses vehicle-specific
offsets. It refuses resources without tag 101, validation-failed hulls,
non-finite/unrepresentable deltas, unexpected geometry relationships, size
changes, source overwrites, and any diff outside authorized vertex records.

## Supported operations

- `serialize_tag101(hull)`: canonical serialization of every confirmed nested
  count, geometry, index/reference list, descriptor, adjacency pair, loop, and
  scalar, retaining collection order.
- `replace_dx_tag101(template, payload)`: same-size replacement of exactly the
  existing tag-101 range.
- `translate_tag101(hull, dx, dy, dz)`: translate the five proven positional
  GeometryBlock vertex arrays.
- `patch_dx_collision_translation(template, delta)`: full-DX fail-closed
  translation and reparse audit.
- `write_dx_collision_translation(...)`: path-level wrapper requiring the
  expected source SHA-256 and a different output path.

## Translation semantics

The translated fields are:

```text
base_geometry.vertices
representation_a.geometry_a.vertices
representation_a.geometry_b.vertices
representation_b.geometry_a.vertices
representation_b.geometry_b.vertices
```

The two `geometry_b` points are not guessed directions: in all 27 finite hulls
each equals the arithmetic mean of its representation's `geometry_a` vertices
within `5.93e-8`. The base point similarly equals representation A's mean.

Counts, triangle indices, references, edges, descriptors, adjacency, face
loops, `base_scalar`, and face scalars remain byte-identical. Radius, pairwise
distances, face areas, and topology are validated after float32 translation.

## Corpus guarantee

- 28/28 structurally parsed tag-101 sections serialize byte-identically,
  including the validation-failed Forklift static outlier.
- 28/28 complete DX templates remain byte-identical after zero-edit
  replacement.
- 27/27 validated finite hulls pass an in-memory translation, full-DX reparse,
  invariant checks, and exact non-tag101 preservation.
- Forklift translation is refused; its non-finite coordinates are not hidden or
  normalized.

## Runtime candidate boundary

The ignored R4C package translates only Astero `car.dx` collision geometry by
`(+0.40, 0, 0)` source units. Source X is the evidenced lateral vehicle axis;
the visual mesh remains byte-identical. Runtime status is **CONFIRMED_BY_RUNTIME** per the project owner's 2026-09-23 report. Detailed observations were not supplied with this update.

## Unsupported

No scale, rotation, individual vertex editing, topology changes, adjacency
generation, new hull construction, BSP/tag-100 writing, cylinder/tag-102
writing, visual-mesh changes, or automatic installation is implemented.
