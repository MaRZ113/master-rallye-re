# R5V-G.2 validation

## Build and candidate verification

* Branch: `research/vehicles`; closeout started from `ed0bb19`.
* Pristine retail: 3,121,214 bytes, SHA256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
* G.1 base: 3,121,214 bytes, SHA256
  `722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`.
* Stock audio matrix SHA256 pinned by the generalized builder:
  `1aa17c4c28a5f35e6017c2c9b3442dd33ea56952b7905c699492db88f108c189`.
* Candidate ID0: 3,121,214 bytes, SHA256
  `636422d0a21b5f75abd3d6233ab0fcbae26cb0dce79c1a8d40d60ad2e8ca488f`.
* Candidate ID19: 3,121,214 bytes, SHA256
  `fb11754c0c6d56b02c175a261e36d0768a72bba6d5a0fd74cbd7c7ad9d34be7b`.
* The ignored sidecar manifests were refreshed to the generalized profile
  schema; both existing candidate binaries then passed normal
  `--verify-existing`. Neither executable's previously qualified bytes
  changed.
* A/B binary comparison: one differing byte at file offset `0x28E688`, the
  profile immediate in the appended selector wrapper.

## Generic selector coverage

The builder reads the hash-pinned canonical matrix and accepts only IDs 0..24
with `explicit_tuned_case=true` and a non-null profile. It rejects mismatched
matrix/build identities and unproven IDs. Synthetic tests exercise wrapper
ABI and deterministic G.1-preserving builds across all 25 accepted profiles.

## Human runtime evidence

The two actual Observatory JSON captures were parsed. Each raw sidecar SHA256
matches both JSON metadata and the bytes on disk. Each capture's executable
hash matches its corresponding exact candidate. Both preserve CarID26/T1 and
Mercedes `CarType`/`WheelType`; the explicit human A/B reports ordinary sound
for ID0 and a clearly bass-heavy sound for ID19. The exact raw hashes and
Broker comparison are summarized in `runtime-results.json`.

The literal untuned-warning message was **NOT DIRECTLY RECAPTURED**. The
runtime status is based on exact candidate identity, controlled one-byte
binary difference, and human audible A/B; the captures themselves are Broker
dumps, not warning logs.

## Automated checks

* Focused `test_vehicle_audio_candidate.py`: **12 passed, 0 failed, 0 skipped**.
* Full `PYTHONPATH=src python -m unittest discover -s tests/synthetic -v`:
  **291 passed, 0 failed, 0 skipped**.
* `python -m compileall src tools tests`: **PASS**.
* Both exact candidate builder `--verify-existing` commands: **PASS**.
* `git diff --check`: **PASS**.

No full stage/results lifecycle or AI-pool behavior is claimed by this short
player-car audio validation.
