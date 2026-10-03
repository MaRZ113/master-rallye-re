# R-COOKER3 Unified Source Cooker architecture

## Current R-COOKER3.1 design

Source Cooker V1 is a human-assisted orchestrator around the original retail
vehicle cooker. It does not implement a GXM-to-DX serializer, a native tag101
descriptor producer, or mesh optimization.

```text
supported GXM/GXI source
    -> source inventory and hashes
    -> isolated copy of verified retail cook harness
    -> Python-owned authoring Junctions
    -> operator triggers complete/car/wheel cache misses
    -> output validation and texture closure
    -> portable cache-only DX/DXT package
```

The product uses one strategy selection layer:

| Model inputs | Model strategy | Result |
| --- | --- | --- |
| All supported `complete.gxm`, `car.gxm`, `wheel.gxm` roles | `retail-native-gxm` | Prepare an isolated native-cook job; operator performs the game interaction. |
| Supported vehicle DX revision 131 for all three roles | `offline-131-to-135` | Delegate conversion and strict generated-output validation to R-COOKER2. |
| Structurally valid revision-135 vehicle DX for all three roles | `pass-through-135` | Validate and copy the bytes unchanged. |
| Revision 127 only, mixed revisions, or unknown layout | Unsupported | Fail closed. |

Texture selection is independent: reuse a valid DXT, or use the existing
offline GXI-to-DXT encoder when the DXT is absent and the GXI is supported.
The tested retail cache-miss path is not relied on to regenerate DXT from GXI.
Portable packages contain `DataGx/Vehicles/<family>/complete.dx`, `car.dx`,
`wheel.dx`, and only the required DXT files. They exclude GXM, GXI, authoring
mirrors, runtime executables, and retail archives.

## Runtime evidence and scope

The native GXM path has runtime evidence for the exact Mercedes and Forester
sources and supported cook-harness profile. Mercedes has the completed
determinism, cache-only, collision, and damage oracles. Forester's native
outputs validate and the operator reports successful model/race loading and
collision/damage under the temporary `Mercedes` runtime namespace. That does
not prove authentic Forester physics or Forester-family cache-only portability.
The separate Forester-named cache-only runtime check remains pending.

No arbitrary GXM support is claimed. Current source grammar checks cover the
supported material, geometry, and triangle prefixes; hierarchy/tail data
remain opaque. Native tag101 secondary descriptor semantics remain unresolved.
The original retail runtime emits usable tested outputs, so that unresolved
offline writer detail is not a blocker for the orchestrated route.

## CLI and job lifecycle

The public repository entrypoint is `python tools/source_cooker.py`; it
bootstraps `src/` itself, so normal use requires no manual `PYTHONPATH`.
`python -m master_rallye.source_cooker` remains available to development users
who configure the source tree themselves. See [the user guide](../../docs/source-cooker.md)
for copy-pasteable commands.

The CLI provides `inventory`, `plan`, `cook` (`vehicle` alias), `status`,
`resume`, `collect` (`package` alias), `cleanup`, `recover`, and
`validate-package` (`validate` alias), plus `--version`. Jobs use schema 2,
store internal paths relative to their job root, and migrate schema-1 manifests
when loaded. `status` reports output presence, texture count, link ownership,
validation dimensions, and a next action. `resume` inspects actual outputs and
Junction state; with missing outputs it may create or restore only an absent
job-owned link whose mirror and existing historical parent match the
manifest. It refuses unsafe links and ambiguous package provenance, and
collects only after output validation.

The state machine records preparation, runtime output, package validation,
and cleanup separately. It does not infer runtime evidence from parser or
package success. `BLOCKED` and `RECOVERY_REQUIRED` preserve manifests and
diagnostics for review instead of deleting evidence.

## Junction safety

The Python Junction manager inspects reparse points without following them.
It creates a link only when the path is absent, the historical parent exists,
and the target is the job's exact authoring mirror. Real directories, symlinks,
unknown reparse points, wrong targets, and unowned links stop the operation.
Cleanup removes only the exact Junction node recorded as created by the job;
it never recursively deletes the target or historical parents. `recover`
reconciles only exact, unambiguous live state. Paths containing spaces are
supported.

New jobs do not generate PowerShell setup/removal scripts. Old schema-1 jobs
remain loadable; any scripts preserved inside those user-owned historical
job folders are not used by the current CLI or included in the release.

## Strategy boundary

R-COOKER2 remains the canonical offline rev131-to-rev135 implementation and
retains its strict generated-output checks. Source Cooker calls that backend;
it does not duplicate or weaken it. Retail-native cooking is an orchestrator
around the original game, not a clone of its collision or draw writers.

Vehicle registration, menu slots, physics configuration, AI, and roster
capacity are not part of Source Cooker. Vehicle Composer is a separate tool.
See [the current capability matrix](capability-matrix.md) and
[Forester qualification](forester-qualification.md).
