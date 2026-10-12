# R5900 byte and function audit

## ELF map

The audited file is the canonical `SLES_509.06` SHA-256 recorded in
[preflight.md](preflight.md). Its header is ELF32, little-endian, `ET_EXEC`,
generic machine `EM_MIPS` (8), entry `0x00100008`, flags `0x20924001`.
The single file-backed `PT_LOAD` is offset `0x1000`, VA/PA `0x00100000`,
filesz `0x38d490`, memsz `0x3d9978`, alignment `0x1000`. Within that
file-backed range:

```text
file_offset = 0x1000 + (VA - 0x00100000)
            = VA - 0x000ff000
```

This mapping is not extended through the zero-filled portion of `p_memsz`.
`EM_MIPS` and ELF32 alone do not select an EE decoder. The Ghidra import was
explicitly `r5900:LE:32:default`, compiler spec `default`; the raw ABI flags
are preserved rather than used to invent a C calling convention.

## Independent decoder check

The reusable headless probe is
[EERevalidation2.java](tools/EERevalidation2.java). It checks the active
program language before exporting exact instruction bytes, listing, bounded
decompilation, xrefs and call flow. The generated raw output and Ghidra
project remain ignored under `ps2-research/data/revalidation2/`.

`verify_r5900_revalidation2.py` reruns against the canonical ELF and reports:

| Check | Result |
|---|---:|
| Frozen TREEBLEND1 original instruction words | 620 checked, zero byte mismatches |
| Fresh Ghidra listing words mapped to original bytes | 6,633 checked, zero byte mismatches |
| Rabbitizer R5900 validity on fresh listing | all valid |
| Current compact phase probes | 576 original words, all valid R5900 |
| Ghidra/Rabbitizer mnemonic spelling or alias differences | 1,218 |

The 1,218 differences are primarily pseudoinstruction/alias spellings such as
Ghidra `move` versus Rabbitizer `daddu`, and `s8` versus `$fp`. They are not
byte disagreements. Original words and addresses are the oracle; see
[instruction-probes.json](instruction-probes.json).

One architecture-specific check is `0x0031d70c`, word `0x03c21018`.
Rabbitizer's R5900 category decodes a three-register `MULT` form
(`mult $v0, $fp, $v0`). `$fp` is the register alias for `s8`. This must not be
read using a generic MIPS LO-only interpretation. In the surrounding queue
index calculation, the destination result is used for the 12-byte bucket
record stride.

## Material references

The direct Ghidra data references independently place the `treeblend` name at
`0x004875e0` in the registration routine beginning `0x003a7468` (reference at
`0x003a7488`) and the `tree` name at `0x00487610` in the registration routine
beginning `0x003a75b8` (reference at `0x003a75d8`). The routines store callback
addresses in the original table; the callback bodies begin at `0x003ae618`
and `0x003ae710`. The separate callback bodies write the mesh fields shown in
[material-and-gs-contract.md](material-and-gs-contract.md).

The data-to-execution chain is therefore:

```text
PSM $shader(treeblend)
  -> token/material resolution (0x00390d98, 0x00391690)
  -> registered handler entry (0x003a7468 / table 0x00487d68)
  -> mesh callback 0x003ae618
  -> runtime mode 2, bucket 1, texture option 1
```

The `tree` path registers at `0x003a75b8`, uses table `0x00487d08`, and calls
the callback at `0x003ae710`, producing mode 6 and bucket 0. This is
CONFIRMED_BY_EXE and cross-checked against the original France1 material and
mesh record in prior TREEBLEND1/GEOM1 evidence; it is not a PC texture-name
heuristic.

## Decompiler boundary

Ghidra pseudocode is a navigation aid, not recovered original source. Unusual
R5900 instructions, delay slots, raw words and indirect call targets were
checked against the canonical ELF and Rabbitizer. The Ghidra export marks
some `LQ/SQ` semantics using temporary low-64-bit surrogates; no claim in this
phase depends on treating those surrogates as original instruction meaning.

The detailed bounded roles and remaining function-boundary uncertainty are
in [elf-functions.json](elf-functions.json).
