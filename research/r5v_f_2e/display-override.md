# Retail display-name override evidence

## Ghidra source

The existing Ghidra Bridge configuration points to Ghidra 12.1.4 on D:. Raw retail assembly for the relevant original functions is preserved outside Git:

- `research-output/r5v_f_2e/raw/retail-004819b0.asm.txt`
- `research-output/r5v_f_2e/raw/retail-0047b040.asm.txt`

The code flow below is checked against those assembly listings. The wrappers do not trust a reconstructed decompiler prototype as the sole evidence.

## Vehicle Select

At `0x004819B0`, the function calls `0x00481E20` to map the selected class/local position to an absolute vehicle ID. The result is saved in `EDI`. The ID is then used to address that vehicle's registry record and passed to the unlock check at `0x0045A150`.

For the two display fields, retail executes:

```text
0x00481A0E  MOV EDX,[EAX]
0x00481A10  PUSH EDI              ; absolute vehicle ID
0x00481A11  PUSH 0x33             ; manufacturer group
0x00481A13  MOV ECX,EAX
0x00481A15  CALL [EDX+0x0C]

0x00481A4B  MOV EDX,[EAX]
0x00481A4D  PUSH EDI              ; absolute vehicle ID
0x00481A4E  PUSH 0x34             ; model group
0x00481A50  MOV ECX,EAX
0x00481A52  CALL [EDX+0x0C]
```

The final profile redirects each complete call sequence to a small wrapper. The ID26 branch returns a static string pointer for `MERCEDES` or `ML-320` in `EAX` and resumes immediately after the original call. Every other ID replays the original object, stack arguments, and indirect call. The original returned pointer is consumed by the existing UI string constructor.

## Quick Race

In `0x0047B040`, each of three contexts calls `0x004ADFB0`, then passes its returned physical ID to localization group `0x35`:

```text
0x0047B0AF -> ID getter; lookup call at 0x0047B0B4
0x0047B13A -> ID getter; lookup call at 0x0047B13F
0x0047B1BA -> ID getter; lookup call at 0x0047B1BF
```

At each lookup the original call pushes the returned ID, pushes group `0x35`, sets `ECX=ESI`, then calls `[EDI+0x0C]`. The ID26 branch returns `MERCEDES ML-320` in `EAX`; other IDs take the original call path. The original caller then passes the result into its existing string construction path.

## Identity and limits

The runtime VehicleRecord remains physical ID26 with owned internal/resource name `Mercedes`. The display wrappers do not alias the car to ID0 or rewrite the race ID. The initializer uses the original full vehicle-record initializer and its deep-copy path for the owned name; static UI display literals are separate from that owned field.

The patch covers the two Vehicle Select fields and these three verified Quick Race lookups. It does not globally patch localization or assert that every unrelated results/menu context uses these same call sites. Normal `GALOCAL UNKNOWN` behavior and visible strings must still be checked in P0.

## Verification

Synthetic tests validate both wrapper branches, exact group values, resume addresses, and literal pointers inside the code cave. The deterministic candidate rebuild matches the packaged executable byte-for-byte. This remains static verification until the human run.
