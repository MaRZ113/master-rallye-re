# R-COOKER1.2 — Forester retail runtime test plan

**Status: READY_FOR_RUNTIME — runtime result PENDING.** Same-source GXM
hashes match between both input folders; all 35 Forester draw records match
the prefix formula; the unchanged generic prototype produced three candidates
that parse as rev135 without errors or warnings.

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

## Test procedure

1. Use the established Forester restoration/Vehicle Composer path in a
   separate runtime test setup.
2. Back up the active Forester `car.dx`, `complete.dx`, and `wheel.dx` and
   record their hashes.
3. Replace only those three DX files with the candidate files, retaining the
   runtime filenames. Leave physics/configuration and the existing compatible
   texture package unchanged.
4. Check the candidate hashes before launch, then test frontend and race.
5. Record each observation below and restore the backups afterward; verify
   their original hashes.

## Operator observations to record

Using the established Forester restoration path, test only the DX
compatibility question and record:

1. Does the complete model appear in the frontend?
2. Does the game load into a race?
3. Is the Forester body visible?
4. Are wheels visible?
5. Are wheel positions normal for the selected physics?
6. Are expected textures and materials present and correct?
7. Does the geometry look correct?
8. Does collision behave as expected for the ordinary Forester car?
9. Does damage behavior remain functional where expected?
10. Does the game crash during frontend loading or race entry?

The central runtime question is whether retail accepts Forester rev131 DX
after only revision and draw-prefix conversion, without the official 9.10.0
triangle reorder. Until the operator reports a result, runtime status remains
`PENDING`.

## Rollback

Before replacing files, save hashes and backups of the active Forester model
package. Restore those exact originals after the test and verify their hashes.
Do not modify either authoritative demo corpus or the retail physics files.
