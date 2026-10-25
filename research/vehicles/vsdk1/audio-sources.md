# V-SDK1 optional GT audio source qualification

## Result

Keep the working synthetic transmission, spool and pressure-release sources.
This bounded pass advances **private audition**, but does not establish an
authentic effect replacement. No audio profile or installed sample was changed.
No proprietary sample belongs in the SDK distribution.

## Directly observed sources

GT3 source remains the user's `D:/Game/GT_Model-Tools/VOL/GT3_Extracted/GT3.VOL`.
The existing bounded RoFS reader was rerun. `sound/se.inf` still has 42 events:
`turbine=0x01010010`, `turbine2=0x01013013`, `b_off=0x01007007`.
The five original INST banks remain distinct from GT4 JAM; the GT4 parser
rejects a missing `SShd` header rather than guessing GT3 layout.
See `research/vehicles/vturbo1/source.md` for prior GT3 provenance and limitations.

GT4 input is the unchanged Beta extracted tree:
`D:/Game/GT_Model-Tools/VOL/GT4-Beta_Extracted/extracted/sound_gt/sound/`.
Its `se.inf` is GTSE v1, 81 named events, SHA256
`3736ebf75f8629fdf7fdb87f0ecfdd01e7a6cbc81de5d19ee7f8ad4606fc5f69`.

| Literal name | Opaque GT4 token |
|---|---|
| b_off | 0x0100013c |
| turbine | 0x03000b3c |
| turbine2 | 0x03000c3c |
| shift_change | 0x03000f3c |

These names support targeting the subsequent native dispatch investigation.
They **do not** prove a token's bank, program, note, PCM, pitch or acoustic role.
In particular, `shift_change` is not evidence for continuous gearbox whine.

## Reusable private audition helper

New `tools/gt4_instrument_audition.py` reads the explicitly identified GT4 INST
body plus JAM program/split layout. Structural reference: local PDTools
`PDTools.Files/Sound/InsHeader.cs`, `Jam/JamHeader.cs`, `Jam/JamProgChunk.cs`
under `D:/Game/GT_Model-Tools/GTPS2ModelTool-master - Copy/PDTools/`.
Those third-party field interpretations are comparative evidence, not original
GT4 source or native dispatch verification. REA native tools were unavailable
for this worker's initial pass; no PC disassembler was applied to PS2 code.

The helper retains raw program/split records, source byte offsets and hashes;
decodes supported SPU PCM with the existing shared codec; records unsupported
SSA/loop structures without dropping their records. Explicit caller-selected
WAV rate is mandatory. It does not guess nominal pitch from a musical-note
field, emulate ADSR/LFO/noise, or apply event labels to anonymous samples.
Budgets cover file size, record counts and aggregate sample scan size.

| Bank | SHA256 | Split records | PCM accepted | Unsupported |
|---|---|---:|---:|---:|
| gt4race.ins | 54a165aa0d417dd0cfe35f67b6c43c9156660b4d6641ee0886b722a02ec76baf | 31 | 5 | 26 |
| gt4race2.ins | b27a2bafe3e428e5ca764e3c99958065d84b22c6c962be09ed85f66631f9b564 | 15 | 4 | 11 |

Unsupported includes SSA values outside the body and loop marker combinations
not admitted by the existing ENGN codec. Their cause could involve special
instrument semantics or incomplete layout interpretation; they are **not**
declared corrupt samples. No offsets or loop flags were repaired speculatively.

An anonymous `gt4race2.ins` program 1 / split 0 exports 20,832 mono PCM samples,
no loop, 11,904 encoded bytes at file offset 43,488. At the explicit nominal
24 kHz audition rate it lasts 0.868 seconds. Its encoded SHA256 is
`48a82a67cd9e6c9feb1d71b1c79d2d514f4c3e63d4516b54a40611d41f7e2a0f`.
This is a structurally decoded source wave, **not an identified turbo/BOV**.
It was not auditioned by a human or integrated into the candidate.

## Commands

Run from the repository with `PYTHONPATH=src;tools;.`:

```powershell
python tools/gt3_audio_inspect.py --volume PRIVATE_GT3_VOL --output PRIVATE_REPORT.json
python tools/gt4_instrument_audition.py PRIVATE_GT4_RACE_INS --output PRIVATE_BANK_REPORT.json
python tools/gt4_instrument_audition.py PRIVATE_GT4_RACE_INS --program 1 --split 0 --sample-rate 24000 --output PRIVATE_ANONYMOUS.wav
python -m unittest discover -s tests/synthetic -p test_gt4_instrument_audition.py
```

Inspect the report before selecting a PCM-valid program/split. Listen to the
private WAV in a local audio player; changing nominal rate changes duration and
pitch and is not source qualification. Each export writes a JSON provenance
sidecar with explicit `authentic_effect_identity: null`. The helper refuses
overwrite, unsupported selections and unspecified playback rate.

Once a user-provided or genuinely qualified sample is selected, use the existing
editable audio-profile source fields and layer preview mute/solo controls for
conversion. The present candidates intentionally retain synthetic provenance.

## Evidence and remaining boundary

Private outputs: `.research-output/vehicles/vsdk1/audio-source/` contains fresh
GT3 inventory, GT4 events, both bank inventories and the anonymous audition WAV
with sidecar. Four fixture-independent tests pass: records/PCM, incompatible
header and pointer rejection, unsupported SSA accounting/export refusal, and
explicit-rate provenance/overwrite refusal.

The smallest next authentic-effect step is to verify GTSE token consumption,
bank registration and note/pitch dispatch in the matching PS2 executable, then
trace the named events through specific original instrument records. GT3 CORE
unpacking and GT4 special SSA semantics remain separate research. Neither a
suggestive name nor a plausible sounding anonymous WAV closes this evidence gap.
These optional blockers do not block multi-addon integration.
