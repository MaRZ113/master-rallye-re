# R-COOKER3 validation layers

Keep parser, package, determinism, and runtime evidence separate. A static
package `PASS` does not promote runtime-only claims.

| Dimension | Evidence required | Mercedes | Forester |
|---|---|---|---|
| `FORMAT_VALIDATED` | Supported rev135 parser and strategy validation pass | PASS for `complete`, `car`, `wheel` | PASS for `complete`, `car`, `wheel` |
| `TEXTURES_RESOLVED` | Every model DXT reference resolves to a valid texture | PASS, 25 referenced DXT | PASS, 23 referenced DXT |
| `COLLISION_STRUCTURALLY_VALID` | Parsed collision structure passes available range/topology checks | PASS; secondary tag101 descriptor meaning unresolved | PASS; tag101 descriptor lists differ slightly from R2 with unresolved semantics |
| `DETERMINISTIC_COOK_CONFIRMED` | Independent same-source cooks have byte-identical outputs | Confirmed for exact three-role Mercedes source/environment | Not established by the current Forester native job |
| `CACHE_ONLY_PORTABLE` | Runtime loads DX/DXT with source GXM/GXI absent in the named namespace | `CONFIRMED_BY_RUNTIME` for Mercedes | Static package passes; Forester-named runtime test PENDING |
| `GAMEPLAY_RUNTIME_CONFIRMED` | Runtime model loads in a race; describe collision/damage independently | `CONFIRMED_BY_RUNTIME` for Mercedes | `CONFIRMED_BY_RUNTIME` for model/race and collision/damage under temporary Mercedes namespace; not Forester physics |

## Forester measured static result

The collected native package has 3 DX resources and 23 DXT dependencies. All
three DX resources are revision 135 and parse without warnings/errors. The
cache-only package under `.research-output/r-cooker3_1/forester-cache-only/`
contains 26 files (three DX plus 23 DXT), no GXM/GXI, and passes
`validate-package --family Forester`.

The current native output hashes and sizes are:

| Role | Size | SHA256 | Collision |
|---|---:|---|---|
| `complete.dx` | 138,687 | `852d2188d8ee3913ea366a684ca818b1e51bed61e4c4b685308dee3939153aa7` | tag102 |
| `car.dx` | 128,522 | `27217ef5129dbb84f4237308400a0285babba12988f9d27eb6ffa8248f187492` | tag101; Rep A 8 vertices/12 triangles, Rep B 30 vertices/56 triangles |
| `wheel.dx` | 13,002 | `ce2b6557cbd8975ec14d1c20a4d3df902512a3433c713dc3822f09bfd35ca01c` | tag102 |

These outputs were supplied from the native cook job. Their runtime
observations are recorded with user-provided provenance in
[Forester qualification](forester-qualification.md); package validation alone
does not create runtime evidence.

## Reporting rules

- Record source, executable, archive, and output hashes with each oracle.
- Keep source identity separate from filename matching.
- Distinguish parser validity, semantic comparison, and runtime appearance.
- Treat tag101 secondary descriptor meaning as unresolved even where runtime
  accepts the native output.
- Do not treat the temporary Mercedes runtime namespace as Forester physics.
- Do not treat a static cache-only package validation as runtime portability.
