# R-COOKER3 source corpus qualification

Mercedes proves that the strategy split and job orchestration work for one
source family. It does not establish arbitrary GXM support.

| Candidate | Source | Static source result | Cook/runtime result |
|---|---|---|---|
| Mercedes | Demo 8.4.1 `DataGx/Vehicles/Copy of Mercedes` | 3/3 GXM supported prefixes; 25 referenced DXT closure; 25 GXI mirrored | Native Cook A/B identical; T1/T2/T3 closed and runtime-confirmed for the exact harness |
| Forester | Demo 9.3.1 `DataGx/Vehicles/Forester` | 3/3 GXM supported prefixes; 23 referenced DXT closure; 23 GXI mirrored | Fresh native job prepared; cook/runtime pending |

Forester's frontend GXM is named `comlplete.gxm` in the corpus. Inventory
normalizes its role to `complete` when it stages a copy as `complete.gxm`;
the source file itself is not renamed or modified. Its exact SHA256 is
`3fa2cff8c100b66236b1f076c164a402ac199fe3502838e0bc18be8a381b790f`.

## Candidate progression

1. Finish review of the prepared Forester native job and its exact isolated
   harness/texture/source hashes.
2. Have the operator cook only in that job's copied runtime, collect the
   three outputs, and inspect format/collision/texture reports.
3. If static checks pass, perform a scoped cache-only/runtime validation.
4. Only then consider one additional family selected from actual source
   availability (Trooper, Jump, NewRav, or Tata), with different source-build
   or collision characteristics where possible.

Do not count duplicate role copies or earlier R-COOKER2 converted DX as a
second native-GXM family. No full-corpus native runtime sweep is required in
V1.

## Cross-strategy evidence

For compatible 9.3.1 vehicles, R-COOKER2 outputs and native-retail outputs
may be compared semantically against an official 9.10.0 reference when the
same GXM source identity is established. Triangle order may differ under the
known upgrader policy. Byte identity is not a goal for this comparison.
