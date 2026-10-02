# R5V-F.2 validation and provenance

## Provenance

- Release project: `research/r5v-f-id26-sparse-t1`, based at F.1 commit `17535391cfda79cf6f37745f8704094f1637ce04` before F.2 documentation.
- Demo/cooker research branch: `research/r-demo-pipeline`, read-only at `0fb0a6ff6d89f2fbca5f6600578a2614b9b8f91a`.
- Existing evidence reused: release `vehicle_config_analysis.py`, `vehicle_config_schema.py`, `sidecar.py`, `dxt.py`; beta `demo_dx.py`, `collision.py`, `collision_analysis.py`, `collision_writer.py`; beta research `r-cooker-closeout/final.md` and `r-bridge/r-bridge2-demo-910-bridge.md`.
- No beta files were merged. No original EXE, Data.sma, demo asset, DXT, DX, screenshot, or Ghidra project was added to Git.

## Static checks

- Recomputed retail Mercedes physics schema: PASS (`COMPATIBLE`; details in [mercedes-physics.md](mercedes-physics.md)).
- Selected `Copy of Mercedes` sidecars: 19 car, 25 complete, and 6 wheel unique DXT dependencies; none missing; all referenced DXT files parsed.
- Selected `Copy of Mercedes/car.dx` tag101: finite closed convex structures and byte-identical zero-edit serializer round-trip; not a retail full-DX parse or runtime result.
- Current retail DX parser/converter: expected failure on selected revision127 model roles; exact blocker in [mercedes-model-conversion.md](mercedes-model-conversion.md).
- Original corpora remained read-only. No candidate/profile/payload was generated.

## Test and Git checks

F.1 cleanup runtime confirmation remains owner-reported; static checks here do
not substitute for a Mercedes human runtime test.

- `PYTHONPATH=src python -m unittest discover -s tests\synthetic -v`: PASS,
  228 tests.
- `mercedes-source-inventory.json`: PASS, parses as JSON with the three expected
  build keys (`demo-8.4.1`, `demo-9.3.1`, `retail`).
- `git diff --check`: PASS before commit.
- No runtime candidate, profile code, executable, archive or model asset was
  created. Final working-tree and diff summary are reported with the commit.
