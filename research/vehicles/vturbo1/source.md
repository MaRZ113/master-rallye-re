# GT3 turbo and pressure-release source qualification

## Directly observed local data

The optional `tools/gt3_audio_inspect.py` reads the original user-provided GT3
RoFS2.2 volume using the existing bounded `gt3_ui_icon.read_member` parser.
No GT files are bundled. It records member offsets, lengths, stored/decoded
SHA256 hashes and the complete named GTSE event table. Current private evidence:
`.research-output/vehicles/vturbo1/gt3-source-report.json`.

Source: `D:/Game/GT_Model-Tools/VOL/GT3_Extracted/GT3.VOL`.
`sound/se.inf` is a 648-byte `GTSE` version1 table containing42 named events.
The directly read names/tokens include:

| Name | Opaque token |
|---|---|
| `turbine` | `0x01010010` |
| `turbine2` | `0x01013013` |
| `b_off` | `0x01007007` |

These are defensible **named candidates**, not proof that a particular encoded
wave is a spool or BOV. The meaning of token bitfields, voice-note dispatch and
nominal playback pitch has not been qualified. In particular, `b_off` must not
be declared an authentic blow-off sample solely from its abbreviated name.

Available banks include `sound/gt3se01.ins` (270576 bytes),
`sound/gt3se02.ins` (206928), `sound/gt3sys.ins` (90016), `sound/se01.ins`
(79916) and `sound/sys.ins` (34644), all headed `INST`.
The GT3 bank's first40 bytes and event inventory are captured without modifying
the source volume. `gt3se01.ins` has header words26 at0x18 and40 at0x1c, followed
by repeated24-byte records and a later table. This differs from the local
PDTools GT4 `JamHeader.Read` expectation of `SShd` at offset0x2c. Applying that
GT4 reader to GT3 would invent structure and is therefore rejected here.

`CORE.GT3` SHA256:
`fdcea2aa43231873592adee0fb96499f2e40979e0269191af1eafcf95da12b0b`.
It is887311 bytes and is not a directly loadable ELF; byte prefix is
`0101f7322500ecbd`. The accompanying `SCUS_971.02` is an ELF, SHA256
`e60a8821d01051cece0ededcd600bca0a79fb460baa2a5babedd72b3d18e5518`.
No unsupported PC/x86 decoder was used on these PS2 inputs. Runtime event
dispatch and the GT3 CORE unpacking path remain independent research work.

## Implemented workflow and honest fallback

```powershell
python tools/gt3_audio_inspect.py --volume PRIVATE_GT3_VOL --output PRIVATE_REPORT.json
python tools/vehicle_turbo_source.py --kind spool --output PRIVATE_SPOOL.wav
python tools/vehicle_turbo_source.py --kind bov --output PRIVATE_BOV.wav
```

The inventory helper intentionally does **not** export an alleged authentic
turbo WAV. Authentic extraction is not yet qualified. Custom user WAV inputs
remain supported by the reusable audio profile workflow.

`vehicle_turbo_source.py` supplies original deterministic synthetic test audio:
a one-second periodic2400Hz whistle with bounded harmonic/modulation components,
and a seeded0.35-second filtered-noise pressure hiss with attack/decay envelope.
They are engineering audition sources, not GT3 recordings or an assertion of
real Lancer turbo acoustics. Their private generated WAVs and SHA256 reports are
under `.research-output/vehicles/vturbo1/`; only the generating tool is a source
deliverable. No private game wave is committed or redistributed.

Five synthetic tests cover strict event pointers/duplicates, deterministic PCM,
peak bounds, loop join and BOV decay. The next robust authentic-source step is
to qualify GT3 instrument dispatch and unpacked PS2 runtime pitch/SSA consumers,
then map these explicit named events through original bytes. A high-frequency
wave chosen by listening alone is insufficient evidence.
