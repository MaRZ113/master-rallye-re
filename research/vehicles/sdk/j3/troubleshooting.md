# Troubleshooting

The CLI returns JSON with `status: FAIL_CLOSED` and a machine-readable
`diagnostic` containing an error code, field (when known), message and
suggested action.

| Diagnostic | What to check |
|---|---|
| `ADDON_DONOR_SOURCE_MISSING` | `vehicle-project.json/source_vehicle_dir`; include car.dx, complete.dx, wheel.dx and required DXT dependencies. |
| `ADDON_ASSET_DEPENDENCY_MISSING` | Restore the exact referenced DXT name or correct the donor DX edit. |
| `ADDON_DONOR_SOURCE_CHANGED` | Re-check source hashes after editing; update only after reviewing the intended donor change. |
| `ADDON_CLASS_SLOT_UNAVAILABLE` | The selected class has no free slot in this capability profile. Currently only additional T1 ID26 and T2 ID27 are supported. |
| `ADDON_PHYSICAL_ID_COLLISION` | Resolve the collision across all manifests or use auto allocation. |
| `ADDON_RESOURCE_FAMILY_COLLISION` | Give each addon a unique runtime/model/wheel/physics family. |
| `ADDON_RETAIL_DATA_MISMATCH` | Use the exact retail Data.sma pinned by the capability profile and its byte-matching unpacked root. |
| `GALOCAL UNKNOWN` in a future runtime | Runtime localization inputs are validated for the bounded J.3-B profile; stop and capture the Broker state instead of patching localization manually. |
| Wrong Vehicle Select after returning to a menu | The J.2 sparse mapping and republisher are included and statically verified in J.3-B bundles. A new runtime identity still needs the human return/reopen test. |
| Audio fallback | Use a tuned stock profile ID 0..24; custom audio authoring is deferred. |
| Runtime patch/preimage conflict | `runtime-prepare`/`runtime-verify` or launcher `--verify` must fail closed. Do not bypass exact preimage, build, or resource checks. |

Unsupported demo assets are not made compatible by renaming their directory.
Keep a failing source diagnostic and use a supported donor until an exact
format/build capability is qualified.
