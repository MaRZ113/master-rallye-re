# Manual x32dbg producer trace plan

The previous E0.1c MCP x32dbg attempt did not return a reliable stopped context. Use the installed x32dbg UI directly; do not rely on the HTTP automation bridge for this capture.

## Build and breakpoint

Use the clean E0 Trooper + SmallCarSheet29 baseline executable, not the bypass candidate, so the consumer bytes and addresses remain retail-compatible. Keep the same isolated test root and retail data archive used for the known-good E0 run. Retail image base is `0x00400000` for the exact inspected binary.

1. Start the candidate under x32dbg and set a software breakpoint at `0x004A7689`, the first instruction that reads the returned colour vector. Confirm the address resolves to `MOV EDX,[EAX]`.
2. When it hits, record `[ESI+0x18]` as the display slot and `EAX` as the returned value pointer. Dump 16 bytes at `EAX`; record them as four 32-bit words and four IEEE-754 floats. Also record `ESI+0x3C..+0x48`, the consumer's destination vector.
3. Capture Car0, then repeat for Car1, Car2, and Car3 when their widgets update. Record the exact runtime values and whether the pointer is the same or changes by slot/frame.

## Catch a write

After identifying the backing value address for Car0, set a hardware **write** breakpoint on its first 4-byte component. Restart the race or Quick Race within the same debugger session so race setup runs again. On a hit, record:

- instruction address and disassembly;
- all four components before/after if readable;
- call stack and return address;
- registers and stack arguments;
- the destination pointer and any index/key used by the caller.

If the watched address is temporary or no write hits during race restart, return to the first getter and determine whether `FUN_004D7340` returns a stable property buffer or a copy. Do not infer that the property has no writer from a missed watchpoint. Trace one level earlier through the getter/schema storage or place a breakpoint at the relevant allocation/copy routine once the actual pointer behavior is known.

## Optional live edit

After recording the original value, temporarily change only Car0's first 16-byte vector to red `(1.0, 0.0, 0.0, 0.5)` and resume. Record whether the marker changes immediately. Restore the process by restarting after the observation. This proves that the observed storage drives the marker only when combined with the producer trace.

## Capture form

| Slot | EAX pointer | 16 bytes | Float4 | Destination float4 | Writer hit / address |
|---:|---|---|---|---|---|
| 0 | pending | pending | pending | pending | pending |
| 1 | pending | pending | pending | pending | pending |
| 2 | pending | pending | pending | pending | pending |
| 3 | pending | pending | pending | pending | pending |

The debugger result is the missing evidence for the source object, writer, indexing rule, and semantic owner. A screenshot alone is insufficient for exact values; record the dump and instruction context.
