# R5T-F.2.1 runtime handoff — completed

Status: **COMPLETED — PASS: TREE_CARRIER_CONFIRMED.** The pre-test selection instructions and decision guide are superseded by the human runtime results below and in [`runtime-results.md`](runtime-results.md).

| Hybrid | Tree donor | tag1400 donor | OLD collision | NEW collision | FinishArea | Visual/texture anomalies |
|---|---|---|---|---|---|---|
| T | modified | baseline | absent | present | normal at original unchanged region | finish-line: none observed; texture: none observed |
| U | baseline | modified | present | absent | normal at original unchanged region | finish-line: none observed; texture: none observed |

The tested physical location follows the tag100 tree donor. In this controlled pairing, modified tag1400 was neither sufficient nor required for the `COLLIDE_finishline03` translation; broader tag1400 runtime semantics remain unknown.

Staging-time validation recorded 2862 non-target files byte-identical across clones. A post-test snapshot comparison found 2 non-target path differences; their origin and runtime role are UNKNOWN. Details and hashes are in `swap-manifest.json` and `runtime-results.md`.

No new experiment, writer, or EXE patch is part of this closeout.
