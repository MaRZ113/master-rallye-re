# Dynamic trace log

## Goal

Observe a real `Race/Car0/Colour` access and trace its write to the semantic source, using the existing x32dbg plus MCP plugin installation. Static Ghidra evidence was used to place breakpoints at the retail consumer's property-exists test and vector read.

## Debug target and scratch data

All debugger targets were scratch copies under ignored `research-output/r5v_e0_1c/debug-run/`; no retail executable or game archive was launched from a writable original path.

| File | SHA-256 | Role |
|---|---|---|
| `MRallye_slot25_trooper_smallsheet29_baseline.exe` | `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df` | Existing Trooper + SmallCarSheet 29 baseline used for the clean retry |
| `MRallye_slot25_trooper_stats_test.exe` | `feb1b072a22bd77312b8f36f39c80dca85893d8b41645a6ee563831014b70976` | Prior stats diagnostic copy involved in the first setup attempt; no colour conclusion was drawn from it |
| `Data.sma` | `9bdf132cfde6e443e32f937b99289b07e9527457ae48fa9c7e0a373b52a28f30` | Scratch copy of the retail archive |
| `DataGame/PlayerState.xml` | `6a6b626a79a6fae9582716f649ddee0af83d4d6913e16750b66479ee6e4f53f7` | Scratch copy of test configuration |

The retail reference executable hash recorded by the preceding R5V-E0.1b validation is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. It was not patched or overwritten in this phase.

## Existing debugger setup

- x32dbg was already installed at `D:\Game\Master Rallye\_reverse-tools\xdbg\release\x32`.
- The existing locally built plugin `MCPx64dbg.dp32` was used; SHA-256 `cfdd428bebdb35b3e3b176fbe26f747402077a8a72bc7a5466cd9c6f375c5a96`, reported local file version `0.0.2.5`.
- Its local HTTP endpoint was `localhost:8888`. The bridge accepted breakpoint setup requests for `0x004A7666`, `0x004A7689`, and `0x004A76A0`.
- `0x004A7666` tests the property-existence result; `0x004A7689` is the first component copy from the returned four-component value; `0x004A76A0` is the absent-property branch target. These locations come from the raw Ghidra export for the matching retail build.

## Outcome

The first run spent its stops in AMD driver TLS callback code rather than the game consumer. The existing x32dbg event settings for system breakpoint and TLS callback stops were temporarily disabled for a clean retry and restored to `1` afterward; the restored `x32dbg.ini` SHA-256 was `338b16f08e4c456b075027d0b7a3e891520de6dcd74350da88c0de6de289c8e5`.

On retry with the baseline candidate, the plugin accepted the target breakpoints, but its HTTP control/query path stopped responding reliably while the debuggee was running. Requests such as status/register inspection could not return a trustworthy stopped context. No breakpoint hit at the game consumer was observed. No `Race/Car0/Colour` or `Car1+` values, property address, writer, or memory write trace were captured.

The plugin endpoint is no longer listening on port 8888. The debugger attempts were stopped; the three x32dbg startup-event settings were restored. Process enumeration through the current PowerShell session returned Access Denied, so this check does not claim a fresh process inventory.

## Evidence status

This is a failed capture, not evidence that the game lacks a writer or that the consumer is unreachable in normal gameplay. The next dynamic pass needs an interactive debugger session that can be advanced into Quick Race while preserving break-on-hit register and memory inspection. No API workaround was applied to the user's debugger installation, and no raw debugger dump was committed.
