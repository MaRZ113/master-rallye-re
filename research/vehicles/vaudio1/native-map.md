# V-AUDIO1: native engine source and independent identity

Target: immutable retail `MRallye.exe`, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA/Ghidra12.1.4 observations, original bytes and controlled x86 replay are
separate from human gameplay qualification. Private REA records and replay
outputs are under `.research-output/vehicles/vaudio1/native`.

## What the native path actually does

| Site | Confirmed observation |
|---|---|
| `00408660` | Sound manager constructs a component for every active race slot, including player Car0 and AI |
| `00408F20` | Absolute CarID selects engine source, object scalars and a table group; existing SDK selector maps only this audio identity |
| `00408FA4` | Native sound object `+54` stores the participant slot, separate from the selected tuning identity |
| `004ADA50` | Race Broker singleton getter; plain `RET`, consumes no stack argument |
| `004AC660` | Reads physical `Race/CarN/CarID` for supplied slot; `RET4` |
| `004D0580` | Interns a resource name into a small string handle; `ECX` output, one stack argument |
| `004F6B50` | Engine-source object constructor; separate from the ordinary sound-effect object (`004F63D0`), allocates120ushort table entries |
| `00409B18..00409C29` | Copies two arrays of60ushort values into the engine object as12rows×10entries; first six rows are control axes, second six output curves |
| `005A6EE0` | `wsDsFxRevs` opens a WAV through the native audio resource root, reads a fixed44-byte header, rejects non-mono engine sources and initializes DirectSound buffering |
| `005A75C0` | Copies the tables to synthesis state, applies listener-distance volume, updates engine controls, then calls `005A7950` |
| `00443900` | Returns clamped engine angular speed divided by configured rev-limit angular speed: normalized RPM |
| `00492CC5..00492CD1` | Calls `00443900`, publishes result into per-car public dynamic state `+8`; same structure's `+4` receives native gearbox index |
| `005A7646..005A7657` | Stock source-object `+1C` scalar multiplied by4096 and rounded into synthesis `+1D0`; it is not a source base-RPM label |
| `005A78C4..005A7904` | Source `+18` normalized control enters a cubic mapping before `005A7950`; this is more than direct WAV pitch scaling |
| `005A7950` | Interpolates the native6×10 control tables, updates bounded synthesis/resampling/filter controls |
| `005A7EC0`, `005A7EF0` | Integer linear table interpolation helpers |
| `005A72F0`, `005A7C30` | Worker dispatches raw PCM generator; generator loops source phase, resamples/interpolates and applies native integer filter/clamp |

The existing source matrix in `research/vehicles/audio/stock-audio-matrix.json`
remains authoritative for all25 stock tuning cases and six named stock sample
resources. Ordinary cases use one engine source (for example `rev9`,
`engine3`, `engine4`, `engine9`) plus native procedural synthesis. These are
**not** independent idle/low/high/load sample bands. Icecream has an extra
ordinary effect object, UFO has special engine state; the first custom-source
workflow deliberately rejects those two as custom tuning baselines.

Original engine resources observed: mono PCM16 at48000Hz (`rev9`, `engine3`,
`engine4`), and mono PCM16 at22050Hz (`engine9`, `ufo`). The engine loader
explicitly rejects stereo. General effect resources can be stereo/PCM8, which
does not establish that those formats are safe for `wsDsFxRevs`. The custom
compiler emits canonical44-byte RIFF/WAVE PCM16 mono48000Hz, matching ordinary
stock engine sources. Rates outside this authoring target are not claimed
qualified merely because DirectSound supports them.

## Driving-state response and boundaries

The previously recovered update method `00409EB0` (existing exact-build
Ghidra export) reads the per-car public dynamic state, not audio-recording
elapsed time. It puts clamped normalized RPM into engine-object `+18`,
engine-volume into `+8`, updates spatial location, performs race-finished
fadeout, and preserves separate gear-change effects. Fresh exact-binary
producer evidence `00443900 -> 00492C90 -> public+8` establishes that the
control is RPM/rev-limit, rather than a guessed semantic label. Gear effects
read the published gearbox index at public+4; native update also checks the
human-player gear-effect flag. No separate throttle/load engine-band selector
was found in this path. Throttle changes actual engine RPM through physics;
do not expose an invented independent accelerator/decelerator mix slider.

Fresh REA default analysis did not identify a function boundary at00409EB0;
the existing purpose-created Ghidra export is retained as complementary
evidence. It has not been silently promoted into a fresh REA result.

The custom candidate leaves this complete native update and synthesis path
unchanged. Consequently the new source responds through the same stock
driving-state controls, spatial attenuation and gear effects. Audibility,
whether the new timbre is convincing under acceleration/overrun, player/AI
mixing and race re-entry require human gameplay testing. No exact GT4 bank
crossfades, separate deceleration layer or modern engine simulation is claimed.

## Scoped runtime implementation

`vehicle_audio_native.append_audio` appends bounded wrappers to the existing
sealed external allocation, preserving the complete old payload prefix.
It changes only a selected stock tuning case's **engine-name interning call**.
For Navara tuning case7:

```
00409397 PUSH original_source_name
0040939C LEA ECX,[ESP+38]
004093A0 CALL004D0580
```

Wrapper preserves integer registers/flags, pushes `[ESI+54]`, invokes the
original no-argument Race singleton getter, then the original CarID getter
which consumes that same slot argument. Only an exact configured physical
addon CarID substitutes the resource-name stack argument. It tailcalls the
original interner with the original `ECX` handle and return address. Stock
CarID7 keeps its original name even while addon27 uses the same tuning case.
No global current-car state, source cache overwrite, registry identity change
or global replacement of `vehicles/rev9.wav` is involved.

Supported source substitutions cover ordinary tuned cases0..22, including
the shared18/21 constructor branch. Multiple configured physical IDs on the
same branch get independent resource names. CarID validation belongs to the
existing collection/capacity layer; audio's representable ID width does not
qualify new roster capacity. Duplicate physical IDs/namespaces, changed EXE
hash/call preimages, changed constructor ownership and allocation overflow
fail closed. With no custom profiles the image/blob are byte-identical.

## Evidence index

- Constructor: `ev_a374761407fc6e6893bcfb8af662ae25cac260327ad69715cc95ee3e994d10f1`.
- Source object: `ev_146a46569fc0196cd07f0688092858d2fe6509ce0f3af25f779fa248ededc449`.
- Loader: `ev_9ba9a6505866bb90439eda31a02d38e7114e3eb7b616bcb8b1bf1cbd8399c867`.
- Synthesis update: `ev_119f4cd67073862281473382894dcabbb3d2cfe3151c8a8d482c5e304657b144`.
- Table consumer: `ev_b15706dbfffa30778c739494a7c0eb6b7a28547443593a57c04f3589f242f7d6`.
- Normalized RPM accessor: `ev_48dfe48ca630f66e4fe0510f7dcd2cf07d2d9f7510af2b794c09adbf6f97cd39`.
- Public RPM/gear publisher: `ev_474ee23d2c718585eccf5e927d74fb84c155f066cd03372f19f27a103218fb00`.
- PCM generator: `ev_49dcdde5f80b4b77cace3eb1e36862a956424f365d44bfce59ee9ea78e633b25`.
- Original case7 call bytes: `ev_5a1a57ad5926c286b538839856399deb69eeef0d0906985df5bb403863bf0bc1`.
- Race getter RET: `ev_f070684bd41796bd7931710a74cb209ec8abd87cad52ee38632698e9a48c08ce`.
- Physical CarID getter RET4: `ev_d063d719fb9af61d5b51451cade370496bfccf7c18766056aed79030acd3ce26`.

`vehicle_audio_validate_native.py` executes the original pre-call instructions
and generated wrapper, with explicitly typed Broker/interner stubs.24 cases
cover4race slots×6physical identities, including two independently named addon
sources, stock donor passthrough, register/flags preservation, stack ownership,
foreign-build rejection and changed-parent rejection. This is ABI/control-flow
evidence, not a DirectSound playback or race test.

## Offline native DSP audition

`vehicle_audio_audition.py` executes the original normalized-RPM accessor,
original DSP constructor remainder, cubic control/table interpretation and
PCM16 source-loop/filter generator in Unicorn. The input is the user's pinned
original EXE and a compiled canonical engine WAV. No retail native code or
recording is distributed with the SDK. Control cadence is fixed20ms, source
phase is deterministic and stock table hashes are verified.

This is closer to native MR audio than generic pitch shifting, but remains an
isolated DSP diagnostic: no DirectSound scheduling/device behavior, listener
attenuation, SFX/engine-volume mix, gear-change effects or vehicle physics
evolution. Supply RPM sequences explicitly. A throttle slider is deliberately
absent because this path has no separately qualified native throttle layer.
The ordinary3D Previewer has not acquired a full race/audio mixer.

Native DSP at1000/3500/6500RPM (7000limit) yields control values around24,
421..446 and2554..2578 respectively, including deterministic sample-dependent
native variation. Lancer's compiled source has peak22295 and RMS8881PCM16.
Native filter clipping still occurs, as in original stock output: the private
isolated comparison observed approximate saturated fractions0.6/7.4/5.8% for
Lancer versus8.5/23.5/21.0% for stockrev9 under the same stock7 controls. This
is a measured diagnostic, not a subjective sound-quality or full game mix claim.
