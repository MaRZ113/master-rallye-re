# R4C canonical tag-101 writer

## Wire coverage

`src/master_rallye/collision_writer.py` mirrors the confirmed reader order:

1. tag 101;
2. base GeometryBlock;
3. base scalar;
4. representation A;
5. representation B.

Each representation writes its two GeometryBlocks, counted references, edges,
face descriptors with two independently counted lists, edge-face adjacency,
counted per-face edge loops, and face scalars. No collection is sorted and no
topology is regenerated.

## Exact round-trip

All 28 corpus tag-101 sections parse and serialize to exactly their original
bytes and SHA-256. This includes Forklift's original non-finite float bit
patterns; the serializer preserves them, while the translation API correctly
refuses that source.

All 28 same-size serialized sections can be placed back into the complete DX
template with a byte-identical whole-file result.

Evidence label: **CONFIRMED_BY_WRITER_READER** for exact serialization of the
known vehicle tag-101 grammar. This does not independently prove field
semantics.

## Full-DX translation audit

Only the existing tag-101 vertex records are authorized. The patcher verifies
the prefix and suffix byte-for-byte, hashes render positions/normals/colors,
UV/local indices, draw/global tables, and tag102/remainder ranges, then reparses
and compares all render structures. Any unexpected diff fails the operation.
