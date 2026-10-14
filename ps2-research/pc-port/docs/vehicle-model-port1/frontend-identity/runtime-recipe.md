# Minimal frontend admission capture

Purpose: close the current resource-owner join; no replacement or native mutation.

1. Use opt-in frontend diagnostics in the PS2-enabled overlay. CPU upload mirroring
   must be enabled before original COMPLETE resources are loaded. Keep replacement
   disabled; other graphics options and menu/HUD cache remain unchanged.
2. Select PC Forester in Vehicle Select. Capture one bounded frame; rotate the
   model and capture a second. Read only current process/session, not historical
   pointers. The completed current scene must equal VehicleSelect.
3. At that frame, join the current CarModel Egg's `gaFrontendCarMoverAI` slot to
   its en3d state. Validate vtable/current scene membership and current name
   string ID at en3d +0xc; require `Vehicles/Forester/complete` in exact original
   resource naming. Observe +0x74 cached object and its current lifetime;
   do not invoke original model-loading/destruction functions.
4. Compare current full-coverage CPU mirror hashes against all 17 source digests,
   retaining actual VB/IB generation/revision, FVF, stride, ranges and native
   world/view/projection. Log at most one full manifest per requested frame.
5. Select another car, then return to Forester. Invalidate on owner/name/resource
   changes. Capture after a real Reset and after menu exit/reentry; frontend
   draw ordinals and raw pointers must never become admission constants.

Expected compact record fields:

```json
{
  "type": "ps2_frontend_model_identity",
  "frame": 0,
  "scene_generation": 0,
  "scene_current": "FrontendScreens/VehicleSelect",
  "owner_validated": false,
  "model_name_current": "UNKNOWN",
  "cached_model_lifetime_validated": false,
  "vb_generation": 0,
  "ib_generation": 0,
  "upload_revision_current": false,
  "matched_source_records": 0,
  "expected_source_records": 17,
  "world_view_projection_current": false,
  "replacement_authorized": false,
  "reason": "current_native_owner_to_mirrored_geometry_join_required"
}
```

This is an example schema, not a record claiming a successful capture. If the
existing observer cannot safely obtain the current Egg/resource join, stop at
that interface. Do not scan arbitrary memory for a vtable, call a factory or
use desired Broker selection as proof of loaded geometry.
