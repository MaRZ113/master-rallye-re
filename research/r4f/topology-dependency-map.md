# R4F topology dependency map

Scope: the 78 protected original vehicle DX resources; source grammar is `src/master_rallye/dx.py`. The writer must reject any resource that fails these structural invariants. Classifications are for a topology-changing rebuild that retains the same draw hierarchy and material/texture identities.

| Serialized field / region | Classification | Evidence and action |
|---|---|---|
| Header magic, words at 0x04 and 0x08 | MUST_PRESERVE | All corpus values are `D00D`, 135, 1337; neither word is a render count/offset. Copy first 12 bytes. |
| Header vertex count at 0x0c | MUST_UPDATE | Controls every vertex array length and all downstream offsets. |
| Position and normal float32 XYZ arrays | MUST_REBUILD | One record per compiled vertex, 12 bytes each; preserve exact source bytes for unchanged source values. |
| Raw four-byte vertex colors | MUST_REBUILD | One record per compiled vertex. |
| UV-set count | MUST_PRESERVE | Existing supported set count remains fixed; no new UV set creation. |
| Every UV float32 pair array | MUST_REBUILD | One pair per compiled vertex per existing set. |
| Local index count and uint16 array | MUST_REBUILD | Draw-local triangle corners, 3 indices per triangle. |
| Draw-table preamble and top-level record count | MUST_PRESERVE | Always preamble 1 in 78/78; draw hierarchy is fixed. |
| Draw tags 2/7/8 and tag-7 label/control words; tag-8 control words | MUST_PRESERVE | Existing child count stays fixed; no new draws/groups. No proven render vertex/index span in these group controls. |
| Draw core `vertex_base` (+0x04) | MUST_UPDATE | Corpus ranges are contiguous/disjoint in 78/78; later bases shift when prior draw gains/removes vertices. |
| Draw core `local_vertex_max` (+0x08) | MUST_UPDATE | Inclusive local maximum is draw vertex count minus one. Empty draw is not representable in this grammar; reject removal of its last vertex/triangle. |
| Draw core `index_start` (+0x0c) | MUST_UPDATE | Consecutive local-index spans; later starts shift after triangle edits. |
| Draw core `index_count` (+0x10) | MUST_UPDATE | Three times triangle count. |
| Draw core +0x14, +0x18, +0x1c, +0x20 flags, +0x24 feature mask | MUST_PRESERVE | Not proven topology counts; +0x14 is 1 in 1476 draws and has an IceCream exception. Preserve bytes, not interpreted values. |
| Draw texture-slot count, strings, terminals | MUST_PRESERVE | Draw identities/material bindings unchanged. Copy original record bytes and patch only four topology fields. |
| Global index table preamble | MUST_PRESERVE | Always 1 in corpus. |
| Global index count and uint32 array | MUST_REBUILD | Every triangle must equal `(local[1]+base, local[0]+base, local[2]+base)`; count equals local count. |
| Tag-101/tag-102 collision payloads | MUST_PRESERVE | They are counted internally and do not contain proven file-absolute offsets or render-index references; copy suffix bytes exactly and verify hashes. Runtime damage behavior remains a human test gate. |
| Marker-1339 44-byte bounds footer | MUST_PRESERVE for in-bounds edits | Present in 78/78 after collision. Min/max equals union of render/collision vertices and center equals midpoint in 78/78. The other scalar is not proven, so no bounds writer is authorized. Reject generated positions outside the original footer bounds; preserve the entire footer exactly. |
| Unparsed or optional trailing bytes | MUST_PRESERVE | Only accepted if parser proves the 44-byte footer and known tag-101/102 structure; exact suffix hash must match. Unknown suffix families block rebuild. |
| Absolute file offsets into render core | MAY_PRESERVE (absent in supported grammar) | No serialized offset field appears in the parsed header/draw/global/collision/footer schemas. The only offset values above are parser-computed positions, not wire pointers. Reject new grammar or ambiguous tail rather than shifting unknown offsets. |

Every declared local vertex is referenced by at least one triangle in 1,478/1,478 source draws; the writer preserves this invariant and rejects orphan compiled vertices.

The topology-dependent binary window starts at byte **0x0c** (vertex count) and ends at the end of the stored global-index table, immediately before the collision/footer suffix. The first 12 header bytes and the complete suffix are byte-preserved. Within the rebuilt window, original draw record bytes are copied, with exactly four core fields patched per draw. The writer validates the entire output after reparse and refuses non-finite generated floats, index/count overflow, unknown trailing grammar, or out-of-bounds geometry.

This map resolves all fields plausibly indexing/counting the rebuilt render core for the observed vehicle grammar. It does not claim course support, new draw/material creation, collision topology, or runtime behavior of damage after topology edits.
