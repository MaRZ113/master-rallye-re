# Passive capture architecture

## Retail Debug sink layout

The reader follows the logger state and Debug object recovered in the retail
program. Addresses below are preferred-image VAs; the utility computes their
runtime addresses from the loaded module base.

| Item | Preferred VA / offset | Evidence |
|---|---:|---|
| Active logger sink pointer | `006F7B7C` (RVA `0x2F7B7C`) | `004D0620` dispatch and `004D05E0` setter |
| Debug sink vtable | `0069CEA8` (RVA `0x29CEA8`) | `0064E4C0` constructor |
| Debug sink object prefix read | `+0x00..+0x2F` | constructor and append/paint methods |
| Window helper pointer | object `+0x0C` | constructor; helper HWND is helper `+0x04` |
| Visible-text start | object `+0x20` | paint/scroll state |
| Allocation end | object `+0x24` | append growth bounds |
| Buffer base | object `+0x28` | constructor and append method |
| Current write end | object `+0x2C` | append/paint methods |

`0064E4C0` initializes a `0x800`-byte allocation. The append path at
`0064E670` grows it through `005C5B15`; the allocator's realloc/copy branches
preserve the old bytes on successful growth. The sink updates the base/end
pointers after movement. A guard around 100,000,000 used bytes is present in
the append path; the capture reader independently refuses to read allocations
larger than 128 MiB.

The proxy vtable is separate (`00692F68`). Its append method
`005AFE10` calls `OutputDebugStringA` and forwards to a second sink pointer.
The Observatory requires the active pointer to have the Debug sink vtable;
if the game currently routes to the proxy, it refuses capture and asks the
operator to open the Debug window.

The chosen strategy is C2, read-only observation of the persistent Debug
history buffer. The mapped Dump call path has no stdout/stderr, console, or
file writer; the startup proxy can mirror messages to the debugger, while the
active Debug sink retains the owner-drawn window's history. Its dynamically
grown buffer avoids screenshot/OCR line loss. A direct broker-state reader was
not added because the original Dump already supplies the documented typed
projection and a stable textual validation target.

## Read-only checks

`tools/runtime/broker_observatory.py capture` performs these checks in order:

1. Require an explicit PID and Windows.
2. Open the process with `PROCESS_QUERY_INFORMATION | PROCESS_VM_READ`
   (`0x410`). No write, operation, thread, or suspend rights are requested.
3. Resolve the image path and require basename `MRallye.exe`, exact retail
   SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
   and size 3,121,214 bytes.
4. Enumerate loaded modules and find `MRallye.exe` to obtain its actual base.
5. Read the active sink pointer, validate the Debug sink vtable, nested helper,
   live HWND, and buffer pointer ordering/range.
6. Read the full current buffer twice, checking sink/buffer metadata before,
   between, and after the byte reads. The reads must agree. The process is not
   suspended, so this is a stability check rather than an atomic OS snapshot.
7. Write the raw buffer to a user-selected local `.dump.bin` sidecar and parse
   the latest complete Broker Dump block into JSON. If parsing fails, the raw
   sidecar remains available for diagnosis.

The tool prints only capture identity and hashes, not the potentially large
broker values. It never invokes `Debug → Dump`; the operator must invoke that
menu item first. The raw sidecar is the byte-exact text buffer read from the
game, including any surrounding Debug messages and a possible NUL suffix. The
JSON identifies the selected block by byte offset, length, and SHA256.

## Consistency limits

The sink can append while the game is running. Triple metadata reads plus two
identical byte reads reduce the chance of accepting an in-progress append, but
they do not provide a formal atomic snapshot. The reader retries five times
and fails closed if the buffer changes. It also fails closed for an unexpected
vtable/layout, a stale HWND, unreadable pointers, a non-retail process, or an
oversized allocation.

Each capture reacquires the loaded module base, logger global, sink pointer,
helper, HWND, and buffer fields. It retains no remote address across commands,
so a scene reload or sink replacement between snapshots does not reuse the
previous sample's pointers.

The original output can format some values (notably Float, vectors, and
Matrix) to two decimal places. The JSON cannot recover precision that the
game's own Debug→Dump omitted. See [snapshot-schema.md](snapshot-schema.md).
