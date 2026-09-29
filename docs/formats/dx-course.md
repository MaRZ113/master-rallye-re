# Course DX render grammar (R5T-A)

Status: **CONFIRMED_BY_CORPUS** for the parsed revision-135 course render regions. Course physical/BSP, route, and surface meanings remain **UNKNOWN**.

## Observed structure

After the shared prefix described in [`dx-common.md`](dx-common.md), the common retail envelope begins with `uint32 1`, a root-record count, and a course root record. Thirty-five retail DX files have one tag-4 root wrapper; `Italy_S2` has two direct root records. Course files can then contain repeated batches, each beginning with `(uint32 1, uint32 record_count)` followed by that many bounded draw/wrapper records.

Existing tag-2, tag-7, and tag-8 render records reuse the proven common DX draw parser. Course-only container tags 1, 4, 5, and 6 are traversed using their observed child counts and retained raw prefix bytes. Their remaining control/prefix values are not assigned semantic names. No heuristic byte scanning is used.

After the parsed render records, the existing collision-section boundary parser recognizes tag 100 in all 36 retail course DX files. The offset is the exact end of the validated render batches. The tag-100 payload boundary/length is unresolved and its bytes are not decoded or rendered as collision.

## Corpus validation

- Retail resources: 36/36 parse and pass complete, disjoint local-index and vertex-range validation.
- Parsed totals: 35,198 render draws and 2,020,603 triangles.
- Tag occurrences reached structurally after render parsing: tag 100 in 36/36; tag 101 in 0/36; tag 102 in 0/36.
- The current vehicle parser alone stops at the first course-specific tag in all 36 files; the new course interpretation is additive.
- Demo 9.10.0 France1 and Italy1 also parse with this grammar. Demo 9.3.1 is revision 131. Its root prefix resembles the later envelope, but interpreting the first tag-2 body with the revision-135 core reads `845116275` (France1) or `1936941426` (Italy1) as a texture-slot count at the 40-byte core boundary; those values come from printable texture-name bytes. This is a concrete body-grammar divergence, not a decoded 9.3.1 layout. Demo 8.4.1 is revision 127 with a different root layout. Both older grammars remain unsupported.

France1 and Italy1 details, per-resource divergence offsets, draw counts, and validation status are in [`research/r5t_a/dx-course-probe.md`](../../research/r5t_a/dx-course-probe.md) and [`research/r5t_a/tag100-inventory.md`](../../research/r5t_a/tag100-inventory.md).

This is a render read model only. It does not implement or imply a course DX writer, a BSP decoder/writer, or full accounting of bytes after tag 100.

## R5T-B cooked-source variation

The 9.10.0 runtime recooked 8.4.1 France1 source into revision 135. That output
is structurally different from native 9.10.0 France1 despite the shared DX
revision: the owner-supplied cooked file has 84,250 vertices, 74,812 triangles,
and 4,620 draws, while native 9.10.0 has 64,961 vertices, 64,569 triangles,
and 977 draws. Both parse through the same render parser. Therefore revision
135 is not by itself a complete course graph/layout signature.

Two forced France1 recooks from identical source produced different render DX
prefixes (the output hashes, vertex counts, triangle counts, and draw counts
differ). Their raw tag100 payloads were byte-identical at 10,118,248 bytes.
The render section is validated; tag100's internal length/semantics remain
unresolved. Cooker render-sort BSP generation is a separate observed pipeline
and is not identified with tag100.

## R5T-B.1 controlled source response

Three baseline and three modified Demo 9.10 France1 cooks used identical
source inputs within each cohort. The modified source changed one float32 in
the first-eight startpoint point candidate by +1.0 source X; the only
cross-cohort source input difference was `France1.gxm`. All six course DX files
passed revision-135 render validation. Their render prefixes naturally vary.
Each raw tag100 region is 10,118,248 bytes. The three baseline regions share
SHA-256 `9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7`;
the three modified regions share SHA-256
`c89654dbf502de96df366d05ecdd87051b0051e8308851550c0e0b6d37c23086`. This is
`CONFIRMED_BY_SOURCE_COMPILED_PAIR` for a deterministic tag100 response to the
single source edit. It does not identify the inner tag100 grammar, physical
collision, or gameplay semantics. The owner's no-obvious-gameplay-change
observation followed a one-corner tracer and is not a whole-volume test.
