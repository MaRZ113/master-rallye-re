# Future Vehicle SDK interoperation note

Vehicle SDK is optional and remains outside R-MOD standalone operation. The
Randomizer must use its audited stock pools when no SDK, addon manifest or
extra vehicle runtime is present. A filesystem directory is not proof that a
physical ID exists in the current process.

A future read-only integration boundary should accept a generated, versioned
registration record only after the Vehicle Runtime proves:

- physical CarID and registry slot are active in this process;
- class and sparse class-local mapping are valid in both directions;
- CarType, WheelType, physics family, model and wheel resources resolve;
- the resource dependency closure is complete and belongs to the active root;
- the addon declares eligibility by mode/pool (including ordinary vs
  bonus/special T3 behavior for Invitation);
- its collection identity and configuration generation are stable.

The Randomizer should reject an inactive or incomplete entry before roster
generation and log the exact reason. It should not scan arbitrary folders,
load a Vehicle SDK binary, or change vehicle registration itself. The
integration should be a separate, optional adapter consumed by the unified
R-MOD patch/runtime owner; it must not create competing hooks.

This capability is `FUTURE INTEROP REQUIREMENT`, not part of R-MOD3 and not a
release prerequisite for the standalone stock-only beta.
