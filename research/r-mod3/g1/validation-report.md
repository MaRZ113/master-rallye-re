# R-MOD3-G1 validation report

**Qualification:** `FULL PASS / CLOSED` by owner-confirmed gameplay and Broker evidence received after the candidate report below.

The exact input retail executable is 3,121,214 bytes with SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
The published `v0.1.0-beta.1` files were not changed. The development package
does not contain `MRallye.exe`, `Data.sma`, or vehicle assets, and does not
include or modify the graphical `d3d8.dll`.

## Test results

| Check | Result |
|---|---|
| `PYTHONPATH=src python -m unittest discover -s tests/synthetic -v` | 651 run; 650 passed; 0 failed; 0 errors; 1 opt-in Windows suspended-child test skipped |
| Focused R-MOD1 core/native-plan tests | 21 passed; 0 failed |
| MSVC x86 shared-core harness | 322 checks; 0 failures |
| `python -m compileall src tools tests` | PASS |
| `git diff --check` | PASS; Git emitted only configured LF-to-CRLF notices for existing dirty files |
| Candidate host-qualified operation preflight | PASS; 13 selected operations, exact retail preimages and negative preimage test |
| DirectInput forwarding harness | PASS; 6 named and 6 ordinal exports |
| One-time bootstrap/fail-closed harness | PASS; 8 concurrent calls and invalid host rejection |
| Runtime image-difference harness | PASS; virtual extent, padding, non-hook differences, hook conflict, and zero-fill cases |
| `build_rmod3_g1_candidate.py --verify` | PASS; exact retail identity, regenerated plan, package hashes and ZIP contents |
| Independent deterministic rebuild | PASS; runtime, proxy, native plan and package ZIP identities matched |

Full and focused test output is preserved in the ignored generated review
evidence directory and copied into the source review archive.

## Candidate identities

| Artifact | SHA256 |
|---|---|
| Current-source F3 parent core, G1 marker disabled | `6992f3f108643769b2e7165c3f8313e8cf8c45bd49942f94830d8b9aeca30ffd` |
| G1 runtime DLL | `0739a5579703a1af836ac4a5833d1fccdfa22a4f96a14ebf235068bf44511784` |
| DirectInput proxy | `52ee1332e7a587878ea846a19dd7fcd5ca4cdd41694355558ee47e72c9c77c36` |
| Native plan template | `bd43b55b438c1f1bc8bdfa1dcd87687b1ecb7f4e44413c5ebcb901ed2f540018` |
| Test ZIP (`first-integrated-candidate-g1.zip`) | `d0ab223c0999cc5f2ae32af41343b7416dd773d5cf1a45bde58b8edae2c9af8b` |

The F3 core hash above identifies this checkout's deterministic development
parent build with the G1-only callback marker disabled. The candidate builder
also compares its F3 operations, remote allocation templates, and code
symbols with the canonical F3 reference, then verifies G1 changes only the
three Quick Race selector operations. The separate public-beta DLL identity
remains pinned by the release builder and is not replaced or redistributed by
this research candidate.

The native plan has 17 non-overlapping operations. The host-qualified
preflight harness selects the 13 Randomizer/Challenge operations, verifies
each pristine preimage, and exercises a negative mismatched-preimage path.
The three opponent-count UI/Start operations and the OEP bootstrap operation
are outside that harness's selected feature mask; the candidate plan and
composition tests still validate their boundaries and preimages. The in-
process package uses its audited in-process installer rather than the OEP
launcher path.

## Runtime limit

## Owner runtime closeout

The owner reports a complete eight-participant T2 race using repeated physical
vehicle identity. The supplied Broker summary records:

- `Race/NumCars=8`, `Race/NumPlayers=1`, and seven AI participants.
- `Car3/CarID=8` and `Car7/CarID=8`, with separate DriverIDs 6 and 5.
- All eight `Race/CarN/Finished` values true in the finish snapshot.
- Eight distinct displayed race results.

This is sufficient to close the G1 duplicate-participant behavior as
`CONFIRMED_BY_RUNTIME` and establish G1 as the G2 development baseline. The
exact candidate SHA and raw snapshot files are not present in this checkout,
so this closeout is explicitly owner-provided evidence; no new hashes or
capture provenance have been inferred. The previously reported
post-dump/results crash is tracked separately as an Observatory safety issue.

The candidate identity table and ZIP above describe the original G1 build and
remain unchanged. Their generation-time runtime-pending labels are historical
metadata, not the current phase status.

