# Static colour precedence and slot-0 bypass candidate

## Consumer path

Retail Ghidra Bridge raw assembly for `FUN_004A74A0` verifies this sequence:

```text
004A7631  read this+0x18 (HUD display slot)
004A7639  form Race/Car%d/Colour with that slot
004A7661  CALL 004D7470          property-exists query
004A7666  TEST AL,AL
004A7668  JZ 004A76A0             absent: skip vector copy
004A7684  CALL 004D7340          value getter
004A7689  MOV EDX,[EAX]          first 32-bit component
004A768B..004A769D                copy four values to this+0x3C..+0x48
```

At entry the function saves `ECX` in `ESI`; therefore `[ESI+0x18]` remains the HUD object's display slot. `FUN_004A72A0` binds `Display Car ID` and XML `ObjectColour` into the HUD object. Static control flow makes the race property a conditional replacement for those loaded colour fields. It does not prove which branch is taken at runtime or whether another later writer changes the tint.

Evidence classification: **RAW_GHIDRA_SUPPORTED** for the consumer control flow, display-slot field, and four-component copy. **NOT RUNTIME CONFIRMED** for XML/property precedence and values. The E0.1c x32dbg automation did not capture a consumer hit.

## Retired diagnostic hook

The old candidate redirected the five-byte call at `0x004A7661` to a helper in the existing file-backed `.text` tail at `0x0068E300`:

```asm
cmp dword ptr [esi+0x18], 0
jne call_original
xor eax, eax
ret
call 0x004D7470
ret
```

This helper is **invalid**. The slot-0 `RET` fails to clean the property argument. The nonzero nested `CALL` is incompatible with the original getter's `RET 4` and corrupts the return stack. The user reports that this candidate crashed during race loading. Do not interpret that crash as colour evidence and do not run this candidate again. The old generator is disabled. The corrected helper and static ABI proof are documented in [R5V-E0.1d.1](../../r5v_e0_1d_1/corrected-bypass.md).

| Operation | VA | File offset | Bytes / value |
|---|---:|---:|---|
| Redirect the consumer call | `0x004A7661` | `0xA7661` | `E8 0A FE 02 00` → `E8 9A 6C 1E 00` |
| Add old helper | `0x0068E300` | `0x28E300` | 15 bytes; invalid stack ABI |
| Extend `.text` `VirtualSize` | section header field | `0x218` | `0x28D300` → `0x28D310`; retained in the old output only |

The next section begins at VA `0x0068F000`; the new virtual size ends at `0x0068E310`. It remains inside the existing `.text` raw extent and does not overlap `.rdata`.

## Retired candidate identity and scope

- Input is the tested E0 Trooper + SmallCarSheet29 baseline candidate, SHA-256 `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`.
- Old output is `research-output/r5v_e0_1d/override-bypass/MRallye_colour_bypass_test.exe`, SHA-256 `2d78b8b990ca1e7fa10171352cc95af3ff8e9d2bcdfac54310b4c28c642aaf7f`; this binary is invalid.
- Length is unchanged at 3,121,214 bytes. Its changed bytes are confined to the call, the old helper, and `.text.VirtualSize`; the new phase documents the corrected disjoint-byte diff.
- Exact byte ranges are in `research-output/r5v_e0_1d/override-bypass/binary-diff.txt`; the manifest records all source bytes and replacements.
- The source candidate and retail executable remain unchanged. The hook has passed four synthetic safety tests and a real-input dry run. It has not run in the game.

The old generator and test instructions are retained only as history. The corrected candidate is prepared but still needs the owner runtime test. A red result from that ABI-correct candidate after the aquamarine XML-only result would confirm the tested fallback/override precedence. See `research/r5v_e0_1d_1/runtime-test-plan.md`.
