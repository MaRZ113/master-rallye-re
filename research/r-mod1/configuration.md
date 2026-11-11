# R-MOD1 configuration and reload contract

The parser is strict ASCII, capped at 4096 bytes, and validates the entire
file before applying any value. Unknown sections/keys, duplicate settings,
unsupported versions, malformed numbers, BOM/NUL/non-ASCII bytes, bare CR and
partial syntax reject the whole snapshot. At initial startup an invalid or
missing file selects safe Stock defaults. During live reload an invalid,
unavailable or changing file retains the last known valid policy snapshot.

## Public ConfigVersion=2

V2 gives every supported mode its own policy. Each `0=Stock` value is that
mode's off switch. The standalone default in
[`MRallyeRandomizer.example.ini`](MRallyeRandomizer.example.ini) is all Stock,
three maximum Quick Race AI, Stock-only eligibility, and logging off.

| Value | Policy | Behavior |
|---:|---|---|
| 0 | Stock | Keep the native class policy. Above the native three-AI ceiling, use the bounded stock-class-compatible class extension; this does not claim vanilla RNG equivalence. |
| 1 | T1 | Restrict AI vehicle eligibility to T1, independent of the player's class. |
| 2 | T2 | Restrict AI vehicle eligibility to T2, independent of the player's class. |
| 3 | T3 | Restrict AI vehicle eligibility to the mode-eligible T3 pool. |
| 4 | Full | Select from the union of verified eligible classes/vehicles. |
| 5 | Mixed | Choose a class first and leave physical CarID and DriverID selection to the native chooser. |
| 6 | Diverse | Use the established shuffled class-cycle policy. |

Full, Mixed and Diverse remain separate algorithms. They are not aliases for
one another. V2 syntax uses numeric selectors; comments in the shipped example
document every field vertically.

`MaxOpponents` is a Quick Race AI ceiling from one through seven, not a fixed
roster size. Three keeps the retail menu ceiling. Four through seven activate
the bounded extended Quick Race path; no hidden V2 enable or experimental key
is required. The opponent extender does not enlarge the other four modes.

`Duplicates=0` means Never and `1` means WhenNeeded. `Addons.Include=0` means
Stock-only; `1` means Auto, which accepts only an explicit verified in-process
provider registration. R-MOD1 has no provider and performs no directory scan,
so Auto currently adds no entries. ID25 remains excluded from standalone
selection because a complete portable model package is not established.

## ConfigVersion=1 compatibility

V1 preserves its historical Quick Race-only schema and semantics, including
the old `Randomizer.Enabled`, `Opponents.Enabled` and
`Experimental.ExtendedAI` switches. Its numeric order differs from V2:

| V1 | Meaning | V2 | Meaning |
|---:|---|---:|---|
| 0 | Stock | 0 | Stock |
| 1 | Full | 1 | T1 |
| 2 | T1 | 2 | T2 |
| 3 | T2 | 3 | T3 |
| 4 | T3 | 4 | Full |
| 5 | Mixed | 5 | Mixed |
| 6 | Diverse | 6 | Diverse |

The parser selects meaning from `ConfigVersion`; a V1 number is never
reinterpreted as V2. Accepted V1 files produce a migration diagnostic. For
example, V1 `QuickRace=1` migrates to V2 `QuickRace=4` for Full. V2 does not
accept the legacy enable/experimental keys.

## Live reload and snapshot lifetime

The runtime rereads the authoritative INI beside the runtime package only at a
new roster-generation boundary. It reads a bounded file twice, requires
identical bytes and unchanged file identity/size/write time, then parses and
validates one whole snapshot. The accepted snapshot's mode policies,
Duplicates value and hash are frozen across every AI callback in that
generation. A half-written or invalid edit does not partially apply.

- Quick Race: a newly generated race reads current policy. Restart/retry keeps
  the native current roster.
- Rallye Cup and Invitation: a new event reads current policy; later stages
  reuse native stored competitors.
- Master Rallye: a new competition reads current policy; save, exit, reload,
  Resume and later stages reuse the native saved roster.
- Challenge: a fresh preview selection reads current policy. The visible
  preview and race use one cached absolute CarID. Editing the INI while the
  preview is visible does not change that identity; Back/reentry creates a new
  selection boundary.

`MaxOpponents`, `Addons.Include` and `Logging.Enabled` are startup-scoped.
Restart the game to change them. Policies and Duplicates are hot-reloaded only
for a later fresh roster. The runtime does not reread the file each frame or
for each AI slot.

## Eligibility boundaries

Stock T1 core is IDs 0..6, T2 is 7..13, ordinary T3 is 14..20. Audited T3
reward IDs 21..24 remain subject to their native progression conditions, but
Invitation deliberately uses only its ordinary T3 pool. Physical ID25 is not
assumed materializable. Player unlock and AI eligibility remain separate.

R-MOD1 still relies on each mode's native physical CarID and DriverID chooser;
the policy callback selects a class where required. No fixed CarN roster or
participant object is created by the Randomizer. Quick Race uses a separate
bounded count subsystem; Cup, Invitation, Master Rallye and Challenge retain
their native roster lifetimes.
