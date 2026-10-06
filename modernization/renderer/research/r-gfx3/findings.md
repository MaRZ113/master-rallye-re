# R-GFX3 findings

READY_FOR_HUMAN_RUNTIME, not a visual PASS. Implemented default-off AF, vertical FOV and Stock/Off shadow policy in long-term renderer. Details in implementation.md and state-virtualization.md; test protocol in runtime-handoff.md.

Confirmed input refinements: projection returnRVA0x0013FA75 differs from VIEW0x00161A26; shadow is DrawPrimitive returnRVA0x001881EB rather than the attachment's indexed description. No constant shadow-opacity equation was proven; opacity deferred. Actual GPU caps are not inferred from native mocks. Shared projection setter and CPU culling require human wider-FOV/extra3D-consumer coverage.

Preserve wheel directed-axle correlation and build-specific allocation/Reset evidence from retired closeout5861ed2. No new lighting/reflection/weather/backend work or game patches.
