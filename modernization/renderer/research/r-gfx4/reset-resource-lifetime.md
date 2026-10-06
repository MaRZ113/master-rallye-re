# Reset resource lifetime

Previous successful Reset erased resources.items entirely. Real MRallye kept its MANAGED objects, while the proxy forgot their creation serials. geometry_signature then returned zero for reused VB/IB/textures. Two later F10 frames remained entirely UNKNOWN; this was metadata loss, not an unusually long classifier warm-up. See resource-lifetime-evidence.json for independently counted creations/Reset segments and input hash.

| Kind/pool | Successful Reset metadata | Generation |
|---|---|---|
|Texture/volume/cube/VB/IB MANAGED|preserve|unchanged|
|SYSTEMMEM/SCRATCH resource|preserve|unchanged|
|CreateImageSurface|preserve, inferred SYSTEMMEM|unchanged|
|DEFAULT texture/VB/IB|erase|fresh serial on observed recreation|
|CreateRenderTarget / CreateDepthStencilSurface|erase|fresh serial on recreation|
|unknown pool/method|erase conservatively|fresh if recreated|

Failed Reset changes neither metadata nor temporal epoch/race context. Successful Reset clears native/logical state shadows, temporal tracks, confidence and race context, independently of logging; it leaves next_serial monotonic. Resource metadata is observation, not an added COM reference. Child Release remains unwrapped, so lifetime_observed=false; pointer reuse observed through Create always receives a new generation and invalidates temporal knowledge. The existing 8192-resource bound retains fail-closed invalidation behavior.

Pool values/argument indices are from pinned D3D8 declarations. Persistence is supported specifically by [Wine's D3D8 Reset contract tests](https://github.com/wine-mirror/wine/blob/master/dlls/d3d8/tests/device.c): test_reset resets with live MANAGED and locked SYSTEMMEM/SCRATCH resources. test_image_surface_pool checks CreateImageSurface returns SYSTEMMEM; do not copy the historically misleading D3D9 migration note equating it to SCRATCH. Consulted 2026-10-06. These tests support API semantics, not a new MRallye runtime pass.

The mock timeline registers managed VB/IB/texture plus default VB, learns a vehicle, fails Reset without mutation, succeeds Reset, verifies preserved serials/default removal/cold epoch and reuses managed objects to learn/modify again. Separate tests cover default texture, RT/depth, system memory, scratch, cube/volume pool argument positions and fresh pointer generation. No real Reset or resource creation call is suppressed/replaced by this fix.

Reset trace records metadata_removed, metadata_retained, classifier_epoch and frame. Successful-reset and relearn counters are cumulative; frame summaries carry constellation/body/wheel counts. Stage A must demonstrate a real successful Reset and new positive IDs/generations after warm-up before proceeding to reflection.
