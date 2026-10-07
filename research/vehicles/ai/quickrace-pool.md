# Quick Race opponent identity producer

## Call chain and values

The current retail Ghidra export identifies `FUN_0047B780` as the setup owner
that calls the shared pool builder `FUN_00458090` at:

| Call | Caller VA | Role | Evidence |
|---|---:|---|---|
| Split-screen | `0x0047B93D` | starts AI slots after two human participants and passes both human vehicle exclusions | `CONFIRMED_BY_EXE` |
| One human | `0x0047B96E` | starts at Car1, passes player class and Car0 physical CarID, second exclusion `-1` | `CONFIRMED_BY_EXE` |

For the one-human branch, the first `FUN_0047B780` operation reads
`Frontend/QuickRace/Car0`, writes that absolute ID to race Car0, and obtains the
vehicle class from `VehicleRecord[Car0]`. It calculates the active AI count and
passes the selected class and excluded player ID to `FUN_00458090`.

## Pool construction

The function receives the class selector as its third argument, the player
CarID exclusion as the fourth, and a second human CarID (or `-1`) as the fifth.
Its switch directly builds the candidate vector from absolute IDs:

* T1: loop values 0 through 6.
* T2: loop values 7 through 13.
* T3: loop values 14 through 20; append 22, 23, 24, and 21 when their
  corresponding stock progress checks succeed.
* Class selector 4 reaches the same arm as selector 2.

The T1 arm's raw Ghidra listing includes the loop body at `0x00458127` and its
bound/exit at `0x00458162`–`0x00458167`. The T2 loop is at
`0x0045816C`–`0x004581B4`. The T3 loop and optional appends occupy
`0x004581B9`–`0x004582D5`.

No `FUN_0045A150` call or G.1 class-local-to-physical conversion occurs in this
function. The T1 loop stores absolute IDs directly. Consequently ID7 cannot be
used as T1 local7: it is the first T2 physical ID. H.1 appends ID26 explicitly
to this Quick Race pool and is now runtime-confirmed; H.2 uses separate native
append seams for other dynamic roster owners and does not route them through
this function.

## Selection and publication

The source candidate vector is copied/shuffled into a working vector. Each
selected physical ID is removed before the next participant is generated; an
empty working list is repopulated from the original candidate vector. For a
stock one-human T1 race with Car0=ID0, the candidate pool after exclusions is
IDs1–6; three AI participants therefore retain distinct stock IDs during that
pool cycle.

After a CarID has been selected, `FUN_00458980` chooses the driver profile.
At `0x00458428`, the chosen absolute CarID is read from the stack local and
published. The subsequent registry lookup derives CarClass; the driver value
is written through its separate setter. The forced proof works at the gap
between selection/bookkeeping and publication.

## Exact retail identity

The static model applies to pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, 3,121,214
bytes. The existing current-branch Ghidra export is from Ghidra 12.1.4. Hook and
call-site bytes are checked by the fail-closed candidate builder at runtime.

## H.1 natural T1 ID26 inclusion

H.1 branches only the T1 loop exit at VA `0x00458167` through a one-time
append shim. The shim re-enters the stock exclusion/append body for absolute
ID26, then restores the original loop end and exits through the common stock
path. The resulting source set is `[0,1,2,3,4,5,6,26]`; no CarID is forced
into a participant slot. ID7 is not added and remains T2. T2/T3 pool builders,
selection/shuffle logic, DriverID selection, participant count, and all
publication consumers remain unchanged. Byte layout, manifest, and tests are
documented in [natural-t1-pool.md](natural-t1-pool.md).
