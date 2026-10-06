# R5V-G.1 validation record

## Static baseline

- Branch: `research/r5v-g1-unlock-architecture`.
- Base: `605481c` (`fix: close Mercedes Race Options identity path`).
- Retail EXE SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Baseline synthetic suite before edits: 242 passed, 0 failed, 0 skipped, using
  `PYTHONPATH=src`.
- Targeted pristine retail Ghidra analysis used Ghidra 12.1.4. Machine exports
  and project are local ignored research output; the derived address/evidence
  summaries in this directory are the reviewable record.

## Candidate

The G.1 research candidate is generated from the pristine retail executable
with:

```powershell
py -3 tools/patch_vehicle_registry_id26.py `
  "D:\Game\Master Rallye\corpora\retail\MRallye.exe" `
  "research-output\r5v_g1\candidate\MRallye_id26_t1_cupcar1_unlock.exe" `
  --profile mercedes-g1-stock-unlock
```

The adjacent `patch-manifest.json` and `binary-diff.txt` record all changed
ranges. Re-run the same command with `--verify-existing` to check the source
hash, output hash, manifest, diff, and deterministic rebuild.

Built candidate:

- Path: `research-output/r5v_g1/candidate/MRallye_id26_t1_cupcar1_unlock.exe`
- Size: 3,121,214 bytes
- SHA-256: `ceb003aff00ee15d45d11fe838fbddfb4aa79baaaecce9a0068bf8b62cd40b8e`
- Profile: `mercedes-g1-stock-unlock`
- Declared operations: 73
- Reproduction/manifest verification: passed with `--verify-existing`.

## Final static checks

- Synthetic suite: 255 passed, 0 failed, 0 skipped. The R5V-G.1 targeted module
  passed 13/13 tests. Tests were run with `PYTHONPATH=src`.
- `python -m compileall src tools tests`: passed.
- Candidate `--verify-existing`: passed; source SHA-256, output SHA-256,
  manifest, changed ranges, and deterministic rebuild matched.
- Machine-readable JSON validation: all three R5V-G.1 JSON files parsed.
- `git diff --check`: passed.

The verified candidate changes only the ID26 Vehicle Select predicate input to
stock ID3, omits the ID25 test-unlock range, and preserves the F.2f frontend
hooks. Automated evidence is static only. The fresh-versus-progressed Human
Runtime handoff remains the gate for `CONFIRMED_BY_RUNTIME`.

## Runtime status

ID26 stock-like availability: **READY FOR HUMAN RUNTIME**.

No unlock profile was mutated, no campaign flag was fabricated, and no full
race stage or save file was changed during static validation.
