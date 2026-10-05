# R5V-F.2 validation and provenance

## Provenance

- Release project: `research/r5v-f-id26-sparse-t1`, based at F.1 commit `17535391cfda79cf6f37745f8704094f1637ce04` before F.2 documentation.
- Demo/cooker research branch: `research/r-demo-pipeline`, read-only at `0fb0a6ff6d89f2fbca5f6600578a2614b9b8f91a`.
- No beta files were merged. No original EXE, Data.sma, demo asset, DXT, DX, screenshot, or Ghidra project was added to Git.

## F.2 and F.2e evidence

- Retail Mercedes physics schema: PASS (`COMPATIBLE`, 144 parsed values; see [mercedes-physics.md](mercedes-physics.md)). This is static schema evidence, not P1 driving evidence.
- Exact retail native cooker route: PASS for Mercedes `complete.gxm`, `car.gxm`, and `wheel.gxm`; Cook A/B DX output hashes match 3/3. Details and log offsets are in `../r5v_f_2b/determinism.md`.
- Cooked rev135 model parsing and tag101 structural checks: PASS. The 36-byte secondary face-descriptor delta against legacy rev127 remains semantically unresolved and explicitly documented.
- DXT closure: PASS, 25/25 required textures resolve, parse, and hash-match.
- The supplied R5V-F.2e prompt reports prior cache-only portability and collision/damage runtime success. These are owner-reported; the local F.2d manifest still has no human cache-only log.
- Final `mercedes-final` profile, candidate EXE, merged Data.sma, and Vehicle Select overlay: statically validated. Exact hashes and member-level archive diff are in ignored `research-output/r5v_f_2e/candidate/candidate-manifest.json`.
- Fresh retail Mercedes physics schema: COMPATIBLE; 144 values, 120/120 fixed fields, six gears, six torque entries.
- Final P0/P1 runtime acceptance: waiting for a human run on the exact candidate.

## Tests and Git

`PYTHONPATH=src python -m unittest discover -s tests\synthetic -v`: PASS, 240 tests. Synthetic tests and static inspection do not substitute for final P0/P1 runtime acceptance.
