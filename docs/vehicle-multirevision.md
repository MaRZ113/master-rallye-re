# Multi-revision vehicle DX import (R5V-D)

The Blender vehicle importer and canonical `DxModel` reader accept the observed
vehicle revisions **127, 131, and 135**. Revision dispatch comes from the DX
header. Unknown revisions and unsupported legacy record tags fail closed.
Course DX parsing is a separate path and is not changed by this work.

## Two validation decisions

`ValidationDiagnostics` now reports two separate outcomes:

- `index_sequence_equal` / `exact_generated_valid` answer whether the stored
  global index array exactly matches the parser reconstruction and the file is
  in the supported writer revision.
- `import_validated` answers whether the geometry is structurally safe to
  import. It requires valid ranges and table counts, complete disjoint draw
  coverage, valid triangles, and matching per-draw oriented triangle
  multisets.

For revision 135, topology comparison is per physical draw and treats cyclic
rotations of one oriented triangle as equivalent. It preserves winding and
triangle multiplicity; a reversed triangle or changed/duplicated triangle
fails validation. Local/global index order can therefore differ while the
resource remains safe for import. `validation_profile` is `EXACT`,
`VALID_WITH_INDEX_ORDERING_DIVERGENCE`, or `INVALID`.

The public `diagnostics.validated` compatibility property remains strict and
means `exact_generated_valid`. Every existing DX writer, authoring operation,
packager, and strict research CLI gate continues to use that profile. Blender
mesh import uses `import_validated`; it does not make a legacy file writable.

## Observed record grammars

Revision 135 retains the existing recursive tag-2/7/8 grammar. Its draw table
and global index table envelopes are checked explicitly. A declared top-level
count that differs from the reconstructed root count is retained as a warning
because 11 stock retail `car.dx` files have that known discrepancy while
otherwise validating exactly.

The supplied revision-127 and revision-131 samples use a flat tag-2 record
stream. Each record contains the common 20-byte geometry core, an 11-byte raw
render prefix, the prefix's length-delimited texture strings, and a zero
terminal. A counted global index table follows. The prefix bytes are preserved
as `raw_revision_prefix`; their render/material meanings remain unknown. This
reader is bounded and corpus-confirmed for the supplied vehicle samples; it is
not a claim about every historical DX resource or any course resource.

Legacy material flags are never interpreted using revision-135 offsets.
Blender uses conservative first-texture preview materials and marks legacy
blend semantics unknown. The ordinary UV import policy remains direct source
V. Blender-calculated display normals remain in use; no native custom-normal
setter is called.

## Blender behavior

Single-resource import and vehicle-folder import use the same revision
dispatcher. Each resource stays one editable mesh. The object stores
`mr_dx_revision`, `mr_source_filename`, `mr_resource_role`, and validation
profile metadata. Its JSON metadata is schema version 4 and includes raw
legacy prefix bytes and strict writer/import validation facts. Filename roles
are `car.dx` = RACE BODY, `complete.dx` = PRESENTATION, `wheel.dx` = WHEEL
TEMPLATE; other DX files are AUXILIARY.

The folder operator imports direct `*.dx` children. Source DX, sidecars, and
textures are read-only. The operator reports structural warnings and index
ordering divergence separately from fatal parse/validation failures.
The Blender panel identifies `STRUCTURAL IMPORT ONLY` resources and disables
DX/collision authoring controls unless the exact revision-135 writer profile
passes.

## Corpus evidence

The read-only audit in `research/r5v_d/` covers 52 supplied demo DX files and
the 78-file retail vehicle corpus: 9 revision-127, 26 revision-131, 15
revision-135 demo, and 78 retail revision-135 resources. Two additional demo
files are revision 125 and intentionally unsupported. All 93 revision-135
resources pass structural checks: 81 have exact index order and 12 demo
resources have a structurally equivalent order divergence. The retail 78/78
remain exact. See `research/r5v_d/findings.md` and its generated matrix for
per-resource provenance labels and diagnostics.
