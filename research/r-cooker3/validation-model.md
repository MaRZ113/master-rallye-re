# R-COOKER3 validation model

## R-COOKER3.1 update

The Forester candidate section later on this page records its original
pre-cook state. The operator has since completed the native cook and reported
runtime model/race loading and collision/damage under a temporary Mercedes
namespace. Current output hashes and separate evidence dimensions are in
[Forester qualification](forester-qualification.md). Forester-named cache-only
runtime portability is still pending; static package validation is not a
runtime claim.

The package manifest keeps six separate evidence dimensions. A single
overall package PASS means the package passed its static assembly gate; it
does not promote unobserved runtime claims.

| Field | Meaning |
|---|---|
| `FORMAT_VALIDATED` | DX revision-135 parser and the strategy-specific validation contract passed. |
| `TEXTURES_RESOLVED` | Every texture reference in the three model roles resolves to a parseable output DXT. |
| `COLLISION_STRUCTURALLY_VALID` | Parsed collision data passed available structural/topology checks and zero-edit tag101 roundtrip where present. |
| `DETERMINISTIC_COOK_CONFIRMED` | Independent cook outputs were compared byte-for-byte for the specified inputs/environment. |
| `CACHE_ONLY_PORTABLE` | Model/DXT dependencies load without source GXM/GXI in the runtime package; runtime status is distinct from static package validation. |
| `GAMEPLAY_RUNTIME_CONFIRMED` | Gameplay use was observed; collision and damage should still be described separately. |

Unassessed fields remain `NOT_ASSESSED`. The six-field record is created by
`build_validation_status`; it preserves each dimension and does not infer
one from another.

## Mercedes golden fixture

The assembled cache-only package from the completed T2 outputs has 30 files:
3 DX, 25 DXT, and 2 JSON records. Static validation passes for all model
roles, texture closure, and collision structures. Its recorded evidence is:

```text
FORMAT_VALIDATED              PASS
TEXTURES_RESOLVED              PASS
COLLISION_STRUCTURALLY_VALID   PASS
DETERMINISTIC_COOK_CONFIRMED   CONFIRMED_BY_BYTES
CACHE_ONLY_PORTABLE            CONFIRMED_BY_RUNTIME
GAMEPLAY_RUNTIME_CONFIRMED     CONFIRMED_BY_RUNTIME
```

The machine-readable package output is generated locally under ignored
`.research-output/r-cooker3/v1/Mercedes-golden-package-final/`; it is not
committed. The native-cook job generated for reproducibility is a fresh
pre-cook job and remains `PREPARED_FOR_HUMAN_NATIVE_COOK`.

## Forester candidate

Forester's source inventory, authoring references, and DXT dependencies pass
static preflight. Its fresh native job contains no cooked DX outputs yet, so
native format, collision, deterministic-cook, cache-only, and gameplay
statuses remain pending/not assessed. Earlier rev131-to-rev135 Forester
runtime results are evidence for R-COOKER2 only; they do not close this
different native-GXM cook test.
