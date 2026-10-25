# Vehicle Select re-entry investigation — superseded hypotheses and current cause

This file previously attributed the reset to stale XYButton Broker values and
treated the restored scene object's class/local state as correct. That
assumption was incomplete. The stack-ABI-correct XY publisher then passed a
human crash test, but ID27 still reset to Navara while ID26 restored.

The current native cause is a one-field error in the inherited J.1 ID27
reverse mapper: its ID27 arm writes class T2 at `this+0x10` but stores local7
at `this+0x14`, the T1 slot. T2's local slot is `this+0x18`; it remains at the
observed/default 0. The J.2 publisher reads the class-selected field, so it
publishes T2/local0 and the forward mapper resolves stock ID7. ID26 remains
correct because T1/local7 is genuinely stored at `+0x14`.

The constructor path is `FUN_00480B60` -> `FUN_004AE700` ->
`FUN_004ADFB0` -> `FUN_00481E50` at `0x00480E5E`. J.2's publication hook at
`0x00481152` remains useful for syncing XYButton state after native restore,
but it is not the owner of this ID27 loss. The J.2 derived root-cause bundle
changes the single inherited displacement byte from `14` to `18`, leaves the
verified J.1 bundle untouched, and keeps the existing stack-fixed 86-byte
stub.

Static emitted-byte verification proves the reverse write lands at the T2
ordinal field and the matching native forward map returns physical ID27. It
also rejects the earlier `+0x14` native write and proves ID26/stock fallback
code unchanged. The corrected candidate still needs same-player human
re-entry confirmation; see [`root-cause/human-retest.md`](root-cause/human-retest.md)
and [`root-cause-2026-10-09.md`](root-cause-2026-10-09.md).
