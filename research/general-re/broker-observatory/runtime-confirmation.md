# Observatory workflow — CONFIRMED_BY_RUNTIME

The owner reported six consecutive successful Dumps on pristine retail.
All six followed SendMessageTimeoutW → ERROR_TIMEOUT 1460 → continued original
game processing → fresh complete Dump → successful paired publication.

Confirmed workflow: automatic process discovery/exact retail verification,
Broker auto-open and reopen, original Dump command, timeout recovery without
resend, fresh-block detection, buffer realloc, multiple-complete-block selection,
JSON/raw publication, latest/history and semantic diff.

This supersedes the automatic frontend's pending runtime gate. The earlier
failed session remains documented in automatic-capture-hotfix.md; no prior
observation is rewritten. Timeout is a normal large-Dump path, not an error to
announce during successful ordinary use. Diagnostic provenance stays in JSON.

The new beta UX and portable package are checked synthetically/offline and still
need a pre-publication installation/UI smoke test. No persistence round-trip
experiment or new Broker architecture work is performed in this task.
