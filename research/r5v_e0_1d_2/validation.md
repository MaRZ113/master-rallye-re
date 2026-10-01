# R5V-E0.1d.2 validation log

## Static evidence

- Retail executable identity was taken from the established R5V evidence: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Existing Ghidra 12.0.4 and local Ghidra Bridge successfully analyzed a bounded cluster: `FUN_00458E70`, `FUN_0044A320`, `FUN_0044A510`, `FUN_0044A710`, `FUN_0044A8E0`, `FUN_0045A3C0`, `FUN_004ABCE0`, `FUN_004AC660`, `FUN_004ACDD0`, and `FUN_004B0630`, plus directly called helpers.
- Raw assembly and P-code were compared for record stride/tail addressing and property setter identity. Exports remain in ignored `research-output/r5v_e0_1d_2/ghidra/`.
- The corpus parser found exactly 25 direct `0x0045A0B0` calls; it reconciled each receiver displacement with ID order 0–24 and record stride `0x34`. All 25 float4 vectors are finite, normalized RGB, alpha 1.0, and unique after 8-bit RGB conversion.

## Diagnostic artifact

- Source candidate SHA-256 before generation: `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`.
- Red-tail candidate SHA-256: `9d56c1ef0682224d3254db0e5e49cb4ecb11076467321f073f15d60526f60e46`.
- Whole-file comparison reports exactly twelve changed bytes, all within the three RGB immediate dwords listed in [runtime-diagnostic.md](runtime-diagnostic.md); the alpha word is identical. The input candidate was read-only and not overwritten.
- Candidate output and generated package files are ignored under `research-output/`.
- Human runtime result: **FULL PASS by user report**. Only the ID25 race marker changed to red; Trooper model/physics/collision, Astero's marker, and opponent colours remained unchanged. This is reported evidence, not an independent launch in this session.

## Tests

- `python tests\synthetic\test_r5v_e0_1d_2_record_colour.py`: 4 passed.
- Full documented synthetic suite, run as `$env:PYTHONPATH='src'; python -m unittest discover -s tests\synthetic -v`: 212 passed in 13.370 seconds.
- `pytest` is not installed in the current Python environment; the project suite uses standard-library `unittest`.
- Final `git diff --check`, status, and stat are recorded in the phase closeout.
