# J.2 review archive reproduction

The review ZIP is a compact source/evidence package. It intentionally omits
the pristine executable, the 243-file runtime resource root, raw Observatory
dumps, user saves, and the compiled launcher. Those remain external local
inputs.

## Offline checks

From the complete canonical checkout, use Python 3.10+ and run:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest tests.synthetic.test_j2_frontend_reentry -v
python tools/verify_j2_runtime_archive.py --write
python tools/j2_frontend_reentry.py verify .research-output/vehicles/sdk/j2-reentry/runtime-candidate/bundle
python tools/addon_runtime.py verify .research-output/vehicles/sdk/j1/reference-runtime-final
python tools/mrtool.py addon verify .research-output/vehicles/sdk/j2/reference-plan
python -m compileall src tools tests
git diff --check
```

The six native patch-plan tests are deliberately conditional on the exact
retail executable and the locally verified J.1 bundle. The four pure model
tests cover sparse mappings and the no-fixed-ID hook contract. The Windows
launcher verifier is built from the checked-in launcher source and the exact
J.2 bundle; `--verify` is read-only and does not start the game.

The full synthetic suite on this Windows sandbox requires a temporary root
that child processes can access. The validation record uses the ignored
`.research-output/vehicles/sdk/j2-reentry/tmp` root and runs without changing
any test semantics.

## Runtime qualification

Only the human screen/game test in
[`human-qualification-handoff.md`](human-qualification-handoff.md) can prove
the re-entry behavior. A successful offline archive check, PE reconstruction,
or native launcher preflight does not prove the in-game constructor hook.
