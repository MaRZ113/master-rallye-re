# R-COOKER3 strategy matrix

This matrix is implemented by the R-COOKER3 source orchestration layer. The
retail-native route is runtime-proven only for the exact Mercedes source and
harness described in this directory. R-COOKER2 remains the independent
revision-131 vehicle DX strategy.

| Input evidence | Implemented strategy | Current status | Fail-closed condition |
|---|---|---|---|
| `complete.gxm`, `car.gxm`, and `wheel.gxm` pass supported prefix checks and source dependencies resolve | Prepare an isolated copy of the supported retail runtime; operator cooks and collects DX | Demonstrated for Demo 8.4.1 `Copy of Mercedes`; Forester job statically prepared, cook pending | Refuse unresolved/ambiguous authoring roots, missing roles/dependencies, unsupported retail build, or unsafe path bridge |
| Supported vehicle DX revision 131 is present and source-side cooking is not required | Use the existing R-COOKER2 revision-131 to revision-135 upgrader | Production-ready within its documented vehicle-DX scope | Refuse unsupported structures/revisions and preserve generated-output validation |
| Supported vehicle DX revision 135 is present | Validate and copy unchanged | Existing-rev135 validation policy is implemented in R-COOKER2.1 | Reject structural/range/topology failures; do not normalize triangle ordering |
| Only revision-127 cached DX is present, with no usable GXM source | No conversion route | Unsupported | Refuse; do not guess-convert revision 127 |

## Selection order

1. Prefer the native retail cook when a complete supported GXM source set and
   its dependencies are available.
2. Otherwise use R-COOKER2 for supported revision-131 vehicle DX.
3. Validate and pass through already-supported revision-135 DX.
4. Refuse legacy revision-127-only inputs and all unknown revisions.

When all three usable GXM roles pass supported prefix checks, `auto` selects
retail-native GXM first. Otherwise it selects one consistent supported rev131
or rev135 DX strategy. Mixed roles are never silently combined.

## Output boundary

The output is a portable model/resource package, for example:

```text
DataGx/Vehicles/<Family>/
    complete.dx
    car.dx
    wheel.dx
    required *.dxt
```

The cooker does not assign registry IDs, menu order, unlocks, AI eligibility,
frontend statistics, localization, or physics configuration. Vehicle
Composer or later roster tooling remains responsible for those systems.

The available native-job command is:

```text
python -m master_rallye.source_cooker vehicle --source <source-folder> --family <family> --model-strategy retail-native-gxm --retail-root <isolated-harness-template> --output <new-job-folder>
```

For GXM input, `--output` names a prepared job directory. After the operator
cooks the three roles, `collect --job ... --output <new-package-folder>`
creates and validates the portable package. The tool does not launch the game
or execute generated Junction scripts.
