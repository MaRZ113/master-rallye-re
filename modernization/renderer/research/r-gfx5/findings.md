# R-GFX5 — Classic+ Quality Pass II

**READY_FOR_HUMAN_RUNTIME; new hardware/image validation pending.** R-GFX4 is CLOSED / CONFIRMED_BY_RUNTIME by the user's explicit acceptance on2026-10-07. This phase retains original assets, material combine, prelighting, native forwarding and optional prior effects. New display/UI/MSAA/freeze features defaultStock/off and require exact pristine retail.

Repository `D:\Game\Master Rallye\master-rallye-re-general`, branch `research/general-re`, starting HEAD `6ede833122bcd32ffb6223548c88587650d0539d`. Preflight tracked tree clean; only untracked user `modernization/input/`. No new branch/worktree/push/deployment. Retired trees, original RE material, game files and supplied patchers remain read-only; all changes under modernization.

| Result | Evidence/limit |
|---|---|
| Native-monitor Borderless; decorated client-sized Windowed; checked Exclusive; Stock control | Implemented; hidden real Win32 window and synthetic native tests. Game task switching pending. [Display](display-pipeline.md) |
| Physical backbuffer/depth and proportional viewport | Create/Reset planner, real GetDesc observation, logical/effective virtualization. Positive1920x1080 mock is not real game high-res proof. |
| Widescreen UI | Third-party modes recovered; exact640x480 orthographic correction plus opt-in packet anchors. No old FOV code. [UI](widescreen-integration.md) |
| Native MSAA | Adapter/type/color/depth/mode checks, sample descent, DISCARD candidate, bounded fallback. Hardware/appearance pending. [MSAA](msaa.md) |
| Freeze | Correlated branch independently verified; opt-in process-byte patch. Efficacy requires A/B. [Freeze](compatibility-freeze.md) |
| Gamma | Not observed in reviewed static map/existing session; coverage-limited, no new control. [Gamma](gamma.md) |
| World distance/LOD | Near/far/fog/ViewDist owners; terrain/vegetation/LOD gaps prevent coherent scale prototype. [Distance](world-distance-map.md) |

Pristine MRallye.exe:3,121,214 bytes, ImageBase0x00400000, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. [Input evidence](input-evidence.json) preserves hashes/short contexts without binary dumps. [Reference analysis](third-party-widescreen-analysis.md) separates old layouts and actual patcher branches.

Evidence grades: CONFIRMED_BY_EXE, CONFIRMED_BY_REFERENCE_EXE, CONFIRMED_BY_EXISTING_RESEARCH, OBSERVED_IN_EXISTING_RUNTIME_CAPTURE, STATIC_INFERENCE, HYPOTHESIS, AUTOMATED_SYNTHETIC_ONLY. New R-GFX5 is not CONFIRMED_BY_RUNTIME. Historical captures are R-GFX4 evidence, not validation of this DLL.

Correction retained here rather than editing old notes: `renderer-recon/device-creation.md` calls numeric SwapEffect3 “DISCARD.” Pinned D3D8 header and existing captures establish **COPY3, DISCARD1**. [MSAA](msaa.md) explains the resulting preservation risk.

[Validation](validation.md), [implementation](implementation.md), [human handoff](runtime-handoff.md), [machine summary](runtime-summary.json). Stop before R-CAM1/F-PHOTO1.
