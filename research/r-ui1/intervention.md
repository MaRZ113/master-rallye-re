# Independent native UI candidate

Exact source is pristine retail
bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4,
size3121214. Output profile retail-r-ui1-opponents-seven-hardened, SHA256
5507f3ebc474931084f9ddf2b06a3f7afe186c4e29a2dbd81519b86d00f32966.

After the existing third Opponents append, hook479DCB..479DD3 jumps to fresh
68E300..68E35C (92 bytes). It saves all registers/flags, constructs localized
bank64 entries3..6, and inserts each into the same EBX native StringList using
407B30(end,1,&enString). Each temporary is released after the list copies it.
It restores state, replays the two original MOVs and continues at479DD3 so the
stock third temporary is freed by its original path. No persistent/custom cache.
Native growable StringList storage handles7 entries; physical participant arrays
are not touched. No class/driver selection or RNG call is added.

47A32C changes CMP EBP,2 to CMP EBP,6 only for Opponents right-arrow status.
Mode/difficulty selectors and actual dynamic navigation remain stock. .text
VirtualSize declares bounded zero padding; no new section or file size change.
Only known research Loading and native NULL-safe Dump guards are composed.
Their ranges68E2A0/68E2C0 do not overlap this stub. Historical capacity/randomizer
caves are absent: construction starts from pristine, never an arbitrary patched EXE.

[Safe manifest](patch-manifest.json) records offsets, lengths and range hashes.
Full reproduction manifests stay with ignored outputs. Builder checks exact
source hash/size, original bytes, PE offsets, non-overlap, localized table identity
and exact output pin. Verification inverts only declared ranges, restores pristine
hash, rebuilds and compares bytes. No unknown-build support.

Reproduce:
`python tools/r_ui1_opponents.py build <pristine-MRallye.exe>
--output .research-output/r-ui1/MRallye.exe`.
Builder refuses overwrite. Verify:
`python tools/r_ui1_opponents.py verify <candidate>`.
No loose data/DLL needed. Keep original in isolated install; restore it when done.
No proprietary executable is committed or proposed for public distribution.
