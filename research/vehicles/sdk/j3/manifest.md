# Addon manifest settings

The stable public contract is `manifest_version: 1` in
[`../schema/addon-manifest-v1.schema.json`](../schema/addon-manifest-v1.schema.json).
Unknown properties, duplicate JSON keys, invalid paths, unsupported policy
values and physical/class-slot conflicts fail closed.

| Setting | Meaning |
|---|---|
| `addon_id`, `description` | Stable collection identity and donor/content provenance. |
| `vehicle_class` | `T1`, `T2` or `T3`; an addon position must also exist in the selected target profile. |
| `physical_id` | `auto` uses stable addon-ID order over available slots; `explicit` pins an allowed ID. This is separate from the authored addon ID. |
| `class_local_placement` | V1 supports `append`; custom ordering is deferred. |
| `identity` | Independent runtime, model, wheel and physics family names. For the current vehicle project bridge these must agree with the declared generated package family. |
| `assets` | Runtime model package root and required DX roles. DXT dependencies are discovered from DX references. |
| `frontend` | Manufacturer, model, combined display name, four stats, known stock Vehicle Select frame and SmallCarSheet frame. Art fallback frames are explicit; unique art is not required. |
| `race_colour_rgba` | Independent four-number marker RGBA. It is not inferred from body DXT colors. |
| `unlock` | `always_available` or a qualified `mirror_stock_unlock` source. Player availability is separate from AI eligibility. |
| `audio` | `stock_profile` with tuned stock profile ID 0..24. Physical CarID is never changed to obtain sound. |
| `ai_eligibility` | Mode-generation boundary. Quick Race, new Cup and new Master Rallye are separate boundaries; Challenge stays authored. |
| `results` | Fixed presentation name, independent of native DriverID. |

Automatic ID resolution is deterministic for a full manifest collection. Under
`retail-2001-known-build-v1`, the only supported added slots are ID26/T1/local7
and ID27/T2/local7. The exact identities qualified by runtime are separately
listed in `runtime_qualified_addon_profiles`. Resolving a different name to an
available slot is **synthetic planning only**, not a runtime qualification.

For example, Glacier Sprint can be planned in ID27/T2/local7, but the current
native runtime bundle still contains the ID27 R5VQualifier profile and requires
its reference composition. No compiler output may silently present that as a
working Glacier runtime package.
