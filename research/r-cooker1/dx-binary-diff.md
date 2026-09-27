# R-COOKER1 DX Binary and Structural Differential

All three pairs are sourced from byte-identical GXM copies, verified against the authoritative 9.3.1 Trooper files. Evidence for each output and section comparison is **CONFIRMED_BY_BYTES**. See `dx-binary-diff.json` for full changed ranges and per-draw triangle-order maps.

## Output and byte comparison

| Resource | Rev 131 size / SHA256 | Rev 135 size / SHA256 | Length delta | Same-offset Hamming bytes | Common prefix / suffix |
|---|---|---|---:|---:|---:|
| `car` | 124,568 / `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` | 124,854 / `c2f44f09e116dad7d9ad16d026b13109c1631360151e4aa2be5b62a333ebcc40` | +286 | 32,686 | 4 / 28,335 bytes |
| `complete` | 134,349 / `27b429e271fc7afb3b71f45bf14c197c779473b087227dbf468fd48ad97a911f` | 134,609 / `85c3f74ca062acb994bd23722dfe1c774845d3db33a85cc5aadd7ab3f3fa242e` | +260 | 16,589 | 4 / 28,619 bytes |
| `wheel` | 12,924 / `9e7da7b3ea525fb5f29b61be763894ae98cd54fd0430c1b46b9f64d76e48d0ed` | 12,989 / `236853cb1d8f1cf068f3639b90e8b372fdab1b9c3b40b3d8793bc959931e7b5c` | +65 | 2,512 | 4 / 3,144 bytes |

The same-offset Hamming count includes unchanged suffix data shifted by draw-record growth. It is not the semantic changed-byte total. The normalized accounting aligns each parsed section and each draw record. In JSON, `explained_edit_bytes` is the edit-model count (revision-byte substitution + changed local-index bytes + changed overlapping legacy-prefix bytes + newly inserted prefix bytes); it is not the count of distinct byte values. Exact local-index old/new values, prefix bytes, and old/new record offsets are retained in the JSON.

## Geometry

| Resource | Positions | Normals | Colors | UV | Triangles | Draw/material mapping | Classification |
|---|---|---|---|---|---:|---|---|
| `car` | byte-identical | byte-identical | byte-identical | byte-identical | 1,911 | 22 per-draw mappings; winding preserved; texture suffixes identical | EQUIVALENT_AFTER_REMAP |
| `complete` | byte-identical | byte-identical | byte-identical | byte-identical | 2,375 | 20 per-draw mappings; winding preserved; texture suffixes identical | EQUIVALENT_AFTER_REMAP |
| `wheel` | byte-identical | byte-identical | byte-identical | byte-identical | 252 | 5 per-draw mappings; winding preserved; texture suffixes identical | EQUIVALENT_AFTER_REMAP |

The per-draw map proves every oriented triangle tuple occurs with the same multiplicity in each version for these resources; triangle order changes within each draw. The 16-bit local-index values differ substantially, while the stored trailing uint32 index block is byte-identical after relocation. No vertex permutation is needed because all vertex attribute arrays are byte-identical in source order. The current parser's local/global index reconstruction diagnostics are retained in the JSON and prevent assigning stronger semantics to that trailing block.

## Aligned byte accounting

| Resource | Changed local-index bytes | Legacy-prefix substitutions | Added per-draw bytes | Explained aligned edit bytes | Entire content accounted |
|---|---:|---:|---:|---:|---|
| `car` | 6,367 | 131 | 286 | 6,785 | yes |
| `complete` | 7,413 | 119 | 260 | 7,793 | yes |
| `wheel` | 675 | 25 | 65 | 766 | yes |

For all three files, the only pre-draw header byte change is the low byte of the revision word at offset `0x04` (`131` → `135`). Positions, normals, colors, UV count/data and local-index count remain byte-identical. The 9.10.0 draw section grows by exactly 13 bytes per record. In each mapped record, the shared first 20 bytes match; the legacy 11-byte opaque prefix and the rev135 24-byte parsed prefix are recorded separately, followed by a byte-identical texture-reference suffix. The stored trailing index block and the complete collision/trailer bytes match after relocation by draw growth. Thus the section-aligned edit model accounts for every content change; raw-offset differences after the draw area are shifts, not altered bytes. This byte model does not establish where the new prefix values originate.

## Collision, bounds, and marker 1339

| Resource | Tags | Collision result | Marker 1339 |
|---|---|---|---|
| `car` | [101] | tag101 SHA256 c6a6c6723611845d62e14115666a76c10d51f3ffefc883337f584afdc99a6bcb; Rep A [8, 12]; Rep B [28, 52] | byte-identical after relocation |
| `complete` | [102] | tag102 SHA256 ce6b85b7a24a7210b5d27bf77e6a4b906918443c49a598b11f97b755e46ec686; values [0.4000000059604645, 0.20000000298023224] | byte-identical after relocation |
| `wheel` | [102] | tag102 SHA256 ce6b85b7a24a7210b5d27bf77e6a4b906918443c49a598b11f97b755e46ec686; values [0.4000000059604645, 0.20000000298023224] | byte-identical after relocation |

No tag100 is present. `car` tag101 raw bytes, `complete`/`wheel` tag102 raw bytes, marker-1339 and the remaining parsed/opaque tail all match exactly after relocation. The collision sections are copied unchanged in the observed pairs; this does not establish whether the cooker universally copies them.

## Parser boundary

The existing rev135 reader parses 9.10.0 draw records but reports local-to-global index reconstruction errors for these three demo outputs. The separate demo reader safely parses the shared geometry/index sections and preserves raw draw bytes. The cross-generation triangle comparison uses the unchanged first 20 bytes of corresponding draw records plus each parsed rev135 draw range, and requires exact oriented-triangle multiset agreement; texture-reference equality is evaluated separately. The topology checks pass for all 47 records.

The machine report records parser diagnostics rather than suppressing them. It also retains all unknown legacy draw-prefix bytes unchanged as evidence; no semantics are assigned to them.
