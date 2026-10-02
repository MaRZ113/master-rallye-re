# Master Rallye executable provenance correction

Status: pristine 8.4.1 and 9.3.1 files independently hash-verified. Prior patched-copy hashes and modifications are recorded, but the old files were not present in the searched corpus/project trees, so exhaustive pairwise byte-diff validation is **NOT VERIFIED**.

## Canonical corpus executables

| Build | File | Size | SHA-256 | Status |
|---|---|---:|---|---|
| 8.4.1 | `corpora/demo-8.4.1/MRallye.exe` | 2,084,926 | `2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a` | `PRISTINE_HISTORICAL_CORPUS` |
| 9.3.1 | `corpora/demo-9.3.1/MRallye.exe` | 2,637,886 | `611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728` | `PRISTINE_HISTORICAL_CORPUS` |
| 9.10.0 | `corpora/demo-9.10.0/MRallye.exe` | 2,883,646 | `13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78` | `PRISTINE_HISTORICAL_CORPUS` |
| retail | `corpora/retail/MRallye.exe` | 3,121,214 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` | `PRISTINE_HISTORICAL_CORPUS` |

8.4.1 and 9.3.1 were freshly reinstalled and designated authoritative by the owner. Their hashes and sizes were independently recalculated from the corpus files. 9.10.0 and retail retain their previously verified identities.

## Prior research-modified copies

| Build | Old SHA-256 | Classification | Known modification (owner-reported) |
|---|---|---|---|
| 8.4.1 | `bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be` | `RESEARCH_PATCHED_COPY` | At VA `004EB994`, pristine `74 35` (`JE`) changed to `EB 35` (`JMP`), bypassing demo time-limit expiration. |
| 9.3.1 | `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680` | `RESEARCH_PATCHED_COPY` | At VA `005FF5B2`, pristine `74 35` (`JE`) changed to `EB 35` (`JMP`); plus the vehicle initializer reference `Astero` → `Forester` around VA `0044D629`. |

The original patched files were not found among the available project/corpus files. Consequently their hashes and patch descriptions are recorded as owner-provided historical provenance, not as an independently reproduced full binary diff. The pristine files do independently contain `74 35` at the two stated time-limit VAs. The 9.3.1 initializer byte/reference cannot be compared without its patched counterpart. No claim is made here that the stated patches are the only differences in the missing old copies.

The Forester change was an intentional research vehicle-selection experiment. The public 9.3.1 demo normally exposes one T2 and one T3 vehicle and allows switching classes, not arbitrary vehicle choice within a class. Any roster finding from that initializer site that identifies Forester as original behavior is contaminated.

## Impact on prior research

The owner confirms these patches do not alter addresses, sections, general control flow, editor framework, menu framework, resource manager, broker architecture, or unrelated systems. Therefore the following remain structurally valid: R-EXE1 general architecture; R-DEV1 embedded editor framework; R-DEV1.1 command reachability; Flow Builder; Broker Editor; BuildData; debug-window architecture; resource manager; and general cross-build function correspondence.

Narrowly affected claims are demo time-limit behavior and 9.3.1 vehicle initializer/roster evidence touching the Astero/Forester entry. Do not generalize contamination to unrelated findings.

## Ghidra project provenance

Do not delete or overwrite existing annotated projects. Classify the old demo programs as `demo-8.4.1-PATCHED_RESEARCH` and `demo-9.3.1-PATCHED_RESEARCH` where their input identities are the old hashes. Future demo analysis must use separate pristine programs named `demo-8.4.1-PRISTINE` and `demo-9.3.1-PRISTINE`. Avoid transferring labels/xrefs attached specifically to modified instructions or the Astero/Forester reference. This task did not modify Ghidra databases or create pristine programs.

## Downstream corrections

R-EXE1 fingerprint reports and R-DEV1 identity tables now point to the canonical pristine hashes; notes identify that earlier detailed analysis used patched copies. R-5V-A registry extractions retain their historical data and original input hashes but are explicitly provenance-qualified; the 9.3.1 roster entry is not pristine evidence. See the individual phase findings for scope.
