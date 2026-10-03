# T2 — Mercedes cache-only portability

## Result

**CONFIRMED_BY_RUNTIME.** The tested Mercedes package loaded from cached DX
and DXT without Mercedes GXM/GXI source access.

The isolated model directory contained exactly three DX outputs and 25
required DXT files. The retail archive has zero Mercedes-namespace members.
The tested DX hashes are:

| Role | SHA256 |
|---|---|
| `complete.dx` | `ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b` |
| `car.dx` | `5ec5f7480ddfc1380131a012b300a4cdeb28b869a1668b6f8bbe97210893ff44` |
| `wheel.dx` | `8707d887a75c452eb739775e21f94109521d9fc6be07726cee28a8e911c590ff` |

The DebugView capture shows all three model roles loading from the isolated
Mercedes cache namespace and all 25 distinct Mercedes DXT dependencies
loading. It contains no Mercedes GXM/GXI access and no access to the historical
`D:\projects\MRallyeTNG` authoring root. It does contain two unrelated
game-wide GXM events (an empty global `.gxm` and a GPS test asset); these are
not Mercedes dependencies and do not invalidate the scoped result.

The T2 log is 152,378 bytes, SHA256
`cded3ff9a024e9335f0e04a5c4bd1c3f6c4195e19caa0616a8435003c8d2b58d`.
The raw log remains local at
`research-output/r-cooker3/oracle-t2-t3/results/oracle-t2-result.log`.

## Cook determinism

The cache manifest records that independent Cook A and Cook B outputs are
byte-identical for all three roles, with the hashes above. This is confirmed
for the exact Mercedes GXM sources, retail build, and harness only.

## Scope

This proves cache-only portability of the Mercedes package in the tested
runtime setup. It does not establish a final public vehicle identity or
general cache-only behavior for every vehicle family.
