# `.dxb` format notes (R0)

Status: **LOW**.

All 113 files begin with:

```text
01 F0 00 00  7D 00 00 00
```

Interpreted as little-endian words, these are `0x0000F001` and `125`.
This shared prefix is **CONFIRMED**; its semantic meaning is **UNKNOWN**.

The third `uint32` varies. Frequent values include 1 (60 files), 4 (17 files),
and font-like values 93/94/96. In `arial_12.dxb` it is 94, followed by paired
integer-looking glyph metrics/codes. In `dummy.dxb`, length-prefixed ASCII
`dummy_000_000` occurs at `0x50`. These observations support a compiled
2D/font/sprite-batch resource hypothesis at **LOW** confidence.

No field is yet labeled as a definitive entry count, glyph code, offset, or
texture binding. The corresponding `.hnt` dependency lists should be used in a
future differential experiment before any parser is implemented.
