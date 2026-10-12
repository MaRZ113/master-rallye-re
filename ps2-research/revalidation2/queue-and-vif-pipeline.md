# Queue, packet and submission chain

## From a mesh to a queued record

The mesh callback at `0x003bca80` sends its runtime mode/bucket and texture
handles through the shared path. `0x0031d250` constructs a compact key from
material/texture fields and appends the group to queue vectors. The R5900
three-operand MULT at `0x0031d70c` is part of the 12-byte bucket-record index
calculation.

## Drain scope

`0x0031cd98` iterates the bucket vectors in ascending bucket order during one
drain. Bucket 0 contains the traced `tree`/ordinary object categories; bucket
1 contains the traced `treeblend` category. The drain invokes the shared
packet/state paths for each queued group and clears the groups after
submission. Thus **bucket 0 precedes bucket 1 within this drain call**.

Two direct route functions call dispatcher `0x003302b8`: route A at
`0x0032ff28` calls it unconditionally; route B at `0x003301c8` calls it when
its comparison field changes. The dispatcher walks two arrays and invokes
visitor `0x00330780`. The visitor loads an object vtable from `+0x148`, loads
slot `+0xb4`, then makes an indirect `JALR` at `0x00330d04`. The vtable slot
at `0x004854a4` holds the queue drain target `0x0031cd98`.

The ancestry ends at these routes. The static trace does not prove how often
the dispatcher runs per frame, which exact route handles the France1 bush,
or whether the bucket drain is the only world pass. It does not prove that
bucket 1 is after every opaque terrain draw in the whole frame. No distance
sort is shown in the traced drain.

## CPU packet to VU/GIF contract

The existing TREEBLEND1 static evidence connects the selected material mode
to a shared VU path:

* `0x0031c438` is a code anchor for committing dirty GS templates and
  selector state; Ghidra did not assign a standalone function boundary at
  this interior address.
* `0x0031af50` prepares the selector upload; tree modes select the common
  selector route.
* `0x0031d7c8` references cached vertex qwords and issues REF/UNPACK/MSCAL;
  `0x0031e010` adds a DMA CALL for cached chains.
* The embedded VU program is uploaded by the init-to-upload chain documented
  in TREEBLEND1. The regular path emits STQ/RGBAQ/XYZF2 and XGKICK at microPC
  `0xfa`; a shared flush path uses microPC `0x3d7`.
* `0x00316b88` / `0x0030ea80` produce VIF1 DMA submissions, including QWC at
  `0x10009020`, TADR at `0x10009030`, and CHCR at `0x10009000`.

These are static executable and embedded-program contracts, not proof of
live micro-RAM contents or the exact packet used in a specific PS2 frame.
There is no PCSX2 runtime capture in this phase.

## Evidence boundary

```text
PSM treeblend material -> callback mode 2 / bucket 1       CONFIRMED_BY_BOTH
queue record -> ascending bucket drain                     CONFIRMED_BY_EXE
VU upload producer -> embedded program bytes               CONFIRMED_BY_EXE
CPU REF/UNPACK/MSCAL + output packet contract               CONFIRMED_BY_EXE
live micro-RAM residency for France1 frame                  UNKNOWN
global opaque-before-transparent ordering                  UNKNOWN
```
