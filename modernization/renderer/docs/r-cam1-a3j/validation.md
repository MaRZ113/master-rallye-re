# R-CAM1-A3j validation

## Static validation

- Pristine retail `MRallye.exe` identity — PASS: SHA-256 and PE32/I386 metadata recorded in [evidence-map.json](evidence-map.json).
- Ghidra — PASS: exact pristine image analyzed with installed Ghidra 12.1.4 in a temporary project outside the repository. Probes were exported to ignored temporary scratch and Ghidra transactions were rolled back.
- Existing findings — READ ONLY: `research/` and prior R-CAM documents were not edited.
- Scope — PASS: no renderer source, configuration, executable, proxy, or runtime behavior was changed.
- Evidence-map JSON, Markdown local links/whitespace, and handoff ZIP integrity — PASS. The ZIP contains only this phase's three research documents and no binaries.

## Not run

- In-game teleport/undo test — NOT RUN; there is no verified safe production relocation path to exercise.
- Win32 build, CTest, Python suites, proxy verifier — NOT RUN; this phase produced read-only research documents only and did not change implementation.

## Repository record

- Starting branch: `master`.
- Starting HEAD: `676ed24b2d32543c3b9356ed359e280f2b36a309`.
- Starting tree: contained the user's ongoing A3h/A3i renderer changes and documentation; they were preserved and not staged or committed.
- No branch or worktree was created. Nothing was pushed.
- Final checks: `git diff --check` and JSON/archive integrity checks are recorded in the task closeout.
