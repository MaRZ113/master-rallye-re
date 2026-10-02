# Flow Builder open-only safety

## Decision

**SAFE_OPEN_CANDIDATE — open only**, medium-high confidence. This classification applies only to opening the Flow Builder window. Do not invoke any local menu action during the inspection test.

## Retail open chain

```text
main dispatcher 005B0990, ID 0x30
  → opener 00662D90
  → if window already exists, activate it
  → otherwise create application window
  → initialize layout 00663150
  → build local menu 00662FB0
  → show window
```

The layout creates text/controls for `Flow File Name`, `DefaultFlow`, `Delta`, and an eleven-column Speed Matrix. No automatic input-file read, output-file write, cache build, broker registration, reset, or conversion was found on the mapped open-only path. File New/Open/Save/Save As are present but disabled in the local menu.

## Keep these actions out of the test

- Clear / Load Speed Matrix local command `8`.
- Load Speed Matrix local command `9`.
- Convert FL to SFL local command `10`; the converter writes a sibling `.sfl` using `CREATE_ALWAYS`.
- Build commands `0–2`; their mode-dependent generators and output writers are write-capable.

Closing the window normally is allowed. The external `tools/runtime/dev_command_trigger.py` helper is restricted to retail command `0x30`, exact retail SHA256, and an explicit confirmation phrase; do not use it with any other tool.
