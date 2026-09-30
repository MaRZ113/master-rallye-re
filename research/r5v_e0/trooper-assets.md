# Trooper model and texture package

## DX conversion

Source DX files are the exact R-COOKER1.1 demo-9.3.1 revision-131 snapshots at
`master-rallye-re-rdemo/inputs/!other_research/9.3.1_dxTrooper`. The runtime
candidate uses the deterministic revision-131 → revision-135 converter. The
full DXT source is `corpora/demo-9.3.1/DataGx/Vehicles/Trooper`; DXT files are
copied without conversion.

| File | Source rev | Source SHA-256 | Output rev | Output SHA-256 | Validation |
|---|---:|---|---:|---|---|
| `car.dx` | 131 | `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` | 135 | `04a9aa09b813a0893953e6813b2d8ec4ac63a5545b987e12a29e692773de06e1` | 2,310 vertices, 1,911 triangles, 22 draws; tag101 retained |
| `complete.dx` | 131 | `27b429e271fc7afb3b71f45bf14c197c779473b087227dbf468fd48ad97a911f` | 135 | `a8ceffebf7f6fc8b8af489e1e4c7f62ca5ef3b537db4af3f8048e687997629bc` | 2,500 vertices, 2,375 triangles, 20 draws |
| `wheel.dx` | 131 | `9e7da7b3ea525fb5f29b61be763894ae98cd54fd0430c1b46b9f64d76e48d0ed` | 135 | `1a1aa4605e0319dd0d3fc68691845ed34559d1635c320986b23f9fe5750406ab` | 220 vertices, 252 triangles, 5 draws |

Each output parses as revision 135 with validated global indices and no parser
errors/warnings. The converter reports geometry, local index ordering,
collision, global index table and trailing bytes preserved. Output hashes match
the R-COOKER1.1 candidates previously reported loaded in retail.

## Referenced DXT files

The composer found 24 dependencies; every one parses and is staged in the
loose Trooper overlay. Hashes below identify the supplied demo files without
including their bytes in Git.

| DXT | SHA-256 | DXT | SHA-256 |
|---|---|---|---|
| `black-tga.dxt` | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` | `bumpbit64b-tga.dxt` | `b737cfbdaa4c8e0ae73be94818c10c87ea11abe617fa038ba8181735c43656d1` |
| `chair2-tga.dxt` | `3d5eab847f8053023132cc461a0f6aaeebc8379dd00b002a3d050e624a433ef4` | `chrome-tga.dxt` | `658946001e0c91939421a40e5ac86a91297d93fc5abc1927bf8ae77a4e89012b` |
| `dcambell-tga.dxt` | `0c8d56d72d5bf83b1530a6e9ccba63efe6bd9b7e0d7c5172b212672c038b2c62` | `drichard-tga.dxt` | `ebc196b631941ce570f78180aee4bef81a5a5d822a86a0ed370bc814fd02774b` |
| `giraffe64-tga.dxt` | `a85f3f13be8496a62b17222d1c1ac941816922784ce517bbe1bd2d55eccc5a5e` | `giraffepanels128-tga.dxt` | `7edb48b39303346855e8436812c7bacfc11fac4fdb203c18d0fe8ad063014731` |
| `glass-tga.dxt` | `f18690e02cad8d249db527ad546bac54db3343894aa136bc84bf0d9531fac71b` | `mastersticker231-tga.dxt` | `bd9d5dcffa7a4f58f1fd58ab19d081837473efef4b56de0ee0601347c11642a6` |
| `perspex-tga.dxt` | `29fddb30997bda1b38b006ffac98fd26a0671d94e8a6c4a86708c0f11f7f8fc0` | `rearsticker-tga.dxt` | `c73dffab0f61843647363e4acf1d64c38be74ea87b8ced26b314d547747a823c` |
| `rubber-tga.dxt` | `f95b5f1932dc01e2410176c624c07543b6442505c8e85e2f80099836cd3d9208` | `tlight64-tga.dxt` | `350b80e64d30287c3c1275448d2332788dbb93d16c0888a618e9863eca5d9f2e` |
| `topdoorl1-tga.dxt` | `e4b7cf607dbeb80fb822ae532c487e4989d8fd46d7662fc2aa644c59de58c376` | `tread-tga.dxt` | `0c13529c677d52f34f72dfb36f51b134cf92e48e67f5fa228e4d6f52ed853705` |
| `trhelmet32-tga.dxt` | `3d948b87bbdd1751161e2bc810a6f4e8295a13fbbe8164885f7ded45778b2999` | `troopwheel64-tga.dxt` | `3dc456826cd912b0313275baf60b484bc1e04dc3fc22615713029d47cad02874` |
| `trwheelrim-tga.dxt` | `39ed45af0dd1c92ddec8b8939fe29b46efcbca4f58c65f73ac461c3176eb091e` | `underdash-tga.dxt` | `0dff39d5744af8d9a9079d19ed6bb2299ed75d7757f79f02caef514c349792d3` |
| `wheel643-tga.dxt` | `aaae214381fc7cf2a364d4c9e00dd468ec65a7cd084185a44e12849dbf4e42fc` | `whitepaint-tga.dxt` | `ffedd8f6542db33a117dc0be72014a7cb7c70f477ce0048c90362cc3f791785d` |
| `whitesuit32-tga.dxt` | `6970fe173313c5449c10042ace0d5e115d73066a6474e8ae57fd7cde80a04c67` | `windscreen32-tga.dxt` | `f8c343db0d8647c62248521800fc7fad2dfba029f055e9a04e14fdb47252a30d` |

`mastersticker-tga.dxt` is present in the demo source folder but is not
referenced by these three DX resources, so it is not staged.

## Effective package

The beta Vehicle Composer resolver reads the retail SMA index and a temporary
loose Trooper tree. It reports `COMPLETE`, `LOOSE_OVERRIDE`, 27 effective
files, and no unresolved texture dependencies. The candidate contains only
these three DX files and the 24 referenced DXT files under
`DataGx/Vehicles/Trooper/`.
