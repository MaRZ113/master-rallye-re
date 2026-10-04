# Keeping the on-disk EXE unchanged

Verdict: **EXTERNAL_RUNTIME_MOD_REQUIRED** for independent AI classes in the
audited ordinary Quick Race path. This is a deployment design, not a loader.

## Data-only / existing engine seam

Loose-file precedence over Data.sma remains established. Changing a file can
only affect values/functions the EXE actually consumes. Frontend XML provides
human absolute IDs, mode, count, difficulty, ghost and track. `0x47B780` reads
these, obtains Car0 class and passes it into `0x458090`. That chooser overwrites
AI CarID/Class/DriverID. Initializing Race/CarN values in XML cannot survive
the unconditional per-N setters. No independent AI-class policy field is read.

Race/OpponentClass is registered at wrapper+0x54, but its getter/setter have no
direct calls in the established path. Campaign participant presets have a
different consumer/mode; they are not a Quick Race seam. Attract Type14 mixes
IDs using native code and zero humans; changing race type would change rules
and overwrite Car0 rather than express the requested policy.

The bounded DataGame XML search and chooser call/control-flow audit found no
supported script/plugin/data callback at this boundary. This is not a claim
that the entire engine has no callbacks. An untraced engine-wide mechanism is
UNKNOWN; none is available as an evidence-backed alternative for this policy.
No invented XML fields or script runtime were added.

## Future small runtime mod

Keep original MRallye.exe byte-identical on disk. A removable DLL/config would
verify file size, exact build hash, loaded image identity/base and original
instructions at all hook ranges before enabling any hook. Unknown build: no
hook, no partial initialization, fail closed. No arbitrary signature-scanning
support. Avoid loading/unloading hooks while a chooser invocation is active.

Config defaults to **STOCK**: hooks absent, native behavior exact. Explicit
MIXED uses per-slot class RNG; DIVERSE uses the documented spread. Minimal
audited seam is the Quick Race loop/pool-build continuation inside `0x458090`
(`0x45810B`, `0x458379`, `0x4582D5` in pristine), retaining native pools,
DriverID bookkeeping and ID-derived publication. It changes neither saves nor
registry, participants, UI counts or game assets. Disabling/removing the mod
returns the original game; no permanent save conversion is needed.

Pristine profile:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Potential widescreen/freeze profile:
`bcf310a79133b03aa89ce51197a37516ee27c1b0e9da19788519e849e7a2f2f6`.
The latter requires its **own** range/layout/loaded-image audit and runtime
test before future mod support; this phase builds/accepts only pristine-derived
instrumentation. A stable ABI, safe loader/injection mechanism, hook lifecycle
and compatibility testing remain future work. No runtime loader or live memory
writer was implemented here. The patched research EXE is a temporary proof
vehicle, not the intended final distribution format.
