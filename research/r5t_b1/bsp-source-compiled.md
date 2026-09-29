# `$bsp` source to compiled DX status

## Source inventory

The paired Demo 8.4.1 France1 source table contains literal `$bsp` node
ordinal 10 with 797 descendants, including 784 `moMesh` descendants and a
summed mesh size of 47,095. Italy1 contains `$bsp` ordinal 783 with 296
descendants, including 292 mesh descendants and a summed mesh size of 32,672.
These are table/hierarchy counts, not decoded BSP faces or indices.

Retail course DX parsing reaches tag100 exactly at the bounded render-tail
boundary in all 36 resources. Tag100 is retained as opaque bytes; no tag100
internal grammar or payload length is claimed. The prior Demo 9.10 France1
unchanged-source recooks both had a 10,118,248-byte raw tag100 region with
identical SHA-256, although the render-prefix sizes and offsets varied.

## Source/compiler correlation

The Demo 9.10 cooker screenshots log `Building BSP tree` and per-object
`Generated BSP` messages while cooking France1. Those messages show a cooker
stage, not that source `$bsp` nodes serialize as DX tag100. The retail and
recook observations do not bind a particular source node or edit to tag100.
Boinds is the only complete small GXM/TXT/DX source/cooked pair currently
available, and it does not provide a controlled `$bsp` source edit in this
phase.

## R5T-B.1 conclusion

`$bsp` to tag100 remains **UNKNOWN**. No BSP source object was edited, no
compiled effect was isolated, and no physical/runtime candidate is prepared.
Next evidence should come from a small source/cooked BSP oracle or from a
future experiment after point/index stream mapping. Do not infer the internal
tag100 boundary by byte scanning.
