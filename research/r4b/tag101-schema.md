# R4B tag-101 schema proof

## Result

Tag 101 is a counted, nested convex-hull collision structure. The parser can
compute its end offset without a guessed fixed size, sentinel search, or
knowledge of the following tag.

```text
101
base GeometryBlock
base float
representation A
representation B
```

Each representation contains two GeometryBlocks, a counted vertex-reference
list, counted edge pairs, counted variable face descriptors, one face pair per
edge, one counted edge loop per face, and one float per face. Each face
descriptor contains **two independently counted vertex-index lists**.

The full field table, reference domains, and validation rules are maintained
in `docs/formats/dx-collision.md`.

## Boundary evidence

- Reader and writer functions serialize the same nested call sequence.
- All counts lead to valid in-range references for 27 finite vehicle hulls.
- All 28 tag-101 resources are consumed to the exact next known boundary.
- Optional tag 102 parses immediately after tag 101 where present.
- All remaining 44-byte tails begin after, rather than inside, tag 101.
- No corpus parser uses signature scanning or resynchronization.

This proves the wire boundaries at **HIGH** confidence for the vehicle corpus.
Runtime field semantics are deliberately assigned a lower confidence where
static data alone is insufficient.

## Validation policy

The standalone parser rejects truncated data, negative/unreasonable counts,
out-of-range triangle/vertex/edge/face references, and non-finite floats.
DX integration retains a structurally parseable asset with non-finite floats
as validation-failed evidence. This permits the Forklift outlier to remain in
the corpus report without treating it as a valid finite hull.

## Tag separation

Tag 100 remains raw because its length grammar is unresolved. Tag 102 is
parsed exactly as two floats after its tag, but its field meanings stay
neutral. Unknown following bytes are preserved separately.
