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

The original passive Broker Observatory reader is now `CONFIRMED_BY_RUNTIME`
from owner-provided captures and observations (large Dumps, realloc, multiple
complete blocks, XmlData continuations). The automatic frontend is also
`CONFIRMED_BY_RUNTIME`; see [six-capture confirmation](broker-observatory/runtime-confirmation.md).

## Current tool

[Broker Observatory](../../docs/broker-observatory.md) has a one-command frontend:

```powershell
python tools/runtime/mr_observe.py
```

It discovers verified retail, opens the reviewed Broker window when needed,
requests original Debug→Dump, requires a new complete block and stores checked
raw/JSON pairs. The previous low-level passive reader is reused and remains
available. No edit/commit/save/gameplay commands are exposed.

## R-BROKER1 architecture

- [Broker core](broker-core/findings.md): indexed entries, type/ownership,
  scope boundaries and revision.
- [XML core](xml-core/findings.md): typed loading, XmlData factories,
  XmlFilename dependencies.
- [Persistence](persistence/findings.md): mode filters, logical SaveFiles,
  native `#` backup/write chain and reload.
- [U1–U4 plan](persistence/runtime-validation-plan.md): U1 observation confirms
  race SCENE survives RaceRetry/QuickRace/GameSelect; U2–U4 remain unexecuted.
  No persistence experiment was executed by the assistant.

Overall R-BROKER1 is **PARTIAL** until the remaining scope lifecycle
gates close. Do not advance to unrelated RE phases from this result.
