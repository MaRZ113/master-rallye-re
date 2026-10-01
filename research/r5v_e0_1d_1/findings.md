# R5V-E0.1d.1 ABI-correct colour override diagnostic

## Status

**Static ABI closure: PASS. Runtime precedence: PASS by user report. Producer: statically traced in R5V-E0.1d.2; ID25 red record-tail A/B: FULL PASS by user report.** The previous candidate crashed during race loading because its helper did not preserve the original stack contract. That invalid candidate remains historical evidence only.

The corrected candidate is `research-output/r5v_e0_1d_1/override-bypass/MRallye_slot25_trooper_smallsheet29_xmlred_colour-bypass-abi-safe.exe`, SHA-256 `ce17e26a87f0d1f6aed4b96e77d2d57a4b3b7f9772c5f19f677af3c35d0a71fb`. It was run by the user in an isolated game copy with the existing XML-red archive, SHA-256 `10f69fde8c9110abb69bb0c004904697af4e2ca024d4e38a24f97bbd04861072`.

## Confirmed ABI

The retail sequence is:

```asm
004A7655  LEA EDX,[ESP+0x58]
004A7659  PUSH EDX
004A765A  CALL 004D8EC0
004A765F  MOV ECX,EAX
004A7661  CALL 004D7470
004A7666  TEST AL,AL
004A7668  JZ 004A76A0
```

`FUN_004D8EC0` returns with plain `RET`; the path pointer pushed at `004A7659` remains on the stack. `FUN_004D7470` uses `ECX` as its object/`this` pointer, loads the pending argument from `[ESP+4]`, returns its boolean result in `AL`, and ends in `RET 4`. The corrected helper has two paths:

```asm
cmp dword ptr [esi+0x18],0
jne original
xor eax,eax
ret 4
original:
jmp 004D7470
```

The slot-0 return consumes the pending argument. The nonzero path transfers directly to the original callee, whose `RET 4` returns to the original consumer continuation and consumes that same argument. It adds no nested return address and changes no input register.

Raw Ghidra Bridge assembly, Ghidra P-code, and the retail bytes agree on the call sequence and dataflow. Exact instruction and stack evidence is in [abi-analysis.md](abi-analysis.md).

## Human results from E0.1d

- Red `ProgressCar0/ObjectColour`: the bottom marker remained aquamarine/cyan-like. The XML value is therefore not the final visible colour in the tested path.
- Previous slot-0 bypass executable: crashed while loading the race. That candidate is invalid and the crash is explained by its stack ABI bug; it is not evidence about colour precedence.
- Corrected bypass + normal XML: the Player1 marker used the grey/white fallback.
- Corrected bypass + red XML: the Player1 marker became red. With bypass active, all Player1-selected cars used the same XML fallback while opponent marker colours remained normal.

These user-reported observations confirm the tested precedence: `Race/Car0/Colour` overrides `ProgressCar0/ObjectColour`, which supplies the fallback when the property-exists query is bypassed.

## Candidate scope and binary safety

The new generator accepts only the tested E0 baseline executable SHA and changes only the five-byte exists-query call, a 16-byte helper in the verified zero-filled `.text` tail, and `.text.VirtualSize`. The helper is exposed through the E0 baseline's existing file-backed section bytes. Its end remains below `.rdata`. The exact operations and disjoint changed-byte ranges are in the ignored candidate's `patch-manifest.json` and `binary-diff.txt`.

The input is the E0 Trooper + SmallCarSheet29 baseline; its SHA matches the EXE in the XML-red package. The retail executable hash still matches the established value. This follow-up did not read or write a retail archive; it reused the pre-existing XML-red candidate archive. A current local archive path differs from its previous phase hash; see [validation.md](validation.md) for the exact paths and hashes. No game assets, runtime candidate, or Ghidra project are committed.

The legacy E0.1d generator now refuses to emit its invalid helper. Its old output remains under ignored `research-output/r5v_e0_1d/` as historical evidence and must not be tested again.

## Producer trace and next step

No runtime backing pointer or Car0..Car3 numeric vectors have been captured. R5V-E0.1d.2 traces VehicleRecord tail values through the shared `Race/CarN/Colour` writer to the HUD consumer. If the red-tail test fails or remains ambiguous, use [../r5v_e0_1d_2/MANUAL_X32DBG.txt](../r5v_e0_1d_2/MANUAL_X32DBG.txt) with the clean E0 baseline. Do not use the bypass candidate for that trace: its slot-0 branch skips the value getter at `004A7684`.

Static evidence and the user-reported isolated ID25 red-tail runtime A/B establish vehicle-dependent production. E0.1d.2 records the colour vector as the race-marker source. R5V-F remains gated on the Vehicle Select icon and other remaining frontend identity work.
