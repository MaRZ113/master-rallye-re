# Generalized policy and exact research patch

**STOCK** returns pristine bytes exactly, using original single Car0-class pool.
**MIXED** chooses class0/1/2 separately at every AI loop iteration, then uses
the native class-filtered absolute-ID chooser. **DIVERSE** assigns Car1=2,
Car2=1,Car3=0 in static x86 emulation only. The sole human candidate is MIXED;
no mode/config/save mutation is added to retail. Future distributable config
must default to STOCK.

Class decisions do not read Car0 class. A current-pool-class cache only avoids
rebuilding when consecutive independently selected classes match. Native pool
cases remain `0x458112..0x4582D5`: T1 0..6, T2 7..13, T3 14..20 plus native
reward-gated bonuses22/23/24/21. Class-switch rebuild clears existing vectors,
retains allocation and excludes Car0 and previously configured AI IDs. Repeated
classes retain the native remaining pool. There are no persistent new per-class
banks. Duplicate classes are allowed; CarIDs are distinct in the controlled
four-participant fresh protocol. No experimental/demo/expansion IDs.

## Hook mechanics

Source SHA `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
MIXED output SHA `f9e8e556842602252ec39b2174e796f6cb67651d8f573f2565f9d2e5569bd9ac`.
Both size3,121,214. Gated to firstAI1,count3,ESI1..3 and native Race/Type2.
Only direct callers of `0x458090` found are the two Quick Race branches.
Wrong setup/type retains pristine chooser output and RNG calls.

| File offset | VA | Length | Original | Replacement / purpose |
|---|---|---:|---|---|
| `0x218` | section header | 4 | `94d22800` | `63d42800`: text VirtualSize `0x28D294 -> 0x28D463` |
| `0x5810B` | `0x45810B` | 7 | `8b84248c000000` | `e9f06123009090`: initialize scratch marker, replay class load |
| `0x58379` | `0x458379` | 9 | `8d4c2430e81e93fbff` | `e9965f230090909090`: independent class before stock draw |
| `0x582D5` | `0x4582D5` | 7 | `8a942494000000` | `e9fb6023009090`: initial driver setup versus class-rebuild continuation |
| `0x28E300` | `0x68E300` | 355 | Zero padding | Reproducible research selector from `general_code()` |

With B=original chooser ESP, B+0x14 stores selected ID (temporarily current slot
during rebuild); B+0x18 stores driver output (temporarily rebuild marker).
Eligible/used vector B+0x20; remaining B+0x30; driver owner B+0x48.
Arguments B+0x84 firstAI, +0x88 count, +0x8C class become the class cache.
Original exclusions +0x90/+0x94 are already callee scratch; rebuild sets them
to -1 and filters actual preceding published IDs instead. PUSHFD/PUSHAD offsets
are accounted for. ESI and loop end EBP are restored after inline pool cases.

Initial pool falls through normal driver setup `0x4582DC`. Rebuild skips that
setup and resumes stock size/draw at `0x458382`, preserving the single driver
pool. Normal selected-ID local, vehicle consumption, `0x458980` and all three
setters execute unchanged. No separate CarClass patch, no direct fixed-ID
substitution, no writes to NumCars/player/rules/course. Original aligned page
count, SizeOfImage, section raw size and participant allocations are unchanged.

## Reproduce / restore

```powershell
python tools/r_ai1_mixed_class.py build-general "<pristine MRallye.exe>" .research-output/r-ai1-1/randomized-candidate/MRallye.exe
python tools/r_ai1_mixed_class.py verify-general .research-output/r-ai1-1/randomized-candidate/MRallye.exe
```

Builder refuses overwrite; for another reproduction choose a new ignored
directory. Manifest alongside EXE contains exact original/replacement hex,
source/output hashes, sizes, ranges and purpose. Inverse verifier restores
pristine in memory and requires its exact hash; additional changes reject.
Restore the isolated install from its preserved original EXE and verify the
source SHA. Never commit/distribute the generated proprietary image.
