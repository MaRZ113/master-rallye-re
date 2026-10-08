# Authored detail directive contract

`CONFIRMED_BY_BOTH`: `38fac0` dispatches PSM tag `103` to `394900`, which
allocates a `0xa4` spatial proxy and calls `2d5100`. The proxy loader reads its
own material-string table after the spatial cells. These short strings are the
actual detail inputs; shader-bearing strings elsewhere in the visual tree are
not used as a substitute for them.

The original parser searches the material string for the first case-sensitive
`$detail` substring (`2d7114 → 213b70`), then the first `)` from that position
(`2d7148`). It extracts start through closing parenthesis inclusive
(`2d71a4/2d71a8` pass start/length in `t0/t1` to `1539a0`). Failed search or
missing/preceding close uses `$detail(none)` at `483cc0`. The interner then
folds ASCII capitals to lowercase and `/` to `\`. The initial search itself
does not fold case. This is substring extraction followed by interning, not a
full property grammar or an enum lookup.

Parser output is an interned integer stored in the proxy's detail vector at
`+0x98`; `2d5ba4` obtains its element storage. Separate material/surface-type
vectors are at `+0x80/+0x8c`. `357628` reads the detail vector using the material
index in a source-cell reference. Comparisons add one to both interner IDs,
preserving sentinel handling. Numeric IDs depend on interner lifetime/order;
the diagnostic reports symbolic categories and does not invent stable IDs.

| Authored token | Canonical anchor | Parser/result | Placement consumer | Grade |
|---|---|---|---|---|
| `$detail(grass)` | `486140` | Interned token, proxy +98 | Owner +102c comparison; pool **1** | CONFIRMED_BY_BOTH |
| `$detail(shrubs)` | `486150` | Interned token, proxy +98 | Owner +1030 comparison; pool **0** | CONFIRMED_BY_BOTH |
| `$detail(stones)` | `486160` | Interned token, proxy +98 | Owner +1034 exists; no eligible pool in 357628 | CONFIRMED_BY_BOTH |
| `$detail(none)` | `486170`, default `483cc0` | Explicit or missing-token default | Owner +1038 exists; no eligible pool | CONFIRMED_BY_BOTH |
| `$detail(shrub)` | Turkey_S1 material 11 bytes | Distinct interned token, no plural conversion | Neither grass nor shrubs comparison matches | CONFIRMED_BY_BOTH |
| `$grass(off)` | Seven CDELTA1 landscape byte occurrences | Not extracted by this parser | No override branch in traced detail consumer | CONFIRMED_BY_BOTH for bounded absence; other semantics UNKNOWN |

All six starting anchors, including `particles/bush1` at `486180` and
`particles/grass1` at `486190`, were read directly in the canonical ELF. Owner
construction independently interns these names; adjacency does not establish
pool order. Ghidra's original reference manager returned no useful anchor xrefs;
raw `LUI`/`ADDIU` references and consumer loads provide the evidence.

The focused spelling controls preserve original behavior:

- `$detail(GRASS)` resolves grass after interning.
- `$DETAIL(grass)` is not found by the case-sensitive search; default none.
- `$detail(shrub) $detail(shrubs)` uses the first token and remains unrecognized.
- `$detailExtra(grass)` is extracted but does not match a known detail ID.
- `$detail(grass) $grass(off)` has no grass-off override in this consumer.
- A spatial material need not have `$surfacetype(...)`: Spain2 includes a
  `$detail(none)`-only record. The target decoder preserves it.

`$grass` has no ASCII token occurrence in the canonical executable, and the
selected spatial material tables do not carry `$grass(off)`. This is evidence
against a direct textual override **in the recovered path**. It does not prove
that cooker flags or other visual-material code ignore the authored directive.
No precedence beyond this path is asserted. Visual material/cooker semantics
remain an explicit open question, not silently normalized behavior.
