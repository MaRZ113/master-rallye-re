# Trooper frontend asset search

The narrow inventory covered Vehicle Select, Race Results, HUD scene XML and
their DataGx frontend/HUD resources in each build independently. Builds are
not merged: demo-8.4.1, demo-9.3.1 and retail.

| Build | Trooper-specific UI finding | Metadata | Meaning |
|---|---|---|---|
| retail | No Trooper-specific Vehicle Select, Race Results or HUD asset/reference found | No Trooper-named frontend asset in the targeted inventory | No retail Trooper icon or label mapping established |
| demo-8.4.1 | One Trooper hit in DataScene/FrontendScreens/Demo2MainMenu.hnt | HNT: 18,701 bytes, SHA-256 BEDF597823C52715BCBDBFE69475D4C9FC7974A4F4F7A8FA59B32D7FDC1E3C93; Vehicles/Trooper/complete.dx: 134,346 bytes, SHA-256 5719028E625AC36542B0679B64F3164AAD773C76672F706D676AC35327149360 | Attract/menu 3D model reference, not a car icon or localization entry |
| demo-9.3.1 | No Trooper-specific UI asset/reference found in the targeted directories | No Trooper-named frontend/HUD resource in the inventory | The Trooper model donor build does not supply an identified Trooper UI icon |

The demo-8.4.1 menu resource uses vehicles/trooper/complete and its textures
to render a 3D menu scene. It does not establish the identity of any indexed
carsheet frame. The retail ID25 runtime Trooper identity therefore has no
proven Trooper-specific frontend icon source in the searched build data.

The retail resources carsheet_025_000.dxt and smallcarsheet_029_000.dxt exist,
but their numeric filenames do not identify them as Trooper assets. No demo
assets were copied into Git; only paths, hashes and structural metadata are
recorded.

## Separate beta evidence

The beta checkout was consulted only for the narrow historical note in
research/r-demo/carsheet.md at beta commit
0fb0a6ff6d89f2fbca5f6600578a2614b9b8f91a. It establishes build-specific
carsheet dimensions and a same-build GXB/TGA transform, but does not identify
an icon by vehicle name. No branch merge or asset import was performed.
