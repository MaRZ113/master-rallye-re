# Manual x32dbg producer-trace instructions

Use this only after the corrected-bypass runtime test passes with a red Car0 marker. The bypass candidate skips the Car0 value getter, so it cannot supply the normal storage pointer. For the producer chase, use the clean E0 baseline executable (`e19e80e...`) with the same red `Data.sma` and Trooper overlay. Keep all files in the isolated test copy.

## Capture the value read by the HUD

1. Start the game under x32dbg. Confirm `MRallye.exe` is loaded at `0x00400000`; if the image base differs, rebase the addresses below.
2. Set a software breakpoint at `0x004A7689`, the verified `MOV EDX,[EAX]` first read of the returned 16-byte colour vector.
3. On hit, record `ESI`, `[ESI+0x18]` (HUD display slot), `EAX` (returned value pointer), and the consumer destination `ESI+0x3C..0x48`.
4. Dump 16 bytes beginning at `EAX`. Record all four raw DWORDs and interpret the same values as IEEE-754 floats. Note whether `EAX` is stable across frames and slots.
5. Capture slot 0 first. If the mode exposes the other progress widgets, repeat for slots 1–3. Do not infer a shared palette from visually similar values.

## Catch the writer

On 32-bit x86 a hardware data breakpoint covers at most one 4-byte DWORD per debug-register slot. To watch all 16 bytes simultaneously, set four 4-byte hardware **write** breakpoints at `EAX`, `EAX+4`, `EAX+8`, and `EAX+0xC` if all four DR slots are available. Otherwise start with the first DWORD and add the other components after releasing an unrelated hardware breakpoint.

Keep the process alive and restart race setup through the game UI so the watched address remains valid. If the process must restart, hit `0x004A7689` again and re-arm the watchpoints using the newly returned pointer.

At each write hit, save:

- EIP and the instruction at EIP; also inspect the immediately preceding instruction because x86 data breakpoints are reported after the store executes;
- all registers, ESP and the stack DWORDs;
- call stack, return address, source pointer and destination pointer;
- the four destination components before/after if readable;
- the participant/CarN index or other caller input used to choose the value.

If no watchpoint fires, do not conclude that the property has no writer. The getter may return a copy or temporary buffer. Re-hit the getter, compare pointers/lifetimes, and trace the copy/allocation source one level earlier.

## Optional live edit

After identifying the stable Car0 storage, optionally edit only that 16-byte vector in process memory to `(1.0, 0.0, 0.0, 0.5)` and resume. Record whether the bottom marker changes. Restart the process afterward to discard the edit. This demonstrates that the watched memory drives the marker; it does not identify the semantic producer.

## Capture sheet

| Display slot | EAX pointer | Raw 16 bytes | Float4 | HUD destination | Writer EIP / function | Source / index |
|---:|---|---|---|---|---|---|
| 0 | pending | pending | pending | pending | pending | pending |
| 1 | pending | pending | pending | pending | pending | pending |
| 2 | pending | pending | pending | pending | pending | pending |
| 3 | pending | pending | pending | pending | pending | pending |

Do not classify the producer until the write path reaches a semantic source such as participant palette, Player1 constant/profile, race setup descriptor, team, network state, or another explicit owner.
