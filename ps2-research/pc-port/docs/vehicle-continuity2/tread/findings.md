# COMPLETE wheel tread: source-backed sampler correction

## Confirmed source/code facts

The accepted race tire correction changes only stage0 ADDRESSU toWRAP for the exact verified WHEEL source1. Stage0 ADDRESSV remainsCLAMP, and captured original sampler values restore through the existing transaction. User runtime previously confirmed correct race tire appearance.

The frontend path calls `FrontendTransaction::material` without its optional primaryU parameter in BOTH material preflight and actual submission. The shared default isCLAMP. Thus COMPLETE retains the original race bug independently of the corrected WHEEL path.

Pinned XTRAIL-COMPLETE.ps2model SHA `ba1cee9a21c2a2ae2935158136ae80b587eca7dc9a6701afc573e069818d772b` contains root19, mode3,528 tread triangles, primary `commontextures/tread-tga` and secondary `commontextures/rubber-tga`. Original sourceU spans[-1.2299022674560547,2.958979606628418], whileV is[0.0004995167255401611,0.9995005130767822]. CLAMP stretches the boundary texels over most of the circumference. Preserve these original source UVs and original COMPLETE texture; do not replace it with WHEEL/merctread or scale the UVs.

`complete-tread-policy.json` records every local converted COMPLETE variant (29 files including superseded/fix variants) with exact converted/source SHA, original mesh path, primary/secondary, face count, mode and original UV ranges. This is an asset-variant audit, NOT29 admitted distinct vehicles. The currently admitted profile registry remains authoritative for actual coverage. Every audited tread primary has authored rubber secondary and V entirely inside[0,1]. Mesh indices vary by family; do not reuse race source1 or X-Trail root19 globally.

## Minimal integration recommendation

Add an exact per-profile `primary_u_wrap_mask`, populated only from the pinned admitted COMPLETE source mesh metadata above. For X-Trail Mode1 fallback the mask is0x00080000. For Mode2 use each admitted source profile's mask. Pass `(mask & (1u << mesh_index)) ? D3DTADDRESS_WRAP : D3DTADDRESS_CLAMP` as the existing final material parameter at BOTH frontend material preflight and actual draw. Leave all other primary/secondary sampler states, reflection routing, native suppression, alpha/depth, primaryV orientation and original private assets unchanged.

This uses existing transaction capture/dirty-before-set/partial-failure rollback/reverse restoration. No new integration seam or baseline edit is required. Runtime selection must use the already hash-pinned active source profile, not an arbitrary currently bound texture name or a generic out-of-rangeUV heuristic.

## Focused validation and A/B

Static audit and metadata checks:2/2PASS. Main integration should assert X-Trail root19 and each admitted profile's exact mask; non-tread/rim/body meshes stayCLAMP. Existing transaction tests should confirm WRAP only onprimaryU,CLAMPprimaryV, exact original ADDRESSU after successful draw and partial failure. Apply the same policy during ValidateDevice preflight.

In game, select X-Trail, compare the rotating COMPLETE tread close-up from the same menu camera, then switch to one differently indexed family (for exampleTata root25 orChevyBlazer root2), return toX-Trail and Reset withMSAA4x. Tread should tile around the circumference; sidewall/rim/body reflections and frontend rotation must remainunchanged. This source/code analysis does not substitute for runtime confirmation of the new frontend correction.
