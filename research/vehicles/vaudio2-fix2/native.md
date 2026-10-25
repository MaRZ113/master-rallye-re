# V-AUDIO2-FIX2 / V-TURBO1 native supplemental audio

Original retail PC target SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA/Ghidra 12.1.4 was used against that original immutable executable. Original
bytes are checked before every seam is emitted. No retail EXE/DLL disk changes.

## Why the original whine can be masked

The original `005A8300` backend does **not** treat authored gain as a linear
DirectSound amplitude. Exact original instructions, replayed through typed COM
device stubs, produce:

| Authored gain | Native SetVolume dB, near listener |
|---:|---:|
| .08 | -61.6 |
| .18 | -31.2 |
| .30 | -18 |
| .55 | -9 |
| .60 | -8 |
| .65 | -7 |

Thus the previous .18 drive gain attenuated the source by **31.2 dB**, not the
14.9 dB a linear-amplitude preview might suggest. The source RMS itself is
roughly 17 dB below full scale. This is strong evidence of masking, not proof
that every silent gameplay observation has exactly this cause. At gain .18,
10/200 m near/far radii, a listener 30 m away gives -34.23 dB, and 150 m falls
under MR's .05 cutoff and becomes -100 dB. Candidate calibration is therefore
based on the actual backend curve, not arbitrary sample clipping/normalization.

Resource naming was checked: `005A7FE0` resolves the native audio root, appends
the interned `vehicles/sdk/.../layer` stem and the original `.wav` suffix at
`006EB3EC`. The existing resource stem was correct.

## Ownership and control

All three optional effects use independent ordinary `004F63D0` SFX objects,
registered through original `004F6750`. They never replace component `+14`,
the engine object, tyre SFX, or a stock channel pointer. Supplemental objects
live in 64 bounded owner slots. Allocation failure/slot exhaustion yields no
supplemental effect; no unbounded fallback allocation.

The component constructor seam remains `00409CAD`; the publisher tap remains
`00492CCA`; the update seam remains `0040A026`. New destruction seam `00409E25`
replays `51 56 8b f1 57` after supplemental cleanup and resumes `00409E2A`.
Original `004F64A0`/`004F67A0` unregister the object and queue native backend
retirement, then original free is called exactly once. Original component
destruction continues unchanged. Both construction and destruction invalidate
the actor-publication map, so a reused owner/public-state address cannot read
a prior race's freed physics pointer. Before fresh publication voices are muted.

The entity is the same native entity bound to the engine SFX (`owner+C -> +28`),
as established by the stock `0040AD10` bind routine. Its supplemental SFX `+24`
is updated without changing stock ownership. Native `004F65B0` supplies its
spatial position, and native `0059A550` handles loading/backend routing.

Engine omega/peak torque/net crank torque/gear are read from the previously
qualified source fields. This is a **load proxy**, not a throttle or boost
sensor. No physics value is written. Turbo pressure is an authored estimate.
Time comes from the existing `timeGetTime` import at `0068F3A0`; unsigned
millisecond subtraction supports wrap, and dt is capped to .1 s. Long pauses
are not integrated as a large spool jump. This is wall-clock smoothing, not
GT turbo simulation.

Whine and spool are independent looping SFX. BOV is explicitly non-looping.
A qualified load release while estimated pressure/RPM exceed profile thresholds
requests one event. Pitch variation is bounded/deterministic; cooldown and the
actual native `+0E` playback request prevent overlap/retrigger. `005A8300` checks
DirectSound status for non-looping sounds, clears `+0E` at completion, and stops
the backend. BOV pressure decay uses the configured release decay while that
request remains active. The backend, not a guessed sample timer, owns completion.

## Memory and reproducibility

`tools/native_audio/layers.c` is source-only x86 helper code; MSVC x86 compiles
it with `/GS- /Zl /Oi /arch:IA32 /fp:strict`. `native_audio_coff.py` admits only
qualified i386 code/constant sections and supported absolute/relative COFF
relocations; mutable globals or unresolved imports fail closed. The report pins
helper source SHA256, compiler SHA256 and canonical options. COFF timestamps or
temporary paths are not part of the deterministic runtime manifest.

Code/profile/constants remain RX. The single aligned **4096-byte RW/NX page**
holds the cursor, 64 publication pairs and 64 40-byte voice owner slots. No
mutable write is directed into executable memory. No new OS import is injected.
Two independent compilations produce identical linked payload bytes.

## Validation and boundaries

`vehicle_whine_validate_native.py` executes generated C and seam instructions,
original construction/list registration, update, original backend Play(loop on
and off), SetFrequency, SetVolume, GetStatus, Stop, native unregister/free and
repeated construction/destruction. A/B/C each pass 28 identity/control cases,
73 bounded-map publications, per-profile preimage rejection, RW/NX protection,
held-release no-spam, spool-up, BOV completion, and stale unmapped actor re-entry
negative checks. Native backend gain calibration is included in the JSON reports.

Broker, interner/resource handle, allocator, manager singleton, frees, clock and
DirectSound COM device calls are **typed stubs**. Consequently these are original
instruction/lifecycle tests, not proof that a physical DirectSound device loaded
the WAV, that real AI/player mixing is audible, or that gameplay race re-entry
is qualified. Gameplay listening remains required.

For live read-only diagnostics:

```powershell
python tools/inspect_vehicle_audio_voices.py --pid GAME_PID --policy PRIVATE_RUNTIME/damage-alpha-policy.json
```

This reports participant slot, source handle, backend creation-request/failure
flags, loop/request, gain, pitch, position, estimated spool and release count.
It does not inject code, write process memory, or equate requested playback with
audible device output. Snapshots can race normal engine updates.

REA fresh evidence includes `ev_308e952241d924285e89dce6a0e1166e564136b47b71e9c543c10e9cdc9cd208`
for `.wav`, and `ev_eb1218c028b2bd202017d3b670ab71a45230f9bae54e6e159cb213c1b23081f5`
for original manager registration; the previous source-qualified audio evidence
under `research/vehicles/vaudio2/native-whine.md` remains applicable.
