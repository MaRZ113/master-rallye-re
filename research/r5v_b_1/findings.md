# R5V-B.1 findings (retail)

**Verdict: STILL_BLOCKED.** Raw assembly closes the full-record initializer ABI and owned-string behavior. It does not close the selected-ID-to-preview/race/physics chain or prove every class-2 UI bound safe. No binary or runtime candidate was changed.

Evidence labels in these notes: `RAW_GHIDRA_SUPPORTED` means a retail assembly/P-code or direct Ghidra xref observation; `REAGENT_SUPPORTED` would require an actual ReAgent reconstruction; `BOTH` requires both; `CONFLICT` identifies disagreement. ReAgent manifest/evidence collection succeeded, but its LLM reverse step was blocked by automatic approval review, so no semantic conclusion has `REAGENT_SUPPORTED` or `BOTH` status.

The limited observed path is class-2 local 11 → absolute ID25 (`0x481E20`) → record pointer `singleton+4+25*0x34` and unlock check (`0x4819B0`, `0x45A150`) → integer `Frontend/VehicleSelect/CarModel` when unlocked. The consumer that resolves this integer to `complete.dx`, the race model name and named physics remains unproven. See the dedicated files for exact edges and gaps.

The ignored `.research-output/r5v_b_1/` directory contains local manifests, evidence packets, assembly windows and decompilations. It is not part of this commit. `demo-8.4.1` and `demo-9.3.1` were not re-audited because their record/UI layouts differ from retail and they do not clarify the outstanding retail dataflow. They use unpacked data, not Data.sma.
