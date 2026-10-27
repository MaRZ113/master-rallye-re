# R-OBS4 — Relocatable Broker/Debug locator (Observatory 0.3.0)

## Problem

Observatory gated every action on fixed retail VAs plus an exact PE layout
(`_family_layout_matches`: timestamp, SizeOfImage, entry point and every section
equal). Two over-strict safeguards followed from that:

- `MRallye_invitation*.exe` were rejected although all ten Broker anchors were
  byte-identical. The mod tool only raised the VirtualSize of `.text`/`.rdata`.
- Any build with shifted code (widescreen-freeze, PL, CMYCHA2002/February2002,
  Leadtek) failed every fixed-VA anchor. Only the two exact profiles connected.

After J.1, native Dump also required the exact pristine SHA256
(`validate_pristine_runtime_identity`), so merc, grid8 and every course mod lost
native Dump even when the fixed-VA audit admitted them.

The 0.2.4 standalone release (R-OBS2 adapter) layered further gates on top: a
hash pin of its own core files, an AST rewrite of two basename comparisons,
nine hash-specific research profiles and audit `retail-broker-v1.1`, which does
not know the two-trampoline walker (so `MRallye_hard.exe` lost Dump there).

## Method

`tools/runtime/observatory_locator.py` finds every item from code: masked byte
signatures (wildcards on absolute addresses and rel32) for prologues, then the
references between them. Each item must match exactly one site.

| Item | Derivation (retail VA) |
|---|---|
| `debug_logger` | logger prologue `mov esi,[sink]; mov edi,[sink+8]` … `call [edx+4]` (004D0620) |
| `debug_sink_global` | dword at logger +5 (006F7B7C) |
| `debug_sink_vtable` | sink constructor `mov [esi],vtable` at +0x10, buffer 0x800 at +0x24/+0x28/+0x2C (0064E4C0 → 0069CEA8); slots 0/1 must be code |
| `broker_editor_dump_route` | Broker dispatcher `cmp eax,0Ah; ja; jmp [eax*4+table]` (0065EC40) |
| `broker_dump_case` | table[2] must be `call accessor; push eax; lea ecx,[esp+80h]; call walker` (0065ECC1) |
| `broker_singleton_accessor` / `broker_manager_global` | first call target; `mov eax,[manager]` prologue (004D8EC0 / 006F9410) |
| `native_dump_walker` | second call target (00601D00) |
| `main_command_dispatch` | `cmp esi,58h; ja; mov al,[esi+bytes]; jmp [eax*4+jumps]` (005B09D1) |
| `broker_editor_opener` | case 0x27 body `app(); esi=[eax+38h]; app(); eax=[eax+10h]; call opener`, opener prologue checked (005B1097 → 0065E990) |
| `flow_builder_opener` | case 0x30, member +0x08 (005B0FEE → 00662D90) |

The walker is classified as exact stock, **relocated stock** (SHA256 of the
walker with its 137 relocation ranges zeroed, derived from retail 00601D00),
an audited hardened variant (R-AI1 inline, two-stub, J.1; only at the retail
VA) or unknown.

## Independent check

For widescreen-freeze, every located address equals the Ghidra results recorded
in [known-builds](../known-builds/findings.md): logger 004D0310, sink 006F6B64,
constructor 00652380 / vtable 0069BF3C, route 0065FDD0, case 0065FE51,
accessor 004D8BB0, walker 00650020, main switch case 0x27 0064B0F7 → opener
0065FB20.

## Local corpus (static)

| Build | SHA256 (12) | Profile class | Read | Dump | Open Broker | Walker | Sink / vtable VA |
|---|---|---|---|---|---|---|---|
| Master Rallye Pristine/MRallye.exe | bf8aef32407e | exact | yes | yes | yes | native_stock | 006F7B7C / 0069CEA8 |
| MRallye_merc.exe | 1fb0a1f1ba02 | exact | yes | yes | yes | native_stock | 006F7B7C / 0069CEA8 |
| MRallye_invitation5.exe | 72dbe7f52804 | located | yes | yes | yes | native_stock | 006F7B7C / 0069CEA8 |
| MRallye_invitation5_mech.exe | c7705da3f9b8 | located | yes | yes | yes | native_stock | 006F7B7C / 0069CEA8 |
| MRallye_invitation_p0.exe | 232e0850c08a | located | yes | yes | yes | native_stock | 006F7B7C / 0069CEA8 |
| MRallye_patched.exe (widescreen-freeze) | bcf310a79133 | exact | yes | yes | yes | native_stock_relocated | 006F6B64 / 0069BF3C |
| Master Rallye PL/MRallye.exe | a30e2317b50d | located | yes | yes | yes | native_stock_relocated | 006F6B64 / 0069BF3C |
| Master Rallye CMYCHA2002/MRallye.exe | caf2de0d38fe | located | yes | yes | yes | native_stock_relocated | 006F40DC / 0069AF2C |
| Master Rallye Leadtek/MRallye.exe | 788c03d82f64 | located | yes | yes | no | native_stock_relocated | 0071E13C / 006C02C0 |
| MRallye_hard.exe | 391d5d864699 | hardened | yes | yes | yes | native_hardened | 006F7B7C / 0069CEA8 |
| MRallye_five.exe | 32a09c466b9b | hardened | yes | yes | yes | native_hardened | 006F7B7C / 0069CEA8 |
| MRallye_grid8.exe | 75942c0b6514 | compatible | yes | yes | yes | native_stock | 006F7B7C / 0069CEA8 |
| MRallye_plus.exe | 5507f3ebc474 | hardened | yes | yes | yes | native_hardened | 006F7B7C / 0069CEA8 |
| Master Rallye 841 DEMO/MRallye.exe | bbdfdb709ed4 | rejected | no | no | no | — | — |

Leadtek's main command switch does not match the signature (different
compilation), so only its opener is unavailable; an already-open Broker Editor
is still used. Demo builds differ in the logger and switch and stay unsupported.

## Live gating

Exact pristine keeps the runtime-confirmed fixed-VA path including the J.1
walker checks. For every other build:

- **Located profiles:** every capability is re-located in the process image
  (`MappedImage.from_reader`). The required items must be present at the RVAs
  resolved from disk.
- **Fixed-VA profiles:** native Dump uses the same live walker classification
  instead of the pristine-identity requirement.

An unknown walker raises `UnknownWalkerError` unless the session policy allows
it (interactive `y` or `--allow-unknown-walker`).

The main window is recognized by the Game menu command IDs 0x32/0x2F. A
located build without a native menu accepts the process's single visible
`Master Rallye` window. Broker Editor is recognized by a submenu with Dump ID 2.

## Evidence boundary

Static: corpus table above, 16 synthetic locator/live-verification tests and
the full synthetic suite. **Live capture on a located build is a pending human
runtime gate** (Status/resolve PID, open Broker, one fresh active-race Dump).
