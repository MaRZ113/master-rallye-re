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

Store the exact command outputs and final counts in `test-report.txt` when the
closeout package is built.
