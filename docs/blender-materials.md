# Blender vehicle material previews (R4D.1 V2)

Preview V2 uses the executable-traced DX flag byte 0 for alpha enable and byte 1 for alpha test selection. The observed 78 vehicle DX resources all have byte 1=0, so their enabled alpha materials preview as blended. Stage-0 texture color is shown through Principled Base Color; stage-1 environment/helper composition is not approximated until M1/M3 game observations.

Each preview material carries ordered serialized slots, the exact four raw flag bytes, the serialized mask, traced alpha choice, source DXT path, and the preview source-slot index. Draw-specific canonical metadata remains on the object. Identical images with different flags/slots/masks receive separate preview materials. The node graph is a preview; source DX and sidecar metadata are canonical. No material writing is supported.

The executable establishes a stage-0 texture/vertex-diffuse modulation and an environment stage-1 path with camera-space normals. The exact slot-to-stage binding for Null-slot cases and body-helper visual response remains open. Preview status: **PARTIAL**. M1-M4 have human in-game results: whitepaint and chrome are reflection helpers, glass and active brake glow show continuous alpha response. Preview still does not claim exact Direct3D 8 parity.

Runtime closeout: research/r4d_1/runtime-results.md. A preview may label slot-1 helpers and alpha paths with runtime confidence, but does not reproduce the exact environment transform or blend sorting.
