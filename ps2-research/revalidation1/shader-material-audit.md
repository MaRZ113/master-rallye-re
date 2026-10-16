# Material and shader audit

## PS2 source contract

The France1 PSM material at node byte offset `3,509,209` and material offset
`3,509,264` contains the exact bytes/text:

```text
bush $alphatest() $clamp(uv) $shader(treeblend)
```

The prior TREEBLEND1 executable chain resolves `$shader(treeblend)` to
internal mode 2 and the mode-2 handler. The same France1 visual geometry is
PC draw source record 54, whose material is `bush $alphatest() $clamp(uv)
$shader(tree)`. The two platform shader labels therefore differ for matched
geometry. The PC course flags predict its alpha-test variant; the exact live
PC course handler invocation is not independently captured in the available
raw artifacts.

The token `$alphatest()` does not force the PS2 final mode-2 GS alpha test on:
the mode handler writes `ATE=0`. Material token text and the eventual handler
state are separate evidence layers.

## Original PC contract from REA

The original retail PE's selector at `FUN_00580360` chooses the alpha suffix
from runtime material flags. REA independently recovered the registration
for `base`, `base_alpha`, and `base_alphatest`. Original PE code at
`0x005867a0`, independently disassembled from the same immutable bytes by
GNU objdump because Ghidra had not defined a procedure there, sets the
generic family state described in [elf-audit](elf-audit.md).

The compiled France1 PC tag2 material bytes at core offset `3,261,170` are
`[1,1,1,1]` at `+0x20`, with feature mask 3 at `+0x24`. Under the researched
selector contract, these select `_alphatest`. This is a static source-to-code
inference, not proof of a particular live D3D8 state without its trace.

## Pilot modes (existing implementation, unchanged)

| Mode | Applied states |
|---:|---|
| 0 | Stock; no active request |
| 1 | Alpha test off, blending on, `SRCALPHA`/`INVSRCALPHA`, depth write off |
| 2 | Alpha bundle above; preserve PC depth-write state |
| 3 | Preserve PC alpha/blend state; depth write off |

The exact mask/transaction contract lives in `ps2-research/pc-port/`; this
audit did not change it. The mode observations remain `USER_RUNTIME_OBSERVATION`
because the four original PILOT1.3 screenshots and raw logs are not present.
