# Observatory workflow — CONFIRMED_BY_RUNTIME

The project owner reported six consecutive successful Dumps on pristine retail.
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

## Final portable Windows live smoke — PASS

`CONFIRMED_BY_RUNTIME`: the project owner tested the extracted portable package
outside the research repository against clean pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Both `frontend` and `frontend2` record tool version `0.1.0-beta`, 6923 entries
(GLOBAL 6863, SCENE 60, USER 0). No added/removed entries, value, type, scope or
SaveFile changes appeared. Only `Frontend/ButtonPulser/Visible` revision changed
757 → 1167, normal revision-only frontend noise.

Both record `dump_dispatch=send_timeout_then_fresh_dump_observed` and
`freshness=post_baseline_complete_dump_proven`. Debug used/capacity grew from
969367/1048576 to 1899252/2097152 bytes. The second raw buffer starts byte-for-byte
with the complete first buffer; its selected fresh Dump begins exactly at the
previous buffer length.

PASS: automatic discovery, pristine-retail verification, automatic Broker Dump,
timeout recovery, fresh-Dump proof, realloc handling, repeated capture, paired
publication and semantic diff. This closes the portable beta live-smoke gate.
No runtime dumps are committed. No persistence round-trip experiment is claimed.

## U1 lifecycle observation

`CONFIRMED_BY_RUNTIME`: race Broker SCENE state survives `RaceRetry`, `QuickRace`
and `GameSelect`. Therefore SCENE is not the current DataScene XML lifetime.
The exact normal SCENE bulk-clear owner remains `UNKNOWN`; this is not a release
blocker and does not authorize U2 persistence work.
