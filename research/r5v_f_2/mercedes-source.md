# Mercedes and MercedesAlpha source audit

All corpora were read directly from the user's supplied `D:\Game\Master Rallye\corpora` tree. Demo builds are separate and do not use `Data.sma`. No corpus file was modified or copied into Git.

## Registered identity across demos

The September demo's constructor table records ID2 as literal `Mercedes`, class0 / T1 local2, record offset `0x4C`, call `0x004478E4`. The November demo independently records the same identity/class/index at call `0x0044D3D4`. Both call sites have raw integer pushes `[0,5,6,3,4,0,2]` (right-to-left call values `[2,0,4,3,6,5,0]`). The four presentation integers are `[4,3,6,5]`; the final integer is 0 and remains untyped for the demo builds.

Demo-8.4.1 has a `DataGx/Vehicles/Mercedes` package and a 121-value `Vehicles/Mercedes` physics section. The model folder contains all three DX roles and 25 DXT files. Hash comparison shows its `car.dx` and `wheel.dx` are exactly the same as the registered `LandCruiser` versions, and all three GXM roles are exactly identical to `LandCruiser`; its sidecars also use LandCruiser material/texture names. `complete.dx` differs, so this folder is a mixed/aliased package, not an authoritative unique Mercedes model.

Demo-9.3.1 again registers Mercedes ID2 and retains a Mercedes physics section, but has no `DataGx/Vehicles/Mercedes` folder or DX/DXT model package. This is an identity/config record without a packaged model in that build.

## Distinct demo-8.4.1 model candidate

`DataGx/Vehicles/Copy of Mercedes` is the distinct source candidate. Its root contains `car.dx`, `complete.dx`, `wheel.dx`, corresponding GXM and sidecars, and 25 DXT files. The sidecars reference 19 unique DXT textures for car, 25 for complete, and 6 for wheel; every dependency exists at the package root, and all referenced DXT containers parse. The material/texture names include Mercedes-specific stems such as `MBackb`, `MBDoor64`, `MFGrill64`, `MercWheel64` and `MercTread`. Hashes and the per-texture dependency list are in the machine-readable inventory.

This package is not a registered folder name or a ready retail package. If later converted, the runtime overlay folder would be `DataGx/Vehicles/Mercedes`; retail currently has no model folder at that path, so this does not overwrite another retail vehicle.

## MercedesAlpha is separate and incomplete

| Folder | DX roles | Other source files | Conclusion |
|---|---|---|---|
| `MercedesAlpha` | None | `car.gxm`, `wheel.gxm`, sidecars/GXI; no DXT | Partial source variant only |
| `Copy of MercedesAlpha` | `car.dx`, `wheel.dx`, both revision125; no `complete.dx` | GXM, sidecars, 19 DXT | Partial alternate package, not a playable three-role vehicle |
| `Mercedes/lpha` | None | Exact GXM/sidecar mirror of `MercedesAlpha` | Nested duplicate of partial source variant |
| `Copy of Mercedes/lpha` | `car.dx`, `wheel.dx`, both revision125; no complete | Exact DX/GXM/sidecar/DXT mirror of `Copy of MercedesAlpha` | Nested duplicate of partial alternate package |

Neither executable contains the literal `MercedesAlpha`, neither demo text/config scan found it, and no `Vehicles/MercedesAlpha` physics family or registry record exists. Treat Alpha as an incomplete alternate/source variant; the corpus does not prove whether it denotes a texture mode, prototype, or another authoring state.

## Source recommendation

Use the root `Copy of Mercedes` package as the only plausible distinct historic model source. Do not use registered `Mercedes` as the payload: it is hash-proven to alias LandCruiser in car/wheel and source GXM. Do not combine `MercedesAlpha` with the full Mercedes package. The selected source remains blocked by the revision conversion gate; see [mercedes-model-conversion.md](mercedes-model-conversion.md).
