# R5V-J.3 validation — 2026-10-09

## J.3-A author/compiler path

An asset-free Glacier Sprint T2 project was initialized from the public
manifest and built using the locally available, exact retail Navara donor. The
donor files and generated runtime resources remain outside Git in ignored
`.research-output`.

The project resolved to physical slot 27 / T2 local7. The capability profile
marks that physical slot qualified but does not qualify the new
`GlacierSprint` runtime identity. The build therefore remains an offline plan
(`runtime_installable=false`) and was not launched in the game.

The compiler validated the pinned retail `Data.sma` (282,396,172 bytes,
SHA256 `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f`)
and the matching unpacked `DataGame/vehicles.xml` and
`DataGame/Modifications.xml`. It generated 147 independent physics-family
rows and 26 modification-family rows without changing donor values. Asset
validation parsed 3 DX resources and resolved 114 DXT dependency bindings;
there were no unresolved dependencies.

Two builds to separate output directories each verified with 47 declared
artifacts, 44 resource-inventory entries, and addon-plan SHA256
`1d64c320cc104d177db3c012986631590183175cdd167051267e68568ad5f492`. Their 48
on-disk files had identical relative paths and byte hashes; the canonical
tree digest was
`426406a9d6ea405f857febbba9ff3055248fcf5d39d1524dc4bfadccf3988c9f`.

## Commands and checks

Focused SDK, donor project, J.1/J.2 composition and J.2 re-entry tests:

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.synthetic.test_addon_sdk tests.synthetic.test_addon_sdk_project tests.synthetic.test_addon_sdk_runtime tests.synthetic.test_addon_sdk_j2_composition tests.synthetic.test_j2_frontend_reentry -v
```

Result: **53 passed, 0 failed, 0 skipped**.

The complete suite was run as:

```powershell
$env:TEMP='<approved writable temporary directory>'
$env:TMP=$env:TEMP
$env:TMPDIR=$env:TEMP
$env:PYTHONPATH='src'
python -m unittest discover -s tests/synthetic -v
```

Result: **421 tests: 419 passed, 1 failed, 1 errored, 0 skipped**. Both
remaining cases are Windows sandbox filesystem restrictions in pre-existing
package/atomic-write tests outside the J.3 SDK changes:

- `test_single_file_writes_valid_dx_and_machine_report` — a child process was
  denied the hard-link/replace operation between two files under the
  temporary directory (`WinError 5`). The other 12 tests in that CLI module
  passed when its temp root was in the approved user-writable scratch path.
- `test_stage_builds_self_contained_package_and_drops_profile_state` — the
  test's symlink/path-resolution fixture under `.research-output` was denied
  (`PermissionError: [WinError 5] Access is denied`).

The tests were not weakened and unrelated DX/package code was not changed.
Full output is included, with user-specific paths sanitized, in the review
archive.

Additional checks:

| Check | Result |
|---|---|
| `python -m compileall src tools tests` | PASS |
| `git diff --check` | PASS; Git printed only LF-to-CRLF working-copy notices |
| J.0 reference output `addon verify` | PASS; plan SHA256 `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989` |
| J.1 canonical `reference-runtime-final` verifier | PASS_STATIC_RUNTIME_BUNDLE; 246 operations, no patched EXE written |
| J.2 corrected re-entry bundle verifier | PASS_STATIC_J2_REENTRY_BUNDLE; 248 operations, correct `C7 46 18 07` store and symbolic stack-ABI audit |
| Deterministic Glacier Sprint build A/B | PASS; 48/48 paths and hashes identical |

The older preliminary J.1 `.research-output/vehicles/sdk/j1/reference-runtime`
directory does not match the current deterministic rebuild. The canonical
`reference-runtime-final` bundle is the unchanged 246-operation parent and
passes verification; it is the parent used by the corrected J.2 verifier.

## J.3-B runtime compiler update — 2026-10-09

The bounded collection compiler is implemented in
`tools/addon_collection_runtime.py` with `mrtool addon runtime-prepare`,
`runtime-verify`, and `runtime-launcher-build`. J.0 offline plans remain
`runtime_installable=false`. Runtime bundles use a separate artifact type.

Focused command:

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.synthetic.test_addon_collection_runtime tests.synthetic.test_addon_sdk tests.synthetic.test_addon_sdk_project tests.synthetic.test_addon_sdk_runtime tests.synthetic.test_addon_sdk_j2_composition tests.synthetic.test_j2_frontend_reentry -v
```

Result: **63 passed, 0 failed, 0 errors, 0 skipped**.

The same focused module command was also run from an extracted source-only
review archive: **42 tests, 40 passed, 0 failed, 0 errors, 2 skipped**. The
two skips require the intentionally excluded retail executable and verified
J.1 runtime bundle. The archive includes the non-proprietary derived JSON
fixtures read by the other focused tests.

Full suite:

```powershell
$env:TEMP='<approved writable temporary directory>'
$env:TMP=$env:TEMP
$env:TMPDIR=$env:TEMP
$env:PYTHONPATH='src'
python -m unittest discover -s tests/synthetic -v
```

Result: **431 tests: 429 passed, 1 failed, 1 errored, 0 skipped**. Both
remaining cases are Windows sandbox filesystem restrictions in existing tests
outside J.3-B:

- `test_single_file_writes_valid_dx_and_machine_report` — the child process
  received `WinError 5` while atomically replacing a temporary DX file.
- `test_stage_builds_self_contained_package_and_drops_profile_state` —
  `Path.resolve(strict=True)` received `PermissionError: [WinError 5]` on a
  test symlink/source fixture under `.research-output`.

No tests were weakened and neither path is used by the collection compiler.
Full output is archived with the source review package.

Other checks:

| Check | Result |
|---|---|
| `python -m compileall src tools tests` | PASS |
| `git diff --check` | PASS; only existing LF-to-CRLF working-copy notices |
| J.0 reference plan | PASS; SHA256 `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`; still `runtime_installable=false` |
| J.1 parent | PASS_STATIC_RUNTIME_BUNDLE; 246 operations |
| Corrected J.2 candidate | PASS_STATIC_J2_REENTRY_BUNDLE; 248 operations; preserves `C7 46 18 07` |
| J.3-B reference pair | PASS_STATIC_COLLECTION_RUNTIME_BUNDLE; RVP `44c139de5b211947857bcb4e70ac84a6b9f1adc23cc9b0fe2a520978a5282f5a`; image reconstruction exactly matches J.2 |
| GlacierSprint bundle | PASS_STATIC_COLLECTION_RUNTIME_BUNDLE; 247 operations; 187 resources; runtime remains unqualified |
| Fresh runtime-compiler rebuilds | PASS; reference pair and GlacierSprint regenerated identical plan, native operation, reconstructed-image, and resource-index hashes |
| GlacierSprint launcher | MSVC 19.50.35729.0 build PASS; launcher SHA256 `f93cb2c1dc92285fb268a99ff462dce63276c0be772fbba41be653fc6f473d1b` |
| Native launcher `--verify` | PASS; 187 resource files and 247 native operations |
| Wrong executable negative test | PASS_FAIL_CLOSED; pristine retail SHA remains unchanged |
| ID27/T2-only negative test | PASS_FAIL_CLOSED; no output bundle and no implicit Mercedes |

## Evidence boundary and current status

J.3-B has a statically compiled and native-preflight-verified candidate for
the exact ID26/T1 plus ID27/T2 layout. The two-addon reference output preserves
the closed J.2 patch semantics. The custom GlacierSprint identity has not been
run in-game; no rendering, physics, AI, re-entry, or gameplay result is claimed
for it. J.3-B is **READY FOR HUMAN RUNTIME**, not `CONFIRMED_BY_RUNTIME`.

The compiler does not claim arbitrary addon layouts or arbitrary-N runtime
support. A T2-only manifest collection is intentionally rejected. J.3-C is not
started and no public release is claimed. Use
[`runtime-handoff.md`](runtime-handoff.md) for the exact candidate and test
sequence.
