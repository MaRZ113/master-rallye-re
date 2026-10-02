# Command sender audit

## Result

The binary maps commands into the main dispatcher but the in-binary sender that should create the original `WM_COMMAND` is missing from the recovered paths. The main window procedure forwards `WM_COMMAND` to the large dispatcher; xrefs show no other direct code caller of that dispatcher in each build. Every global tool command ID examined is absent from the main menu builders and from the PE dialog control IDs. No accelerator resource or accelerator/hotkey translation route was found.

This supports **D — HANDLER_PRESENT_BUT_ORIGINAL_SENDER_UNKNOWN** for the hidden global tool commands. It does not establish that no external development harness existed.

## Sender classes checked

| Class | Evidence and conclusion |
|---|---|
| Main native menu | Each build creates only `Game → Reset… / Exit`. The global editor, BuildData, and Game/Scene file IDs are not inserted. |
| Other native menu roots | Six tool/editor menu roots are present, in addition to the main root. They appear on their own tool windows and use local menu IDs. They cannot explain how the parent window was first opened. |
| PE MENU / ACCELERATOR | No `RT_MENU` or `RT_ACCELERATOR` resource exists in any EXE. Menus are built dynamically. |
| Dialog controls | All four builds have 24 dialog templates. No control uses any ID in the inclusive `0x26–0x58` range, covering the hidden editor, generic editor, Game/Scene I/O, and BuildData commands. |
| Accelerator/hotkey APIs | No xrefs to `CreateAcceleratorTable`, `TranslateAccelerator`, `RegisterHotKey`, `GetKeyState`, or `GetAsyncKeyState`. Main WndProc has no mapped `WM_KEYDOWN` / `WM_SYSKEYDOWN` route. |
| Message construction | `SendMessageA` has many call sites, chiefly control/list interactions. Search of constant and nearby dataflow candidates found no construction of `WM_COMMAND (0x111)` with a hidden opener ID. `PostMessageA`/`PostThreadMessageA` do not provide an evidenced hidden opener route. |
| DirectInput | Game input is present, but no dataflow from key state to the tool command switch was established. No shortcut claim is made from virtual-key constants alone. |
| External sender | A separate launcher, development harness, debugger, or another process sending a window message is outside these EXEs; none is evidenced by current data. |

## Coverage limit

The search combined API xrefs, direct switch cases, menu construction, dialog resource IDs, `WM_COMMAND` handling, and immediate/dataflow review of message calls. It is a strong negative within the analyzed binaries, not a proof that another process or a non-shipped development component never sent the messages.

Machine-readable scope and per-mechanism results: `command-senders.json`.
