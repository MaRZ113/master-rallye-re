# R-BROKER1 Observatory automatic-capture hotfix

> Subsequent status: **CONFIRMED_BY_RUNTIME**, including six consecutive
> timeout-recovery captures. See [runtime confirmation](runtime-confirmation.md).
> The failed session and delivery-time validation notes below are historical.

## Reported runtime failure, 2026-10-03

The owner reported a pristine retail session starting with Broker closed,
Debug used 0.04 MiB/capacity 0.06 MiB and three captures. After capture attempts,
Broker was open, Debug used 5.61 MiB/capacity 8.00 MiB, but still three captures.
The frontend raised `Broker Dump command timed out; it may still run. No retry
was sent.` No new raw/JSON pairs were published.

This is owner-reported runtime failure evidence, not a successful hotfix test.
Buffer growth supports execution of the original Dump, but does not alone prove
a new complete block or its freshness. No runtime action was performed by the
assistant for this hotfix.

## Root cause: SOURCE_EVIDENCE

`capture_fresh()` called `send_broker_dump()` before entering its polling loop.
The sender raised RuntimeError for every zero SendMessageTimeoutW result,
without examining LastError. A slow original Dump could therefore continue in
the receiver while the frontend had already aborted before observing its output.

## Dispatch contract and fix

The recipient identity checks, Broker-local WM_COMMAND 2, flags and 10000 ms
SendMessageTimeoutW timeout are unchanged. The sender clears ctypes LastError
before the use_last_error=True call, sends once, then distinguishes:

| Result | Action |
|---|---|
| nonzero | return `COMPLETED_SYNCHRONOUSLY`; poll for fresh output |
| zero, ERROR_TIMEOUT (1460) | return `TIMEOUT_COMPLETION_UNCERTAIN`; warn and poll |
| zero, another nonzero error | raise WinError immediately |
| zero, LastError zero | raise generic dispatch failure immediately |

The last case follows [Microsoft's SendMessageTimeoutW contract](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendmessagetimeoutw):
the function does not always set LastError on failure. A zero code must not be
invented into ERROR_TIMEOUT or successful delivery. Timeout also does not promise
the receiver will finish; the complete-block observation is the success gate.

The coordinator has a 120-second default **post-dispatch** polling window,
starting after the synchronous call returns. Neither this loop nor the sender
resends the Dump. Real dispatch errors stop before polling. Successful capture
still requires current buffer to start with baseline and selected complete-block
offset >= baseline length. Failure publishes nothing.

Snapshot source metadata records `dump_dispatch=completed_synchronously` or
`send_timeout_then_fresh_dump_observed`, the dispatch Win32 error and baseline
proof. Manual Dump retains a separate `manual_original_menu` provenance.

## Passive recovery

`mr_observe recover [label]` verifies/selects retail using the existing discovery,
then only reads the Debug buffer. It sends no opener or Dump, selects the latest
complete block and preserves the full raw buffer. The same checked new-file-only
pair writer is reused. With no complete block, nothing is published.

Metadata explicitly records `freshness=not_command_proven`,
`dump_request=none-passive-recovery` and `dump_dispatch=not_sent`; the console
also warns that the salvaged Dump may be old. Recovery is not the normal capture
path and does not establish baseline freshness.

## Synthetic validation and runtime gate

Required cases cover synchronous completion, timeout followed by later complete
output, incomplete-to-complete output after timeout, timeout with no fresh block,
non-timeout dispatch error and persisted timeout provenance. Dispatch count is
one. Additional checks cover zero LastError generic failure, manual no-dispatch,
recovery without commands, latest-complete selection/full raw preservation and
recovery rejection without complete output.

Validation performed: frontend suite 35 tests PASS; command-trigger suite 16
tests PASS; full synthetic suite **277 tests PASS**. `compileall -q src tools
tests` and `git diff --check` pass. Window/process operations in the synthetic
tests are mocks; no live game command was sent by these checks.

New Windows automatic capture remains **AWAITING_RUNTIME_VALIDATION**.
Retest in the same disposable pristine retail install: salvage the existing
session first if needed, then request one labelled normal capture, allow polling
to finish and inspect the pair/provenance. Do not request another Dump while
waiting, edit Broker values or invoke persistence commands.

No architecture research, process memory write, injection, executable patch,
native save, new branch/worktree or push is part of this hotfix.
