# R-DEV1 corrective pass

Status: completed before R-DEV1.1 menu/sender research. These changes are isolated in the R-DEV1.1 worktree; the original R-DEV1 worktree remains untouched.

## Shipped configuration values and provenance

The verified historical shipped `DataGame/dev.xml` values are:

| Build | `Menues/Enabled` | `DebugWindow/Enabled` | Evidence class |
|---|---:|---:|---|
| 8.4.1 | true | true | HUMAN_CORPUS_VERIFIED |
| 9.3.1 | true | true | HUMAN_CORPUS_VERIFIED |
| 9.10.0 | false | false | HUMAN_CORPUS_VERIFIED |
| retail | false | false | HUMAN_CORPUS_VERIFIED |

This establishes the shipped-config transition between 9.3.1 and 9.10.0. It is distinct from compiled fallback/default registration and from effective runtime state after parsing or later mutation. The config inventory has been regenerated from the current supplied corpora and now stores each source XML's corpus identity, relative path, byte size and SHA256; no source XML is copied into the repository.

The old R-DEV1 inventory was stale for 9.10.0 and has been replaced. The newly generated current source files report the same false/false transition. Inventory lookup models Windows case-insensitive filename resolution: the config value `Dev` resolves to the corpus file `dev.xml` on case-sensitive analysis hosts.

## Owner-reported runtime flag isolation

The owner reports that `Menues/Enabled=true` opens the native Debug window. Toggling `DebugWindow/Enabled` produced no observable effect in the tested configuration. Classify the `Menues/Enabled` Debug-window gate as **CONFIRMED_BY_EXE** and **CONFIRMED_BY_RUNTIME**. Classify `DebugWindow/Enabled` as **ORPHANED_OR_REDUNDANT_KEY**, **STRONG_HYPOTHESIS**; do not call it absolutely dead.

The tested executable/build, exact four case outcomes, captures and before/after hashes were not supplied. They are therefore recorded as UNKNOWN rather than reconstructed. This runtime result is attributed to the owner and was not repeated by the research agent.

## BuildData counter correction

Retail Ghidra disassembly at `005B2F80` zeros EBX at `005B2F9E` and stores it to the counter globals. It clears `006FE040` at `005B303B`, then calls the recursive walker `005B2DA0` at `005B3041`. The previous cumulative-image-bank-counter hypothesis is **DISPROVED**. `006FE040` is reset alongside the other BuildData counters before each walk.

Affected R-DEV1 documents have been corrected; the obsolete counter question was removed from `known-unknowns.md`.

## Synthetic inventory portability

The test fixture used uppercase `Dev.xml` in one case while the supplied corpus uses lowercase `dev.xml`; Windows masked the mismatch. The fixture now uses the corpus spelling, while the scanner explicitly resolves configured filenames case-insensitively to model Windows behavior. A synthetic assertion verifies `Dev` → `dev.xml`, and provenance fields are tested.

## Executable identity discrepancy to resolve before early-build claims

The current supplied corpora directory contains 8.4.1 `MRallye.exe` SHA256 `2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a` and 9.3.1 `MRallye.exe` SHA256 `611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728`. Both files retain the previously documented sizes, but neither matches the R-EXE1 verified hash for that path (`bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be` and `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680`). 9.10.0 and retail still match their documented hashes.

No replacement binary was found in the project corpus during this check. Do not treat fresh analysis of the current 8.4.1/9.3.1 EXE files as verified original-build evidence until this discrepancy is resolved. Existing R-EXE1/R-DEV1 derived exports remain reference evidence from the prior hash-verified analysis; their provenance must be kept explicit when reused.
