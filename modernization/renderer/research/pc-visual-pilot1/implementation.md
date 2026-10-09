# Diagnostic implementation

`foliage_probe.hpp/.cpp` provides known fixed-function XYZ layout validation, finite float32 face signatures, bounded native getters and READONLY resource snapshots. `visual_policy` reads PS2FoliagePilot.Mode and Diagnostics with ConfigVersion1. Mode0/missing/invalid/version failure remains Stock;Mode1 requested remains effectively0 with blocked_on_draw_identity. Unknown build disables diagnostics. Optional texture Mode2 is invalid and remains Stock.

`visual_wrappers.cpp` adds an opt-in probe between existing native repair and ReflectionScope in draw_indexed_at. The original native DrawIndexedPrimitive still executes once and its HRESULT is returned unchanged. The probe has no SetRenderState/SetTexture/SetTransform calls. UP/nonindexed draws retain existing generic tracing and are unsupported by this content probe; no native API family is assumed to own the source merely because this diagnostic currently supports indexed lists.

Trace appends ps2_foliage_probe to the existing F10 draw record. It stores at most128 records outside the original FrameBuffer; its32MiB static allocation gate is retained. At most256 triangles and2048 vertices per candidate, and1MiB of resource bytes per captured frame. Only the existing F10 capture interval is sampled; idle frames and Stock default incur no new native getters/locks. No active classifier or per-frame full-scene hash cache exists.

All additions live in the existing proxy,CMake/native test infrastructure and renderer tools. No second DLL or alternate renderer was created. Existing producer/schema labels and fields remain intact; the diagnostic uses its own additive foliage-probe-v1 schema.
