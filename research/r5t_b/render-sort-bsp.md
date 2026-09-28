# Render-sort BSP and course DX tag100 (R5T-B)

The cooker screenshots show render-sort generation messages: `Inserting
moSortPlane nodes`, `Building BSP tree`, `Generating BSP draw planes`, and
per-object `Generated BSP` summaries with opaque/transparent/plane counts. The
same logs include candidate-triangle and bad-plane-choice errors. This is
evidence for a cooker/render ordering structure.

The course DX parser reaches a separate tag100 region after its validated
render batches. Its payload boundary is still unresolved; bytes are kept raw.
Across two forced France1 9.10 cooks, tag100 was 10,118,248 bytes with the same
SHA-256 (`9a3ea510…ef5a7d7`) even though render vertex/draw counts and the tag100
file offset changed. The owner-cooked France1 output from the earlier run has
the same raw payload hash. Native 9.10 and retail France1 have different
tag100 hashes and lengths.

This supports keeping the two BSP-related systems separate. It does not prove
the cooker log's sort tree is absent from all compiled bytes, nor that source
`$bsp` creates tag100. No controlled `$bsp` geometry change was possible with
the current GXM geometry grammar. The next discriminating experiment is a
small developer track with one isolated `$bsp` object and a one-object source
change, followed by all-output structural comparison.
