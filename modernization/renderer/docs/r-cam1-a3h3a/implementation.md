# R-CAM1-A3h.3a Implementation

## Change

Clean View now separates the operator's H request from the current paused-Freecam context and the individual native UI draw. Non-UI `DrawPrimitive` calls never run Clean View admission. An unverified UI draw is forwarded and records a rejection without clearing the request; only a real lifecycle/context invalidation disarms it.

The camera scheduler publishes a bounded snapshot containing its completed scheduler generation, Trace frame, race generation, owner lifetime, camera, render thread, device identity, and sample tick. The verified UI draw boundary accepts that snapshot only for the same scheduler generation and Trace frame, on the same thread/device, within 250 ms. Pause, focus, race certificate, Freecam state and hook ownership are revalidated at the draw boundary. Admission no longer requires the temporary CameraFrame pose scope or synchronized frustum to remain open.

CameraFrame modification/restoration boundaries were not extended or moved. The exact UI callsite, consumer identity, FVF `0x142`, triangle-list topology, exact-build check, and fail-open behavior remain required. `BeginScene`/`EndScene` now maintain the device scene-active flag through the interface generator, preserving deterministic generated-file checks.

## Diagnostics

The bounded `ui_margins` F10 metadata now reports user request, context validity/reason, whether the H edge or initial arm was observed, UI consumer scopes and draw candidates, draw admission rejections and last reason, suppression count, disarm count/reason, and associated Trace/scheduler frame IDs.
