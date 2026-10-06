# Classic+ implementation — 2026-10-06

**READY_FOR_HUMAN_RUNTIME.** Starting HEAD7ef461057c32ba1ab700d67f976ac90db553d14f on research/general-re, clean. The user's repository consolidation instruction overrides the attachment's proposed modernization/classic-plus branch. No worktree or alternative branch was created.

Frozen source baseline is modernization/d3d8-proxy, original commit929caef; closeout5861ed2 is preserved in retired graphics git-metadata and was read without checkout/mutation. Native source had not changed in that closeout. Human-tested DLL b21ae8c587f6d6a14809c5c4715e557307e045a5db6d147d460d1f1537c6a5d5 and external pristine MRallye_orig.exe bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 were rehashed. Seed copies only tracked runtime sources, licensed headers, ABI data and relevant tools/tests; no old builds, captures, dumps or analysis were imported into source control. Source-copy hashes are in starting-state.json.

## Config and build gate

MRRRenderer.ini is resolved relative to proxy_module/DLL path, never process CWD. It is read once into Session, copied to each device, and not hot-reloaded. Version1 is required for any override. Missing config/version or unknown version is Stock. Strict true/false flags, positive integral MaxAnisotropy1..65535, finite vertical FOV30..110 and exact Stock/Off modes; invalid individual values disable only their feature. Raw requested strings and rejection reasons remain in session JSON. Only executable SHA256 equality activates any visual policy; forwarding/tracing remain available on unknown builds. No profile is inferred from compatible RVAs alone.

## Anisotropy

Pinned D3D8 values: MAGFILTER16, MINFILTER17, MIPFILTER18, MAXANISOTROPY21; LINEAR2, POINT1, ANISOTROPIC3. D3DCAPS8.TextureFilterCaps MINFANISOTROPIC0x400 and MAGFANISOTROPIC0x04000000; MaxAnisotropy. Query native GetDeviceCaps once per created device, only when supported-build AF was requested. Unsupported MIN or failed caps/max<2 disables AF without failing device creation; other features remain independent. Actual GPU caps remain unobserved until human runtime. Synthetic caps8/16 and MIN-only combinations passed.

Stage0 LINEAR MIN becomes ANISOTROPIC if MIN supported; LINEAR MAG only if MAG supported. Stage1..7, POINT, other filter modes and MIP are untouched. MAX is min(config,cap) for valid positive game MAX requests. Extra native MAX write precedes a converted filter when needed; initially absent logical MAX is the documented D3D8 initial/reset default1. Failed MAX leaves the original filter setter stock, disables AF and logs rejection. Rejected transformed filter retries the original requested setter, records failed native attempt and returns its real retry HRESULT. Successful logical/effective tracking only follows actual successful setters. Extra writes are explicit native_override trace entries.

AF scope is stage0 LINEAR, not an unproven world-vs-UI texture classifier. UI POINT remains POINT; UI LINEAR may receive the same supported filtering. Human inspection of UI/alpha cards is therefore required. No textures, UVs, mip contents or environment stages are replaced.

## Gameplay FOV

Target-gated main-EXE caller must equal returnRVA0x0013FA75 /VA0x0053FA75, CALLVA0x0053FA6F, cached projection ownerVA0x0053F9E0 /RVA0x0013F9E0. This is distinct from gameplay VIEW returnRVA0x00161A26 (not altered). Evidence: frozen R-GFX1 callmap/camera-pipeline and pristine R-GFX2 A/B/C trace. Exact matrix must be finite symmetric LH: only indices0,5,10,11,14 populated, _34=1, positive X/Y, _33>1, _43<0. Unknown caller/module, ortho/off-center/malformed shape or unknown build forwards the identical input pointer and values. Valid override copies input, computes aspect=_22/_11 and cot(VFOV/2), replaces only indices0/5. All14 remaining float bits, including Z coefficients/near/far semantics, remain unchanged. Failed rewritten native setter retries original input and records the failed attempt. VIEW, camera, sky position and CPU culling are not changed. Wider projection can reveal existing upstream culling limitations.

Synthetic stock input VFOV67.500000448; test override80.0 within float tolerance, original aspect preserved. Ortho640x480 is not modified. The cached 3D projection seam may have other 3D consumers; frontend 3D previews/replays/split-screen require additional human coverage rather than universal gameplay-only claims.

## Shadow isolation

Attachment called the shadow indexed; pristine trace and frozen callmap prove DrawPrimitive. Rule: slot70/DrawPrimitive, main-EXE returnRVA0x001881EB /VA0x005881EB, CALLVA0x005881E5 in ownerVA0x00587DB0 /RVA0x00187DB0; triangle list, known FVF0x142, blend1/fog0/Z-write0. Off returns S_OK without the native draw, preserving tracked device state. Ambiguity/unknown state/module/build/caller/method forwards. Stock always forwards once. No shared-world indexed draw is suppressed.

Opacity DEFERRED: observed SRCALPHA5/INVSRCALPHA6 and stage0 alpha MODULATE4 of texture2 and diffuse0. This depends on texture/vertex alpha; no proven isolated constant-opacity control exists. VB/texture mutation and guessed blend equations are prohibited. V1 is only Stock/Off.

## Preservation and scope

Full16/97 ABI, identity/QI/GetDirect3D, raw child resources, exports, explicit system loader, bounded F10 and read-only provenance retain the inherited contracts. Wheels still correlate by position+directed X axle, not full spinning basis or fixed draw order. No modern lighting/reflection/weather/postFX/freecam/backend work began. DLL was built but not deployed; EXE/assets and frozen research remain untouched.
