# R5V-F.2f static validation

## Build

- Source SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Candidate SHA-256: `1fbb3489208de9bc0af3802902a8611ea9a149c245031d1563960bd91b430c14`.
- Reproducible verified candidate and matching manifest/diff: `research-output\r5v_f_2f\candidate-verified\`.
- Size: `3,121,214` bytes.
- Exact source hash is checked by the existing fail-closed retail builder; expected original bytes are checked at every patch site.
- F.2e behavior remains a separate `mercedes-final` profile with 72 patch operations. F.2f adds only two Race Options string-writer hooks (74 total operations).
- Candidate verify-existing mode reproduces the exact image, manifest and categorized diff. Inverse/reproduction verification is provided by rebuilding from the pristine source and comparing exact bytes; the source is never modified.

## Patch scope

| VA | Original bytes | Replacement | Purpose |
|---|---|---|---|
| `0x0047A65F` | `8b10566a338bc8ff520c` | relative JMP to ESI-guarded helper + 5 NOP | ID26 group-0x33 manufacturer returns `MERCEDES`; all other IDs replay the original call |
| `0x0047A6C4` | `8b10566a348bc8ff520c` | relative JMP to ESI-guarded helper + 5 NOP | ID26 group-0x34 model returns `ML-320`; all other IDs replay the original call |

The existing 617-byte F.2e code payload is deterministically rebuilt with two additional wrappers and retains the direct string literals. The candidate does not edit global `gaLocal` behavior, class mapping, registry record semantics, `Race/Car0/CarID`, `CarType`, or `WheelType`. Non-ID26 lookup branches replay the exact native instructions. Existing Vehicle Select and group-0x35 Quick Race paths remain in place.

## Tests and evidence boundary

- The F.2f synthetic tests inspect both x86 branches, literal pointers, continuation addresses and exact original call replay; a separate semantic writer-order model covers the capture-supported Vehicle Select → Race Options → Quick Race refresh order. This is static/emulated code-shape evidence, not execution of the game frontend.
- Capture source/raw SHA-256 pairs and key Broker values are recorded in `frontend-writer-map.json`; raw captures stay outside Git.
- Candidate builder verify-existing: PASS.
- Human P0: WAITING.
- Human P1: BLOCKED UNTIL P0 PASS.
