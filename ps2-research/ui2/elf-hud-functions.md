# Bounded ELF work and provenance

Canonical ELF SHA256:
`b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`.
All function VAs and offsets are exact-build evidence. Working labels are
descriptive. The machine-readable function map contains **63** admitted
records, direct JAL call sites, direct callees, important offsets and grades.
Indirect owner/renderer slots are recorded separately; this is not a
whole-program call graph.

## Method

Analysis used ghidra-ai-bridge exporters with the newest installed D: Ghidra
**12.1.4**, at `D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC`.
The existing ignored PS2PackFS_MIPS3 project/program was opened read-only.
Every temporary discovery/listing/stack surrogate was inside a transaction
rolled back in finally. No original ELF or saved program database was patched.

`elf_ui_query.py --track ui2` routes exports to ignored data/ui2/elf;
default remains UI1. Query windows are hash locked, aligned, text-bounded and
at most 0x20000 bytes. Only purpose-relevant callees were followed.
No grass/water/reflection spawning or renderer subsystem was investigated.

Generic MIPS LE64/o32 is not an exact R5900 language/ABI. In particular:

- Original SQ/LQ stack instructions may be replaced in query memory with
  SD/LD for scalar low64 dataflow only.
- `--ee-scalar` also maps nonzero-rd EE MULT/MULTU to low32 MIPS MUL,
  refusing any query window containing MFHI/MFLO. HI/LO and packed/MMI effects
  are not modeled, including consumers outside the query window.
- EE SQRT.S takes Ft, unlike generic MIPS Fs. The optional scalar query
  maps that operand for positive finite scalar dataflow only. It does not
  implement EE precision, denormals, saturation or exception behavior.
- The game passes extra float arguments in f12..f19 and integer arguments
  beyond o32. Decompiled parameter lists and in_fX names are not authoritative;
  arguments and offsets were checked against assembly/original words.
- COP2/VU operations stay opaque. `3cb2d0` is a concrete matrix-product
  boundary whose numerical model is still UNKNOWN; generic copFunction
  output and 64-bit COP2 placeholders cannot prove final sprite rectangles.

EE MULT/SQRT operand distinctions were checked against primary implementation
sources: [PCSX2 R5900 opcode implementation](https://raw.githubusercontent.com/PCSX2/pcsx2/master/pcsx2/R5900OpcodeImpl.cpp)
and [PCSX2 FPU implementation](https://raw.githubusercontent.com/PCSX2/pcsx2/master/pcsx2/FPU.cpp).
These references validate ISA interpretations, not game behavior.

## Important verified paths

| Path | Functions |
| --- | --- |
| Owner resolution | 15b190 / 1fc760 / 1fc500 / 1fc4c0 / 295d58 / 292a48 / 21e620 |
| Map lifecycle | 146118 ctor / 146960 config / 1461f8 init / 147038 update-draw |
| Course markers | 1ff618 / 1ff6a0 / 1ff7a8 -> 1fde60 / 1fdba8 -> 147038 |
| Map segments | 1469f0 clip / 146d80 endpoint-pair batching / concrete slots +ac,+bc,+c4 |
| Map PS2 packets | 32ee40 / 32f498 / 32f710 -> 32fce0 -> 318e10 -> 318bd8 |
| Dial/needle placement | 14b290 -> 14b388 -> HUD broker -> 14b6c8 |
| Dynamic rank | 14de38 / 14dfc0 / 14e250 / 14e360 -> 14e028 |
| Sprite bank commands | 205ce0 / 205dc8 / 2062a8 -> 337a98 |
| Sprite projection | 338ab8 -> 2dd510 -> 3280d0 / 328168 -> 343458 |
| Remaining matrix/packet boundary | 36a5a8 -> 3432b8 -> 342b90 -> 3cb2d0; submission 3376c0 |

The function start must be a direct JAL/vtable target or otherwise validated
entry, not merely a stack adjustment. Exploratory exports at 2068d4,
33ff7c and 21e800 were rejected as mid-function starts. 338d88 is cleanup;
3402f0 is a frame pacer. They are not minimap producers and are excluded.
Raw exploratory exports are ignored and do not constitute admitted findings.
Some early exports stopped at query-window boundaries; longer queries closed
the map producer and projection builder. No semantic claim depends on an
uninterpreted tail. Existing UI1 exports supply three unchanged dial/needle
constructor/config records to the UI2 metadata builder.

## Reproduce

Run from the active repository. Existing local project/runtime are required;
this does not install Ghidra or recreate its database.

```powershell
& 'D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\.venv\Scripts\python.exe' `
  ps2-research/tools/elf_ui_query.py `
  --elf 'D:\Game\Master Rallye PS2\SLES_509.06' `
  --install 'D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC' `
  --track ui2 --ee-scalar --window 0x318e10 0x31b000 --addresses 0x318e10

python ps2-research/tools/build_hudruntime_report.py `
  --elf 'D:\Game\Master Rallye PS2\SLES_509.06'
```

The metadata builder takes only the explicit admitted address list and drops
raw code, decompilation, CFG/pcode and asset payloads. Call sites are checked
from original JAL words, including calls the temporary Ghidra listing did
not resolve. Full source map regeneration requires ignored UI1/UI2 exports;
ordinary tests and hudruntime math do not require Ghidra.
