# R-COOKER1 initial findings

## Status

The controlled Trooper comparison is **CONFIRMED_BY_BYTES** for the supplied
source/output snapshots. This is a three-resource experiment, not a complete
description of every DX role or cooker revision. No 131-to-135 converter has
been implemented. Upgrader feasibility is **D — evidence insufficient**.

## Inputs and source identity

The 9.3.1 and 9.10.0 input folders contain byte-identical GXM copies for
`car`, `complete`, and `wheel`; their hashes also match the read-only Demo 9.3.1
Trooper corpus. The supplied `Black-tga.gxi` copies match as well. Exact sizes
and hashes are in [`input-manifest.json`](input-manifest.json) and the readable
[`input-manifest.md`](input-manifest.md).

The supplied 9.10.0 output grouping is paired with the GXM snapshots in
`inputs/9.10.0_dxTrooper/`. Demo 9.10.0 has no Trooper source directory in the
available corpus. No invocation log or per-run file-read trace was supplied,
so source-content identity is proven, while the actual source path read during
each cooker run is not independently traced.

## Controlled DX result

The outputs are rev131 (`9.3.1`) and rev135 (`9.10.0`). Their exact hashes,
sizes, binary changed ranges, parsed section comparisons, and draw mappings are
in [`dx-binary-diff.json`](dx-binary-diff.json). The summary is:

| Resource | Rev131 / rev135 bytes | Draws | Triangles | Explained edit-model bytes | Byte accounting |
|---|---:|---:|---:|---:|---|
| car | 124,568 / 124,854 | 22 | 1,911 | 6,785 | complete |
| complete | 134,349 / 134,609 | 20 | 2,375 | 7,793 | complete |
| wheel | 12,924 / 12,989 | 5 | 252 | 766 | complete |

Positions, normals, color bytes, UV sets, and their ordering are byte-identical
for each pair. Per-draw oriented triangle multisets also match with winding
preserved; the local 16-bit index order changes. The result is
`EQUIVALENT_AFTER_REMAP`, not byte-identical index data. No vertex remap is
needed. Every matched draw keeps the same first 20 bytes and has the same
length-prefixed texture-reference suffix.

The header revision field at offset `0x04` changes from 131 to 135. Each draw
record grows by 13 bytes: the observed legacy prefix is 11 bytes and opaque;
the rev135 prefix parsed by the current reader is 24 bytes. The exact bytes and
changed local-index values are in the machine report. Prefix fields are not
assigned unproven meanings.

For normalized accounting, every pair has identical geometry attribute
sections and local-index count, one revision byte change, recorded local-index
value changes, recorded overlapping prefix-byte substitutions, 13 additional
bytes per draw, and byte-identical post-draw index/collision/trailer sections
after relocation. The `explained_edit_bytes` values above are counts in that
edit model, not same-offset Hamming counts. All three reports set
`all_changed_content_accounted=true`.

## Material and collision observations

Each mapped draw retains its exact texture-reference byte suffix, including
slot order. This supports unchanged texture-name references for these pairs;
it does not prove that every material state is unchanged. The changing draw
prefix may contain material or renderer state, but its legacy semantics remain
unknown. See [`material-131-vs-135.md`](material-131-vs-135.md).

`car` contains tag101; its raw payload is identical after draw relocation
(5,296 bytes; Rep A 8 vertices/12 triangles; Rep B 28 vertices/52 triangles).
`complete` and `wheel` each contain tag102 with identical 12-byte payloads
(`0.40000000596`, `0.20000000298`). No tag100 occurs in these three files.
Marker-1339 and the remaining 44-byte trailer are identical after relocation.
This establishes output identity, not whether the cooker copied or recomputed
these values.

The only paired DXT supplied is `black-tga.dxt`. Both are 1,044 bytes and
byte-identical (SHA256
`c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82`). The
20-byte header, 16×16 dimensions, CRC32, and 1,024-byte pixel payload all
match. Its GXI source snapshots also match.

## Parser and runtime boundary

The project's current retail-layout DX parser cannot parse the rev131 draw
prefix as a reasonable texture-slot count: it reads 1,752,392,036 for `car`
and `complete`, and 1,701,144,695 for `wheel`. The rev135 files parse their
draw records, but the parser reports local/global index reconstruction errors
(5,552 car, 6,730 complete, 675 wheel positions). Those diagnostics are
retained in the JSON. They show a limitation or mismatch in the current
parser's interpretation of that index relationship; they are not evidence
that the game rejects rev135.

Prior project/runtime evidence says 9.10.0-generated vehicle DX is
retail-compatible and raw 9.3.1 output is not directly retail-compatible;
see the [R-BRIDGE2 result](../r-bridge/r-bridge2-demo-910-bridge.md).
This experiment localizes visible byte deltas to revision and draw/index
serialization while preserving geometry attributes, texture-reference
suffixes, and collision/trailer bytes. It does not yet prove the retail
reader's exact failure gate.

## Reconstruction readiness

| Component | Status | Basis |
|---|---|---|
| Source GXM/GXI identity | `CONFIRMED_BY_BYTES` | Equal supplied source hashes; no per-run read trace |
| Render vertex attributes | `IMPLEMENTABLE_NOW` | Exact output bytes and ordering match |
| Per-draw triangle topology | `IMPLEMENTABLE_WITH_CONSERVATIVE_POLICY` | All 47 oriented triangle multisets match; retain explicit order maps |
| Header revision field | `IMPLEMENTABLE_NOW` | 131 → 135 at offset `0x04` in these files |
| Shared draw core | `IMPLEMENTABLE_NOW` | First 20 bytes equal per mapped draw |
| Draw prefix conversion | `NEEDS_MORE_ORACLE_DATA` | 11 opaque legacy bytes versus 24 parsed rev135 bytes |
| Texture-reference suffix | `IMPLEMENTABLE_NOW` | Exact bytes per matched draw |
| Trailing index block semantics | `UNRESOLVED` | Bytes persist, current reconstructed relation fails |
| Collision and marker data | `NEEDS_MORE_ORACLE_DATA` | Output bytes equal after relocation; copy versus recompute unknown |
| Full 131 → 135 serialization | `NEEDS_MORE_ORACLE_DATA` | New prefix generation and reader contract not known |

The next narrow step is targeted writer/reader analysis for the draw-prefix and
index-table changes in the two cooker executables, or one additional same-source
asset pair if that is needed to distinguish constants from source-derived
values. Do not build a production upgrader until the rev135 prefix and index
semantics are understood and validated against more than this one vehicle.

No cooker was rerun during this phase. The fresh supplied outputs are the
comparison inputs; no repeatable safe cooker invocation or invocation log was
available to establish same-build determinism independently.

## Artifacts

- [`input-manifest.md`](input-manifest.md) / [`input-manifest.json`](input-manifest.json)
- [`dx-binary-diff.md`](dx-binary-diff.md) / [`dx-binary-diff.json`](dx-binary-diff.json)
- [`draw-131-vs-135.md`](draw-131-vs-135.md)
- [`material-131-vs-135.md`](material-131-vs-135.md)
- [`minimal-delta.md`](minimal-delta.md)
- [`executable-evidence.md`](executable-evidence.md)
