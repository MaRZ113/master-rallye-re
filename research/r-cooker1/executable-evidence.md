# Targeted cooker executable evidence

## Executables

| Build | File | Size | SHA256 | Observed PE |
|---|---|---:|---|---|
| Demo 9.3.1 | `corpora/demo-9.3.1/MRallye.exe` | 2,637,886 | `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680` | PE32 x86 |
| Demo 9.10.0 | `corpora/demo-9.10.0/MRallye.exe` | 2,883,646 | `13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78` | PE32 x86 |

## Targeted strings found

Evidence label: **CONFIRMED_BY_BYTES** for the executable hashes, PE headers,
and literal-string locations below. No field-writer behavior is
`CONFIRMED_BY_EXECUTABLE` in this report.

ASCII string searches in the exact binaries found these relevant literals at
file offsets (not function addresses):

| Literal | Demo 9.3.1 offset | Demo 9.10.0 offset |
|---|---:|---:|
| `Making dx model` | `0x273730` | `0x2AF800` |
| `Reading GXM` | `0x27375C` | `0x2AF82C` |
| `.dx` | `0x2737B0` | `0x2AF880` |
| `.gxm` | `0x2737A8`, `0x27CCE1` | `0x2AF878`, `0x2B8BF5` |
| `Vertex welder` | `0x2747C0` | `0x2B09BC` |

## Direct code references

A bounded PE32 x86 immediate-reference scan found `push imm32` references to
the strings. The addresses below are instruction VAs, not function starts.
The adjacent calls are confirmed bytes/instructions; their semantic identities
remain candidate interpretations.

| Context | 9.3.1 xref / following sequence | 9.10.0 xref / following sequence | What this proves |
|---|---|---|---|
| `Reading GXM` | `push` at `0x51F285`; log call `0x4A7C30`; next call `0x4A7B80` at `0x51F294` | `push` at `0x552845`; log call `0x593B20`; next call `0x593A70` at `0x552854` | The literal is logged immediately before an unidentified call in the cooker path; GXM-reader identity is plausible, not proven |
| `Making dx model` | `push` at `0x51F29A`; log call `0x4A7C30`; next call `0x5BDD40` at `0x51F2AB` | `push` at `0x55285A`; log call `0x593B20`; next call `0x5EBEE0` at `0x55286B` | A named model-building stage is logged; the next routine is unidentified |
| `Vertex welder` | `push` at `0x543236`; log call `0x4A7C30`; next call `0x578014` at `0x543242` | `push` at `0x56AABD`; log call `0x593B20`; next call `0x5A67E4` at `0x56AAC9` | A vertex-welder stage is logged; the following routine is unidentified |
| `.dx` path literal | `push` at `0x51F174`, `0x51F42C` | `push` at `0x552734`, `0x5529EC` | The literal participates in path-building code at these sites |
| `.gxm` path literal | `push` at `0x51F1B8` plus additional references | `push` at `0x552778` plus additional references | The literal participates in path-building code at these sites |

These code references are **CONFIRMED_BY_EXECUTABLE**. They narrow the next
inspection to the calls adjacent to GXM/model construction and the later draw
writer; they do not identify the 131/135 writer, material serializer, revision
emission, or source of the new prefix. No function boundary or function
semantics is assigned solely from these call sites. `analyzeHeadless.bat` was
not available on PATH, and no Ghidra analysis against either exact demo EXE
hash was performed. No broad decompilation was attempted.

## Questions not answered

- Which code emits revision 131 versus 135.
- Which writer serializes the observed 11-byte legacy prefix and 24-byte
  rev135 prefix.
- Whether rev135 prefix values are copied, defaulted, or computed from GXM or
  intermediate render/material data.
- Why local-index order changes while the trailing uint32 index bytes remain
  equal, and what invariant the retail reader actually validates.
- Which reader condition makes raw rev131 DX incompatible with retail.

These are the specific remaining executable-analysis targets. The current
evidence is intentionally classified `UNKNOWN`; the results here do not
support an upgrader implementation.
