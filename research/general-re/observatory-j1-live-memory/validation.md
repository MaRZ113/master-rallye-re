# Validation — Observatory J.1 Live-Memory Compatibility

## Static and mock-memory evidence

The focused suite uses a compact text fixture reconstructed from the exact
retail file and J.1 patch manifest. It does not load or ship a game EXE, game
assets, Broker capture, or process dump.

Required mock-reader cases:

- Exact stock walker accepted with Results safety false.
- Exact J.1 walker and both exact trampoline targets/instruction hashes
  accepted.
- One-byte walker mutation rejected.
- Changed hook/trampoline destination rejected.
- One-byte trampoline mutation rejected.
- Missing/unreadable trampoline rejected.
- Wrong/unknown executable identity rejected.
- Wrong mapped PE base, size, or header bytes rejected.
- Unrelated required Broker anchor mismatch rejected.
- Mutated pinned trampoline reference rejected.

## Live-only gate

The above tests do not exercise Windows `ReadProcessMemory`, a running J.1
loader, an Observatory connection, actual Broker Dump dispatch, or race/Results
gameplay. The following remain **NOT RUN** until human validation:

- J.1 live status recognition.
- Fresh normal-race native Dump.
- ID26/ID27 values in that live Dump.
- Optional Results-screen native Dump.
- No-crash and unchanged on-disk EXE confirmation after exit.

The exact command outputs and final counts are stored in `test-report.txt` and
included in the source-only review archive.

## Static compatibility closeout

On 2026-10-08, the complete synthetic suite passed **607/607** tests with
**0 failures, 0 errors, and 0 skipped**. The focused live-memory,
compatibility-auditor, and build-profile suites passed **33/33**; the
three affected status/capture UX modules passed **70/70**. `compileall` and
`git diff --check` passed. The source-only review archive was extracted and its
focused J.1 verifier passed **10/10** and its changed capture/status suite
passed **70/70** from the archive itself.

The exact retail executable in the research corpus was rehashed as
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
(3,121,214 bytes). The J.1 native patch bundle verifier returned
`PASS_STATIC_RUNTIME_BUNDLE`, preserving addon-plan SHA256
`357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`, patch
manifest SHA256
`78c1070f2e656677f02d22f5d4fdff457e43c7ba74c67bb4e5a5c1488ca53179`, and
reconstructed analysis-artifact SHA256
`dd03adbd9f45c679e59d09e0a9f09337bd99c787d81f4ce018edb654c1cec881`.
The reconstructed file is not a launched executable. The detailed commands,
sanitized test transcript, and verifier output are in `test-report.txt`.

Result: **STATIC COMPATIBILITY PASS**. The Windows live process check,
normal-race native Dump, ID26/ID27 Broker contents, and post-exit on-disk hash
remain **NOT RUN** pending the human runtime handoff. Results-screen safety is
not authorized until the active process reports the fully verified hardened
variant.

The standalone Observatory 0.2.2-beta release builder also passed and emitted
a 14-file candidate ZIP with SHA256
`b9ffa53d1a119f8c6cfad752a115688827658a7fa5ecd6274518b96c90c1ae31`.
It contains no game executable, game assets, or repository dependencies.
That candidate was staged into the requested Observatory folder after all 14
existing package files matched the verified pre-update backup. Every installed
file then matched the release manifest; `observatory-data` and captures were
left untouched. The installed package returned the expected 0.2.2-beta
version, and its verbose Status command ran with no game process attached.
