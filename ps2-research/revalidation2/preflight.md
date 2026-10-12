# Preflight and source integrity

## Repository

The active repository is `D:\Game\Master Rallye\master-rallye-re-general`,
branch `master`, starting HEAD `61cb84d5c7f28d3bd88a3f1f9a8ce16d4c178390`.
It was two commits ahead of `origin/master`. The working tree already had
uncommitted changes under `ps2-research/pc-port/` and
`ps2-research/revalidation1/`, plus this new untracked phase. Those changes
were preserved. `modernization/renderer/` had no diff.

The read-only Course SDK checkout was branch
`research/r5t-course-archaeology`, HEAD
`4244fa0c4d878523c9947f54816bf377cdfb2589`, clean when checked. This phase
read its DXT parser only; no SDK source was changed.

## Canonical inputs

| Input | Size | SHA-256 | Result |
|---|---:|---|---|
| `SLES_509.06` | 3,739,852 | `b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2` | PASS |
| `SYSTEM.CNF` | 56 | `db08eef06278820a562f9cdacd6a2d5d2bb31870e7cf3a51e83daee3a90c5df2` | PASS |
| `TNG.PAK` | 135,556 | `d98c7cf1049a8a3bc2f90a528a2b6f52cd43c16c2e0564830d5ecb9c592ab28d` | PASS |
| `TNG.000` | 1,225,915,283 | `004ac1676376275bf40c1fd5c1c4a9dcfaae870bf1a7916434eb73b0b1faff86` | PASS |

The four hashes were read directly from the canonical PS2 source directory.
The original ELF and PackFS inputs were not modified. Existing PackFS
provenance is reused; this phase does not duplicate archive extraction.

The PC runtime logs identify the retail executable as SHA-256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and the
single proxy as
`a0035c53b749bcbdb2135174ebc73fdac366b8545ab255b370b6bb1823af11f9`.

## Tool inventory

* Ghidra 12.1.4 `analyzeHeadless.bat`; Emotion Engine Reloaded release v2.1.38
  is installed for this Ghidra generation. Its installed extension metadata
  says version `12.1.4`; the actual language file reports processor
  `MIPS-R5900`, 32-bit little-endian, ID `r5900:LE:32:default`, compiler spec
  `default`.
* Java: OpenJDK 25.0.2 LTS.
* Rabbitizer 1.16.2 in the existing ignored Python 3.11.9 environment at
  `ps2-research/data/revalidation1/tooling-venv`, explicitly using
  `InstrCategory.R5900`.
* PCSX2 Nightly: `C:\Games\PCSX2_Nightly\pcsx2-qt.exe`, product version
  `2.9.117.0`, executable SHA-256
  `b6e399ee41033c68e29e89ec5fa03a586bc41a8a45127b2bea025e1aba4e0365`.
* REA's configured Windows provider does not admit this R5900 ELF. That
  limitation was verified in REVALIDATION1; this phase uses direct Ghidra EER
  plus an independent R5900 decoder instead of relabeling generic MIPS output.
* No PS2DEV EE binutils were found in the checked tool locations/PATH.

The PCSX2 installation contains `docs/debugger.txt` and the R5900 debugger
layout. A live emulator session was not started in this static phase.
