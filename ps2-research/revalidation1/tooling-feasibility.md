# Direct R5900 Tooling Feasibility — SLES_509.06

## Result

**A reproducible direct R5900 static-analysis lane now works on this machine.**
Ghidra 12.1.4 plus Emotion Engine Reloaded v2.1.38 imported and analyzed the
canonical ELF with the explicit EE language. Rabbitizer 1.16.2 independently
decoded all 620 frozen TREE/TREEBLEND CPU instruction words when explicitly
configured for `InstrCategory.R5900`; all original words matched and all were
valid. The new Ghidra listing also matched the original ELF bytes for all 1,372
instructions emitted by the bounded probe.

The user approved installing those two tools. No PS2DEV toolchain or PCSX2 was
installed. The ELF, frozen renderer, PS2 port, and prior research findings were
not modified. Analysis projects, downloaded packages, and raw probe output are
under ignored `ps2-research/data/revalidation1/`.

Preflight repository: `D:\Game\Master Rallye\master-rallye-re-general`, branch
`master`, HEAD `61cb84d5c7f28d3bd88a3f1f9a8ce16d4c178390`. Pre-existing changes
were present under `ps2-research/pc-port/` and `ps2-research/revalidation1/`;
they were preserved. `modernization/renderer/` had no diff.

## Target identity and ELF contract

| Field | Observed value |
|---|---|
| Path | `D:\Game\Master Rallye PS2\SLES_509.06` |
| Size / SHA-256 | 3,739,852 / `b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2` |
| ELF class / byte order | ELF32 / little-endian |
| OSABI / ABI version | `ELFOSABI_NONE` (System V) / 0 |
| Type / generic machine | `ET_EXEC` / `EM_MIPS` (8) |
| Entry | `0x00100008` |
| `e_flags` | `0x20924001`: `EF_MIPS_NOREORDER`, `EF_MIPS_MACH_5900` (`0x00920000`), MIPS III architecture marker (`0x20000000`), and `EF_MIPS_ABI_EABI64` (`0x4000`) |
| Load segment | One `PT_LOAD`: file offset `0x1000`, VA/PA `0x00100000`, file size `0x38d490`, memory size `0x3d9978`, RWE, alignment `0x1000` |
| File-backed VA mapping | `file_offset = 0x1000 + (VA - 0x00100000) = VA - 0x000ff000` |

The generic ELF machine field does not identify the EE; the MIPS machine field
does. The ELF is 32-bit even though its ABI flag says EABI64. Both raw facts
are preserved. Ghidra's selected `default` compiler spec reports 4-byte
pointers and 8-byte `long`; this is the spec actually used for the test, not a
claim that all C types or calling conventions have been independently
recovered. `.text` starts at VA `0x00100000` / file `0x1000`, `.reginfo` is
present, and `.MIPS.abiflags` is absent.

The pre-existing verifier was rerun on this exact ELF and frozen TREEBLEND1
evidence: **620 instruction words, 10 data anchors, zero mismatches**. The
TREEBLEND handler at VA `0x003ae618` maps to file offset `0x002af618`; its first
eight words are `27bdfff0 7fbe0000 03a0f02d 0080102d 00a0182d 24040002
ac640028 24040001`. The compact verifier output remains ignored at
`ps2-research/data/revalidation1/r5900-tooling-byte-check.json`.

## Compatibility matrix

| Option | Installed state | Exact R5900 support | Test/result |
|---|---|---|---|
| REA native provider | Connected; the existing readiness record says its Windows Ghidra P0 accepts PE x86/x64 | Not admitted for this ELF/provider | Not retried because the exact-target admission was already rejected as `capability_unavailable`; see `tool-readiness.md`. Native Ghidra was tested independently. |
| Native Ghidra 12.1.4 `analyzeHeadless.bat` | Installed on D: | EE language supplied by EER | **PASS after EER install.** Import reports `r5900:LE:32:default:default`; full analysis completed in 84 seconds. |
| Emotion Engine Reloaded | v2.1.38 installed in the Ghidra 12.1.4 user `Extensions` directory | **Exact:** processor `MIPS-R5900`, little endian, 32-bit, `PS2`, language `r5900:LE:32:default`, extension language version 1.4.0 | **PASS.** Explicit-language ELF import and bounded decompile/xref probe succeeded. Release archive SHA-256: `e389ff3e921d9f7d4db2ece9906f808545ce4ff519d9e25a019b72ea509f240b`; JAR SHA-256: `825d6f5f506acef68985ebfaab77e90896d3c687a1e512dd440efa2014b2fe07`. |
| Rabbitizer | v1.16.2 installed in ignored Python 3.11.9 venv | **Exact R5900 category** selected per instruction with `InstrCategory.R5900` | **PASS.** 620/620 frozen CPU words valid and byte-identical to the ELF. Windows ABI3 wheel SHA-256: `3066c0484b9ea458a5b446ca41cf42b9ee9163f602a7796b699037f2aa9a8524`; sdist SHA-256: `29b624573bb57f3287eb4a88f18e5daf5616f22b19230f6c75a7ae3283cdd048`. |
| PS2DEV EE binutils | Not installed in checked locations/PATH | Official EE target prefix is `mips64r5900el-ps2-elf` | **NOT TESTED.** No `mips64r5900el-ps2-elf-objdump` or `ee-objdump` found. Installation was not approved or needed for this pass. |
| PCSX2 debugger | No local PCSX2 process/executable or matching uninstall entry in checked locations | Later runtime EE inspection | **NOT TESTED.** Current official CLI docs say `-debugger` opens the debugger and breaks at the entry point. This does not by itself capture GS packets or prove live VU residency. PCSX2 was not installed. |

Official release information confirms EER v2.1.38 added Ghidra 12.1.4 support.
Rabbitizer's project documents R5900/PS2 decoding and recommends a stable
version range containing 1.16.2. [EER v2.1.38](https://github.com/chaoticgd/ghidra-emotionengine-reloaded/releases/tag/v2.1.38),
[Rabbitizer 1.16.2](https://pypi.org/project/rabbitizer/1.16.2/),
[Rabbitizer documentation](https://github.com/Decompollaborate/rabbitizer).

## Installation and exact probes

Approved installation locations:

- EER: `C:\Users\MaRZ\AppData\Roaming\ghidra\ghidra_12.1.4_PUBLIC\Extensions\ghidra-emotionengine-reloaded`
- Rabbitizer: `ps2-research/data/revalidation1/tooling-venv`, Python 3.11.9 x64
- Downloaded release archives and analysis scratch: ignored `ps2-research/data/revalidation1/`

The EER archive was downloaded from the official v2.1.38 release asset matching
Ghidra 12.1.4, and its hash matched the release metadata. The Rabbitizer
wheel's local SHA-256 matched PyPI's release digest. No global Python package
was changed.

The first exact-language headless probe, before installing EER, failed with
`InvalidInputException: Unsupported language: r5900:LE:32:default`. After
installation this command succeeded:

```powershell
& 'D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat' `
  'D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\revalidation1\ghidra_headless_probe' `
  R5900Probe -import 'D:\Game\Master Rallye PS2\SLES_509.06' `
  -processor 'r5900:LE:32:default' -cspec default -noanalysis -overwrite
```

The log states `Using Language/Compiler: r5900:LE:32:default:default`. Ghidra
maps `.text` to `0x00100000..0x0040da73`, `.data` to
`0x0040da80..0x00442167`, and `.rodata` to `0x00444800..0x0048d0ef`, consistent
with the ELF load range. The entry `0x00100008` maps to file offset `0x1008`.
Full auto-analysis completed; the EER MIPS-R5900 constant-reference analyzer
ran. A second headless pass emitted a bounded assembly/decompiler/xref probe.
Every one of the **1,372 instruction rows** in that probe was compared back to
the original file through the `PT_LOAD` mapping: **zero byte mismatches**.

The analyzed project was processed with:

```powershell
& 'D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat' `
  'D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\revalidation1\ghidra_headless_probe' `
  R5900Probe -process 'SLES_509.06' -analysisTimeoutPerFile 300 -max-cpu 2
```

The installed headless launcher is not started with PyGhidra, so its Python
script provider rejected the first attempted probe with
`Ghidra was not started with PyGhidra. Python is not available`. The successful
bounded probe uses a Java `GhidraScript`; this is the reliable current
headless scripting route unless PyGhidra is deliberately configured later.

The Ghidra importer warned that zero-sized `.vutext` and `.vubss` sections were
skipped and that one language-defined `rom0` block conflicted with an existing
block. The ELF's EE `.text`/`.data`/`.rodata` mappings and selected function
bytes are correct. DVP overlay label-sync also reported no byte-mapped overlay
blocks; this pass did not treat those overlay warnings as evidence about the
selected CPU functions.

The compact ignored Java probe is
`ps2-research/data/revalidation1/GhidraTreeblendProbe.java`; its raw output and
Ghidra database also remain ignored. Its complete output is
`ghidra-treeblend-probe.txt` in that local data directory.

Rabbitizer's explicit call form used for each original little-endian word is:

```python
ins = rabbitizer.Instruction(word, va, rabbitizer.InstrCategory.R5900)
```

On the same 620 words previously frozen for TREE/TREEBLEND, Rabbitizer marked
all 620 valid. Its R5900-specific decoding corrects meaningful generic-MIPS
mislabels: `0x7fbe0000` is `sq $fp,0($sp)` (not generic `sd`),
`0x7bbe0000` is `lq $fp,0($sp)` (not generic `ld`), and `0x70623000` is R5900
`madd` rather than an opaque `SPECIAL2`. Branch aliases such as `beqz` versus
`beq` are presentation differences; bytes remain the comparison authority.
The word groups included ordinary integer/FPU instructions, R5900 LQ/SQ,
R5900 MMI, and R5900 COP1 forms. This CPU decoder pass does not decode VU
microinstructions.

## Bounded TREE/TREEBLEND cross-check

Fresh Ghidra results are checked against raw bytes and the frozen evidence;
they do not overwrite the earlier TREEBLEND1 conclusions.

| Evidence point | Fresh direct result |
|---|---|
| Program language | `r5900:LE:32:default`, compiler spec `default`, little-endian |
| Shader name xrefs | `treeblend` at `0x004875e0` has code reference from `0x003a7488` in registration function `0x003a7468`; `tree` at `0x00487610` from `0x003a75d8` in `0x003a75b8` |
| Registration callbacks | The bounded code stores the distinct vtable pointers `0x00487d68` for treeblend and `0x00487d08` for tree |
| Material callback | `0x003ae618` writes mode `2` at object `+0x28`, queue `1` at `+0x2c`, option `1` at `+0x3c`, zero at `+0x40`, and float32 `0x3e19999a` at `+0x44`; `0x003ae710` writes tree mode `6`, zero queue/options, and float32 `0x3e4ccccd` |
| Parser/dispatch points | Functions at `0x00390d98`, `0x00391690`, and `0x003a6c58` are defined and disassembled at the expected VAs; their references/calls are visible in the saved probe |
| Shared render producer | `0x00312610` is a large `0x51f4`-byte Ghidra function. The probe intentionally bounded its assembly windows and skipped whole-function decompilation above `0x2000` bytes; mode2/mode6 interiors and shared tail were disassembled separately |
| Other pipeline functions | `0x0031af50`, `0x0031cd98`, and `0x003bca80` have direct listing and decompiler output in the probe |

The fresh handler pseudocode is structurally useful but weakly typed: for
example, Ghidra emits `undefined8` for the return/first parameter and `int` for
the mesh parameter, with the actual writes represented as pointer arithmetic
and `undefined4` stores. Therefore the raw R5900 instructions, exact bytes,
original xrefs, and previous bounded data-flow evidence remain authoritative;
do not treat generated C types as recovered structure declarations. The probe
does not independently prove runtime invocation, live VU residency, or GS
frame output.

The TREEBLEND findings now have an independently reproducible instruction
decode, confirmed string xrefs, and direct R5900 assembly. This is independent
static confirmation, **not** a new finding that changes the prior rendering
contract.

## Recommended direct workflow

1. For EE function boundaries, cross-references, data flow, and decompiler
views, use Ghidra 12.1.4 with EER v2.1.38 and explicit
`r5900:LE:32:default` / compiler `default`. Keep the project under ignored
`ps2-research/data/`; record the language, compiler spec, memory map, and entry
before analyzing.
2. Independently validate selected words from the original ELF using the
verified `PT_LOAD` mapping and Rabbitizer 1.16.2 with
`InstrCategory.R5900`. Compare original words first, then decoded mnemonics;
normalize only known aliases for presentation, never for byte identity.
3. Keep the existing frozen-byte verifier as the provenance guard. Use
PS2DEV's `mips64r5900el-ps2-elf-objdump` only if a third disassembler becomes
necessary. Do not substitute generic MIPS32, MIPS64, or Allegrex.
4. For later live validation, the current official PCSX2 CLI offers
`-debugger` to open the debugger and break on entry. A save-state can then be
examined with EER's PCSX2 importer, but GS/VU packet capture and runtime
residency need their own evidence. No local PCSX2 debugger was available or
tested in this pass. See the [PCSX2 CLI documentation](https://github.com/PCSX2/pcsx2-net-www/blob/main/docs/advanced/cli.md).

## Sources

- [Emotion Engine Reloaded v2.1.38 release](https://github.com/chaoticgd/ghidra-emotionengine-reloaded/releases/tag/v2.1.38)
- [Rabbitizer 1.16.2 on PyPI](https://pypi.org/project/rabbitizer/1.16.2/)
- [Rabbitizer R5900 support and Python API](https://github.com/Decompollaborate/rabbitizer)
- [PS2DEV toolchain](https://github.com/ps2dev/ps2toolchain)
- [PCSX2 command-line documentation](https://github.com/PCSX2/pcsx2-net-www/blob/main/docs/advanced/cli.md)
- [MIPS ELF flags](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/BinaryFormat/ELF.h)
