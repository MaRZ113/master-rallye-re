# Kia brake continuity and color

## Confirmed cause

Original EXE SHA256 bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4. Original PS2 Kia CAR SHA256 b4afabfab7437eae01ee72ca424beb90967c7b849cebdb9cf94e104560be33ce. The existing source material/GS contract remains unchanged: root.25.1.0 is brake ON mode1; root.25.1.1 is additive mode14; OFF is a separate carshiny surface. Source vertex colors are all white.

User captures PID15144 frames7921/10852 show exact-current glow true then UNKNOWN, while the native32v/32f draw, original texture generation779 and SRCALPHA/INVSRCALPHA logical blend remain. Fresh capture DLL92ef2779... then PID9516 frames1226/2800 provides original current buffer bytes. Owner/packet, material vector/token and texture generation agree; private-tree selection and native mesh/VB/IB change; XYZ changes. Ordered UV and normalized triangle indices are byte-exact across the pair (SHA4a075be51521d4e13fceefe349870b474996abfb90ea3a3b957b449b755c1c43). This establishes the failed old positional-geometry gate, not a missing brake signal.

## Narrow implementation

Only Kia with a current complete CAR certificate may use continuity. The current native queue record, mesh descriptors, VB/IB ranges, owner/packet/model links, selected tree and WORLD must match the already rendered chassis in the same frame. Healthy exact source seeds references bound to device/race/owner lifetime and material token/current texture generation. A damaged native clone requires the same references and exact normalized UV/index topology, finite current XYZ and complete current CPU mirrors. Final descriptor/owner/world/generation/revision checks occur before the one native draw. No replay, extra glow draw or damage mutation is used. Unknown paths fall back with a reason. GPU Reset releases private textures, and current owner/resource checks revalidate retained references; a changed engine material/texture identity fails closed.

The native damaged positions are drawn unchanged. Healthy positional hashes remain strict. There is no fleet rollout, generic UV-only matching, static pointer authority, controller read, private native object, body/wheel source edit or integration patch change.

## Color evidence

The existing additive halo already uses original PS2 BREAKLIGHTSONGLOW GXI b6350f92... with ONE/ONE and a fade in RGB; alpha is zero. Recoloring it would corrupt the original gradient. The remaining PC ON-core texture has blue mean105.09 and green mean102.36, with near-white center pixels. Original PS2 BREAKLIGHTSON GXI fd4c121f... has blue0 throughout and red212..254, green0..166. The code now binds this exact source only on Kia's source-verified native ON draw, with native opaque/depth behavior, explicit source RGB and no secondary environment. Uploaded alpha255 represents PS2 mode1 TCC0 ignoring source alpha0; this does not turn ON into additive glow. Missing asset fails closed. No global tint, lighting change or postprocess is introduced.

This is source-backed red/orange color correction, not measured pixel parity. Exact GS inherited state, PC/PS2 exposure and final screenshot color remain game A/B requirements.

## Validation boundary

Native actual-buffer replay covers healthy recognition, old rejection of actual damaged geometry and new owned-clone acceptance; wrong owner/lifetime/material/texture/UV/index/revision/nonfinite cases reject. ON-source fixture verifies exact source identity. Managed ON texture loading/reset and partial scalar rollback are tested. Full baseline/PS2 CTest and Python regressions must pass before packaging. Updated DLL runtime acceptance and color screenshots are pending until user tests it.

## USER RUNTIME CONFIRMED

New DLL d8e01ce1ddb98514a1e53671756a3380add65ec79ea774bff6ed008c8f58e9d7, PID9508. Frame1332: healthy ON_CORE and ADDITIVE_GLOW owner_verified/override_applied=true; all apply/draw/restore HRESULT0. Frame5191: private damaged tree, both layers owner_verified/damaged_branch_matched/override_applied=true; glow reason=damaged_owned_clone_uv_index_match; all HRESULT0. The second frame is after successful Reset epoch1, both captures MSAA4x. Both frames retain successful PS2 CAR and four independent PS2 wheel submissions. User confirms brake color applied and no damage breakup.

Acceptance: (a) measured Kia damaged-glow continuity FIXED; (b) original PS2 ON red/orange color APPLIED, user visually confirms; (c) exact pixel parity not claimed. Fleet rollout remains out of scope; each other family needs its own current owner/healthy material and topology proof. Kia cold already-damaged sessions without an exact lamp reference, altered UV/material/texture identity still deliberately fall back. OFF release/restart exhaustive coverage is not newly measured by this two-frame pair.
