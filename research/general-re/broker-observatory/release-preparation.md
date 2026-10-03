# Observatory beta release preparation

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
Ghidra data or third-party packages are included. No LICENSE was present; no
license was invented. See the packaged notice before publication.

UX changes: concise startup/status/capture, normal timeout processing message,
verbose/debug diagnostics, installation show/change/clear/reset, first-run setup,
pair-integrity errors and diff counts/labels. Same-second history ambiguity found
in the portable check was fixed with microsecond creation metadata. Schema v1
retains legacy compatibility and adds optional tool_version. Existing observations
and captures remain unchanged; runtime confirmation is recorded separately.

Validation: 302 synthetic tests PASS, zero failures/skips; compileall src/tools/
tests PASS; git diff --check PASS. Tests cover UX, timeout/provenance, corrupt
config/pairs, allowlist/staged guard, deterministic bytes and manifest integrity.
The portable archive was extracted to a system temporary directory outside the
repository and exercised with version, offline latest, diff and config show.
No live game command or persistence experiment was executed by the assistant.

Pre-publication check: inspect manifest/notice; settle project licensing; extract
ZIP into a fresh writable folder, perform installation/setup and two ordinary
captures plus diff; review privacy before sharing. The capture workflow itself
is already CONFIRMED_BY_RUNTIME; beta UX/package Windows smoke is distinct.
