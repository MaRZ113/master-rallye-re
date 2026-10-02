# Persistent general RE

This branch is the long-lived home for cross-subsystem executable and runtime
observation tools that do not belong to a narrowly scoped course or vehicle
experiment. Preserve the read-only boundaries and evidence grades of the
existing Master Rallye research.

## Runtime-confirmed embedded tools

| Tool | Evidence state |
|---|---|
| Broker Editor | `CONFIRMED_BY_RUNTIME` — opens and displays live typed broker state. |
| Broker Editor → Debug → Dump | `CONFIRMED_BY_RUNTIME` — previously emitted the large text broker diagnostic. |
| Flow Builder | `CONFIRMED_BY_RUNTIME` — open-only behavior was observed in earlier work. |

The Broker Observatory code itself remains `AWAITING_HUMAN_RUNTIME_VALIDATION`.

## Current tool

[Broker Observatory](broker-observatory/findings.md) parses the game's original
Broker Editor Debug→Dump output and can passively capture the existing retail
Debug text buffer. It does not invoke the Dump command or edit broker values.

Live capture has not yet been exercised against a running game process. The
prepared procedure is in
[runtime-validation-plan.md](broker-observatory/runtime-validation-plan.md).
