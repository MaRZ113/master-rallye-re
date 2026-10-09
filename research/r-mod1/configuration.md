# R-MOD1 INI contract — version 1

The parser is implemented in `src/native/rmod1/core.hpp`. It is a strict ASCII
parser, maximum 4096 bytes, no BOM or NUL, LF/CRLF only, no inline comments,
no duplicate sections/keys and no unknown keys. A malformed file is rejected
as a whole and replaced by safe defaults; no partially parsed option survives.

```ini
[General]
ConfigVersion = 1

[Randomizer]
Enabled = true
QuickRace = Full
Duplicates = WhenNeeded

[Opponents]
Enabled = true
MaxOpponents = 7

[Addons]
Include = Auto

[Logging]
Enabled = false
```

Defaults when the INI is absent or invalid are: randomizer disabled, Quick Race
policy Stock, opponent extension disabled with a native maximum of three AI,
registered addon entries only, and logging disabled. Diagnostics carry stable
error codes and line numbers.

Supported Quick Race policies are `Stock`, `Full`, `T1`, `T2`, `T3`, `Mixed`
and `Diverse`. `Full` samples the eligible class union; `T1/T2/T3` constrain
physical IDs by registry class, independent of the human class. `Mixed` selects
a class per AI before selecting an ID. `Diverse` cycles a shuffled eligible
class list before beginning another cycle. The native DriverID owner is not in
the selection API.

Stock pools are T1 IDs 0..6, T2 IDs 7..13 and ordinary T3 IDs 14..20. T3 reward
IDs 21..24 require their audited progression bits outside Invitation. ID25 is
excluded because the standalone corpus does not establish a complete portable
model package. Challenge, Cup, Master Rallye, Invitation and Practice remain
native Stock in this first Quick Race-focused implementation.

`Duplicates=WhenNeeded` first avoids the human physical ID when another eligible
ID exists, then chooses unused eligible physical IDs. Only after those are
exhausted may the same physical CarID be selected again. The integration must
still create a separate native participant/controller/physics/progress object
for every AI slot. This pure policy core does not allocate actors.

When randomization is off, the count extension still has a stock-compatible
roster path: for an extended race it keeps the human's class and applies the
same unique-first/duplicate-when-needed policy. This is a separate extender
behavior; enabling the Randomizer is not required to request more opponents.
For counts within the retail limit, disabled/Stock means the native chooser.

`Addons.Include=Auto` does not scan directories and does not load Vehicle SDK.
The core accepts an addon only if an integration adapter supplies a physical ID
already registered in the active game process and confirms class, resources,
physics and Quick Race eligibility. No such provider is implemented here.

Configuration expresses a desired maximum, not a guarantee that every course
can safely start that many participants. The runtime course gate is separate
and fails closed as described in [`grid-safety.md`](grid-safety.md).
