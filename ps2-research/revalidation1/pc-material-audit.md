# Original PC material and D3D8 contract

The REA target is the verified pristine retail `MRallye.exe` described in
[target compatibility](target-compatibility.md). REA currently supplies the
best independent executable evidence for the PC selector/registration path.

## Material selection

`FUN_00580360` reads runtime fields `+0x22/+0x23` and composes `shader/base`,
`shader/base_alpha`, or `shader/base_alphatest`. `FUN_00565DA0` registers those
three variants and passes their flag pairs to a common factory. A separate
REA observation of the factory shows writes to `+0x24/+0x25`; these are
outputs in that constructor and should not be conflated with the selector's
input fields.

At the selected France1 compiled DX record, the raw tag2 flags and feature
mask predict the alpha-test family. This path is an original-PC static
contract. The specific original PC live course draw state is not independently
recovered from raw logs in this checkout.

## State-family interpretation

Original PE bytes at `0x005867a0`, independently decoded using GNU objdump
against the same verified retail executable because REA Ghidra has no defined
procedure there, support this generic family mapping:

| State | `base_alpha` family | `base_alphatest` family |
|---|---|---|
| `ALPHATESTENABLE` | FALSE | TRUE |
| `ALPHAREF` / `ALPHAFUNC` | not set by this branch | 128 / GREATER |
| `ALPHABLENDENABLE` | TRUE | FALSE |
| `SRCBLEND` / `DESTBLEND` | SRCALPHA / INVSRCALPHA | values written but inactive while blending is disabled |
| `ZWRITEENABLE` | FALSE | TRUE |
| `ZENABLE` | TRUE | TRUE |

The bounded original byte path writes `ZENABLE=TRUE` for both branches. It
does not establish the final `ZFUNC` or all inherited/cached render state.
This is a static handler-family table, not a full final state snapshot:
subsequent overrides, texture stages, and the exact live draw remain separate.
Do not promote it to
`CONFIRMED_BY_RUNTIME`.

## Proxy evidence

The previous independent build-overlay report identifies two different
`d3d8.dll` outputs. The PS2-enabled extension changes state only around the
strictly classified target draw and restores the masked native states; its
mode 0 is Stock. The executable hashes, proxy export checks and tests are
recorded in `ps2-research/pc-port/overlay/build-report.json`. This audit did
not rebuild or modify that implementation.
