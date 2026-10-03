# Forester cache-only namespace check

**Status:** PENDING. Static package validation passes; no runtime result is
claimed yet.

The ignored runtime package is prepared at:

```text
.research-output/r-cooker3_1/forester-cache-only/DataGx/Vehicles/Forester/
```

It contains only `complete.dx`, `car.dx`, `wheel.dx`, and the 23 required DXT
files. Its canonical package validation passed. Do not use the original
Forester native-cook job for this check: that job intentionally used the
temporary Mercedes runtime namespace and still contains authoring inputs.

## Operator procedure

1. Use a separate isolated copy of the verified runtime/harness and a normal
   existing test registration that resolves the `Forester` resource namespace.
   Do not change vehicle counts or create a new slot for this test.
2. Copy the prepared `DataGx/Vehicles/Forester/` resource folder into that
   isolated test tree. Keep this namespace limited to the three DX and 23 DXT
   files. Do not copy GXM/GXI, job files, or an authoring mirror.
3. Confirm the old authoring Junction/path used by the source is absent for
   the test. Do not remove a path unless it is the exact link owned by the
   isolated test job and its live target is verified.
4. Open Vehicle Select, then load the Forester model into a race. Capture the
   relevant debug/file-access log for the Forester namespace.
5. Report whether all three DX resources and required DXT files load, and
   whether the Forester-scoped log contains any GXM/GXI or historical
   authoring-path access. Ignore unrelated game-wide source reads.

## Assertions

- `Forester/complete.dx`, `Forester/car.dx`, and `Forester/wheel.dx` load from
  cache.
- The 23 Forester DXT dependencies load from cache.
- No Forester-scoped GXM or GXI read occurs.
- No access to the historical authoring root occurs for Forester.
- Record frontend/race result separately from physics identity; this is a
  model portability test, not a Forester physics test.
