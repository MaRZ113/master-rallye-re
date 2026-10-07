# Implementation and retained contracts

quality.hpp/cpp owns per-device display/AA/window snapshots; quality_wrappers.cpp owns Reset/Present/viewport forwarding/metadata; visual_wrappers.cpp adds exact UI projection beside existing FOV. ui_margins.hpp/cpp and margin_rules.hpp own gated packet bridge/frame edits; menu_freeze.hpp/cpp owns transactional exact-context byte patch. Parser/sample INI add local controls, unknown-build Stock.

Generated interfaces preserve every ABI slot. Root/Device COM identity,parent references/raw child interfaces unchanged. Root planner transfers to its Device retaining actual adapter/type/HWND/descriptors. No child wrapper,shader,texture,render target,new light/compositor.

Preserved: stage0 MIN-only AF/cappedMax; MAG/MIP/stage1Stock; gameplay VFOV+CPU hook; preview45 exclusion/five cameras/backview; shadowStock/Off; generation/poolReset; race/HUD temporal lifetime; dynamic/stationary constellation discovery; sticky brake identity; body0x152 learned signatures;0x112 wheels/0x102 brakes/alpha/static excluded; draw-local reflection/exactTCI restore; boundedF10; exact-build gates. R-GFX4 Reset/scene clear-and-relearn unchanged. No grace tuning/appearance/light/vertexRGB/oldFOV patch.

Trace R-GFX5-1/schema1 additive quality/UI headers, requested/logical_baseline/effective PP,monitor,physicalGetDesc,reasons/canvas. Effective viewport reconstructed from native Set/GetViewport events, invalidated on Reset/target/state-block changes; logical state remains. Masks16viewport/32UI/2FOV/8reflection/1AF. Existing32MiB allocation bound retained; no expanded per-draw state allocation. Native overrides record their HRESULT.

quality_research.py is read-only/exact-input/deterministic/bounded cave interpreter and Present/Clear audit, writes phase-local outputs only. reference_ghidra.py rejects wrong patcher hash before Java and uses ignored phase-local scratch/export. New tests inspect their safety boundaries/current native capture.

Native quality suite: hidden real HWND client/style restore; production x86 bridge on synthetic code; caps/descent/Create/Reset failures and echo; viewport/UI aspect; frame-coordinate mutation/overflow; byte/jump rollback; production wrapper trace and local UI failure without AF loss. No launched game/GPU validation.

Limits: margin half can precede split-camera viewport update; unknown external HWND replacement/multiple devices not human target; unreviewed backbuffer preservation may invalidate DISCARD; mixed-DPI/monitor migration untested. Keep exact failure evidence and narrow follow-ups.
