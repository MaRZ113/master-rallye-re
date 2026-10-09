# R-GFX5 stable display scope decision

The project will continue MRRenderer development on the supported Windowed and Borderless baseline while deferring Exclusive Fullscreen recovery.

The user reports that Windowed live resizing passes after the R-GFX5-8 correction and that PreserveMargins v2 remains stable in runtime testing. Earlier human testing accepted Borderless as the fullscreen-like mode. The Exclusive restore failure is still reproducible as Error 2010 after minimizing and restoring. The device previously created true Exclusive successfully; recovery is the broken operation.

Exclusive is deferred because the exact runtime owner and recovery ordering are not established well enough to justify another behavioral change. R-GFX5-8 identified a possible interaction between the game's native window-mode owner, HWND restoration, and its WM_SIZE Reset path, but the complete cause remains a hypothesis. Preserving genuine D3D8 lost-device results and avoiding unsafe window-state writes is more important than masking that error.

This is a scope waiver, not a claim that Exclusive works or that its bug is deleted. `Mode=3` remains in the INI with its original meaning for future investigation. It is experimental and not recommended for ongoing testing. Windowed and Borderless remain suitable for R-CAM1 work. That phase focuses on renderer camera/control seams and can target either supported mode without depending on Exclusive recovery.

The current report and handoff are [R-GFX5-8 validation](../r-gfx5-8/validation.md), [R-GFX5-8 runtime handoff](../r-gfx5-8/runtime-handoff.md), and the focused [R-EXCL1 deferred issue](../r-excl1-deferred.md). The latter retains the static owner map, prior trace summary, known failure state, hypothesis and unanswered questions. Raw runtime captures are not included in the source handoff.

Reopen R-EXCL1 when a later milestone prioritizes true Exclusive recovery, or new runtime evidence identifies a safe owner synchronization seam. Keep its exact-retail build gate, native HRESULT behavior, resource-reset contract and reentrancy constraints. The scope decision can be revisited after R-CAM1; it does not permanently abandon Exclusive support.
