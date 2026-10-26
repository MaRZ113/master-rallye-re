# GT3 vehicle audio: original-bank structure and native consumers

Research date: 2026-10-26. This work reads the user's original
`E:/Games/GT_Model-Tools/VOL/GT3_Extracted` files. It recovers a complete local
bank catalog, CAR-to-ENGINE sound references, GT3 INST samples, named-event
dispatch and native leaf pitch. These are static findings. No game or PCSX2
session was run, and the exported raw voices do not reproduce the gameplay mix.

## Source identity and address mapping

| Source | Bytes | SHA256 |
|---|---:|---|
| Original `GT3.VOL` | 3,876,222,976 | `27c84369911bf2352bbe5f6ba21830357c23cd82fe529b25c38c22986d37fa88` |
| Original `CORE.GT3` | 887,311 | `fdcea2aa43231873592adee0fb96499f2e40979e0269191af1eafcf95da12b0b` |
| Raw-deflate expansion | 2,437,879 | `67f4c71addfdfbd2cd539229b6976259ffe2343a4c888e663f33308901a388fd` |
| Original mapped segment | 2,437,603 | `e7a00af1e924711e2441c9c0c00ad3a1f4b3f8b251cafac644a94d059abf3645` |
| Generated analysis ELF | 2,441,699 | `0ec332928ab4ff1ea48f9c36f57ca19019c1cfe4e3b3fbd3279176ee6cf110b9` |

The container starts with two load-source bytes and a uint32 expansion length;
raw deflate starts at original file offset 6. The expanded image contains two
uint16-length-prefixed 128-byte RSA values, then one segment and entry address.
RSA authentication was **not** performed. The initial blobs are not instructions.

Expanded offset `0x114` maps to native address `0x100000`; entry is `0x100008`.
For this build, `expanded_offset = address - 0x100000 + 0x114` and the generated
ELF's `file_offset = address - 0x100000 + 0x1000`. The tool retains original segment
bytes exactly. Its ELF header and RWX permissions are generated analysis aids.
The paired original `SCUS_971.02` supplies the MIPS ELF flag convention; this is
not an assertion that the generated ELF was an original disc member.

The local PDTools `PDTools.GT4ElfBuilderTool/GTImageLoader.cs` describes the same
length-prefixed RSA/segment carrier and explicitly discusses pre-GT4 GP handling.
Ghidra 12.1.4 with Emotion Engine Reloaded successfully imported this generated
ELF as `r5900:LE:32:default`. Original entry instructions establish GP `0x3579f0`
and BSS clearing beginning at `0x353200`; the script adds an uninitialized BSS
analysis block. Neither that block nor Ghidra's pseudocode is original source.
REA's Windows native provider was not used as an R5900 decoder.

## Complete volume catalog

The existing bounded `gt3_ui_icon.inventory/read_member` parser admits 5,333
RoFS2.2 members. There are 1,216 `sound/` members: 1,215 banks plus `se.inf`.
GT3 uses `sound/`, while the supplied GT4 corpus uses `carsound/`.

| Category | Banks |
|---|---:|
| `sound/engine` | 135 |
| `sound/normal0` | 135 |
| `sound/normal1..3` | 134 each |
| `sound/turbo0..3` | 134 each |
| INST banks | 6 |
| `sound/rn_01.es` ENGN | 1 |

All 1,215 banks pass complete header/span and ADPCM frame/terminal/padding
validation: 1,209 ENGN and six INST; 8,554 voice/entry records refer to 8,501
distinct bank-local sample spans. Of these records, 8,480 have repeat loops.
There are 548 distinct whole-bank decoded hashes, including 262 hash groups
with multiple original member names. Equal hashes are byte identity, not proof
that differently named tuning stages have different acoustic roles.

The original spelling `sound/engine/3406` and `sound/normal0/3406` is preserved;
the tool never silently pads or repairs original member names. Source offsets,
stored/decoded hashes, record locations, full allocated spans and actual sample
spans are retained in the private catalog. Metadata scanning validates every
frame; full PCM decoding was exercised on selected entries, not every span.

## GT3 INST is distinct from GT4 JAM

| Header offset | Recovered field |
|---:|---|
| `0x00` | `INST` |
| `0x04` | CPU relocation base, zero on disc |
| `0x08` | Header bytes |
| `0x0c` | SPU relocation byte base, zero on disc |
| `0x10` | Body bytes |
| `0x14` | Body pointer/offset |
| `0x18` | Voice-record count |
| `0x1c` | Voice-record pointer/offset |
| `0x20` | Program count |
| `0x24` | Program-pointer table |

Voice records are 24 bytes. Their uint32 at `+0` is an SSA in eight-byte units;
the decoder therefore uses `body + SSA*8`. This is now independently supported
by original native code: the relocator at `0x268630` relocates the header pointers
and program pointers, then shifts the SPU byte-base difference right by 3 at
`0x2686dc` before adding it to each voice's uint32 SSA. `0x22c1a0` selects the
voice table at header `+0x1c` and multiplies the voice index by 24.

Program records contain a four-byte header followed by byte voice indices,
padded to four bytes; the table contains absolute bank-relative pointers.
The pointer/index graph is recovered. Program header mix/envelope semantics
have not been reconstructed.

| Bank | Voices | Programs | Unique sample spans |
|---|---:|---:|---:|
| `gt3sys.ins` | 14 | 1 | 11 |
| `gt3se01.ins` | 26 | 3 | 21 |
| `gt3se02.ins` | 10 | 1 | 5 |
| `menu.ins` | 46 | 13 | 14 |
| `se01.ins` | 18 | 2 | 13 |
| `sys.ins` | 11 | 1 | 8 |

The parser accepts the observed zero header/body padding of 0, 4 or 16 bytes.
Each distinct SSA partitions a complete bank body. Repeat streams terminate
with flag 3 and retain the actual loop-start marker. One-shot streams terminate
with flag 1 and may include a canonical flag-7 silent trailer, excluded from the
audition PCM. A flag-4 start marker in a one-shot does **not** become an active
WAV loop. Unknown frames, unaccounted trailers and out-of-range pointers fail.

## Named events now have original-code routing

`sound/se.inf`, volume offset `1505542144`, is a 648-byte GTSE v1 member,
SHA256 `8bd74f6834a52e39ea0708db4b875a5910e3151d1f7e35e417864953ac9d376e`.
The initializer at `0x22c3e8` loads the following instrument slots:

| Token high byte | Bank |
|---:|---|
| 0 | `sound/gt3sys.ins` |
| 1 | `sound/gt3se01.ins` |
| 2 | `sound/gt3se02.ins` |

`0x22c3a0` relocates GTSE strings. The initializer compares names against the
40-entry native event-name table at `0x2e9380`. `0x22c588` fetches the matching
GTSE token. `0x22c5b0` extracts the bank as `token>>24`, the primary voice as
`(token>>12)&0xfff`, and the secondary voice as `token&0xfff`; selector 2 selects
the secondary voice. `0x22c658` handles the firing wrapper. Therefore event
association is independent of listening, spectrum guesses or filenames.

Of 42 GTSE names, 39 match this native enum. `bolt`, `j_up` and `j_down` have
valid tokens but no entry in this particular 40-name enum. Conversely native
`slide` is absent from the supplied GTSE member. These bounded observations do
not establish that those sounds are globally unused.

| GTSE event | Token | Voice in `gt3se01.ins` | Sample offset in bank | ADPCM bytes | PCM samples | Loop, exclusive end |
|---|---|---:|---:|---:|---:|---|
| `b_off` | `0x01007007` | 7 | 96,256 | 4,544 | 7,952 | one-shot |
| `turbine` | `0x01010010` | 16 | 28,560 | 6,480 | 11,340 | 56..11,340 |
| `turbine2` | `0x01013013` | 19 | 173,696 | 8,960 | 15,680 | 2,856..15,680 |

Both selectors resolve to the same voice for these three events. Their bank is
at volume offset `1504524288`, SHA256
`d3170ce8123c8fbed12164e7898f0e4984d55f5bbc63bf6e0065d59f51aac426`.
The sample hashes are respectively:

- `b_off`: `fb3700a4bb8e409d965bb2bfec404ebae3c90048534c5fe31d429c1acc878aa3`
- `turbine`: `4a42f9316ca426fd06a4c73ab180296a30910345bc4e2fba9cb5c056ca6fdb47`
- `turbine2`: `850298d690b2027ebc3e9dd1e23925c2d56b9fcc4d655af6d1012132e4abae8a`

These are original GT3 named-event samples. The abbreviated `b_off` label alone
does not establish a particular real-world valve, engine or recording source.

## Source pitch and engine bank selection

The one-shot/voice leaf at `0x22bbf8` reads a requested note byte at voice `+16`,
shifts it left 8, reads the base fixed-point note ushort at `+8`, and calls
`0x2687b0`. That helper uses octave steps of `0xc00` and a 384-entry ushort
pitch table at `0x345ae8`, with the residual divided by 8. The implemented helper
preserves its integer shifts and quantization. The recovered leaf pitch words
are 1,485 for `b_off`, 2,778 for `turbine`, and 2,048 for `turbine2`.

At an assumed nominal SPU2 clock of 48,000 Hz, `rate = 48000*pitch/4096` gives
17,402.34375; 32,554.6875; and 24,000 Hz respectively. Native event auditions
round those rates to integer WAV Hz and preserve loop metadata. The raw sample
and leaf pitch are source-derived; later modulation, ADSR, LFO, volume,
pan/layer interactions and the full SPU2 output are not reproduced.

ENGN uses a 48-byte header and two optional tables of 16-byte records. Native
`0x267d18` reads the reference RPM as signed16 at entry `+0`, the base pitch as
uint32 at `+8`, multiplies by requested RPM, divides, and applies a current pitch
multiplier initialized to 4,096. **The original instruction at `0x267d50` is
DIVU**, although Ghidra's pseudocode prints a signed division. The helper uses
low32 arithmetic and unsigned division, and returns the pitch before the
previous-frame clamp/smoothing. `0x267f30` applies a minimum input of 200 and
selects at most two adjacent layers using bounds at entry `+2/+4`;
`0x267d98` supplies lookup-based gain/crossfade logic. A simple linear playback
of all samples would not reproduce those consumers.

For `sound/engine/22601`, table0 entry0 has reference RPM 800 and source pitch
1,633, yielding 19,136.71875 Hz at its anchor under the same clock conversion.
`native_engn_pitch` exposes this exact static calculation and its limitations;
the generic bank WAV command continues to require a caller-selected rate.

The native bank loader at `0x1a6a60` loads `sound/engine/%05d` plus
`sound/%s/%05d`. The category array at `0x2c2088` is ordered `normal0..3`,
`turbo0..3`. `0x2340d0` obtains the installed ENGINE row in table 6 and reads
sound number at `+0x16`, agreeing with the independent database layout.
`0x2340f8` takes MUFFLER table20 category byte at `+16` (default zero), and adds
4 when predicate `0x234048` finds a nonzero TURBINEKIT table12 byte at `+17`.
Local metadata calls that byte `wastegate`. Thus the suffix 0..3 is selected by
the muffler category; it is not simply the installed turbine-stage integer.

## Vehicle-to-sound references

The supplied `GTDataSQLiteConverter-main` source and original GTAR/GTDT bytes
agree on 36 tables and version 2087. CAR table30 has 264-byte rows; ENGINE
table6 has 88-byte rows. CAR's uint64 engine key at `+56` resolves to ENGINE's
primary uint64 key at `+0`; its ushort sound number is at `+22`. Labels are
resolved using the regional IDDB/STDB files and cross-checked against CAR's
explicit label string. The row offsets and row SHA256 hashes are retained.
Non-ASCII bytes in unresolved multibyte strings are escaped, because assuming
the local converter's EUC-JP encoding fails on actual `-1` strings in this corpus.

The US source has 244 CAR rows, 235 ENGINE rows and 118 referenced sound numbers;
all 244 resolve to existing banks. Nine `sample00x` rows intentionally reference
the `rx7_rz_00` engine owner and are preserved as explicit aliases. EU has 244
CAR rows; the unsuffixed JP database has 242. Short model-code association such
as `sb0097` remains separate: IDDB contains that name, but this research did not
establish a CAR-field link and therefore does not guess one.

| CAR label | Sound number | US CAR/ENGINE offsets within `paramdb_us.db` |
|---|---:|---|
| `lancer_evo6_gsr_99` | 21,801 | 1,447,392 / 68,248 |
| `evo6_wrc_99` | 22,601 | 1,439,208 / 61,032 |
| `impreza_wrx_99` | 21,204 | 1,479,072 / 58,832 |

`paramdb_us.db` starts at volume offset `1512814592`, SHA256
`291de73bd549577ee4ca2b91e19d6cd62ec9755aa9a6265444298fe7a3949830`.
Default MUFFLER/TURBINEKIT keys at CAR `+176/+104`, combined with the observed
native selector, resolve default secondary categories for all 244 rows:
normal0 102; turbo0 81; turbo3 29; normal3 23; normal1 4; turbo1 3; normal2 2.
These source defaults do not claim the currently installed parts in a save or
the state of a running car. All nine bank variants remain browsable.

The metadata sources are local files, not proof of runtime by themselves.
Relevant SHA256 identities include `CarDataBase.cs`
`25b176eb79a07bdfc18c22aede83c051e55ff90aec21fda41ff70079e9848b9e`,
`Headers/BASE_CAR.headers`
`0000a893a7de29b1a07c28d05eaca92133315ccfb1a4a03a4940bdf9c179253e`,
and `Headers/ENGINE.headers`
`579616f748adcda4416592f67d9cd1de678e594c4ce2d614f0537042c561edcc`.
The original-code sound-number read independently corroborates the sound field.

## Reproduction and verification

The source-only tool is `tools/gt3_sound_lab.py`. No GT samples, proprietary
fixtures, decompiler output or original machine words are included in source.
Native admission gates use whole-source hashes plus instruction length/digest
checks; actual instruction bytes are emitted only into private evidence.

```powershell
python tools/gt3_sound_lab.py --volume '<GT3.VOL>' --output '<new private catalog.json>'
python tools/gt3_sound_lab.py --core '<CORE.GT3>' --output '<new private core.elf>'
python tools/gt3_sound_lab.py --volume '<GT3.VOL>' --native-core '<CORE.GT3>' --output '<new private native-events.json>'
python tools/gt3_sound_lab.py --volume '<GT3.VOL>' --native-core '<CORE.GT3>' --event b_off --output '<new private b_off.wav>'
python tools/gt3_sound_lab.py --volume '<GT3.VOL>' --member sound/engine/22601 --entry-id table0:0 --sample-rate 24000 --output '<new private nominal.wav>'
python -m unittest discover -s tests/synthetic -p test_gt3_sound_lab.py -v
```

Twelve synthetic tests pass, covering malformed spans, SSA/program bounds,
one-shot/repeat distinctions, aliasing, source-key joins, unsigned engine pitch,
octave conversion, changed CORE identity and truncated container rejection.
Complete-corpus checks admit all 1,215 banks; six selected original samples were
decoded/exported across nominal and native-pitch paths. The three native event
WAVs were reopened and checked as mono signed16 with their expected frame counts
and integer rates. Ghidra-exported bytes for **2,576 distinct instructions** were
matched against mapped original segment bytes and independently decoded with
Rabbitizer 1.16.2 `InstrCategory.R5900`; all 2,576 were valid R5900 decodes.
Validity is a static check, not execution evidence.

Private evidence remains under ignored `scratch/gt_sound_lab/gt3` and
`scratch/gt_sound_lab/gt3_native`. The useful entry points are `catalog-final.json`,
`native-event-map-final.json`, `core_gt3_reconstructed.json`, `dispatch.txt`,
`voice_pitch.txt`, `engine_selection.txt`, `turbo_predicate.txt`, and
`native-cross-check.json`. The source/docs/test handoff should exclude that
diagnostic tree and all WAV/ELF derivatives.

Remaining work is controlled runtime corroboration, complete gain/pan/envelope
and modulation reproduction, exact gameplay condition attribution for each
event, and any short vehicle-model-code association. This report does not claim
PS2 audible parity or a finished GT3 audio-engine emulator.
