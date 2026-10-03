# Observatory beta release preparation

**RELEASE READY — 0.1.0-beta.** Final portable Windows live smoke is
CONFIRMED_BY_RUNTIME; see [runtime confirmation](runtime-confirmation.md).

Public quickstart: [observatory-quickstart.md](../../../docs/observatory-quickstart.md).
Release notes: [beta notes](../../../docs/releases/observatory-0.1.0-beta.md).
Canonical version is tools/runtime/observatory_version.py. Build command:

```text
python tools/build_observatory_release.py
```

The builder requires committed release inputs, rejects forbidden staged file
classes, collects an explicit flat-file allowlist, normalizes line endings and
uses fixed ZIP timestamps/permissions/order. It emits an archive and external
manifest under ignored dist/observatory. The manifest records archive/file hashes,
supported game hash, Python requirement and exact build commit without local
paths. Nothing is pushed, tagged or published.

The portable layout keeps config/captures under observatory-data; repository
layout retains research-output/general-re. No game files, dumps, personal config,
Ghidra data or third-party packages are included. The user selected MIT; LICENSE
uses the neutral holder Master Rallye Refreshed Research contributors (2026).
LICENSE is automatically included by the allowlisted builder.

UX changes: concise startup/status/capture, normal timeout processing message,
verbose/debug diagnostics, installation show/change/clear/reset, first-run setup,
pair-integrity errors and diff counts/labels. Same-second history ambiguity found
in the portable check was fixed with microsecond creation metadata. Schema v1
retains legacy compatibility and adds optional tool_version. Existing observations
and captures remain unchanged; runtime confirmation is recorded separately.

Validation: 306 synthetic tests PASS, zero failures/skips; compileall src/tools/
tests PASS; git diff --check PASS. Tests cover UX, timeout/provenance, corrupt
config/pairs, allowlist/staged guard, deterministic bytes and manifest integrity.
The portable archive was extracted to a system temporary directory outside the
repository and exercised with version, offline latest, diff and config show.
No live game command or persistence experiment was executed by the assistant.

Final portable Windows live smoke PASS: two ordinary captures plus semantic diff
outside the repository; exact details are in runtime-confirmation.md. No further
live smoke is requested: the closeout changes licensing, documentation and early
Python version checks only; capture mechanics are unchanged.

Pre-publication check: inspect final ZIP/manifest/notice and privacy guidance.
Push, tagging and GitHub publication are left to the project owner. No persistence
write experiment is executed or authorized by this release readiness.
