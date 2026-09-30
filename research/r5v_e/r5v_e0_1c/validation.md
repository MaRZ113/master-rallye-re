# R5V-E0.1c validation record

## Inputs and preservation

- Retail reference hash from the preceding R5V-E0.1b validation: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Scratch Trooper + SmallCarSheet29 baseline executable: `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`.
- Scratch stats diagnostic executable: `feb1b072a22bd77312b8f36f39c80dca85893d8b41645a6ee563831014b70976`.
- Scratch `Data.sma`: `9bdf132cfde6e443e32f937b99289b07e9527457ae48fa9c7e0a373b52a28f30`.
- Scratch `DataGame/PlayerState.xml`: `6a6b626a79a6fae9582716f649ddee0af83d4d6913e16750b66479ee6e4f53f7`.
- Ghidra Bridge targeted exports and the HUD palette extraction remain under ignored `research-output/r5v_e0_1c/`; they are not included in Git.
- The existing x32dbg startup-event options were restored to their original enabled values. No retail EXE, Data.sma, asset, T1/T2 mapping, or registry content was modified.

## Static validation

- Retail consumer and schema-registration decompilation/P-code were read from targeted Ghidra Bridge exports and cross-checked against the direct string/xref results.
- `FUN_004A74A0` confirms the consumer's display-slot key, four component reads, and tint copy. It does not reveal the property writer.
- `FUN_004A72A0` confirms HUD `ObjectColour` configuration is bound to HUD widget state. A writer link to `Race/CarN/Colour` was not found.
- `FUN_004ABCE0` registers `/Colour` and is not a value writer.
- Dynamic Car0/Car1 values, property backing address, and producer inputs remain uncaptured.

## Tests and Git checks

Command:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m unittest discover -s tests\synthetic -q
```

Result: **PASS**, 200 tests ran in 11.182 seconds (`OK`). `git diff --check` also passed before staging. No new parser, patcher, runtime candidate, or test was added in this phase.

The E0.1c commit contains documentation and evidence summaries only. The ignored `research-output/r5v_e0_1c/` debugger scratch, Ghidra exports, copied executable/archive, and parsed HUD palette are excluded.
