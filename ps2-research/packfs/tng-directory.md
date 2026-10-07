# TNG directory inventory

Canonical body: 391929a42dac29eaa6a4306d9e178ad7da925a5426de0befd5550524cc6a56c4

Directories: **137**. Files: **3599**.
Hash buckets: 1024; codec descriptors: 4.

Manifest order is serialized node-pool order. `entry_index` is a zero-based offline index, not a proven engine resource ID.

| Extension | Files |
| --- | ---: |
| .BSP | 36 |
| .CFL | 36 |
| .DAT | 2 |
| .DISABLED | 1 |
| .GXI | 3177 |
| .ICO | 1 |
| .JBF | 1 |
| .PSB | 54 |
| .PSM | 163 |
| .PSS | 46 |
| .XML | 82 |

| Storage | Files |
| --- | ---: |
| packfs_lzo | 3345 |
| raw | 254 |

Total stored bytes: **1225915283**.
Total unpacked bytes declared by resource headers/raw directory sizes: **1419944771**.
The latter is a header inventory, not full decompression validation of all resources.

All 3599 file ranges are valid. No overlaps; ranges cover TNG.000 completely with no gaps.
All 3345 codec `gz` resources have header `(compressor_id=1, unknown_0x05=1, block_size=8192)`.

## Resource families

- HUD: 135 name-matched candidates.
- grass_detail: 175 name-matched candidates.
- water: 46 name-matched candidates.
- reflection: 19 name-matched candidates.

Course: 2232 files.
CommonTextures: 368 files.
Particles: 27 files.

Exact target records and hashes are in `extraction-provenance.json`; family inventories are in `graphics-targets.json`.
