# Flow Builder safe-open confirmation

## Classification

**SAFE_OPEN_CANDIDATE — open-only.** This is a narrow static confirmation of R-DEV1.1; it does not classify any local tool command as safe.

## Retail route

```text
005B0990 main WM_COMMAND dispatcher, command 0x30
  → 00662D90 Flow Builder opener
  → activate existing window if present
  → otherwise create window/layout 00663150
  → construct local menu 00662FB0
  → finish/show window
```

Static inspection of the opener, layout/menu construction, direct callees, and file API references found no automatic `.fl`/`.sf`/`.sfl` read, cache generation, SFL write, Build/Clear operation, or `CREATE_ALWAYS` output before user interaction. Local File actions are disabled in the constructed menu. The separate file/build commands are not part of this decision.

## Keep out of the human test

- Build command IDs `0–2`.
- Clear / Load Speed Matrix IDs `8–9`.
- FL-to-SFL ID `10`.
- Any New/Open/Save/Save As, conversion, load, save, build, or clear action.

Open, inspect labels/layout, move/resize, and close only. No runtime observation has been made in this phase.
