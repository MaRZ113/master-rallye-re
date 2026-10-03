# Retail-native vehicle model cook architecture

**Status:** Mercedes native cooking and the first Source Cooker orchestration
are implemented. Current commands and behavior are in
[architecture.md](architecture.md); this file's earlier design text is retained
as context, not as a pending implementation plan.

## Proven Mercedes slice

For the exact Demo 8.4.1 `Copy of Mercedes` source and the existing isolated
retail cook harness, the native runtime read `complete.gxm`, `car.gxm`, and
`wheel.gxm`, emitted revision-135 DX, and reloaded the caches. A fresh second
cook produced the same three DX files byte-for-byte. The evidence is
source-specific; it does not establish arbitrary GXM support.

Role identities and Cook A/B hashes are listed in
[findings.md](findings.md). The harness is an existing ID26 / T1 local7
`mercedes-cook-harness` profile and is not a final presentation identity.

## Orchestrator boundary

The Source Cooker prepares an isolated human-assisted job around the original
retail runtime instead of implementing its DX/model/collision serializers:

```text
source discovery + hashes
    -> GXM path/dependency inventory
    -> source/cached-DX strategy choice
    -> disposable retail workspace
    -> verified authoring-path bridge when needed
    -> native cache-miss trigger for complete/car/wheel
    -> collect DX and required DXT
    -> format/collision/texture validation
    -> optional A/B determinism and source-cache semantic checks
    -> portable cache-only package + provenance manifest
    -> Junction cleanup
```

The model output is a resource package, not a vehicle registration system.
It must not decide registry IDs, menu order/unlocks, AI eligibility,
localization, frontend statistics, or physics family. Vehicle Composer or a
future add-on layer consumes the package separately.

## V1 constraints

- Keep R-COOKER2 unchanged for supported revision-131 DX when source cooking
  is unnecessary.
- For source-bearing assets, require all necessary GXM roles and resolve
  authoring paths using an isolated, reversible bridge.
- Use a separate copied retail runtime; never mutate canonical retail or demo
  installs.
- Require human frontend preview and Practice/Quick Race loads for v1. A
  headless harness is not a prerequisite.
- Emit a portable package with `complete.dx`, `car.dx`, `wheel.dx` when
  present, and resolved DXT dependencies, plus a manifest.
- Refuse unknown path layouts, unsupported revisions, incomplete dependencies,
  and sources without a proven route. Never guess-convert rev127 DX alone.

The public entrypoint is `python tools/source_cooker.py`; it bootstraps the
bundled/repository `src` package without a manual `PYTHONPATH`. Native GXM
mode creates a fresh cook job. `--launch` can start the isolated retail game
and resume collection after exit; the tool does not automate menus or run a
headless cooker. Without `--launch`, use `resume` or `collect` after the
operator finishes in-game cooking.
