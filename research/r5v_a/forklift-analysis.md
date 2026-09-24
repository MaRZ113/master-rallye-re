# Forklift archaeology

**Classification: ASSETS_WITHOUT_REGISTRY.** It is a substantial leftover vehicle asset set, not a confirmed playable vehicle. This label means no named initializer in the final 25-record EXE constructor; it does not prove that no other code path can instantiate it.

| Evidence | Observation |
|---|---|
| Asset folder | `DataGx/Vehicles/forklift` exists in the final unpacked SMA. |
| Main DX | `car.dx`, `complete.dx`, `wheel.dx` are present. |
| Textures | 16 DXT files; exact names and SHA-256 in final JSON. |
| Physics | No `Vehicles/Forklift/` section in final `DataGame/vehicles.xml`. |
| Registry | No Forklift literal in the 25 named records at final EXE 0x458E70-0x4598CB. Record index 25 is default constructed, not proven to name Forklift. |
| Text | `STEEL MONKEYS FORKLIFT` at EXE VA 0x6E0924 and `FORKLIFT` at 0x6E0B0C; localization table includes an entry after Ufo. |
| Frontend/events/progress | No Forklift literal in final DataGame or DataScene XML; no per-car unlock found. |

Previous R4B/R4C corpus analysis found `forklift/car.dx` tag101 structurally parseable but with non-finite collision coordinates. The 25 normal cars use a different finite hull pattern. Forklift thus does not pass the same collision-readiness gate as a stock vehicle. No runtime claim is made.

**First extra-slot proof payload:** duplicate an existing normal vehicle under a new name with matching physics and display metadata. Only after slot creation works should a separate Forklift trial address its physics and collision outlier. This prevents an asset failure from being mistaken for a slot failure.