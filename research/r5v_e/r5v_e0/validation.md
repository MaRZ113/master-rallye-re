# R5V-E0 validation record

## Candidate preparation

- Retail executable matched the supported source SHA-256:
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Trooper revision-131 source hashes matched the R-COOKER1.1 report. The
  resulting three revision-135 hashes matched the prior runtime-tested set.
- All converted DX files passed parsing, stored-global-index validation, and
  finite position/normal checks, with no parser diagnostics.
- All 24 referenced Trooper DXT dependencies parsed and were included. The
  composer reported a complete 27-file loose override and zero unresolved
  texture references.
- Retail Trooper family validation: `COMPATIBLE`, 147 fields, 120/120 fixed
  required fields and 13 Player1 fields.
- Trooper tag101 collision: serializer roundtrip byte-identical, finite
  positive scalar/areas, 28-vertex/52-triangle closed representation, and
  translation invariants `PASS`.
- Existing R5V-C candidate independently rebuilt and verified byte-for-byte
  against its clean retail source and stored manifest; source SHA-256
  `bf8aef...96b4`, candidate SHA-256 `672d1945...20222c2`.
- R5V-E0 candidate SHA-256: `3022bdc6eb07d1e388f9c8ef693b83ce1c20c12c2c1a62719aad1cc59a1b1f13`.
- Retail source executable and `Data.sma` were read only during automated
  validation. The automated run did not launch the game; the owner separately
  reports a P0/P1 FULL PASS as recorded below.

## Automated tests

Run with the bundled Python runtime:

```powershell
$env:PYTHONPATH = 'src'
& 'C:\Users\MaRZ\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests\synthetic -v
```

The full synthetic suite, including the release tests, ported DX conversion,
semantic config, family binding, composition, and the R5V-C/R5V-E0 patcher,
passed: **195 tests, 10.424 seconds**.

## Runtime status

The owner reports R5V-E0 P0 = FULL PASS and P1 = FULL PASS: ID25 is selectable
in T3; Trooper preview/race/wheel assets, physics, collision, and damage work;
a full stage completes; Race Results and return to menu work; original
vehicles remain available. The observed frontend identity is
`STEEL MONKEYS FORKLIFT`, Astero-derived stats, no Vehicle Select icon, and
Astero icons for race 1P, progress, and Race Results. The exact tested EXE
hash and raw runtime captures were not supplied. Automated checks do not
independently reproduce owner-reported gameplay.
