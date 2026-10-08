# J.1 Observatory Live-Memory Review

This source-only review package records Observatory's exact live verifier for
the J.1 in-memory hardened native Dump walker. It separates static
compatibility evidence from the still-pending Windows live capture.

## Reproduce the focused mock-memory checks

Extract the archive so `tools/runtime`, `tests/synthetic`, and
`research/general-re/observatory-j1-live-memory` are at the archive root. With
Python 3.11 or newer, run:

```powershell
python -m unittest discover -s tests/synthetic -p 'test_observatory_live_memory.py' -v
python -m compileall tools/runtime tests/synthetic
```

The focused test uses only the Python standard library and the included
bounded mock-memory fixture. It does not require Windows, a game executable,
game assets, a capture, or process access.

## Repository-level validation

In the complete Observatory source checkout, run:

```powershell
python -m unittest discover -s tests/synthetic -v
python -m compileall src tools tests
git diff --check
python tools/build_observatory_release.py --output dist/observatory/j1-live-memory
```

The full suite also covers other project modules and therefore requires the
complete checkout. The exact run command, output, counts, Git state, and
changed-file summary are stored in `test-report.txt` and `project-metadata.json`
inside the review ZIP.

## Evidence boundary

`exact-build-compatibility-report.json` audits a deterministically
reconstructed analysis image. That reconstruction is not a launched EXE and
is not included. `LIVE NATIVE DUMP PASS` remains pending until a human confirms
Status against J.1 `--integrated` and captures a fresh normal-race native Dump.

No Observatory process-memory write or injection is implemented.
