# R5V-E0.1b validation

## Static and artifact checks

- Retail executable SHA-256 before candidate creation: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Runtime-confirmed Trooper + SmallCarSheet 29 baseline candidate regenerated successfully and matched its prior SHA-256 `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`.
- Stats candidate SHA-256: `feb1b072a22bd77312b8f36f39c80dca85893d8b41645a6ee563831014b70976`.
- Patcher `--verify-existing`: PASS; output and manifest reproduce exactly.
- Baseline-to-diagnostic comparison: same file length; exactly four changed bytes, at the four stat initializer immediates listed in `frontend-stat-runtime.md`.
- Original retail EXE hash checked again after generation: unchanged.
- Owner-reported runtime test: FULL PASS; the four Vehicle Select bars followed `(3,4,6,10)` in order with Trooper configuration retained.
- No color candidate was generated because no producer/input with a proven Player1-only scope was found.

## Tests

`$env:PYTHONPATH=(Join-Path (Get-Location) 'src'); python -m unittest discover -s tests\synthetic -v` passed **200 tests**. The suite needs `PYTHONPATH=src`; without it, two test modules cannot import the local package. The README's documented synthetic suite is the relevant automated suite; `tests/blender` contains standalone Blender scripts, not unittest cases.

## Runtime status

- Stats: **FULL PASS**, owner-reported Vehicle Select inspection.
- Progress tint: **BLOCKED** pending the producer and safe Player1-only control point.
- No game launch was performed by the research tooling.
