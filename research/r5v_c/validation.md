# Automated validation; no gameplay claim

- Supported clean retail SHA-256 checked before any write: bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4.
- Patcher dry-run accepted the retail source; unsupported hash and expected-byte mismatches are fail-closed.
- Patched copy SHA-256: 672d1945681900f3de5921e7a9032ea6d6e57d5e3fe1b49270e04994520222c2; original source hash remained unchanged after generation.
- --verify-existing rebuilt the candidate in memory from the clean source and compared both complete output bytes and manifest.
- Independent byte audit: same source/output file length (3,121,214), 88 changed bytes, zero changes outside the five declared patch ranges. The original 0x458E70–0x4598CF normal-vehicle initializer sequence is byte-identical.
- objdump parses the candidate as PE32, reports .text VirtualSize 0x28D300, and disassembles the hook to 0x68E2A0, the stub's calls to 0x4D11D0, 0x45A0B0, 0x4598D0, and the ID25-only unlock return.
- Synthetic patcher tests cover hash rejection, expected bytes, PE translation, non-overlap, deterministic output, source preservation, dry-run, exact manifest ranges and tamper detection. The full repository test result and commit are recorded with this phase.

**RUNTIME VALIDATION: WAITING FOR HUMAN P0.** Static checks cannot prove frontend rendering, gameplay resource selection or physics behavior.