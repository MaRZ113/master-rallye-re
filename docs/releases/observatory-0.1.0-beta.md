# Master Rallye Observatory v0.1.0-beta

First public beta of the runtime-confirmed observability workflow.

## Quick Start

1. Extract the release ZIP to a writable folder.
2. In your own `DataGame/dev.xml`, set `Menues/Enabled=True`.
3. Start pristine retail Master Rallye.
4. Run `MRallye-Observatory.cmd`.
5. Capture a game state, then compare snapshots with `Diff Last Two`.

This v0.1.0-beta release supports pristine retail only. It is not replaced by
the unpublished v0.2.1-beta candidate.

## What it includes

- Automatic discovery and exact verification of pristine retail.
- Broker Editor opening/reopening and original Debug→Dump automation.
- Read-only Debug-buffer capture, including realloc and multiple Dumps.
- Fresh-block proof and timeout recovery without automatic resend.
- Checked JSON/raw pairs, automatic naming/history and semantic snapshot diff.
- Simple installation setup, concise status/errors and revision-only filtering.
- Passive recovery and offline persistence metadata reports.
- Portable Python ZIP; no full research repository or third-party packages needed.

Pristine retail only. Diagnostic float precision and omitted empty slots follow
the original game output. This is an observability/research tool, not a gameplay
trainer or save editor. Review captured paths/state before public sharing.

The existing core/frontend workflow was runtime-confirmed in six consecutive
captures; all six recovered from dispatch timeout before observing fresh complete
Dumps. The final portable Windows live smoke outside the research repository
also passed: two 6923-entry captures, fresh-Dump proof across buffer realloc and
semantic diff showing only normal revision noise. The package is MIT licensed.

Local preparation only: no tag, GitHub Release or upload is created by the builder.
