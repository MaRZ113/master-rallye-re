# R5V-G.2 validation

## Static baseline

* Branch: `research/vehicles`.
* G.1 HEAD at phase start: `3d5dbae`; tracked tree was clean.
* Pristine retail: 3,121,214 bytes,
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
* Rebuilt G.1 profile: 3,121,214 bytes,
  `722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`, 78
  operations. The source rebuild matched exactly.
* Target call bytes at VA `0x00408FB4` are the expected five-byte rel32 call to
  `FUN_004AC660`.
* G.1 cave payload is 985 bytes at `0x0068E2A0`; the append range starts at
  `0x0068E679`, is zero-filled, remains inside `.text` raw data and ends before
  `.rdata`.
* Curve-table A's 240 concatenated bytes match across retail, demo 8.4.1, demo
  9.3.1 and demo 9.10.0.

## Synthetic coverage

`test_vehicle_audio_candidate.py` covers selector preservation for IDs 0–25
and unknown IDs, ID26-only selection, wrapper stack cleanup and forwarded
getter, exact G.1 profile preservation, hash/byte fail-closed behavior,
deterministic build, and A/B binary diff limited to the donor immediate.

The complete repository synthetic suite passes **288/288** with
`PYTHONPATH=src`; the focused audio-candidate module passes **9/9**.
`python -m compileall src tools tests`, `git diff --check`, and both candidate
`--verify-existing` commands pass.

Candidate A is 3,121,214 bytes with SHA256
`636422d0a21b5f75abd3d6233ab0fcbae26cb0dce79c1a8d40d60ad2e8ca488f`.
Candidate B is 3,121,214 bytes with SHA256
`fb11754c0c6d56b02c175a261e36d0768a72bba6d5a0fd74cbd7c7ad9d34be7b`.
The verifier rebuilds from pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and exact
G.1 base SHA256
`722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`.

Static results do not establish audibility. Human A/B remains the runtime
gate.
