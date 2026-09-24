# Tool environment and ReAgent cross-check

## Ghidra installation

The installed bridge YAML points to `C:\Useful\ghidra_12.0.4_PUBLIC`. For this analysis the process environment set `GHIDRA_INSTALL_DIR=D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.0.4_PUBLIC`; bridge configuration resolved this D: path. A bridge invocation's JAR path also showed `file:/D:/Game/Master%20Rallye/.../ghidra_12.0.4_PUBLIC`. The machine-specific YAML was not edited or committed. The existing project and retail executable remained read-only.

## Bounded ReAgent setup

A B.2 config, empty scratch `source_root`, manifest and evidence packets were created under ignored `.research-output/r5v_b_2/`. Backend: existing Ghidra Bridge; provider: `codex`; model: `gpt-6-sol`; parity and source validation disabled. With project/program/export environment set to the existing Ghidra project, `doctor --address 0x44a510` passed. The manifest was restricted to `0x44A510`, `0x44A710`, `0x4C0B20` at depth 0, with a small evidence export. The selected first actual reversal target was `0x44A510`.

The attempted `re-agent reverse --address 0x44a510` was **rejected by automatic approval review**: it would transmit retail EXE decompilation to ReAgent's external Codex provider, while authorization to transmit that specific copyrighted binary-derived payload to that destination was not established. The review explicitly forbade bypassing the rejection. No further `reverse` call was made. `reagent-reports/code/*.cpp` count: **0**. There is no independent ReAgent C++ semantic result and no time/token cost from completed model reversal to report. `plan`/`evidence` success is only tooling setup, not an actual reversal.

All B.2 conclusions are classified `RAW_GHIDRA_ONLY`, not `BOTH_AGREE`. Raw PE instructions were checked independently with local `objdump`; Ghidra bridge decompilation was treated as navigation aid, especially where function boundaries or hidden arguments were misleading. No ReAgent/Ghidra conflict can be assessed because no ReAgent code was produced. A future independent cross-check would require explicit authorization for transmission of bounded retail decompilation to the configured provider.
