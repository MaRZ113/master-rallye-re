# R-GFX5 stable display scope decision

The project will continue MRRenderer development on the supported Windowed and Borderless baseline while deferring Exclusive Fullscreen recovery.

Windowed live resizing passed in-game validation after the R-GFX5-8 correction, and PreserveMargins v2 remains stable in gameplay testing. Prior in-game validation accepted Borderless as the fullscreen-like mode. Exclusive restore failure remains reproducible as Error 2010 after minimizing and restoring. True Exclusive device creation succeeded; recovery is the failing operation.

Exclusive is deferred because the exact runtime owner and recovery ordering are not established well enough to justify another behavioral change. R-GFX5-8 identified a possible interaction between the game's native window-mode owner, HWND restoration, and its WM_SIZE Reset path, but the complete cause remains a hypothesis. Preserving genuine D3D8 lost-device results and avoiding unsafe window-state writes is more important than masking that error.

This is a scope waiver, not a claim that Exclusive works or that its bug is deleted. `Mode=3` remains in the INI with its original meaning for future investigation. It is experimental and not recommended for ongoing testing. Windowed and Borderless remain suitable for R-CAM1 work. That phase focuses on renderer camera/control seams and can target either supported mode without depending on Exclusive recovery.

The current report and validation procedure are [R-GFX5-8 validation](../r-gfx5-8/validation.md), [R-GFX5-8 runtime procedure](../r-gfx5-8/runtime-handoff.md), and the focused [R-EXCL1 deferred issue](../r-excl1-deferred.md). The latter retains the static owner map, trace evidence, known failure state, hypothesis and unresolved questions. Raw runtime captures are not included in the source handoff.

Reopen R-EXCL1 when a later milestone prioritizes true Exclusive recovery, or new runtime evidence identifies a safe owner synchronization seam. Keep its exact-retail build gate, native HRESULT behavior, resource-reset contract and reentrancy constraints. The scope decision can be revisited after R-CAM1; it does not permanently abandon Exclusive support.
