# Executable audit

## PS2 ELF: preserved evidence and REA boundary

The canonical ELF identity is recorded in [target compatibility](target-compatibility.md).
REA refused this exact R5900 ELF through its configured Windows providers, so
this audit does **not** claim a fresh REA disassembly, decompilation, procedure
boundary, or R5900 semantic review. Existing TREEBLEND1 files preserve the
prior ELF-derived function inventory and bounded instruction evidence at
original VAs. Those remain historical executable evidence, not new REA output.

The existing material path records the following original ELF anchors:

| Role | VA |
|---|---:|
| `$shader` token extraction / material resolution path | `0x00390d98`, `0x00391690` |
| `tree` registration / handler | `0x003a75b8` / `0x003ae710` |
| `treeblend` registration / handler | `0x003a7468` / `0x003ae618` |
| queue drain used for bucket order | `0x0031cd98` |

The addresses and roles above are copied from the prior phase's
`elf-functions.json` and reports. They were not re-imported or re-decoded by
REA in this pass. `render-contract.json` identifies the same canonical ELF
hash and marks live VU residency/runtime validation unknown/not performed.

To add an independent raw-byte check without overstating the decoder result,
`verify_ps2_evidence.py` parsed the current ELF32 little-endian header and its
single `PT_LOAD`, then compared every `original_word` and data anchor in the
frozen TREEBLEND1 `instruction-evidence.json` against the mapped file bytes.
All stored words/anchors matched with zero mismatches. The compact counts,
segment mapping and per-window hashes are in
`ps2-elf-byte-recheck.json`. This only proves that the previously recorded
words correspond to the canonical ELF; it does not independently decode
R5900 branch delay, MMI, COP2/VU semantics or the GS state meaning.

## Original PC PE: independent REA results

REA decompiled `FUN_00580360` (body `0x00580360..0x0058077c`, 1,053 bytes;
evidence `ev_0c95ffe030d9264eff8d73a8b6746e7b15fe4097285062e535d8fe70f99a8f99`).
It reads runtime material fields `+0x22` and `+0x23`; these select no suffix,
`_alpha`, or `_alphatest`, then resolve a `shader/` name. This independently
supports the original PC material selector description.

REA decompiled registration `FUN_00565DA0` (body
`0x00565da0..0x005660c0`, 801 bytes; evidence
`ev_caaf2a23caba01fff90e3055e2079ab6348bf2a02a5c9d7219ae91b05a896de6`). It
registers `shader/base`, `base_alpha`, and `base_alphatest` with flag pairs
`(0,0)`, `(1,0)`, and `(0,1)` and a shared factory. Earlier REA evidence
`ev_a9bcf1bc3aab5aebf859757139dcc389aab89c8c24c0716421c0cef7e35830ba`
shows that factory writes its supplied values to object fields `+0x24/+0x25`.
Do not conflate those output fields with selector inputs `+0x22/+0x23`.

REA confirmed the code-writer/cache wrapper `FUN_0053F8B0`
(`0x0053f8b0..0x0053f92d`, 126 bytes; evidence
`ev_b693ad787852bb22af6d7f97c6e3d5ce3b5a4a78f1427866d0970f1903680b6a`)
and the adjacent state wrapper `FUN_0053F930`
(`0x0053f930..0x0053f9d5`, 165 bytes; evidence
`ev_377eda43611c0e8d75acedb80c261497ee1182a384936d75b233a4da86b6ea50`).
The first updates cached state and writes through a device vtable slot mapped
by the prior PC callmap to `SetRenderState`.

## Handler address `0x005867a0`

REA mapped `0x005867a0` to file offset `1,599,392`
(`ev_df218c6f8132e05eee768029a367f537ec02c20e018e1d6c0c1806260ff8c26f`),
but its Ghidra listing had no defined procedure or decodable instruction
there. Therefore this audit does **not** claim a Ghidra/REA function boundary
or decompilation at that VA.

The immutable PE bytes at that VA were independently decoded in this turn by
GNU objdump from the exact hash above. The branch on object flags corresponds
to the prior original-PC alpha/alphatest state map: the alpha branch disables
depth writes and alpha test, enables blending and selects `SRCALPHA` /
`INVSRCALPHA`; the alphatest branch enables `GREATER` with reference 128,
disables blending and permits depth writes. This corroborates instructions
from original bytes through a second decoder, but it is still static evidence
and not a live France1 course-handler capture. The old PC evidence is
therefore more specific than a “REA decompiled this handler” claim would be.

Short original instruction probe (VA bytes from the verified PE; state/value
arguments are passed to the cached state wrapper at `0x0053f8b0`):

```text
005867b8  8a 47 24       mov al,[edi+0x24]
005867bb  84 c0          test al,al
005867bd  74 45          je   0x00586804
005867c2  6a 00 6a 0e    push value 0; state 14 (ZWRITEENABLE)
005867c6  e8 e5 90 fb ff call 0x0053f8b0
005867d3  53 6a 07       push value 1; state 7 (ZENABLE)
005867d6  e8 d5 90 fb ff call 0x0053f8b0
005867de  53 6a 1b       push value 1; state 27 (ALPHABLENDENABLE)
005867e1  e8 ca 90 fb ff call 0x0053f8b0
0058680c  53 6a 0e       push value 1; state 14 (ZWRITEENABLE)
0058680f  e8 9c 90 fb ff call 0x0053f8b0
0058680c  ...            alternate branch continues with ZENABLE=1, blend=0
00586843  8a 47 25       mov al,[edi+0x25]
00586846  84 c0          test al,al
00586848  74 32          je   0x0058687c
0058684a  8b 4e 10       load device state cache
0058684d  53 6a 0f       push value 1; state 15 (ALPHATESTENABLE)
00586850  e8 5b 90 fb ff call 0x0053f8b0
00586858  6a 05 6a 19    push GREATER (5); state 25 (ALPHAFUNC)
0058685c  e8 4f 90 fb ff call 0x0053f8b0
00586864  68 80 00 00 00 push reference 128
00586869  6a 18          push state 24 (ALPHAREF)
0058686b  e8 40 90 fb ff call 0x0053f8b0
```

The displayed `push` pairs summarize the cdecl arguments visible in the
surrounding instructions. They are a compact interpretation aid; the exact
raw bytes remain in the original hash-identified PE and are not included as a
binary dump. State IDs use the established D3D8 enum mapping. This probe is
not a proof that all of these writes are the final values at a live draw.

## Exact PC material names

REA's defined-string search returned `alphatest` and related base-family
names. A bounded search for `tree` returned only UI-related matches, which is
not proof that all possible tree-related strings or runtime paths are absent.
