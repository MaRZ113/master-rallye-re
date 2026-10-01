# ABI-correct slot-0 bypass candidate

## Source and paired data

- Source executable: `research-output/r5v_e0_1d/xml-red/MRallye_slot25_trooper_smallsheet29_xmlred.exe`, SHA-256 `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`. This is byte-identical to the tested E0 baseline and is not the retail executable.
- Paired `Data.sma`: `research-output/r5v_e0_1d/xml-red/Data.sma`, SHA-256 `10f69fde8c9110abb69bb0c004904697af4e2ca024d4e38a24f97bbd04861072`. It has the red `ProgressCar0/ObjectColour` fallback.
- Candidate output: `research-output/r5v_e0_1d_1/override-bypass/MRallye_slot25_trooper_smallsheet29_xmlred_colour-bypass-abi-safe.exe`, SHA-256 `ce17e26a87f0d1f6aed4b96e77d2d57a4b3b7f9772c5f19f677af3c35d0a71fb`.
- Machine manifest and exact byte diff are beside the output as `patch-manifest.json` and `binary-diff.txt`.

## Corrected helper

The helper starts at `0x0068E300` (file offset `0x28E300`) and is 16 bytes:

```asm
83 7E 18 00       CMP dword ptr [ESI+0x18],0
75 05             JNE short original_tail_jump
33 C0             XOR EAX,EAX
C2 04 00          RET 4
E9 60 91 E4 FF     JMP 0x004D7470
```

Slot 0 returns `AL=0` and consumes the original stack argument with `RET 4`. A nonzero display slot takes the five-byte tail `JMP` to the original getter. It does not add a nested call frame. The consumer continuation remains `0x004A7666`.

## PE bounds and existing references

The target is the E0 baseline candidate, not the untouched retail EXE. The source E0 candidate has `.text VirtualSize=0x28D300`, `.text RVA=0x1000`, `.text raw size=0x28E000`, and `.rdata RVA=0x28F000`. Thus the helper begins exactly at the old virtual end, is backed by raw bytes, and ends at RVA `0x28E310`, before `.rdata`. The patch exposes only those 16 bytes by setting `.text.VirtualSize=0x28D310`.

The untouched retail executable's `.text VirtualSize` is `0x28D294`; it is not the generator input. This difference is why the generator pins the E0 candidate hash and its section layout rather than making a retail-wide claim.

Both retail and E0 source have 16 zero bytes at the helper range. A scan of all source `.text` bytes found no `E8`/`E9` relative target within the helper range and no existing absolute VA/RVA value for the helper. Ghidra Bridge's `xrefs-to` cannot query this unused address because it is not yet a defined function; that query failure is not counted as proof. No overlap with live code/data was found in the intended 16-byte range.

## Exact changes

The only semantic executable change is the Player1/Car0 `Race/Car0/Colour` property-exists bypass. All five changed-byte runs map to three reviewed operations:

| File range | Before → after | Meaning |
|---|---|---|
| `.text.VirtualSize` field (`0x218` in this image) | `0x0028D300` → `0x0028D310` | Makes the 16-byte tail helper part of virtual `.text`. |
| `0x004A7661` call displacement | `E8 0A FE 02 00` → `E8 9A 6C 1E 00` | Redirects the property-exists query to the helper. |
| `0x0068E300..0x0068E30F` | sixteen zero bytes → helper above | Adds slot check, `RET 4` bypass, and original tail jump. |

The byte diff reports the five disjoint changed runs because unchanged zero bytes inside the helper (including the zero compare immediate and RET immediate terminator) remain unchanged. File size and all bytes outside these ranges remain identical.

## Runtime status

Static ABI verification and candidate generation passed. The user reports that this candidate loaded the race: with normal XML the Player1 marker used the grey/white fallback; with red XML it became red. With the bypass, selected Player1 cars shared the XML fallback and opponents retained their colours. This confirms the tested fallback/override precedence. The report is owner-provided, not a debugger capture. Never test the old `2d78b8b990ca1e7fa10171352cc95af3ff8e9d2bcdfac54310b4c28c642aaf7f` candidate again; it has the invalid helper.
