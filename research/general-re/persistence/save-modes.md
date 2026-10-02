# Actual save modes and command mapping

`CONFIRMED_BY_EXE`: main dispatcher `005B1370`, save helpers `005B16C0/005B18A0`,
`005229B0`, generic filter `005FE460`, per-entry serializer `005FE580`.

| Mode | Entry selection | Developer command | Typical target |
|---|---|---|---|
| 0/internal | all nonempty entries, no save-bit/group filter | no observational helper route | in-memory temporary Broker XML |
| 1/Game | Game bit 1 **and** SaveFile equals requested group | 0x33 all groups; 0x34 SaveGameAs | `DataGame/<group>.xml` |
| 2/Options | Options bit 4, all SaveFiles/scopes | 0x35 SaveOptionsAs | normal gameplay `DataGame/options.xml`; dialog-selected basename for developer path |
| 3/PlayerState | PlayerState bit 2, all SaveFiles/scopes | 0x36 SavePlayerStateAs | normal gameplay `DataGame/PlayerState.xml`; developer-selected basename |
| 4/PS2-labelled alternate | Game bit 1, excluding XmlFilename tag B | 0x37 | dialog-selected DataGame XML |

Every mode excludes type C. Scope and revision are not filter predicates.
Mode 4 must not be called equivalent to mode 3 simply because its UI title
mentions player state. Its purpose beyond the recovered filter is UNKNOWN.

`005B16C0` refreshes the registry and separately excludes __NO_SAVE/__NO_CHANGE
before issuing mode-1 saves. It also invokes the GameParticles side path
`005B1C10`; a whole Game save has broader effects than one Broker XML group.

`005B18A0` normalizes a user-selected DataGame filename, strips the prefix and
extension, and delegates according to mode. SaveGameAs can **retag live groups**
through `004D5400` before saving. “As” is not guaranteed copy-only behavior.

Normal gameplay callers use logical options/mode 2 and PlayerState/mode 3.
Mapped PlayerState callers include `004501D0`, `00450310`, `004841B0` and
application call sites `005B0505/005B0526`. The latter enclosing function boundary
is not confidently named. None of these commands was invoked in this phase.
