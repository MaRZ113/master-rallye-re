# Future project-derived identities — design only

No Registry Expansion, patching, persistence activation or manifest enrollment is
implemented here. Arbitrary third-party manifests are never authorization.

Proposed later provenance: a trusted project patcher starts from a verified base
profile and emits source_sha256, output_sha256, output_size, base_observatory_profile,
patcher identity/version, exact patched ranges and an explicit check that
Observatory-sensitive ranges remain unchanged. Those ranges must cover logger
global references, sink vtable and methods/object layout, the main and local
command dispatchers, window/menu identity code and any relevant relocations.

A maintainer independently verifies the manifest against both actual inputs,
reviews overlaps and dependencies, then enrolls one exact output identity. The
runtime must still match output SHA256 and size before inheriting base addresses.
Changed PE layout or sensitive ranges demand a new static profile audit. An
unsigned/user-provided manifest alone cannot grant runtime acceptance. No
--force, --allow-any-exe, signature-only or filename-only acceptance is proposed.
