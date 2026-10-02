# Quick Race localization group 0x35

## Keep three channels distinct

| Channel | Retail evidence | Cleanup behavior |
|---|---|---|
| `0x33` | Vehicle Select lookup at `0x481A10` | Existing ID26 display alias selects donor0. |
| `0x34` | Vehicle Select lookup at `0x481A4D` | Existing ID26 display alias selects donor0. |
| `0x35` | Quick Race lookups in `FUN_0047B040` | New wrapper aliases returned display selector26 to0 at three call sites. |

Ghidra Bridge raw assembly shows the `0x33` and `0x34` pushes in Vehicle
Select. The current ID26 frontend wrapper preserves absolute EDI=26 for record,
stats, preview and resource lookup, while EBX becomes0 only for the two display
pushes. The Quick Race channel is a separate dataflow and needed its own fix.

## Quick Race call chain

In `FUN_0047B040`, the Quick Race code queries the configured Car0/Car1 selector
through `FUN_004ADFB0`, pushes its return value, pushes group `0x35`, and invokes
the frontend localizer. The relevant lookups are:

| Getter call | Following localization group push | Display key flow |
|---:|---:|---|
| `0x47B0AF` | `0x47B0B5: PUSH 0x35` | CurrentVehicleString / Car0 lookup |
| `0x47B13A` | `0x47B140: PUSH 0x35` | second Quick Race vehicle string |
| `0x47B1BA` | `0x47B1C0: PUSH 0x35` | CurrentVehicle2String / Car1 lookup |

The getter's raw string references are `Frontend/QuickRace/Car0` at `0x6E5868`
and `Frontend/QuickRace/Car1` at `0x6E5850`. The UI keys include
`Frontend/QuickRace/CurrentVehicleString` and
`Frontend/QuickRace/CurrentVehicle2String`. These are display paths. The
cleanup patch does not write the configured value or `Race/Car0/CarID`.

The reported runtime error `gaLocal: Can't find id [53]` refers to localization
group 53 decimal (`0x35`); it is not vehicle ID53. The owner reports selector
26 fails in this group. The cleanup wrapper aliases only the getter return
value 26 to display selector0 for these three lookups. All other return values
pass through unchanged.

## ABI-safe wrapper

Raw `FUN_004ADFB0` ends in `RET 4`. At each retail call site, one stack argument
(0 or 1 for the Car0/Car1 lookup) is already pushed, and ECX carries the
receiver. A direct nested call would shift the argument and leak the outer
stack value. The wrapper therefore:

1. copies `[ESP+4]` onto a new stack slot;
2. calls the original getter with the original ECX receiver;
3. lets the getter's `RET 4` consume the copied argument;
4. changes EAX only if EAX is 26, setting it to0;
5. uses `RET 4` to consume the original call-site argument.

Emitted bytes decode as `push [esp+4]; call 0x4adfb0; cmp eax,0x1a; jne
return; xor eax,eax; ret 4`. The three existing direct calls are retargeted to
this wrapper; their group-`0x35` pushes remain unchanged.

This is a display-only patch. Candidate P0 must confirm the Quick Race pre-race
name is valid and no longer displays `GALOCAL UNKNOWN`; this is not yet
human-confirmed.
