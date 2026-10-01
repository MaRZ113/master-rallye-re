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

## Diagnostic hook

The candidate redirects the five-byte call at `0x004A7661` to a helper in the existing file-backed `.text` tail at `0x0068E300`:

```asm
cmp dword ptr [esi+0x18], 0
jne call_original
xor eax, eax
ret
call 0x004D7470
ret
```

For slot 0, the helper reports the property absent; the original `TEST AL,AL` takes the existing fallback branch and leaves the XML-loaded colour in place. For nonzero slots, it calls the original property-exists getter with `ECX` unchanged and returns its `AL` result. The hook does not change the generic render colour setter or the getter implementation.

| Operation | VA | File offset | Bytes / value |
|---|---:|---:|---|
| Redirect the consumer call | `0x004A7661` | `0xA7661` | `E8 0A FE 02 00` → `E8 9A 6C 1E 00` |
| Add helper | `0x0068E300` | `0x28E300` | 15 bytes in verified zero-filled file-backed tail |
| Extend `.text` `VirtualSize` | section header field | `0x218` | `0x28D300` → `0x28D310` |

The next section begins at VA `0x0068F000`; the new virtual size ends at `0x0068E310`. It remains inside the existing `.text` raw extent and does not overlap `.rdata`.

## Candidate identity and scope

- Input is the tested E0 Trooper + SmallCarSheet29 baseline candidate, SHA-256 `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`.
- Output is `research-output/r5v_e0_1d/override-bypass/MRallye_colour_bypass_test.exe`, SHA-256 `2d78b8b990ca1e7fa10171352cc95af3ff8e9d2bcdfac54310b4c28c642aaf7f`.
- Length is unchanged at 3,121,214 bytes. Four changed byte runs occur only at file offsets `0x218`, `0xA7661..0xA7663`, and `0x28E300..0x28E30E` (the stub tail is split into two runs because zero bytes remain in its relative call displacement).
- Exact byte ranges are in `research-output/r5v_e0_1d/override-bypass/binary-diff.txt`; the manifest records all source bytes and replacements.
- The source candidate and retail executable remain unchanged. The hook has passed four synthetic safety tests and a real-input dry run. It has not run in the game.

Run this diagnostic with the red XML candidate archive, after recording the XML-only test. See the ignored [bypass test instructions](../../../research-output/r5v_e0_1d/override-bypass/TEST_INSTRUCTIONS.txt). A red result after an aquamarine XML-only result would support the XML fallback → slot-0 race property override chain at runtime. A non-red result needs investigation of scene selection, later writes, and property storage.
