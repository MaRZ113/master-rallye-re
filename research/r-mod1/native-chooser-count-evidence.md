# R-MOD1-E native count and physical chooser evidence

## Scope and confidence

This note records static evidence from the exact pristine retail executable:

`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`

Function exports were generated from the current exact-build Ghidra project
into ignored `scratch_rmod1/ghidra/`. Relevant function records are
`0047b780.json`, `00458090.json`, `004116a0.json`, and `00458980.json`.
This establishes native control flow and byte identity, not successful v12
gameplay.

## Count handoff

`FUN_0047B780` is the mode-2 Quick Race setup owner. At `0x0047B88A` it reads
the selected opponent count; the value plus one is published to
`Race/NumCars` through `0x004AC3D0`. At `0x0047B8DD` it reads the selected
count again. In the one-human path it calls `FUN_00458090` at `0x0047B96E`
with `first=1`, the selected count, the player's class, the player's physical
CarID, and no second excluded player. The SplitScreen path calls the same
chooser at `0x0047B93D` with a different first/count topology.

The v11 runtime pass selected Four and produced five active participants in
the composed R-MOD candidate. R-MOD1-E retains both retail count readers and
does not add the historical R-AI2 count shims. The candidate's Start gate
admits selected counts 4..7 only when the extender and experimental opt-in are
enabled, the requested count is at or below `MaxOpponents`, mode is Quick
Race, SplitScreen is off, and total cars stay at or below eight.

## Physical vehicle and DriverID chooser

Exact native function identity:

- `FUN_00458090`: VA `0x00458090`, end `0x004584D6` (including `RET 0x14`),
  length `0x446`, SHA256
  `2daec5f26455c98bfa399308ce8a3030ebe5871dfe4fd13a675526bb97842a71`.
- `FUN_004116A0`: VA `0x004116A0`, length `0x13`, bytes
  `8B 51 04 85 D2 75 03 33 C0 C3 8B 41 08 2B C2 C1 F8 02 C3`.

`FUN_00458090` builds a physical-ID vector for the requested class and
excludes the current human CarID. Its participant loop uses the caller's
`count` endpoint (`first + count`); no literal four-participant loop limit is
present. Each iteration:

1. Checks the temporary physical-ID vector length using `FUN_004116A0`.
2. If empty, copies the original eligible class pool back into the temporary
   pool and shuffles it with `FUN_00450580`.
3. Selects and removes one physical CarID from that temporary pool.
4. Calls `FUN_00458980` to select a DriverID from its separately initialized
   ten-entry driver pool, which has its own refill path.
5. Writes CarID, registry-derived CarClass, and DriverID through native
   per-slot setters (`0x004ACAF0`, `0x004ACC10`, `0x004ACCD0`).

Thus `Duplicates=WhenNeeded` can retain a class-restricted policy after all
unique eligible physical IDs have been consumed; the native chooser refills
its ID pool and creates new participant-slot state rather than cloning an
actor, controller, or DriverID object. This is static behavior. A repeated-ID
race, all participant actors, finish, Results, and frontend return still need
human runtime qualification.

`Duplicates=Never` stays distinct: the class selector refuses a class once
the remaining eligible identity set is empty. It is not used by the required
first extended qualification profiles, which use `WhenNeeded`.

## Patch composition

R-MOD1-E preserves the seven v11 image operations and their ownership. Its
three Randomizer hooks replace only class-policy selection seams inside
`FUN_00458090`; the selected-count readers `0x0047B88A` / `0x0047B8DD`, caller
sites, physical CarID pool/refill and per-slot CarID/Class/DriverID writes
remain retail bytes. No fixed CarN roster is generated. The Randomizer feature
remains independently selectable from the opponent extender; with Randomizer
off, its class-policy hooks are not installed and the engine retains its
native Stock-class physical chooser.

Static envelope: one human plus 4..7 AI, 5..8 total cars, no Car8 access.
Runtime-qualified envelope: one human plus four AI / five total in v11 only.
