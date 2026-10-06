# AI driver and vehicle identity

In `FUN_00458090`, the vehicle ID is first selected from the class candidate
vector and removed from the working list. The function then calls
`FUN_00458980(&local_68)` at `0x00458423` to choose a DriverID. It publishes the
selected CarID beginning at `0x00458428`, derives CarClass from the registry,
and publishes DriverID afterward.

At this call, the driver helper receives a destination for its result; the
selected physical CarID is not passed as a call argument. The static evidence
does not establish an obligatory Mercedes-specific driver mapping. It supports
only the narrower statement that the selected DriverID is produced by a
separate native path after vehicle choice.

The forced ID26 proof changes only the selected-CarID local after the native
driver chooser has completed. It leaves that local DriverID and all native
driver bookkeeping untouched. There is no Mercedes-specific driver in this
phase.

**Evidence:** call order and visible arguments are `CONFIRMED_BY_EXE` from the
current retail Ghidra export and raw code. Full AI personality/skill semantics
and all vehicle-driver combinations remain `UNKNOWN`.
