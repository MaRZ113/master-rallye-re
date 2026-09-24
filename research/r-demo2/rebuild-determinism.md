# Repeated 9.3.1 Trooper car.dx build A/B

The user supplied two independent runtime rebuilds from one unchanged 9.3.1 Trooper `car.gxm` in scratch copies. Both binaries remain ignored at `.research-output/r-demo2/input/rebuild-A/car.dx` and `rebuild-B/car.dx`; the exact source GXM SHA256 is `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` in the authoritative corpus. The user reports deleting scratch DX and restarting the demo for each build. Scratch executable/configuration hashes and a file trace were not supplied.

| Copy | Size | SHA256 |
|---|---:|---|
| Rebuild-A | 124,568 | `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` |
| Rebuild-B | 124,568 | `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` |
| Previously supplied single regenerated DX | 124,568 | `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` |

`compare_demo_dx` returned **BYTE_IDENTICAL** for A vs B. This supports a deterministic cooker output for these two controlled 9.3.1 runs of this fixed source. It does not establish universal determinism across computers, configurations or builds. The supplied shipped original hash `bf644c0530b3908789676564b4761cd670cc2bb187b084983d414bba458fa041` differs. Historical cook conditions or source provenance are plausible explanations; the exact reason is **UNKNOWN**. Full metadata remains ignored at `.research-output/r-demo2/rebuild-A-vs-B.json`.
