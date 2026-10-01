# VehicleRecord tail to Race/CarN/Colour

## Evidence source

Retail executable SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

Ghidra 12.0.4 and the repository's existing Ghidra Bridge were used against a local project copy. Raw assembly and P-code exports are ignored under `research-output/r5v_e0_1d_2/ghidra/bridge-exports/`. All conclusions below are cross-checked against those raw instructions; decompiler parameter labels are not used as the authority.

## 1. Registry initialization and tail offsets

`FUN_00458E70` calls `FUN_0045A0B0` once for each retail ID 0–24. The receiver address is `registry_base + 4 + ID*0x34`. The vector setup supplies four 32-bit words, and the previously audited initializer stores them at record offsets `+0x24`, `+0x28`, `+0x2C`, and `+0x30`. The base is returned by `FUN_0045A3C0`; its singleton is `DAT_006F5ED4`.

This mapping is directly visible in the initializer call setup and the raw initializer body documented in `research/r5v_b_1/initializer-abi.md`. Stock call-site colours are inventoried in [corpus-colours.tsv](corpus-colours.tsv).

## 2. Participant iteration

`FUN_0044A320` obtains the race's car count and iterates participant slot `i` from zero to that count. For ordinary race modes it calls `FUN_0044A510(this, i, count)`. For race modes 5, 6, and 8 it calls `FUN_0044A710(this, i, count)`. The original callsite pushes the loop's count and slot and places the race configuration object in `ECX`.

## 3. Ordinary path: slot -> CarID -> record tail -> Colour

In `FUN_0044A510`:

1. The first stack argument is the race participant slot `i`. It is passed to `FUN_004AC660`.
2. `FUN_004AC660` uses the shared `Race/Car` path helper and the `/CarID` schema field at object offset `+0x68`; its getter returns the absolute vehicle registry ID.
3. The code calls `FUN_0045A3C0`, multiplies the returned ID by `0x34`, adds `0x28`, and reads a contiguous 16-byte vector. Since registry record zero starts at base `+4`, `base + ID*0x34 + 0x28` is exactly `VehicleRecord[ID] + 0x24`.
4. The four dwords are copied to a 16-byte stack vector. The participant slot `i` is passed separately to the generic vector setter.
5. The setter is called at `0x0044A6B5` as `FUN_004ACDD0`.

Representative raw assembly:

```asm
0044A67C  CALL 0x004AC660       ; read Race/Car[i]/CarID
0044A681  MOV ESI,EAX           ; absolute registry ID
0044A683  CALL 0x0045A3C0       ; VehicleRegistry base
0044A688  LEA ECX,[ESI + ESI*2]
0044A68B  LEA EDX,[ESI + ECX*4]  ; 13*ID
0044A691  MOV ECX,ESP           ; destination vector
0044A693  PUSH EBP              ; EBP is participant slot i
0044A694  LEA EAX,[EAX + EDX*4 + 0x28] ; base + ID*0x34 + record +0x24
0044A698..0044A6AB              ; copy four dwords
0044A6AE  CALL 0x004ADA50       ; schema object
0044A6B5  CALL 0x004ACDD0
```

Ghidra P-code independently emits the multiply by `0x34` and the `+0x28` record-vector displacement at `0x0044A694`.

## 4. Alternate race-mode path

`FUN_0044A710` calls `FUN_004B0630` with participant slot `i`; its return is used as the VehicleRegistry index. The function then calculates `registry_base + index*0x34 + 0x28`, copies the same 16 bytes, and calls `FUN_004ACDD0` at `0x0044A88E`. The writer receives `ESI`, the participant slot, separately from the four vector words. This is an alternate path selected by the parent for race modes 5, 6, and 8.

## 5. Property identity in the setter

`FUN_004ABCE0` initializes the race schema. Raw instructions associate:

```asm
004ABD72  PUSH 0x006E54C8  ; literal "/Colour"
004ABD77  LEA ECX,[ESI + 0x8C]
004ABD7D  CALL 0x004D1990
```

Therefore `[RaceSchema + 0x8C]` is the `/Colour` member. `FUN_004ACDD0` is a thiscall-shaped vector setter: it receives the participant slot as its first stack argument, the next four stack dwords as the vector, resolves the `Race/CarN` prefix, selects `this+0x8C`, and serializes all four components. It returns with `RET 0x14`, consuming the five stack arguments.

The stack setup at `FUN_0044A6B5` and `FUN_0044A88E` matches this contract: 16 bytes reserved for the contiguous vector plus one separately pushed participant slot.

## 6. Additional setup writer

`FUN_0044A8E0` contains three more reads of `registry_base + index*0x34 + 0x28`, followed by calls to the same `FUN_004ACDD0` setter (`0x0044AB25`, `0x0044AD7C`, and `0x0044B27E`). This confirms the tail is consumed as the shared race colour vector in more than one setup flow. No claim is made here that each such write is a visible HUD marker update.

## 7. HUD consumer and runtime boundary

`FUN_004A74A0` reads its display slot from the HUD object at `+0x18`, formats `Race/Car%d/Colour`, and calls the property value getter at `0x004A7684`. The next instructions at `0x004A7689..0x004A769D` copy four components into the HUD colour state. Earlier ABI-safe bypass runtime observations supplied by the user establish that the property overrides the XML fallback for the Player1 marker.

The static source-to-property path is **RAW_GHIDRA_SUPPORTED** (assembly plus P-code). The resulting HUD effect of changing only synthetic ID25's source vector is **RUNTIME_PENDING** until the red-tail candidate is tested.

## Raw export anchors

Small relevant exports are in ignored `research-output/r5v_e0_1d_2/ghidra/bridge-exports/`: `0044a320.json`, `0044a510.json`, `0044a710.json`, `0044a8e0.json`, `0045a3c0.json`, `004abce0.json`, `004ac660.json`, `004acdd0.json`, and `004b0630.json`. Raw listing excerpts for initialization and the full registry consumer scan are adjacent under `research-output/r5v_e0_1d_2/ghidra/`.
