# Known unknowns and limits

> **R-BROKER1 update:** original passive live capture is now owner-confirmed;
> automatic fresh-Dump capture remains unrun. Type C is resolved as empty.
> SaveFile/sentinel policy is mapped in [persistence](../persistence/findings.md).
> Scope lifecycle and object-specific serialization limits remain open. The
> list below preserves the original delivery's historical unknowns; use the
> linked R-BROKER1 documents for current status.

- **Live memory layout validation pending.** The reader's object layout and
  vtable are static retail evidence; it has not yet captured a running process.
- **No atomic process snapshot.** The tool double-reads bytes and triple-checks
  pointers without suspending the game. It fails closed when observed state
  changes, but this is not a formal lock.
- **Prior Dump selection.** The original output has no timestamp. The parser
  picks the latest complete block in the current Debug buffer, which can be an
  earlier Dump if the operator does not invoke Debug→Dump immediately before
  capture.
- **Type tag `0x0C`.** `00601D00` skips it. No output parser can recover those
  omitted manager rows from the text dump.
- **Numeric precision.** Float, vectors, and matrices are emitted to two
  decimal places. Underlying full-precision values are unavailable here.
- **Scope identity.** `ID=` prints a scope label selected from the entry's
  scope tag. The row does not expose a separate numeric interned key ID.
- **Unrecognized dump formats.** An unknown typed row intentionally makes the
  parser reject the block. Its raw sidecar is kept during live capture; add
  parser support only after comparing the new form against the executable.
- **ANSI decoding.** Raw bytes are always retained exactly. The current text
  view decodes with cp1252 and reversible surrogate escapes; a non-1252 Windows
  active code page may display some non-ASCII game strings differently.
- **Ring/truncation behavior.** Static evidence shows a growable allocation and
  a large-size guard, but no runtime test has established what happens at that
  guard or after unusually long Debug sessions.
- **SaveFile semantics.** Prior owner runtime evidence associates `__NO_SAVE`
  with transient entries, but this phase has not proved the serialization
  policy in code. `__NO_CHANGE` was visible as a selectable pseudo-value; its
  effect remains unknown. `__IGNORE` has not been established as a runtime
  SaveFile registry entry. The text and parser preserve labels exactly.
- **Broker Editor mutations.** This utility neither opens the editor nor tests
  Commit Changes. The editor's open-time metadata registration remains as
  documented in R-DEV1.2.
- **Game-state differences.** Human-observed entry counts vary by state. The
  first frontend/race comparison is not authorization to investigate race
  participants, mixed-class behavior, or XmlData internals in this task.
- **XmlData object contents.** Runtime UI evidence shows `CarN` and
  `Drivers/DriverN` XmlData leaves with class-name labels, not expandable
  subtrees. The parser retains emitted text only; it does not inspect object
  memory or synthesize child broker paths.
