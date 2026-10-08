# Detail-specific drawing contract

The renderer path is the original CPU→DMA/VIF1→VU1 route. A final GIF/GS
instance capture is absent. The following steps are `CONFIRMED_BY_EXE` and
are bounded to this two-pool detail producer.

| Stage | Exact producer / operation |
|---|---|
| Select mode | 3581e8 supplies mode **11** to concrete virtual 312610 |
| Bind category image | Cached handle → virtual 311c50 → TEX0/TEX1/MIPTBP templates |
| Snapshot state | 31c8f8, first-context helper 31e478 |
| State transfer | DMA CNT `0x1000000b`, STCYCL `01000404`, V4_32 UNPACK `6c0b8000` of eleven quadwords from `42dec0`, MSCAL `1400037c` |
| Input records | 3597e0 emits 64-byte point/size/color records, at most 30 accepted per group |
| Record transfer | 31da60 emits DMA REF `30000000 | (count*4)`, STCYCL `01000404`, V4_32 UNPACK `6c008000 | (count<<18)` |
| Primitive entry | MSCAL `14000449`, VU1 pc **449**; matching embedded code at ELF4443e8 |
| Fix addresses | 31dce8 replaces record-start index with `(recordBuffer & 0fffffff)+index*64` |
| Completed packet | 3581e8 finishes packet and rotates context handles |
| Submit | 32ff28→359610: identity world state (3432b8), commit31c228, virtual317120 |
| Queue into frame | 317120→31e010: DMA CALL `50000000` to packet chain physical address, zero VIF words |

VIF interpretation is checked against primary
[PS2SDK VIF encodings](https://ps2dev.github.io/ps2sdk/vif__codes_8h_source.html).
UNPACK is four vectors per point, TOPS-relative base `0x8000`; a 30-point group
transfers 120 quadwords. It is not a 120-vertex CPU quad mesh.

## Encoded drawing state

This is a checked **template contract**, not a screenshot-derived blend claim
or a live GS-register dump. `3411d0` assigns original register IDs:
`42dee8=47 (TEST1)`, `42def8=08 (CLAMP1)`, `42df08=42 (ALPHA1)`,
`42df28=06 (TEX0_1)`, `42df38=14 (TEX1_1)`, `42df68=4e (ZBUF1)`.
Original stores at `341248..341288` independently establish ownership.
Their identification and bit fields use primary
[PS2SDK GS definitions](https://ps2dev.github.io/ps2sdk/gs__gp_8h_source.html).

The actual mode-11 switch entry is **312dc8**, read from canonical table
`4850c0[11]`. Original instructions branch at `313004` to shared tail
`315a00`; interpreting that tail as an independent function would be wrong.
Its original mask/OR chain agrees with the decompiled mode-11 values:

| Template | Mode-11 value / fields | Meaning |
|---|---|---|
| GIF PRIM in 42dec0 | Lower seven PRIM bits **0x56**; higher bits inherited | Sprite, texture enabled, alpha blend enabled, fog off; initial first-template ST/Q/context0, effective inherited flags need capture |
| TEST1 42dee0 | `old & fffffffffff9c000 | 41000` | Alpha test **disabled** (ATE0), depth test enabled, ZTST2/GEQUAL; destination-alpha fields inherited |
| ALPHA1 42df00 | Low selector byte44, fixed factor byte cleared | `(Cs-Cd)*As + Cd`; relevant source-alpha selector present |
| ZBUF1 42df60 | Bit32 set | Depth writes masked; buffer address/format inherited |
| TEX0_1 42df20 | TCC bit34 set; bound image fields from311c50 | Texture color+alpha participates; exact live VRAM/format unobserved |
| TEX1_1 42df30 | Mode bits then texture-cache values | Filtering/LOD values can be overwritten by bind; no universal fixed filter claim |
| CLAMP1 42def0 | 3582f0..35835c sets low value5, clears selected other fields | Both axes clamp in this detail snapshot; this is **not TEST1** |

Stored image alpha, alpha test and blend are distinct facts: the GXIs have
alpha content; the detail template enables blending and disables alpha testing.
CPU fade supplies an additional alpha input. Effective live GS parity remains
a separate proof gate even though matching embedded state/GIF code is decoded.

## Embedded MPG state, sprite and output programs

Canonical `.vudata` is ALLOC|WRITE, VA442170/file343170, size2680. Its DMA RET
header is60000267. Five MPG chunks upload pcs000/100/200/300/400, with counts
256/256/256/256/201; command/source addresses and hashes are in
[vu-contract.json](vu-contract.json). CPU MSCAL addresses and input format match
these embedded programs. **STATIC_INFERENCE** is the linkage grade: the CPU
upload call and live VU residency of this exact stream were not established.
The explicit442170 Ghidra xref was only an ELF-section-header reference;
searched CPU address-construction leads did not resolve the upload.

Under that conditional linkage, pc37c (ELF443d78) obtains TOPS, caches input
qword7/TEX1 at VU data318, loads input qword0 into `vf31` (sprite GIF prototype),
reads the AD-tag count from qword1, and copies that tag and its state quadwords
into the output buffer. pc449 uses the same `vf31`, expands each record into
the two corners/STQ/RGBA specified in [primitive-geometry.md](primitive-geometry.md),
then writes NLOOP=2*count.

Common allocator pc3c9..3db (ELF443fe0..444070) checks a **194-quadword** output
half. If the next request exceeds space and prior data exists, it sets EOP on
the prior GIF tag, toggles ring offset0/194, and executes **XGKICK at pc3d7,
ELF444050**. Output bases are VU data636 and830. pc0d is an E-bit return, not
XGKICK; pc4c3 branches there with 11-bit micro-PC wrap. A point batch can be
buffered until a subsequent allocation/flush. Shared force-budget entry pc3a1
exists; its final frame caller and the actual final flush of a captured detail
batch remain unproved. `31ddd8` only changes a DMA tag to RET.

The embedded program supplies geometry/GIF, state-copy and XGKICK contracts
without closing the upload/last-flush execution link. No final frame hardware
DMA start/completion or actual texture VRAM handle was captured. Conditional
static linkage must not become runtime evidence.

Integration proves that completed detail packets enter the frame drawing
queue; it does not prove precise ordering against every terrain pass or actual
visible counts. Only grass then shrubs traversal within the detail builder is
established. Treeblend, water, HUD and unrelated renderer modes were not reversed.
