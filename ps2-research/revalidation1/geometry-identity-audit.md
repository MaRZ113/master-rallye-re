# France1 `bush01` geometry and live identity

## Source geometry correspondence

| Fact | PS2 source | PC compiled source |
|---|---|---|
| Resource | `\\TNG\\DATAPSM\\COURSE\\FRANCE1\\FRANCE1.PSM` | `DataGx/Course/France1/france1.dx` |
| File hash | `d0b9845218ddd1ff4f12b3b16e77eff43aa182ac73992b5cbea8d81be04f935d` | `a6bfcef97684f41154596f91fdfaa9522a8fdf6b65d181f4d1ac327b9caf07d5` |
| Material owner | node offset `3,509,209`; material offset `3,509,264` | draw 54; `course.batch.1.21`; core `3,261,170` |
| Source topology | 24 visual faces | 48 records, 24 unique unsigned faces |
| Vertex/index provenance | PSM authored strip | vertex base 4,299; index start 9,792; index count 144 |
| Texture/material | `bush01-tga`, shader `treeblend` | `bush01-tga`, shader `tree` |

All 24 PS2 source faces have strict source-coordinate matches to the 24
unique PC unsigned faces. The PC's 48 records contain the studied surfaces in
both orientations. The original tolerance profile is `0.001` source units.
This proves a strong compiled-source geometry correspondence; it does not
prove identical runtime vertex buffers, D3D8 submission identity, visibility,
or draw ordering.

The PC course has other `bush01-tga` groups, so texture matching is
non-unique. The current implementation's live classifier is based on
geometry/content ownership plus current resource generations and exact
geometry digest, not a historical draw ordinal or texture-only key. The
reported live D3D8 identity is not independently revalidated here because the
raw trace is missing.

## Runtime observation carried forward

The user reports that the selected target was observed in
`DrawIndexedPrimitive(4,11940,28,22944,48)`; it appeared at ordinal 46 of 704
in one frame, and many later draws wrote depth. Those ordinals and arguments
are historical observations, not durable classifier keys. Without the raw
trace and its provenance, this audit cannot independently check resource
generation, course ownership, device/reset generation, HRESULT, or the full
state transition sequence.
