# `.dx` vehicle format notes (through Phase R3)

Status: **HIGH** for the vehicle geometry/draw grammar. The corpus result covers
all 78 files under `DataGx/Vehicles`; it does not claim compatibility with
course DX resources.

All values below are little-endian. The reusable implementation is
`src/master_rallye/dx.py`; structured models and diagnostics are in
`src/master_rallye/model.py`.

## Leading geometry layout

| Offset | Representation | Interpretation | Confidence |
|---:|---|---|---|
| `0x00` | `uint32 0xD00D` | format magic | **CONFIRMED** |
| `0x04` | `uint32 135` | constant, meaning unknown | value **CONFIRMED**, meaning **UNKNOWN** |
| `0x08` | `uint32 1337` | constant, meaning unknown | value **CONFIRMED**, meaning **UNKNOWN** |
| `0x0C` | `uint32 N` | vertex count | **HIGH** |
| `0x10` | `N * 3 * float32` | XYZ positions | **HIGH** |
| next | `N * 3 * float32` | XYZ normals | **HIGH** |
| next | `N * 4 bytes` | color-like per-vertex values | representation **HIGH** |
| next | `uint32 U` | UV-set count | **HIGH** |
| next | `U * N * 2 * float32` | UV pairs | **HIGH** |
| next | `uint32 I` | local index count | **HIGH** |
| next | `I * uint16` | draw-local triangle indices | **HIGH** |

Every extent is checked before unpacking. Counts have explicit safety limits;
malformed data raises a section-specific structured error.

## Draw-table envelope and stopping rule

Immediately after local indices are two words:

| Relative offset | Type | Interpretation | Confidence |
|---:|---|---|---|
| `+0x00` | `uint32`, observed `1` | preamble/control, meaning unknown | value **CONFIRMED** |
| `+0x04` | `uint32 R` | declared top-level/root-related count | representation **CONFIRMED**, exact semantics **MEDIUM** |
| `+0x08` | variable | physical record stream | **HIGH** |

R0.5 treated `R` as a universal recursive parse bound. Corpus evidence refines
that rule: physical records are read sequentially until the following global
index envelope `(uint32 1, uint32 I)` is reached. Type-7 hierarchy is then
reconstructed from child counts. In 67 files `R` equals reconstructed root
count; in 11 car resources it is one smaller. Those 11 still have complete,
disjoint draw coverage and exact stored-global agreement, so the mismatch is a
diagnostic rather than a parse failure.

## Draw core (tag 2)

Offsets are relative to the 40-byte core. Type-7/8 records add prefixes before
the same core fields.

| Core offset | Width/type | Proposed meaning | Evidence | Confidence |
|---:|---|---|---|---|
| `+0x00` | `uint32` | core tag (`2`) | all 78 vehicle files | value **CONFIRMED** |
| `+0x04` | `uint32` | vertex base | exact global reconstruction | **HIGH** |
| `+0x08` | `uint32` | maximum local vertex, inclusive | all observed local indices fit | **HIGH** |
| `+0x0C` | `uint32` | index start in local buffer | exact range reconstruction | **HIGH** |
| `+0x10` | `uint32` | index count | exact range reconstruction | **HIGH** |
| `+0x14` | `uint32` | `unknown_0x14` | raw value preserved | **UNKNOWN** |
| `+0x18` | `uint32` | `unknown_0x18` | raw value preserved | **UNKNOWN** |
| `+0x1C` | `float32` | unknown scalar | raw value preserved | **UNKNOWN** |
| `+0x20` | 4 bytes | flags/control bytes | raw value preserved | **UNKNOWN** |
| `+0x24` | `uint32` | `unknown_0x24` | raw value preserved | **UNKNOWN** |
| `+0x28` | `uint32 T` | texture-slot count | parseable ordered strings and sidecar matches | **HIGH** |
| next | repeated | `uint32 length` + bytes | texture resource stem | **HIGH** |
| final | `uint32` | observed terminator/control | boundary **HIGH**, semantics **UNKNOWN** |

Astero wheel draw 0 begins at `0x24F8`: base 0, inclusive local maximum 53,
index start 0, index count 216, then slots `asterowheel64-tga`, `rubber-tga`,
and `Null`. The five records consume the table exactly and account for all 252
triangles.

## Tags 7 and 8

Tag 7 has a length-prefixed label, five preserved `uint32` control words, an
embedded draw core, and zero or more direct child records. Corpus comparison
shows that the **fifth** control word is the direct child count. The older R0.5
word-3 inference was accidental: those two values happened to agree in the
four-file sample. Boundaries and fifth-word child count are **HIGH** across 25
vehicle files; other controls remain **UNKNOWN**.

Tag 8 has two preserved `uint32` prefix words followed by a draw core. It occurs
as a child form in the same 25 files. Type-7 labels such as `screenfront` match
sidecar source-node names, but the runtime semantics of the prefix controls are
not claimed.

The parser exposes both the flat physical draw sequence and reconstructed group
hierarchy. Unknown tags stop parsing with offset, tag, context bytes, and known
neighbor information; none appeared in the vehicle corpus.

## Local-to-global addressing and winding

For each stored local triangle `(a, b, c)` in a draw:

```text
stored_global_triangle = (b + vertex_base,
                          a + vertex_base,
                          c + vertex_base)
```

The global table has this envelope:

| Relative field | Type | Interpretation | Confidence |
|---|---|---|---|
| preamble | `uint32`, observed `1` | control, meaning unknown | value **CONFIRMED** |
| count | `uint32` | global index count | **HIGH** |
| indices | `count * uint32` | stored global triangle indices | **HIGH** |

The formula exactly matches all stored indices in all 78 vehicle resources.
For the R0.5 sample it covers 14,844 indices: Astero wheel 756, Astero complete
7,269, Bruno wheel 756, and Astero car 6,063. Geometric face normals using this
order agree with averaged stored vertex normals for 119,454 corpus triangles,
oppose for 98, and are near zero for 425, supporting this winding for glTF.

A global table may be absent at clean EOF in the reusable grammar; that case is
parsed but cannot earn the stored-table validation. A truncated envelope/table
is an error.

## Coverage diagnostics are not grammar

Across this particular corpus, draw index ranges and vertex ranges are complete
and disjoint in all 78 files. The library reports uncovered/overlapping indices
and unused/shared vertices, but does not reject an otherwise safe model merely
because ranges do not partition the full vertex buffer. Synthetic tests cover
unused and shared/overlapping vertex ranges.

## Sidecars and material matching

DX parsing never requires TXT. Where present, matching uses normalized ordered
texture tuples; shorter sidecar tuples are padded with `Null` to the binary
width. A draw may therefore have zero, one, or several material candidates.
No material-index field has been identified. Binary texture slots are retained
as the authoritative binding evidence.

The corpus has 132 ambiguous matches and 63 unmatched draws. Six resources lack
a sidecar. No non-`Null` texture reference is missing from its vehicle asset
directory. The preview exporter selects the first non-`Null` slot only and
preserves every original slot/candidate in glTF extras and `metadata.json`.

## Trailing sections

The bytes after the global index table are represented neutrally as
`TrailingSection`.

A recognized 56-byte family contains:

| Footer offset | Type | Interpretation | Confidence |
|---:|---|---|---|
| `+0x00` | `uint32` | unknown | **UNKNOWN** |
| `+0x04` | `float32` | unknown | **UNKNOWN** |
| `+0x08` | `float32` | unknown | **UNKNOWN** |
| `+0x0C` | `uint32` | unknown | **UNKNOWN** |
| `+0x10` | `3 * float32` | observed bounding-box midpoint | **HIGH** |
| `+0x1C` | `float32` | unknown | **UNKNOWN** |
| `+0x20` | `3 * float32` | position bounding-box minimum | **HIGH** |
| `+0x2C` | `3 * float32` | position bounding-box maximum | **HIGH** |

It occurs in 49 resources: 24 `complete` and all 25 `wheel` files. Opaque tails
occur in all 26 `car` files, two `complete` files, and one `sus` file. Sizes
range from 44 to 6,600 bytes. Opaque content is preserved, hashed in reports,
and makes a resource `PARTIALLY_ACCOUNTED`, not failed.

## Astero car sidecar discrepancy

Binary draws cover 2,021 triangles while `car.txt` spans 2,089. The sidecar
`$chull(Astero)` node starts at 1,937 and has size 68; the binary `screenfront`
group begins at 1,937 while its sidecar span begins at 2,005. Removing only
that source span aligns every later screen/brake-light span. This supports
omission of the source hull from this render DX at **HIGH** confidence; no
claim is made about collision use.

## Still unresolved

Header constants, draw flags/control meanings, runtime multi-texture semantics,
opaque trailing families, and course variants remain unresolved. No executable
analysis was used.

## R2.5 sidecar discovery and writer evidence

Sidecar lookup is no longer limited to `<dx-stem>.txt`. Every same-directory
TXT is parsed and scored from normalized ordered texture-tuple matches,
unique/ambiguous/unmatched draws, mesh-span compatibility, and weak filename
hints. Exact-stem matching receives a small preference but cannot defeat
substantially stronger structural evidence. Equal top scores remain ambiguous.
The 78-file vehicle scan selected 78 unique best-evidence candidates, including
12 non-exact names; all candidates and scores remain metadata.

TXT texture entries preserve nullable `HasAlpha`, `UsesAlpha`, and `IsNoise`.
These are sidecar fields, not inferred renderer flags, and `HasAlpha` remains
distinct from `UsesAlpha`.

Legacy same-topology v1 evidence supports a future byte-preserving template
patcher: Astero complete reproduced byte-identically in positions-only,
no-bounds mode, and a one-vertex edit changed only one position byte while the
modern parser still validated. This does **not** constitute a production DX
writer. Legacy v3 is **CONTRADICTED**: its output had invalid local ranges and
6,285 reconstructed/stored global-index mismatches.

## R3 template-preserving position writer

The vehicle parser now exposes the exact position buffer as
`position_offset`, `vertex_count`, and a 12-byte stride. The writer derives
all patch locations from those parsed values; it performs no byte-pattern or
float-sequence search.

The complete 78-file vehicle corpus passed:

- 78/78 byte-identical zero-edit round trips;
- 78/78 safe temporary single-position edits;
- zero unexpected changed bytes;
- exact preservation of known draw/index/material/trailing structures and
  pre-existing diagnostics after reparse.

This evidence is **HIGH** for template-preserving same-topology position
replacement in the known vehicle corpus. It does not establish a general DX
serialization grammar or game-runtime acceptance. Bounds are not rewritten;
safe mode requires the candidate inside the original AABB and rejects any edit
that changes parser diagnostics.
