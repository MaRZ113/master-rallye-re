# Debug→Dump call path

## Static route

```text
Broker Editor menu builder 0065EEB0
  creates Debug → Dump, local command ID 2
        ↓
Broker Editor window/event dispatch 0065EC40
  case 2
        ↓
manager accessor 004D8EC0
        ↓
Dump enumerator 00601D00
  walks the manager's active 0x1C-byte entry array
        ↓
formatted logger 004D0620
  formats into the process Debug sink
```

**CONFIRMED_BY_EXE.** The Debug→Dump menu item and handler agree with the
existing retail menu reconstruction. `0065EC40` case 2 obtains the shared
broker manager via `004D8EC0` and calls `00601D00`. The dump routine then
iterates entry records and formats them through `004D0620`; this route does
not call a file serializer.

## Row construction

`00601D00` reads the typed entry vector begin/end/capacity and advances by
`0x1C` bytes. The observed fields include the type at `+0x08`, save-mask bits
at `+0x0C`, revision at `+0x10`, scope tag at `+0x14`, and SaveFile string ID
at `+0x18`. The path/key ID at `+0x00` is resolved to text for the row. This
is consistent with the pre-existing broker-entry layout reconstruction in
`research/r-exe1/findings.md`.

For each printed row the format contains:

```text
[Rev=n] [ID=<scope label>] [Save: S=T/F, O=T/F, PS=T/F] [SaveFile=name] path (Type) = value
```

Save-mask mapping from the retail instructions is `S=bit 0`, `O=bit 2`, and
`PS=bit 1`. Scope tags 0 and 1 print as GLOBAL and SCENE; other values use the
USER-formatted path. The broker diagnostic skips type tag `0x0C`. Float,
vector, and matrix output uses two decimal places. Matrix and StringList
values span continuation lines; `xmlData` may invoke a type-specific display
path. The Observatory preserves these lines verbatim as emitted.

After the rows, the routine prints GLOBAL/SCENE/USER/TOTAL counts, closes the
broker block, then prints the SaveFile-name list. A candidate snapshot is
accepted only when the row total and scope totals agree and the named file
list has its declared number of lines and closing brace. From a rolling Debug
buffer the parser selects the latest such complete block and records any
incomplete newer candidate.

## Output route

The formatter `004D0620` dispatches formatted lines through the active sink
pointer at `006F7B7C`. Startup can install a proxy sink; its append slot calls
`OutputDebugStringA` and forwards to its downstream sink. With the Debug window
active, the application-owned Debug sink receives the output. The sink's
owner-drawn window paints its existing text buffer; it is not a standard Edit
control and the Debug→Dump handler itself does not open a text file.

The direct read path and object checks are detailed in
[capture-architecture.md](capture-architecture.md). Absence of a writer in
this mapped call path is a static call-graph finding, not a claim that the
whole application can never write unrelated files.

## Evidence boundary

- **CONFIRMED_BY_EXE:** retail menu builder, event case, manager accessor,
  enumeration formats, 0x1C stride, save-bit mapping, and logger dispatch.
- **CONFIRMED_BY_RUNTIME (previous owner observation):** the menu command
  produced a large visible text dump with the example row and state counts
  recorded in `findings.md`.
- **UNKNOWN:** actual live buffer capture consistency on the user's Windows
  process; interpretation of the display label for nonstandard scope IDs;
  full-precision numeric values hidden by the diagnostic's formatting.
