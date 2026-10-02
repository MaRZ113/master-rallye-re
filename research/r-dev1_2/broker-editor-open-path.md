# Retail Broker Editor open path

## Command and opener

```text
main WM_COMMAND dispatcher 005B0990
  command 0x27
    → Broker Editor opener 0065E990
      → activate existing HWND, if present
      → otherwise create the window and controls
      → register __NO_SAVE and __NO_CHANGE key IDs
      → create/attach local menu and title
      → enumerate broker entries into the UI
      → finish window setup and show
```

`0065E990` is also called by the lifecycle restore path `005AF9F0`; that does not add a second command ID. Its duplicate-window branch activates an existing HWND and returns before registration/population.

The owner object is constructed during application initialization by `0065E650`. Its startup constructor references `DataEditors/BrokerEditorHelpInfo.txt` and uses the generic resource reader; this is a resource read, not a write. It is separate from the first-window command path.

## First-open side effects before user interaction

| Step | Function(s) | Effect | Class |
|---|---|---|---|
| resolve shared manager | `004D8EC0` | return or lazily initialize the shared manager shell and linked-list sentinel | `EDITOR_BOOKKEEPING` / `BROKER_METADATA_ONLY` |
| register `__NO_SAVE` | `004D54A0` with string-ID object `0070AEE8` | deduplicate or append one interned key-ID node | `BROKER_METADATA_ONLY` |
| register `__NO_CHANGE` | `004D54A0` with string-ID object `0070AEEC` | deduplicate or append a distinct interned key-ID node | `BROKER_METADATA_ONLY` |
| create UI | `0064EF10`, `0067F700`, `00680250`, `0065EEB0`, and window helpers | create window/controls/menu/title | `UI_ONLY` |
| populate rows | `0065F9A0`, `0065FA20` | walk the manager's typed-entry vector; skip observed type `0x0c`; read values and send list/tree-view messages | `UI_ONLY` / `BROKER_METADATA_ONLY` |
| show/finish | window helpers in `0065E990` | finish control setup and display/activate the window | `UI_ONLY` |

`004D54A0` operates only on the linked string-ID registry at manager `+0x14`; the typed value vector is separate. The opener/populator path does not call the generic broker setter `004D8000`, nor a serializer, save handler, delete/remove command, or broker edit/commit handler before the first user interaction.

## Write-safety audit of the open-only chain

| Side effect sought | Static result |
|---|---|
| `CreateFile` with write access / `CREATE_ALWAYS` | no write-capable open on the mapped first-open chain |
| XML serialization or save writer | not called |
| broker value setter / generic typed broker write | not called; `004D54A0` only adds string-ID metadata |
| `Progress` mutation | no setter path observed |
| `Vehicle` mutation | no setter path observed |
| `Race` mutation | no setter path observed |
| `Scene` mutation | no setter path observed |
| `Editing/EditorsOpen` | not updated by Broker Editor open/close paths |
| in-memory metadata change | yes; two reserved-looking key IDs may be appended to the process-global list |
| resource read | Broker Editor help resource is referenced by owner construction; no write is involved |

The absence conclusions are scoped to the command → opener → constructor/control population call graph before user interaction. They do not cover Commit Changes, Save Game/Options/Player State, or any local edit/remove/update menu action.

## Safety decision

**LOW_RISK_BUT_METADATA_MUTATION.** Opening does not write disk or typed broker values on the mapped path, but it can append two string-ID nodes to shared global metadata. The exact policy meaning of those labels remains unresolved, so an open is not described as strictly read-only. The controlled human test is permitted only with the separate stronger confirmation phrase in `tools/runtime/dev_command_trigger.py`.

No human runtime test has yet been performed. The helper was not invoked during this analysis.
