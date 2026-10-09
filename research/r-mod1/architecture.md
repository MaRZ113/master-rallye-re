# Shared core and integration boundaries

## One semantic core

`src/native/rmod1/core.hpp` contains the common code that either activation
adapter must use:

- strict versioned INI parsing and all-or-default diagnostics;
- stock pool eligibility and guarded reward IDs;
- Stock / Full / class-specific / Mixed / Diverse vehicle selection;
- unique-first repeated-CarID policy, without DriverID mutation;
- one-human Quick Race count planning and the course/roster fail-closed gate;
- exact retail disk/mapped-image identity checks;
- native patch operation ownership, preimage, bounds, dependency, mapping and
  overlap validation.

The external launcher owns process creation, suspended-thread lifetime, remote
memory and page protection. A future `dinput8.dll` proxy owns export forwarding
and module startup. Neither adapter is allowed to reimplement policy or patch
planning. Both must provide verified observations to the shared core before
any write.

## Product boundaries

Randomizer chooses vehicle class/physical ID. AI Extender chooses a validated
participant count and causes independent native participants to be published.
The randomizer can run at native counts; the count extension can use Stock
class-compatible IDs. Neither subsystem is a prerequisite for the other.

The initial semantic product is Quick Race only. It does not rewrite saved Cup
or Master rosters, challenge-authored entries, Invitation's ordinary-T3 pool,
or player unlock progression.

The addon integration seam is an in-process registration record, never a scan
of addon folder names. Vehicle SDK/Runtime and its launcher are explicitly
outside the standalone dependency graph.

## Patch plan boundary

All historical candidates were produced separately. The audit at
[`patch-composition-audit.json`](patch-composition-audit.json) identifies two
real code-cave conflicts:

- R-AI1.2 Quick Race selector and R-AI2.1 participant publisher both use the
  `0x68E400` range.
- R-AI2.1 count shim and R-UI1 native localization/list helper both use the
  `0x68E300` range.

Three branches also carry duplicate PE VirtualSize fields which must be
recomputed once, and identical hardening ranges can be deduplicated if still
needed. These are not a final integration plan. No historical patched image is
used as a product base.

The portable patch-plan validator is ready to reject overlaps and mismatched
preimages. The exact R-MOD1 operation bundle, relocated code/data, control-flow
fixups and byte-by-byte source map are not yet generated. No launcher may use
the generic validator as evidence that an empty plan installs a mod.
