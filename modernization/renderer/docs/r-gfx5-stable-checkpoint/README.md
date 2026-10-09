# R-GFX5 Stable Baseline

Status: **`STABLE_BASELINE_CHECKPOINTED`**. This checkpoint accepts a supported renderer baseline for continued development. It is not `R-GFX5_ALL_FEATURES_COMPLETE`; the experimental display matrix has not all been closed.

## Supported and deferred modes

Use Windowed for interactive development and resizing. Use Borderless for fullscreen-like play. Stock (`Mode=0`) remains the default compatibility control. Exclusive (`Mode=3`) remains selectable for future work, but is experimental and known broken after minimizing or losing focus: it may end in Error 2010 during device recovery. Do not use Exclusive as the primary R-CAM1 test mode or silently substitute Borderless.

Recommended development display settings:

```ini
[Display]
Mode=1
Width=1280
Height=720
RefreshRate=0
```

The configured Windowed size initializes the normal client. A later normal-window resize updates its current target. Borderless retains its existing monitor-sized policy. This is a documentation recommendation; Stock defaults and other quality settings are unchanged.

## Runtime evidence

- **Windowed live resize — `CONFIRMED_BY_RUNTIME`, PASS.** In-game validation confirmed immediate manual resizing with explicit initial dimensions, without a Maximize/Restore workaround. The source fix compares the original Reset request with actual HWND client dimensions before normalizing echoed dimensions. R-GFX5-8's temporal native tests also cover this order; see its [implementation and validation](../r-gfx5-8/validation.md).
- **PreserveMargins v2 — `CONFIRMED_BY_RUNTIME`, PASS.** In-game validation confirmed stable HUD and animated menu decorations, including pause/resume and extreme aspect. The implementation uses a temporary draw-local WORLD transform and restores it immediately; it does not edit persistent UI packet coordinates.
- **Borderless — prior supported baseline retained.** Prior in-game validation established Borderless, Alt+Tab and high-resolution operation. This checkpoint adds no new test and makes no new combined-feature claim.
- **Exclusive restore — `CONFIRMED_BY_RUNTIME`, FAIL.** Error 2010 is reproducible after minimizing and restoring. Earlier trace summaries show successful true Exclusive device creation and initial Reset, followed by device loss and a failed native Reset during recovery. The exact internal cause is not confirmed.

Earlier R-GFX3/R-GFX4 features and previously accepted R-GFX5 graphics behavior remain the development baseline: Centered4x3, AF16 with stage-0 MINFILTER behavior, native MSAA, Gameplay FOV with synchronized CPU culling, frontend preview separation, MenuFreezeFix, shadows, vehicle semantics and reflections, cursor handling and shutdown. Their regression coverage remains in R-GFX5-8. This checkpoint does not claim a new combined runtime pass for every feature combination.

## Preserved diagnostic pilot

PC-VISUAL-PILOT1 is **`BLOCKED_ON_DRAW_IDENTITY`**. CPU upload provenance, WRITEONLY VB/IB observation, Lock/Unlock forwarding, buffer generations and revisions, QueryInterface/COM ownership, F10 capture and conservative Reset invalidation remain integrated. Mode 1 stays visually Stock until runtime draw identity is established. `Mode=0` and `Diagnostics=0` remain the defaults. No PS2 material override or vegetation effect was introduced.

## Continue development

R-CAM1 is **`AUTHORIZED_NEXT_PHASE` / `READY_TO_PLAN`**. Its first supported target is Windowed or Borderless. Freecam, teleport, HUD hide, camera pose save/load, configurable FOV and camera roll do not require Exclusive recovery. Preserve the existing Gameplay FOV/culling and frontend preview boundaries, vehicle and UI semantics, resource lifetime, D3D8 forwarding, and foliage diagnostics.

Photo Mode remains a separate future phase. R-GFX5 closeout of the original full display matrix is not implied by this checkpoint.

## References

- [Scope decision and Exclusive waiver](decision.md)
- [Deferred Exclusive issue R-EXCL1](../r-excl1-deferred.md)
- [Checkpoint manifest](checkpoint.json)
- [R-GFX5-8 validation and build identity](../r-gfx5-8/validation.md)
- [R-GFX5-8 Exclusive static analysis](../r-gfx5-8/exclusive-static-analysis.md)
- [PC-VISUAL-PILOT1 status](../../research/pc-visual-pilot1/final-report.md)
