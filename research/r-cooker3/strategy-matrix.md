# R-COOKER3 strategy matrix

This is the current implemented strategy policy. R-COOKER2 remains the
independent offline revision-131 converter.

| Input evidence | Strategy | Current evidence | Fail-closed condition |
|---|---|---|---|
| `complete.gxm`, `car.gxm`, and `wheel.gxm` pass supported prefix checks and dependencies resolve | `retail-native-gxm` | Mercedes and Forester native-source model outputs have runtime evidence for their tested cook cases | Refuse unsupported prefixes, missing roles/dependencies, unverified retail/harness builds, unresolved authoring paths, or unsafe Junction state |
| All three DX roles are supported vehicle revision 131 | `offline-131-to-135` | R-COOKER2 is production-ready within its documented vehicle-DX grammar; Trooper and Forester converted candidates passed runtime | Refuse unsupported structures/revisions; preserve strict generated-output validation |
| All three DX roles are supported revision 135 | `pass-through-135` | Validate according to existing-rev135 policy, then copy unchanged | Reject structural/range/topology failures; do not normalize index ordering |
| Revision-127 DX only, with no usable GXM set | Unsupported | No conversion is implemented | Refuse rather than infer a converter |

Texture strategies are independent:

| Input state | Strategy | Behavior |
|---|---|---|
| Valid required DXT exists | `reuse-valid-dxt` | Parse, hash, and reuse unchanged. |
| Required DXT missing; supported GXI exists | `offline-gxi-to-dxt` | Use the established offline encoder, then validate. |
| Retail DXT cache miss | Not relied on | The tested ordinary path did not regenerate DXT from GXI. |

## Selection order

1. Prefer a complete supported GXM source set when native cooking is requested
   or `auto` finds one.
2. Otherwise use R-COOKER2 for a consistent supported revision-131 set.
3. Validate and pass through a consistent supported revision-135 set.
4. Refuse mixed/unknown layouts and revision-127-only inputs.

No silent mixing of model roles is allowed.

## Current native-GXM coverage

| Family | Source build | Static preflight | Native-cook runtime evidence | Cache-only family namespace |
|---|---|---|---|---|
| Mercedes | Demo 8.4.1 `Copy of Mercedes` | Pass | Runtime-confirmed for the exact source/harness; deterministic and gameplay oracles closed | Confirmed for the tested Mercedes package |
| Forester | Demo 9.3.1, with source typo `comlplete.gxm` staged as `complete.gxm` | Pass; 46 authoring refs, 23 unique referenced GXI, 23 DXT dependencies | Runtime-confirmed under a temporary Mercedes namespace; authentic Forester physics not proven | Static cache-only package validates; Forester-named runtime check pending |

These cases do not establish support for every GXM variant.

## Output boundary

Successful output is a portable resource package such as:

```text
DataGx/Vehicles/<family>/
    complete.dx
    car.dx
    wheel.dx
    required *.dxt
```

The package excludes GXM/GXI and authoring/runtime machinery. Source Cooker
does not assign IDs, menu order, unlocks, AI eligibility, localization,
frontend statistics, or physics configuration.

Use `python tools/source_cooker.py --help`; the wrapper adds the repository's
`src` path, so no environment variable or generated PowerShell helper is
required. The exact workflow is in [docs/source-cooker.md](../../docs/source-cooker.md).
