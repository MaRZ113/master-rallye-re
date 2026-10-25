# GT4 local engine audio qualification

## Source identity and limits

The authoritative audio input is the user's unchanged
`D:/Game/GT_Model-Tools/VOL/GT4-Beta_Extracted/extracted/` tree. No other
vehicle's sample was substituted. The completed Lancer source qualification
already associates `lancer_evo4_wrc_97` with model `mits0015` (see V-LANCER3).
This pass follows original database **keys**, rather than assuming an ENGINE
label or a sound filename from the model number.

The supplied sibling CORE has Online-US identity, as already documented in
V-LANCER3: encrypted CORE SHA256
`0cf52c3ad8e9c1ddba55e7538a35dfed1c02cd0e38e5c348bdf80975046617ff`,
reconstructed ELF SHA256
`962523fb4156aefa4e7d255c4937825614e0b99a9a48e94f1c9fcbe7c586c5c0`.
Its formulas are explicitly identified as supplied-CORE native evidence;
exact pairing with a historical GT4 Beta runtime is not asserted.

## Recovered association

| Step | Actual recovered reference |
| --- | --- |
| `GENERIC_CAR`, label `lancer_evo4_wrc_97`, row 223 | DefaultParts key `(3128, table36)` at byte0 |
| `DEFAULT_PARTS`, row3128 | Engine key `(1605, table12)` at byte88 |
| `ENGINE`, row1605 | little-endian ushort `soundNum=22601` at byte24 |
| Sound bank | `carsound/engine/22601`, SHA256 `9060242d08160809949ce87324bb910ba8a738b597438f3dde6801b95aa5ebfa` |

Qualified database row sizes are 24/208/113 bytes. Source table and row hashes
are recorded privately in `vaudio1/gt4/mapping.json`. Field names and table IDs
are corroborated by user-local PDTools `GenericCar.cs`, `DefaultParts.cs`,
`Engine.cs`; these C# names are not presented as original GT4 source code.

Eleven ENGINE rows reference sound22601: 1478,1487,1488,1605,1772,1777,1882,
1908,2012,2282,2297. Thus it is a **source-selected shared bank**, not a claim
that this is a unique recording of this exact rally car.

The source contains six matching bank paths: engine, normal3, turbo0, turbo1,
turbo2, turbo3. Their entry counts are 8,8,7,6,8,8 respectively. `normal3` and
`turbo3` are byte-identical. Missing normal0/1/2 were not replaced by unrelated
files. The current extraction does not decide which tuning bank the original
car would select in every game mode.

## ENGN and native interpretation

The 78464-byte engine file has a 176-byte header and 78288-byte mono SPU-ADPCM
body. Header fields at8/16/20 give header size, body size and body pointer;
count/pointer pairs at24/32 support two tables. Entry records are16 bytes:

| Offset | Recovered meaning / evidence |
| --- | --- |
| +0 signed16 | Reference RPM: native pitch divides by it |
| +2/+4 signed16 | Full-volume RPM interval; two adjacent entries can crossfade between intervals |
| +6 signed16 | Gain coefficient used by the native lookup/fade multiplication |
| +8 uint32 | Base SPU pitch, scaled by requestedRPM/referenceRPM |
| +12 uint32 | Source SPU byte address / relocated body offset |

The original instruction sequence at `00532A60` computes base-pitch × RPM /
reference-RPM and limits pitch change during ongoing playback. `00532C88`
chooses up to two entries from their RPM intervals, and `00532AD8` applies a
lookup-table crossfade and gain. The result goes through voice+0x94 into the
SPU control packet in `00537FC0`; global pitch/doppler can multiply it further.
`00273170` loads both `%s/engine/%05d` and `%s/%s/%05d`, with bank names
normal0..3/turbo0..3. **One WAV does not reproduce that whole mixer.**

Ghidra12.1.4 Emotion Engine Reloaded `r5900:LE:32:default` was used read-only on
the existing supplied CORE project. 137 selected instruction words were mapped
back to exact ELF program segments and independently decoded with Rabbitizer
`InstrCategory.R5900`. Private evidence is `gt4/native-evidence.json` and ignored
`scratch/vaudio1/`; recovered pseudocode is an analysis aid, never original code.

At the 48kHz SPU2 nominal clock and unity global pitch, anchor wave rate is
`48000 * basePitch / 4096`. The optional extractor requires the exact supplied
CORE hash and instruction preimages before interpreting this mode. It keeps an
explicit nominal-rate mode for other sources instead of silently applying the
same binary semantics to an unknown game build.

## Lancer adaptation input

Recommended first MR timbre input: engine22601 **band04**, source anchor4000RPM,
base pitch1831, exact nominal rate21457.03125Hz, WAV integer rate21457Hz.
Its SPU loop is samples `[28,17696)` (17668 samples, about0.8234seconds).
Private full and loop-only PCM files are in
`.research-output/vehicles/vaudio1/gt4/engine22601-sourcepitch/`.

`table0-band04-loop.wav` SHA256:
`6cb99e0c853ebc88f89ce893e6c2d7eb5c32fa5f5b7a6663b076a621c2fc9c59`.
It is decoded mono PCM16 with no normalization, fades or cosmetic changes.
Selecting one midrange band for MR's own granular engine synthesizer is a
controlled translation, not original GT4 layered playback. Full GT4 exhaust
mixing, tuning selection, throttle response, spatialization and Doppler are
not transplanted. All eight engine bands remain independently available.

## Codec and validation

The decoder uses low-nibble-first Sony ADPCM, integer coefficients and +32
predictor rounding with clamped history, matching the arithmetic visible in
[PCSX2's SPU2 mixer](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/SPU2/Mixer.cpp).
Original loop flags are preserved; full WAVs carry `smpl` points, and loop-only
WAVs contain the indicated region. Captured initial decode history is used;
exact repeated SPU interpolation/history output is not claimed.

A comparison against the locally installed FFmpeg VAG decoder recovered the
same12572 samples for band00, with maximum50/32768 amplitude difference due to
integer/float rounding. The difference is reported, not described as bit-exact.
[vgmstream's decoder notes](https://github.com/vgmstream/vgmstream/blob/master/src/coding/psx_decoder.c)
also distinguish rounding variants. [PS2SDK libsd definitions](https://github.com/ps2dev/ps2sdk/blob/master/common/include/libsd-common.h)
provide independent pitch-register and loop-flag names.

Seven synthetic test cases cover original key routing, hash/byte admission,
header bounds/overlaps, predictors, nibble sign/order, clipping, loops, WAV
layout, extraction, nominal-rate provenance and output overwrite rejection.
All available matching local banks pass structural and codec checks. No
GT4 audio or database fixture is required by these tests.

Remaining human checks: perceived timbre and volume in MR, idle/acceleration,
shifts, overrun/reverse, AI simultaneous audio, finishing and race re-entry.
Offline extraction does not establish gameplay or exact original GT4 parity.
