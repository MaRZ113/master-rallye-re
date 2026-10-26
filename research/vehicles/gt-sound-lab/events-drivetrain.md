# GT4 named events and drivetrain sound

## Static GTSE dispatch

This uses the exact supplied CORE and source/binary boundary documented in
`gt4-native.md`; no acoustic labels were assigned by hearing.

`002E29B0` loads and registers `gt4sys.ins`, `gt4race.ins`, `gt4count.ins` in
slots 0, 1 and 2. `002E2768` conditionally loads `gt4race2.ins` in slot 3.
`se.inf` is loaded separately and its names are matched to the CORE's 81-name
event table. `002E2CC0` retrieves the original token after this name mapping.

`002E2CE8` splits a token into bank slot (bits 24..31), mode (bits 16..23),
index (bits 8..15) and low byte (bits 0..7). Its ELF file offset is `001E3D00`.
The bank slot indexes the registration array with stride `0x24`.
`002E22F0` chooses the direct-program path when mode is zero and the SE sequence
path when mode is nonzero. Sequence routing is retained as unsupported by the
new high-level resolver; it is not guessed from field names.

For direct mode, `00533FC8` selects the program via `00533878` and initializes
the split pointer to `program+8`, the first split. It does **not** use its fourth
argument containing the token low byte. Therefore interpreting `3C` as a MIDI
note that selects a split would misrepresent this particular native path.
`00533C78` consumes that selected split and creates/updates the playback voice.

| GTSE literal | Original token | Native slot/program/initial split | Corpus result |
|---|---|---|---|
| b_off | `0100013C` | race, program 1, split 0 | PCM-valid source found |
| turbine | `03000B3C` | race2, program 11, split 0 | PCM-valid loop found |
| turbine2 | `03000C3C` | race2, program 12, split 0 | PCM-valid loop found |
| shift_change | `03000F3C` | race2, program 15 | table entry is `FFFF`, absent |

`shift_change` has a named token but no direct program in the supplied Beta
bank. The report exposes this as `DIRECT_PROGRAM_ABSENT`. Neither a nearby
program nor another vehicle's sound is substituted. A disabled source entry,
authoring choice or a build difference may explain it; this pass does not
choose among those possibilities.

## Correct original sample ranges

These use the native shift-3 SSA scale, with unmodified encoded data and the
strict shared SPU-ADPCM decoder:

| Event | Split record file offset | ADPCM file offset | Encoded bytes | Decoded mono samples | Original loop samples |
|---|---:|---:|---:|---:|---|
| b_off | 248 | 14576 | 13824 | 24192 | none |
| turbine | 466 | 181184 | 6464 | 11312 | `[28,11312)` |
| turbine2 | 490 | 187648 | 8944 | 15652 | `[2828,15652)` |

Encoded SHA256 values, in the same order:

- `43e9130fb48f2a47f5c4ee35574889c8e7b9db1ca4531f9cc0f00ec9ddbca1dc`
- `7051a1f619d48627db5e0781c6b431cac88cc6c9a5a2165683acbb2bb8aa0e0b`
- `a842879a8319fb2342b8d8eba496a682d7b8a190920b7d941cf3e5d5ed53bdcb`

These are named-event-to-source-record associations under the supplied CORE
dispatch. They do not establish exact Beta runtime envelopes, perceived role,
relative mix level or native playback rate.

## Persistent turbine and drivetrain streams

`00272ED0` binds literal event indices `4B` (turbine) and `4C` (turbine2) to
persistent sound objects at audio `+280` and `+2A0`. `00273480` supplies separate
gain/pitch pairs from control packet `+64/+68` and `+6C/+70`, respectively.

The first stream receives gain based on a view-dependent factor and dynamic
byte `+726`, with pitch control `ushort(dynamic+61C)/6144`. This pass has not
qualified the complete producer or physical units of that packed dynamic field;
it does not claim a measured turbine-speed value merely from the literal name.

The second stream has a substantially stronger drivetrain identity than its
name suggests. Its gain/pitch pair is produced by `00212B28` (ELF file offset
`00113B40`) and forwarded by `0027E420` to that same persistent `turbine2` slot:

- A native operation-state gate (`0022AB18`, result greater than 2) admits it.
- Some drivetrain types take explicit alternate branches (`00218910`,
  `0022C708`, `00219950`, `0022D880`), so the ordinary formula below is bounded.
- Ordinary playback requires spec byte `+111D` nonzero and dynamic gear-state
  byte `+646` nonzero; otherwise gain is zero and pitch factor is one.
- `0020FF40` initializes spec `+111D` from the installed GEAR category returned
  by `00305C78`, or from another spec discriminator at `+32 == 2`.
  `00305C78` reads equipment `+48`, record byte 34; local GEAR table metadata
  independently names byte 34 `category`.
- Ordinary gain uses `abs(dynamic+640)`, clamps it by a global threshold, and
  scales it by the current gear ratio at `spec+280+gearIndex*4` relative to
  `spec+284`. Global minimum/maximum coefficients map that normalized value.
- Pitch factor is `global_base + abs(00213A38(dynamic))*global_slope`.
  `00213A38` selects front/rear drivetrain-speed fields `+650/+654` or their
  combination according to the drivetrain discriminator at `spec+240`.

The coefficients are populated by `00212250` from original parameter bytes
`+1E0..+1E4`; their numeric values were not guessed from listening. The exact
physical names/units of all underlying state members remain bounded inferences.

This trace establishes a continuously controlled **sample playback** path using
the looped race2 program 12. Gain and pitch are procedurally driven by gearing,
drivetrain speed and state. It does not support replacing the original with an
unqualified standalone sine oscillator. It also shows why naming every
`turbine2` sample a second turbo recording would lose evidence: the native
consumer, rather than the label, determines its drivetrain use.

No recording or runtime A/B test was performed. The statement above identifies
the native mechanism and route; perceived continuous transmission whine and
parity with a specific historical GT4 Beta runtime remain unconfirmed.

## BOV and shift-event boundaries

The one-shot event-array mapping at `006F0330` starts with event 13 (`b_off`)
and ends with event 79 (`shift_change`). In `0027E420`, the b_off scalar is a
view-dependent gain times dynamic float `+628`. The producer and exact throttle
release thresholds of that dynamic float were not qualified in this pass.
`00273480` gates event scalars by a threshold, and `00273D48` resolves the event
token, initializes a one-shot object and submits it to the same mixer.

The shift scalar is set on changes to dynamic gear byte `+644`, with additional
view/player-state gating in `0027E420`. Its dispatch identity is established,
but the missing Beta program 15 prevents a source-sample export for this event.
The separately traced continuous drivetrain stream is unaffected by assigning
no speculative sample to that missing entry.

## Tool API

`gt_sound_jam.inspect(raw)` preserves original program and split records,
including absent table slots and unsupported codec combinations.
`resolve_events({slot: bank_report}, {literal_name: uint32_token})` resolves only
the proven direct first-split path and returns explicit gaps for missing banks,
absent programs and SE-sequence mode. Low-byte semantics are kept explicit.

`extract(source, output, kind, program, split, sample_rate)` requires a supported
selection, explicit nominal rate and new WAV/JSON paths. Its sidecar records
source hashes/ranges, native interpretation provenance, unconfirmed runtime
pairing and `authentic_effect_identity: null`. It exports the source wave without
inventing the original ADSR/LFO, live pitch, spatial mix or auditory identity.
