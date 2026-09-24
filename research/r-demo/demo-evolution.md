# September to November demo evolution

The generated `demo-evolution.json` compares case-folded relative paths, then SHA256 for paths present in both builds. An exact-hash path move is only a rename **candidate**. The same path can change contents without changing identity, and independent paths can contain identical bytes.

| Classification | Files |
|---|---:|
| Same relative path and SHA256 | 991 |
| Same relative path, different SHA256 | 340 |
| Only in demo-8.4.1 | 2,567 |
| Only in demo-9.3.1 | 1,163 |
| Removed-to-added unique-hash candidate | 52 |

The most visible shift is in image resources: 1,723 GXI paths appear only in 8.4.1, while 354 GXI and 624 DXT paths appear only in 9.3.1. The 38 GXP paths are new in 9.3.1 and are concentrated in frontend graphics. Counts are path-set results and do not by themselves prove conversion or deletion of individual artworks.

Both builds retain `DataGx/Vehicles/Trooper`, `Jump`, and `Wildcat`-named folders, but their resources must be compared by build. Vehicle folder presence and component counts are recorded in `cut-content.md`. Runtime loading differences between builds remain untested in this workspace.
