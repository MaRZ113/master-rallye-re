# V-AUDIO2 independent transmission layer

Target original PC EXE SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
The original EXE and renderer are not edited. The sealed external SDK payload
appends three reversible process-code adapters. V-AUDIO1 engine source bytes,
native synthesis tables and engine DSP remain separate.

## Native evidence

REA/Ghidra 12.1.4 private observations are retained in
`.research-output/vehicles/vaudio2/native-evidence.json`. Decompiled C is
analysis output, not original source. Missing default REA function boundaries
for `00409EB0` and `0040AD10` are covered by the existing exact-build Ghidra
exports under `research/vehicles/audio/ghidra-exports`, with original bytes
checked again before each adapter is emitted.

| Address | Observed behavior |
|---|---|
| `00408F20` | Ordinary cases 0..22 initialize optional SFX owner at sound component `+14` to zero. Special icecream case23 owns it; schema excludes cases23/24. |
| `004F63D0`, `004F6750` | Ordinary 0x5C-byte SFX constructor initializes fields and registers the object in the native manager's intrusive list. |
| `0040AD60..0040AD6A` | Native bind assigns the component's entity to the optional SFX `+24`. |
| `004F65B0` | Manager follows entity spatial position for ordinary SFX. |
| `00409E10`, `004F64A0`, `004F67A0` | Native component destructor unregisters and frees optional SFX; backend retires its DirectSound object. |
| `0059A550` | Ordinary effects enter `005A8300`, while engine rev objects separately enter `005A75C0`. |
| `005A8300` | SFX `+0E` requests playback, `+0F` selects looping; `+10` feeds spatial volume and `+14` multiplies source sample rate passed to DirectSound frequency. |
| `00443900`, `00492C90` | Engine is actor `+10`; its `+28` angular speed and `+44` rev limit produce public normalized RPM. Publisher retains actor argument and public-state pointer. |
| `0043C570` | Engine `+94` holds net crank torque after drive torque and engine damping. `+50` is configured peak torque; gearbox index1 selects neutral. |

Relevant REA evidence IDs:

- SFX constructor: `ev_4a33d5581f5416471989695d23e04c919dc121859c7c39c032aed279bb2e9e4e`.
- Native destruction: `ev_96f1155e21f3f67b37fe223360be8df25fe9b3c0ca4efcbdd5b3727ac9270747`.
- SFX playback/pitch/gain: `ev_b714e0184988201006621b523a722e8b71a401454f76a99c3d7fa36750d27f0c`.
- Engine torque: `ev_64e214c407d79a78fc70e6234ba798db9ec88bc1bf33e8ef0db2f61ae71a115a`.
- Publisher assembly: `ev_7715d5b0186e6032ee32257d1ab76aa9da1c4415e40e22b8f0952b7de15a1aeb`.

## Adapter and authored controls

`tools/vehicle_whine_native.py` exposes
`append_whine(source,image,blob,payload_va,profiles,allocation_size)`, matching
the existing append-audio return convention. No configured whine returns the
same image/blob with no report. A configured layer appends its code/data while
preserving the previous payload byte prefix and its SHA256.

| Process seam | Exact overwritten original bytes | Purpose |
|---|---|---|
| `00409CAD` | `8b8c2488000000` | After ordinary sound construction, match physical CarID via original slot/Race getters, create an extra native SFX, leave original native bind/lifetime in control. |
| `00492CCA` | `8b4f088b54241c` | Read-only tap associates public-state pointer with that publication's native physics actor. |
| `0040A026` | `8b4f088d5678` | Update the configured participant's extra SFX using its matched actor; resume unchanged engine/tyre/gear code. |

The map has64 entries and bounded replacement. It stores pointers only inside
the appended allocation; it writes no physics field. New optional owners clear
prior-race mappings. An absent mapping, missing object, invalid speed or invalid
peak torque leaves the loop muted. The native constructor attaches a unique
effect to each sound owner, including AI owners. No current-car global or
stock donor resource is replaced.

Authored response:

```
rpm = abs(native_engine_omega) / 0.10471967
pitch = clamp(rpm / reference_rpm, pitch_min, pitch_max)
load_proxy = clamp(net_crank_torque / configured_peak_torque, 0, 1)
gain = lerp(gain_coast, gain_drive, load_proxy)
       * clamp(rpm / fade_in_rpm, 0, 1) * Sound/SFX/Volume
```

Neutral can mute the loop. Race-finished state mutes it. Signed net crank torque
provides an explicit load proxy; this is not an exact throttle accessor, wheel
torque, original GT4 transmission logic, measured gear-mesh acoustics or output
shaft speed. The referenceRPM/pitch/gain values are authoring decisions.
Native SFX also has its own distance attenuation and a volume cutoff below0.05;
quiet authored values can therefore become inaudible at distance.

## Profile and compiler

Version1 profiles keep their existing required keys and gain one optional key:

```json
{
  "transmission_whine": {
    "source": {
      "source_path": "audio/transmission_whine.wav",
      "source_sha256": "<64 lowercase hex characters>",
      "trim_frames": [0, 48000],
      "gain_db": 0,
      "remove_dc": false,
      "crossfade_frames": 0
    },
    "response": {
      "reference_rpm": 4000,
      "pitch_min": 0.2,
      "pitch_max": 1.8,
      "gain_drive": 0.18,
      "gain_coast": 0.08,
      "fade_in_rpm": 1000,
      "mute_neutral": true
    },
    "provenance": "Explicit source identity or authored approximation."
  }
}
```

Source uses the same bounded RIFF/hash/path/link/trim/clipping guards as the
existing engine source. Compilation emits an independent canonical monoPCM16
48000Hz `DataAudio/vehicles/sdk/<namespace>/transmission_whine.wav` and records
it under `report.transmission_whine`. Existing engine PCM is identical with and
without the optional declaration. `audio_resource_hashes(report)` validates
exact compiled engine/whine paths and hashes for collection/resource allowlists.
Pitch is bounded to0.125..2, keeping a48000Hz source below96000Hz.

## Verification boundary

`tests/synthetic/test_vehicle_whine.py` covers additive resource/engine equality,
strict malformed-profile/resource allowlists, deterministic source/audition,
controls and neutral/finish behavior. No game samples are in these fixtures.

`tools/vehicle_whine_validate_native.py` executes generated seams, original SFX
constructor/registration, entity binding and original destruction/unregister/free
in Unicorn. Current private replay passes28 control/identity cases and73 extra
bounded-map publications, verifies register/flags/x87 stack balance and no
physics-state writes, and rejects changed seam bytes, foreign EXE and allocation
overflow. Broker, resource interner, heap allocator, singleton and free are typed
stubs. This does not confirm a DirectSound device, audible race mix, AI/player
gameplay, seamless race re-entry or subjective sound quality.

For private local validation, use existing Unicorn packages on `PYTHONPATH`:

```powershell
$env:PYTHONPATH='src;tools;.;.research-output/vehicles/scale1/python-tools'
python tools/vehicle_whine_validate_native.py --exe ../MRallye.exe --profile PRIVATE_AUDIO_PROFILE --output .research-output/vehicles/vaudio2/native-candidate-replay.json
```
