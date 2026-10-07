# Optional local fixture validation

Run owner-supplied retail-binary and corpus checks explicitly:

```powershell
python -m unittest discover -s tests/integration -v
```

The tests use local-only inputs when present:

- `inputs/MRallye_merc.exe` for Observatory build-profile and Broker checks;
- `corpora/retail/MRallye.exe` for GRID8 candidate reproduction;
- `corpora/retail/Data.sma_unpacked` for the retail course map audit.

Missing inputs skip only their corresponding integration test class. Do not
commit proprietary executable or game-data fixtures. The public synthetic
suite under `tests/synthetic` does not depend on these files.
