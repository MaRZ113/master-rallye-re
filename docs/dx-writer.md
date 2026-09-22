# Experimental DX position writer

Phase R3 adds a deliberately narrow writer for Master Rallye **vehicle** DX
resources. It is:

- **EXPERIMENTAL**;
- **POSITIONS ONLY**;
- **SAME TOPOLOGY**;
- **TEMPLATE PRESERVING**.

It is not a general serializer. The exact original DX bytes remain the
authoritative template.

## Canonical operation

`src/master_rallye/dx_writer.py` reparses the supplied template with the
canonical vehicle parser. The parser supplies:

- position buffer offset: `VertexData.position_offset`;
- vertex count: `len(VertexData.positions)`;
- position stride: 12 bytes;
- buffer end: `position_buffer_end`.

The writer never searches for float sequences. For source vertex `i`, the only
authorized output span is:

```text
position_offset + i * 12 .. position_offset + i * 12 + 12
```

Candidate XYZ values are finite little-endian IEEE-754 float32. If their
encoded 12 bytes equal the template record, the original bytes are retained
verbatim. This preserves exact float bits, including signed zero. A zero-edit
operation is therefore required to match the complete input byte-for-byte and
by SHA-256.

## Safety gates

`patch_dx_positions()` requires the original vertex count and, in safe mode,
every new point to remain inside the original position AABB. Bounds are not
rewritten. It then:

1. patches only changed position records in a copy of the template;
2. audits every changed byte against the authorized spans;
3. reparses the complete result;
4. compares local/global indices, draws, tags, groups, texture strings,
   normals, colors, UVs, trailing bytes, diagnostics, and validation status;
5. verifies hashes for every non-position section.

Any unexpected difference raises `DxWriteError`. Existing diagnostics such as
the known declared/root-count warnings must remain exactly the same; the writer
may not introduce a new warning.

`write_dx_positions()` additionally requires the import-time source SHA-256,
checks source byte size at the Blender layer, and refuses to overwrite the
source path.

## Blender workflow

The add-on exposes:

**File > Export > Master Rallye DX — Positions Only (Experimental)**

Export is allowed only for an imported Master Rallye mesh with:

- unchanged vertex and face counts;
- a complete 1:1 `mr_source_vertex` mapping;
- valid source triangle, draw, and group attributes;
- unchanged topology/draw-membership provenance fingerprint;
- an unchanged source template SHA-256;
- identity object transforms;
- positions inside the original AABB.

The supported authoring states are:

- `SOURCE_IDENTICAL`;
- `POSITIONS_ONLY_CHANGED`;
- `UNSUPPORTED_TOPOLOGY_CHANGED`;
- `INVALID_PROVENANCE`.

Only the first two are exportable. Object transforms must not be used as a
substitute for Edit Mode vertex edits in R3.

## Unsupported

The writer does not change normals, colors, UVs, indices, topology, draw
records, group hierarchy, texture/material strings, trailing data, or bounds.
It does not install output into the game. Runtime acceptance remains a human
test gate for every capability outside the confirmed scope below.

## Runtime validation milestone

**FIRST CONFIRMED WRITABLE MASTER RALLYE VEHICLE GEOMETRY**

- Date: **2026-09-22**
- Scope: same-topology vertex-position edits
- `complete.dx`: confirmed in the presentation/menu context
- `car.dx`: confirmed during an actual race
- Game load, model load, and visible edit: **PASS**
- New visual artifacts: none observed

The correctly modified `car.dx` retained collision, normal damage/deformation,
and glass breakage in the tested race. This confirms that the template writer's
positions-only output is accepted by the original game runtime. It does not
confirm topology-changing, UV, normal, or material writing.

## Runtime-confirmed repack method

The tested archive workflow was: unpack `Data.sma`, modify the intended
resource, pack the unpacked tree as a normal ZIP archive with 7-Zip, rename the
archive from `.zip` to `.sma`, and launch the game. The original runtime
accepted that repacked archive. This records only the tested procedure; no
additional ZIP implementation or option requirements are inferred.

## Preliminary vehicle-resource roles

Controlled runtime use and swaps support these preliminary roles:

- `complete.dx`: presentation/menu vehicle resource;
- `car.dx`: race vehicle body/chassis resource;
- `wheel.dx`: wheel geometry instantiated separately by the race runtime.

Using `car.dx` in the menu role omitted normal embedded wheels and exposed
driver/co-driver geometry. Using `complete.dx` in the race role produced its
embedded wheels plus separately instantiated `wheel.dx` wheels, a lifted or
incorrect placement, and loss of normal collision/damage behavior.

This does **not** prove that collision data is stored inside `car.dx`. The
supported conclusion is that the race runtime expects the structure/role
represented by `car.dx` for normal vehicle collision/damage behavior, and that
substituting `complete.dx` is incompatible with that pipeline. The exact
dependency remains unresolved and is reserved for R4A.
