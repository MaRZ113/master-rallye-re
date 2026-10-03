# R-COOKER3 validation layers

Keep validation claims separate. A parser pass, a deterministic cook, and a
successful gameplay test establish different things and must not collapse
into a single generic `PASS`. The current package manifest has six independent
evidence fields; see [validation-model.md](validation-model.md).

| Status | Evidence required | Current Mercedes state |
|---|---|---|
| `FORMAT_VALIDATED` | DX revision and canonical parser checks; draw/material references, geometry ranges, footer/bounds and texture records pass | Cooked `complete`, `car`, and `wheel` DX are revision 135 and parser-valid |
| `COLLISION_STRUCTURALLY_VALID` | tag101/tag102 parse, finite values, in-range indices, topology checks and zero-edit serialization where supported | `car.dx` tag101 core checks pass; secondary face-descriptor semantics remain unresolved |
| `TEXTURE_DEPENDENCIES_VALIDATED` | Every non-null model texture reference resolves to a parseable DXT; dimensions and payload validate | Existing 25 DXT dependencies parse; this does not prove a native GXI cache miss |
| `DETERMINISTIC_COOK_CONFIRMED` | Two clean cooks of the same locked sources in the same supported environment produce byte-identical outputs | Confirmed for the three Mercedes DX roles; not a general claim |
| T1 ordinary DXT cache miss | Runtime log shows DXT miss but no GXI read or DXT write; negative result scoped to the tested consumer | **CLOSED — `CONFIRMED_BY_RUNTIME`** |
| `CACHE_ONLY_PORTABLE` | Runtime loads required DX/DXT with source GXM/GXI absent; assertion scoped to Mercedes | **CLOSED — `CONFIRMED_BY_RUNTIME`** |
| `GAMEPLAY_RUNTIME_CONFIRMED` | Model loads in gameplay; collision and damage recorded separately | **CLOSED for Mercedes T3 — `CONFIRMED_BY_RUNTIME`** |

## Reporting rules

- Record source, executable, archive, and output hashes with each oracle.
- Distinguish format validity from semantic equivalence and visual appearance.
- Keep collision and damage observations separate.
- Keep the 36-byte secondary face-descriptor delta unresolved; native output
  availability is not proof of its semantics.
- A result applies to the exact source and runtime case tested. Broader
  retail-native GXM support requires additional controlled vehicle families.
