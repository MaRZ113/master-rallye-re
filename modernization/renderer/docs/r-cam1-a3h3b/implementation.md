# R-CAM1-A3h.3b — Scheduler/UI Admission

## Diagnosis

The A3h.3a F10 capture `frame-17888-d1-00005934.jsonl` records a valid live France1 race certificate, an armed CleanView request, the verified native UI consumer, 474 captured UI ownership draws, and `scheduler_context_stale_or_uncompleted` as the admission rejection. The associated session reports 3,100,206 UI candidates and 554,106 rejected requested draws across the session, with no eligible or suppressed draws. The old capture did not record scheduler depth at the draw boundary, so it cannot independently prove whether those particular draws were in-flight.

The source ordering explains the impossible case: `scheduler_begin()` advances the generation and clears the snapshot; `before_submit()` publishes the validated camera/race/device/thread/Trace snapshot during scheduler execution; only the outermost `scheduler_end()` marks it complete, after restoring CameraFrame. Requiring `completed` at a UI draw that occurs before the outer scheduler returns rejects a valid current snapshot. The verified UI consumer path can now pass an explicit in-flight phase without changing scheduler ownership or the CameraFrame restore boundary.

## Admission rule

At the exact `DrawPrimitive` UI return RVA, CleanView accepts a snapshot only when all of these agree: current scheduler generation, current Trace frame, render thread, D3D device, timestamp (maximum age 250 ms), valid race/owner/camera identity, current native UI consumer scope, exact supported executable, live race certificate, active Freecam, focused window, confirmed native pause, owned UI hook, and the existing exact UI draw signature. The scheduler phase must be either:

- `current_inflight`: depth is nonzero and the same-generation snapshot is valid but not yet completed; or
- `current_completed`: depth is zero and the same-generation snapshot is valid and completed.

All other phase combinations fail open. An old generation/Trace frame, invalid identity, wrong thread/device, expired time, or missing UI scope is still rejected. The H request is not cleared by a draw-level miss. Only verified UI draws with current scope identity, FVF `0x142`, triangle-list topology, exact callsite and positive primitive count may be suppressed. Non-UI draws remain untouched.

No native hook, scheduler ABI, scheduler lifetime, CameraFrame byte range, Freecam ownership, or restoration boundary changed. The wrapper still returns `S_OK` only for the exact verified primitive suppression path.

## Diagnostics

F10's `ui_margins` record now preserves draw-boundary phase/depth, snapshot valid/completed flags, current and snapshot scheduler generations, current and snapshot Trace frames, their match flags, thread/device/UI-scope checks, snapshot age, detailed first/last rejection reasons, and counters by gate. Counters are labeled `cumulative_since_diagnostics_reset`. `clean_view_rejected_inflight` separates failures while a scheduler is active from `clean_view_rejected_stale` outside it. The next runtime capture can therefore confirm the actual phase at the exact consumer without an extra diagnostic build.
