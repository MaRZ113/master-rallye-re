# GS alpha, depth and texture state

These are **ELF-derived templates**, not a captured GS register snapshot.
`312610` handles modes9/10/19; `311c50/312130` insert texture-dependent fields;
`31c438` transfers independently dirty first/second context templates through
`31e478/31e6a8`. `3411d0` assigns their actual GS register IDs: TEST1/2=47/48,
ALPHA1/2=42/43, TEX0_1/2=6/7, TEX1_1/2=14/15, ZBUF1/2=4e/4f.

Bit positions were independently checked against the primary
[PS2SDK GS definitions](https://ps2dev.github.io/ps2sdk/gs__gp_8h_source.html).
The selector equation and state values below are reconstructed from original
register writes; the external definitions are not evidence that a particular
game draw executes them.

| Field | Puddle primary | Puddle secondary | Water primary | Water secondary |
|---|---|---|---|---|
| Context |1|2|1|2|
| Primitive |triangle strip|triangle strip|triangle strip|triangle strip|
| IIP/TME/ABE |1/1/1|1/1/1|1/1/1|1/1/1|
| Fog bit |1|0|1|1|
| FST |0, STQ|0, STQ|0, STQ|0, STQ|
| TEX0 TFX |0 modulate|0 modulate|0 modulate|0 modulate|
| TEX0 TCC |1 RGBA|**0 RGB**|1 RGBA|1 RGBA|
| ALPHA low byte/FIX |44/0|**68/56**|44/0|44/0|
| Blend equation |(Cs-Cd)*As/128+Cd|**Cs*56/128+Cd**|(Cs-Cd)*As/128+Cd|(Cs-Cd)*As/128+Cd|
| TEST ATE |0|0|0|0|
| TEST ZTST |2 GEQUAL|2 GEQUAL|2 GEQUAL|2 GEQUAL|
| TEST ZTE |inherited|inherited|inherited|inherited|
| ZBUF ZMSK |0 writes permitted|1 writes masked|0 writes permitted|1 writes masked|

`ALPHA=44` gives A=source, B=destination, C=source alpha, D=destination.
Puddle secondary `ALPHA=0000003800000068` gives A=source, B=zero,
C=FIX, D=destination. Its alpha texture channel is neither the texture-combine
alpha input (TCC0) nor the blend coefficient (FIX56). Calling every layer
"transparent because WATERSURFACE2 has alpha" would be incorrect.

Primary TEST update is `(old & fffffffffff9c000) | 41000`; water/puddle second
context uses the same preserve mask with4040c. ATE is forced0 and ZTST2,
while ZTE/DATE/DATM are retained. AREF/ATST bits in the second value do not
enable alpha testing when ATE0. No claim is made that the depth test is enabled
merely because its comparison field is GEQUAL. The relevant inherited enable
must be checked in a live packet or complete initialization state.

Both texture templates force TEX1 low control fields through mask/or160:
LCM0, MMAG1, MMIN5, MTBA0. Maximum mip level and addresses come from actual
texture metadata; K also depends on shared mip helpers and per-strip scale.
CLAMP is set through generic mesh clamp flags, without a special water override.
FRAME and TEXA inheritance are not fully resolved here.

Waterfall/waterall use the same alpha-selector44 and TCC1 in both layers, but
set ZMSK0 for **both** contexts and TEST_or41000 for both. They therefore must
not inherit puddle's masked-secondary-depth contract in a future implementation.

Queue order is known only within `31cd98`'s grouping and state/geometry sequence.
The VU-compatible strip contract has two streams/context templates. No universal
claim that water always follows all terrain, or that a screenshot establishes
its final framebuffer ordering, is made.

`render-contract.json` preserves numeric words, fields, inheritance and evidence
boundaries for reproducible inspection. Alpha content, alpha test, blending,
depth comparison and depth writes are represented independently.
