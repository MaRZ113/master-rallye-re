# GXM structural prefix (R-DEMO)

`src/master_rallye/gxm.py` parses the 32-byte header in all 109 demo GXM files and a material/geometry prefix in 80 files. The remaining 29 are `demo-8.4.1` variants with a different prefix; their post-header bytes are deliberately opaque.

The header consists of eight little-endian u32 words. The first word's low byte is `02` in this corpus; its other bytes vary. In all 109 files, `word_0x10 == 3 * word_0x18`. The meanings below are restricted to the 80-file material-table variant. See `research/r-demo/gxm-header.md` and `gxm-header-corpus.json` for exact offsets and bounds.

1. At offset 32, `word_0x0c` material records. Each has a u16-length ASCII name, a u8 slot count, then for each slot three raw control bytes and a u16-length ASCII reference. All 1,263 records parsed without resynchronization.
2. `word_0x10` float3 vectors in array A. All vectors are finite and unit length within `1e-4`; normals are a **HIGH_CONFIDENCE_INFERENCE**.
3. `word_0x14` finite float3 vectors in array B (empty in one frontend file), followed by 12 `FF` bytes. Their exact role is **UNKNOWN**.
4. `word_0x18` records, each ten u32 words. A 12-byte `FF` separator follows every record except the last. The first word is a material index or `FFFFFFFF`; the three index triples address B, C, and A respectively. The B triple may be all `FFFFFFFF`. All 102,636 records satisfy these bounds and separators. Triangle interpretation is **HIGH_CONFIDENCE_INFERENCE**.
5. `word_0x1c` finite float3 vectors in array C. In Trooper, many C vectors match paired demo DX positions after `(x, y, z) -> (x, z, -y)` and rounding to four decimals; this supports coordinate semantics but does not prove all source-to-compiled transforms.
6. The remaining hierarchy/object bytes are preserved opaque. No general GXM writer or compiler is exposed.

The GXM files contain source-side names and length-prefixed directives such as `$paint`, `$glass`, `$perspex`, `$chull(Trooper)`, and `$cylinder_0.766_0.39`. The `$chull(Jump)` source geometry has a float-precision numerical correspondence with retail tag101 (see `research/r-demo/collision-source-map.md`). The 9.3.1 same-build regenerated tag101 now maps numerically to source `$chull(Trooper)`, while the isolated hull position edit crashed both demos. Exact compiler dependencies and other directive effects remain **UNKNOWN**; see `research/r-demo2/gxm-to-tag101.md`. `research/r-demo/gxm-directives.json` retains corpus identity and byte offsets.

For Trooper, same-build TXT sidecars exactly match GXM material counts, record spans, and ordered suffix names. They identify crew nodes in `car`, four wheel/hub groups in `complete`, and the final `$chull(Trooper)` source mesh. See `research/r-demo/gxm-hierarchy.md`. The binary hierarchy control fields remain opaque.


First-pass human testing confirms that one identified Vector C position edit changes Trooper body geometry in demo 8.4.1 (**CONFIRMED_BY_RUNTIME**). Trooper `car.gxm`, `complete.gxm` and `wheel.gxm` are required for the tested race body, presentation model and visual wheels respectively. This does not establish DX file access or `$chull`-only collision semantics. See `research/r-demo/runtime/gxm-live-loading.md` and `chull-test.md`.
