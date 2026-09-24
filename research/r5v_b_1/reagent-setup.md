# ReAgent bounded experiment

- Local source: `D:/Game/Master Rallye/_reverse-tools/reagent-main` (0.4.0).
- Backend: existing `ghidra-bridge` CLI in `D:/Game/Master Rallye/_reverse-tools/ghidra-bridge-main/.venv/Scripts/`; existing retail Ghidra export/project. No installation or dependency upgrade.
- Config/output: ignored `.research-output/r5v_b_1/re-agent.yaml` and adjacent raw outputs. Provider configured as `codex`, model `gpt-6-sol`; no model response was obtained.
- `doctor --address 0x45A0B0`: PASS. `plan --max-depth 0` and `evidence` completed for initializer (6 functions) and selection/resource (7 functions). Seeds respectively: `0x458CD0, 0x458D60, 0x458E70, 0x45A080, 0x45A0B0, 0x4D1990`; `0x481E20, 0x481E50, 0x4819B0, 0x4AD840, 0x436700, 0x443D40, 0x4BC590`.
- `estimate --address 0x45A0B0`: about 10,750 input tokens and 8,192 output-token allowance for one reverser/checker attempt; actual LLM token/cost use: zero/none observed. Preparation time was minutes; no trustworthy full time-cost metric.

The `reverse` invocation was rejected by automatic approval review because it could send retail-executable decompilation to an external Codex/LLM provider without specific authorization for that data transfer. It was not retried through another route. Consequently ReAgent produced evidence bundles, **not** independent C/C++ reconstruction. Its value here was limited to bounded collection; use it only as a secondary verifier if that data transfer is explicitly approved later. Raw assembly/P-code remains authoritative.
