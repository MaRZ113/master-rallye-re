# Bounded root17 material decision

Original canonical `SLES_509.06` hash was verified again. Rabbitizer with explicit
`InstrCategory.R5900` checked original mapped words in
`default-material-evidence.json`; no generic MIPS decoder was used.

The literal `shit` material has no primary map and no `$shader` token. Resolver
`391690` initially writes mesh+28=0 (`3916dc`), queue+2c=0 and both texture names
to empty values. At `39177c`, primary-present field+3c is zero, so the branch
goes to `3918fc`, skipping all automatic textured-mode inference and the slot1
copy. Absent `$shader` then branches at `391b68` to `391bd4`, skipping callback
registration. Later brake-name checks examine the empty primary name and do not
match `breaklightsonglow-` or `breaklightson-`. Thus **static mode0 is proved**;
authored slot1 `silverpaint` is not its effective sampled secondary.

Mode0 jump-table entry `4850c0` targets `3126e4`. Its original GS case sets an
opaque primary template (controlled IIP/TME/FGE enabled, ABE disabled); this does
not prove an untextured white draw. In particular, `0x412` written at `312844`
is the GIF register list ST/RGBAQ/XYZF2, not a primitive value.

Missing effective primary is handled explicitly: `3715b4` negative interned
name takes `37163c ->2fd788`. That helper returns texture-owner+58 through
manager+24/+144. `371648` assigns this default resident handle to mesh+dc.
Therefore this is neither a null binding nor inheritance of the preceding
draw's texture. The original manager initializer stores this handle at `2f8044`
after `2f84f0` creates its supplied default named texture. The actual caller
initializer `2dc6e8` constructs the default interned name at `2dc760`; its argument
is original ELF string `483f58`, **`default.gxi`**. That value passes through the
interned lookup to a3 at `2dd220`, the call `2dd22c`, saved stack word `2f7b28`,
and texture creation `2f8030`. The empty string at `483da0` is a conditional
generic fallback, not the normal explicit default name at `483f58`.

Canonical PackFS resources `\\DEFAULT.GXI`, `\\TNG\\DEFAULT.GXI` and
`\\TNG\\DATAPSM\\DEFAULT.GXI` are byte-identical: SHA-256
`ad2960c11407794294b6d188db3660478f21ecea1a9b0fef4e69fc0a4ccef6d5`,
264 bytes, 8x8, every RGBA pixel `(0,0,0,255)`. This closes the original
default texture without guessing white or binding authored silverpaint. The
different particle-directory `default.gxi` is not substituted. The converter
extracts the exact root/TNG resource and fails closed on hash drift.

The runtime converter keeps mode0 and authored slots for provenance and supplies
verified effective default black primary for these two faces. Source material
selection is now closed for this mesh; live PC rendering/state equivalence and
native frontend owner admission remain independent gates.

Original strip flags are preserved. This follow-up does not prove their culling
meaning. CULL_NONE remains an explicit diagnostic approximation, not a recovered
PS2 culling rule. No runtime model transform or ownership claim follows from
these original PS2 bytes.
