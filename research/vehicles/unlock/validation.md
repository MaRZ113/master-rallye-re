# R5V-G.1 correction validation

## Baseline

At the start of this correction, the repository suite passed **255 tests** when
run with the project source path set. Running it without `PYTHONPATH=src`
produced two import errors in the DX revision-upgrade tests; that was an
invocation issue, not a code failure.

The initial focused run found a missing canonical profile file after the stock
matrix was migrated; the file and test path were corrected before final
verification.

## Candidate verification

The EXE builder verifies the exact source SHA, every original byte range,
non-overlap, deterministic output, output hash, and structural manifest. The
XML overlay tool verifies the exact source scene SHA, the stock locked-capable
template controls, deterministic output, and that removing the appended
`T1_Car8` block restores the source text byte-for-byte.

Synthetic tests validate the native ID3 locked-reason table, the ID26-only
selector substitution, the retained stock gaLocal call for non-ID26 Vehicle
Setup names, and the stock slot's same-path unlocker/disabler configuration.
They do not execute the game or prove visible UI behavior.

## Runtime status

The current candidate is **READY FOR HUMAN RUNTIME**. Await the ID3 locked
oracle, ID26 locked visual/commit check, unlocked Vehicle Setup name, and short
race smoke in `runtime-handoff.md` before marking the correction runtime-pass.

## Final static verification

* Synthetic suite: **263 passed, 0 failed, 0 skipped** (`PYTHONPATH=src`).
* Focused G.1 tests: **20 passed**; ID26 patcher regression tests: **11 passed**.
* `python -m compileall src tools tests`: passed.
* EXE candidate: deterministic rebuild and patch-manifest verification passed;
  75 operations, source SHA256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, output
  SHA256 `3346eb00442b88cca3f76f7a65606ca56006c5b981acdbf0ee4ad16412e5b055`.
* Vehicle Select overlay: deterministic rebuild and source-restoration audit
  passed; source SHA256
  `ec7fd6372fe5008b1039eb8e09890ef3b37396dad1581568af439cbb611b58e1`, output
  SHA256 `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`.
* `git diff --check` and `git diff --cached --check`: passed before commit.
