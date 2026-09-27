# R-COOKER1.2 — Forester retail runtime result

**Status: PASS — CONFIRMED_BY_RUNTIME.** Same-source GXM hashes match between
both input folders; all 35 Forester draw records match the prefix formula;
the unchanged generic prototype produced three candidates that parse as
rev135 without errors or warnings, and the operator reports a retail pass.

## Candidate package

The ignored candidate package is:

```text
.research-output/r-cooker1_2/forester-runtime-candidate/
    car.dx
    complete.dx
    wheel.dx
```

The files were generated from Forester rev131 DX by the existing generic
R-COOKER1.1 prototype. Do not substitute official 9.10.0 DX. Candidate
SHA256 values are in [`prototype-results.json`](prototype-results.json).
The candidates preserve rev131 local index order. Keep verified physics
configuration unchanged.

## Reported runtime observations

- Frontend complete model works.
- Race model works.
- Wheel model works.
- Textures/materials appear correct.
- No visible model problems were reported.
- The minimal candidates preserve rev131 local index order; the official
  9.10.0 reorder was not reproduced, and retail accepted the conversion.

Wheel placement, collision, damage, and crash behavior were not separately
reported. No additional runtime observations are inferred here.

## Rollback

The test used the established Forester restoration path. For any repeat,
save hashes and backups of the active model package, restore those exact
originals afterward, and do not modify either authoritative demo corpus or
the retail physics files.
