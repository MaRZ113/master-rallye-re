# R5V-F.2 validation and provenance

## Provenance

- Release project: `research/r5v-f-id26-sparse-t1`, based at F.1 commit `17535391cfda79cf6f37745f8704094f1637ce04` before F.2 documentation.
- Demo/cooker research branch: `research/r-demo-pipeline`, read-only at `0fb0a6ff6d89f2fbca5f6600578a2614b9b8f91a`.
- No beta files were merged. No original EXE, Data.sma, demo asset, DXT, DX, screenshot, or Ghidra project was added to Git.

## F.2 and F.2d evidence

- Retail Mercedes physics schema: PASS (`COMPATIBLE`, 144 parsed values; see [mercedes-physics.md](mercedes-physics.md)). This is static schema evidence, not P1 driving evidence.
- Exact retail native cooker route: PASS for Mercedes `complete.gxm`, `car.gxm`, and `wheel.gxm`; Cook A/B DX output hashes match 3/3. Details and log offsets are in `../r5v_f_2b/determinism.md`.
- Cooked rev135 model parsing and tag101 structural checks: PASS. The 36-byte secondary face-descriptor delta against legacy rev127 remains semantically unresolved and explicitly documented.
- DXT closure: PASS, 25/25 required textures resolve, parse, and hash-match. Previous cooker logs report all dependencies loaded.
- Cache-only package: assembled and statically verified; authoring Junction removed by the fixed helper, with the source directory and its 25 GXI files preserved. Human preview/race load remains pending.
- Final Mercedes ML-320 profile: target values are fixed in [mercedes-profile.md](mercedes-profile.md), but implementation remains gated until cache-only PASS.

## Tests and Git

`PYTHONPATH=src python -m unittest discover -s tests\synthetic -v`: PASS, 239 tests. Earlier F.2 tests do not substitute for the cache-only human runtime test. `git diff --check` is run before the F.2d research commit.
