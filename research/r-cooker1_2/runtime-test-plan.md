# R-COOKER1.2 — Forester retail runtime test plan

**Status: PENDING — static candidate gates have not been reached.** Do not
run this test until fresh same-source rev131/rev135 output pairs are present,
every paired Forester draw record matches the established prefix formula,
the existing generic prototype generates all three candidates, and the
canonical rev135 parser accepts them without errors or unexplained warnings.

## Candidate package

The future ignored package path is:

```text
.research-output/r-cooker1_2/forester-runtime-candidate/
    car.dx
    complete.dx
    wheel.dx
```

All three files must be generated from Forester rev131 DX by the existing
generic R-COOKER1.1 prototype. Do not use official 9.10.0 DX as candidate
input. Preserve the rev131 local index order. Keep verified physics
configuration unchanged.

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
