# One original prop control, identity-filtered and capped

**Conditional recipe; not executed here.** A real original PC physical prop is
not yet identified. Do not spawn one, call the factory, replace an AI slot or
use previous vehicle addresses just to produce observations.

1. Identify the original course/object/trigger. Exact supported EXE/hash and
   current race/scene identity must be documented. Source/user scans alone do
   not prove native absence. No control found means this gate remains blocked.
2. Generate one original-class discovery recipe, using the exact EXE:

```powershell
python ps2-research/pc-port/docs/rigid-port1.2/prop-logpoint-policy.py `
  --exe 'D:/Game/Master Rallye Pristine/MRallye.exe' `
  --output ps2-research/data/rigid-port1/prop-discovery.x32dbg
```

The supplied `discover-original-prop.x32dbg` is that diagnostic policy example.
In manually loaded x32dbg use `scriptload "<absolute recipe path>"`, `scriptrun`
and manualF9. Observe the actual original trigger for at most60seconds. Only
initializer4C9CF0 with vtable691470 logs one matched owner and its original
Egg argument. No match proves only no observation in this bounded control.
Invalid debugger expressions/target context must stop the control; never treat
an error-triggered log as a verified owner. Source EXE bytes remain immutable;
INT3/debug variables alter only explicitly participated debugger execution state.

3. After proving that original Egg/AI/body/prototype/instance relation, generate
the **selected** recipe with all four current session pointers. The CLI requires
`--egg`, `--body`, `--instance`, `--prototype` and the exact `--exe`.
Pointers are not supplied in docs because no original prop was observed.
Verify each against original owner/current scene, not merely readable memory.
Scope the same known object through normal lifetime and native release, with a
separate cold-admission run if needed; historical pointers cannot carry across
restart/processes. The generator is not a course/lifetime certificate.

Eight selected points record original admission43E2A0, attach56EEF0,
clone621220, bind621310, Egg retirement/destruction, body deleting destructor
4FEDC0 and shape destructor6212C0. Each has **two identity matches**, using
debugger-only `$rp12_*_matches` counters in BOTH log and command conditions.
No `$breakpointcounter` quota is used. Hundreds of other Eggs cannot consume
the recorded-event cap. At the known clone direct call, parent Egg is recovered
at childESP+28; original prologue/call byte windows ground that stack relation.
No guessed stack scan or persistent `attach_active` flag is used.

Remove only this recipe's named `rp12_*` breakpoints after the control. Conditional
INT3 hits can still perturb timing; the matching log cap is not a claim of zero
debugger overhead. There is no automated `run`, native `call`, allocation,
manager vector write or feature activation. Source/native pointer validation
and synthetic policy tests are not runtime teardown proof.

Output: bounded `PROP12` lines, source EXE SHA, original owner identity, actual
course/race lifetime, the original reader/model/prototype link, exact clone/body
membership and destructor/free ordering. If those links are absent, preserve
the missing gate instead of executing a private spawn.

Debugger semantics follow official
[SetBreakpointCommand](https://help.x64dbg.com/en/latest/commands/conditional-breakpoint-control/SetBreakpointCommand.html)
and [mov/set](https://help.x64dbg.com/en/latest/commands/general-purpose/mov.html).
The generated commands assign debugger variables only, not registers or memory.
