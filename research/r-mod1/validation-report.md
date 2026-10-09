# R-MOD1 implementation validation

## Environment and scope

- Branch: `research/r-mod1`
- Base HEAD: `594c8737ee9c8e18589037d0167a96f7324f593c`; the archive index records final review HEAD.
- Target retail SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Vehicle SDK worktree: unchanged and not imported.
- Existing Observatory edits in this checkout were pre-existing and remain outside the R-MOD1 archive/commit.

## Validation results

| Check | Result |
|---|---|
| Focused R-MOD1 Python tests | 3 passed, 0 failed, 0 skipped |
| Portable shared-core harness, MinGW x64 | 76 checks, 0 failures |
| Portable shared-core harness, MSVC x86 | 76 checks, 0 failures |
| Full `tests/synthetic` suite | 616 passed, 0 failed, 0 errors, 0 skipped |
| `python -m compileall -q src tools tests` | passed |
| Native patch-plan JSON parse | passed |
| Historical patch composition audit | passed; 15 identical operations need deduplication, 3 shared PE-size fields need one recomputation, 2 native cave conflicts remain |
| `git diff --check` | passed; only existing LF-to-CRLF working-copy warnings on unrelated Observatory files |

The full suite used `TEMP` and `TMP` set to a writable scratch directory outside the checkout. The sandbox's default Windows Temp location denied cleanup permission changes. An in-checkout temp path also violated an Observatory test's required extraction boundary. The successful run used an approved external scratch path and left no game or project files there.

Commands:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -p 'test_r_mod1_*.py' -v
.\tools\r_mod1_core_tests.ps1
python -m compileall -q src tools tests
python -c "import json,pathlib; json.loads(pathlib.Path('research/r-mod1/native-patch-plan.schema.json').read_text(encoding='utf-8'))"
python tools/r_mod1_composition_audit.py --output research/r-mod1/patch-composition-audit.json
git diff --check
```

Full-suite command (set `TEMP` and `TMP` to a writable scratch directory outside the checkout first):

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -v
```

The dedicated x86 harness printed `checks=76 failures=0`; the portable MinGW
test also printed `checks=76 failures=0`.

## Evidence limits and release gate

These checks validate portable policy/planning code and historical-manifest overlap analysis. They do **not** validate a composed native operation bundle, Win32 launcher, DInput proxy, injected code, graphics-wrapper coexistence, or game runtime.

No R-MOD1 runtime candidate has been built. The launcher and `dinput8.dll` adapter are both absent. The optional DLL remains unsupported; the four required renderer configurations have not been runtime-tested. The known five-car Track10 result does not establish course clearance for six through eight participants. Therefore the release state is **FOUNDATION IMPLEMENTED / NOT READY FOR HUMAN GAME RUNTIME**.
