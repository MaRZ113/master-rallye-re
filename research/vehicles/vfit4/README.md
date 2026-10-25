# V-FIT4 + V-AUDIO2 — Lancer visual attachments, shadow and transmission layer

Status: **offline-qualified candidate for human gameplay testing**. The game
was not launched for qualification. Work remains on `research/vehicles`.

## Candidates

- Main: `.research-output/vehicles/vfit4/candidate/Launch-Vehicle.cmd`.
  Dynamic brake attachments, corrected shadow and optional authored whine.
- Audio A/B: `.research-output/vehicles/vfit4/candidate-no-whine/Launch-Vehicle.cmd`.
  Identical visual resources and physics, original engine audio only.
- Earlier `candidate-static` / `candidate-whine` are intermediate rest-pose
  controls, not the recommended final attachment implementation.

## What changed

### Brake discs and calipers

GT4 callbacks11..14 had been baked into the body at source hubs
`X=±0.745, Y=0.18535, Z=±1.255 m`. Current MR unloaded attachment data gives
`X=±0.745, Y=0.15, Z=±1.30 m`. This explains a 57.224 mm rest-frame mismatch;
the asymmetrical caliper bounds are not used to guess a rotor centre.

The final candidate removes only the twelve qualified mechanical draws from
`car.dx`, preserves their attributes in four `mechanicsN.dx` resources and
attaches them through native scene entities. Native `00441270` publishes
hub/jounce/steer/camber without spin; `004485E0` adds wheel spin separately.
The auxiliary instances use the native base interpolation path `005090F0`.
Their inverse rest basis preserves the positive-side half turn and the rotor's
37.34 mm lateral inset relative to its hub. There are no physics offsets.

All 107 retained body draws preserve triangle attributes, normals, UVs, RGBA,
material/control words and blight cases. Body collision bytes are identical.
The unsprung mechanical instances are independent visuals, like native wheels;
they do not receive body-panel damage deformation. Remaining body damage and
coverage-alpha ownership continue through the source-bound native bridge.

`complete.dx` already had source-consistent embedded wheels/brakes and is
unchanged. The rest-pose preview does not simulate tyre contacts or settled
suspension. No additional body translation was justified or introduced.

See [native attachment evidence](brake-attachments.md) and
[source/rest-frame analysis](brakes.md).

### Shadow

Native `00588200` obtains marker1339 model bounds and expands width by 1.75,
length by 1.5, using shared `misc/shadow/shadow.dxt`. Lancer retained Navara's
donor X/Z bounds. Editing that shared texture would change stock vehicles.

The optional `shadow-profile.json` instead supplies shadow-only bounds at the
single shadow-consumer call. Admission checks the entire case/slash-normalized
model resource name and all 40 original bounds bytes. The build also pins the
emitted DX and original texture SHA256. Collision/spatial bounds and the shared
texture remain unchanged.

At alpha>=32, the flat-ground footprint changes from
`X[-1.29842,1.32357], Z[-3.19047,2.70415] m` to
`X[-0.94087,0.94087], Z[-2.39199,2.30361] m`.
That shortens the rear extension by 0.79848 m and front by 0.40054 m. Explicit
default margins are 50 mm per side and 100 mm per end. Scale and offset controls
remain editable. Texture softness beyond this alpha threshold is preserved.

See [shadow evidence and controls](shadow.md). Private before/after diagram:
`.research-output/vehicles/vfit4/captures/shadow-footprint.png`.

### Transmission whine

Optional `audio-profile.json.transmission_whine` adds a separately owned native
SFX loop. Pitch follows actual inputshaft/engine speed; gain uses a bounded
signed net-crank-torque/peak-torque response and drive/coast settings. Neutral
can mute it. The existing engine source and native engine DSP are unchanged.
The effect uses original creation, entity binding, manager and destruction
paths, scoped to the physical addon CarID.

No authentic GT transmission sample was identified reliably. The test source
is explicitly synthetic: a periodic 800 Hz tone with authored harmonics, 4000 RPM
reference and a 12-tooth design choice. These are not recovered Evo IV values.
It is optional, namespaced and replaceable with a user-provided WAV. Native
SFX has a 0.05 cutoff, so low gain/distance can make the layer inaudible.

See [native controls](../vaudio2/native-whine.md) and
[GT source investigation](../vaudio2/transmission-source.md).

## Reusable SDK interfaces

- `mechanical-attachments.json`: source-pinned draw groups and qualified hub
  frames. Explicitly list the four generated DX names in `assets.required_roles`.
  Future models provide their own source-qualified selections; no Lancer draw
  numbers are embedded in converter/native code.
- `mechanical_attachments.build_mechanical_resources()`: extract selected
  mechanics, audit retained attributes, preserve native brake-switch grammar.
- `visual-fitment.json`: optional position-only static control. Mutually
  exclusive with dynamic mechanical attachments, preventing double correction.
- `vehicle_shadow.generate_profile()` / `bind_profile()`: regenerate shadow
  admission whenever emitted model bytes change; supports scale/offset/margins.
- `audio_profile.compile_audio()` / `audio_resource_hashes()`: optional whine
  resource with an exact resource/hash allowlist. No arbitrary DataAudio paths.
- `build_vehicle_extensions_candidate.py`: reuse the existing sealed builder
  while preserving the selected project's physics.

Native family/count/allocation guards are SDK guards, not new engine-capacity
claims. SCALE1 registration/capacity code was not changed.

## Preview and reproduction

Private retail/GT source inputs are required. None are included in the source
archive. Rebuild into a fresh directory, for example:

```powershell
$env:PYTHONPATH='src;tools;.;.research-output/vehicles/scale1/python-tools'
python tools/build_vehicle_extensions_candidate.py --project .research-output/vehicles/vfit4/candidate/project --output .research-output/vehicles/vfit4/rebuilt-candidate
```

Inspect the actual converted body, wheel and sealed auxiliary resources:

```powershell
python tools/preview_vehicle.py .research-output/vehicles/vfit4/candidate/author-build/DataGx/Vehicles/LancerEvo4/car.dx --physics-xml .research-output/vehicles/vfit4/candidate/author-build/DataGame/vehicles.xml --physics-family LancerEvo4 --physics-profile .research-output/vehicles/vfit4/candidate/project/physics-profile.json --attachment-build .research-output/vehicles/vfit4/candidate/author-build --model race
```

Preview profiles now admit explicit `attached_models` tied to wheel poses.
`--mechanics-profile` adds hash-pinned red source/green target hub overlays for
the static diagnostic. Markers are depth-independent diagnostics, never game
geometry. Existing viewer controls/reload are retained. Audio preview adds
optional whine, signed-load and gear controls; engine rendering still uses the
original read-only native DSP. The whine audition mix approximates loop playback,
not DirectSound spatial scheduling.

## Validation and preservation

- Full synthetic suite and separate exact-x86 replay reports are in
  `.research-output/vehicles/vfit4/`; see `validation.json` for final counts.
- Native shadow replay: 54 cases, including original getters/interner and
  footprint arithmetic; backing cache service remains a stated boundary.
- Whine replay: 28 identity/control cases, 73 bounded-map publications, native
  construct/register/bind/destruct/free. Backend/Broker/allocator boundaries are
  explicit in the report; no audible/gameplay qualification is inferred.
- Mechanics replay: repeat scene cycles, duplicates, name variants/nearmisses,
  all allocation-failure points, original non-spin pose, transform controller
  and generic interpolation. Services are controlled stubs where documented.
- Final-body native damage replay: source/native deformation and RGB match,
  zero exact-position splits, zero coverage vertices incorrectly losing alpha.
- 228 declared immutable resources are byte-identical to V-PHYS3/V-AUDIO1.
  Changed: `car.dx`; added: four mechanics DXs and optional whine WAV. Physics
  XML/profile, collision, wheel, frontend model, UI and engine WAV are unchanged.
- Previous author build reproduces all 94 files; new author/runtime determinism
  is checked separately. Frozen Subaru V-MESH4.13, Lancer V6, SCALE1 29/30
  launcher verification passes. The original EXE and graphics DLL hashes match.
- Fresh candidates do not inherit generated PlayerState/settings save files
  from earlier gameplay. Those are excluded from immutable asset comparisons.

## Human gameplay gate

1. Start with the main candidate; use a fresh neutral Vehicle Setup and the
   same track/camera as the prior test. Handling settings were not changed.
2. Observe rotor centres at rest, over bumps and while steering. Calipers must
   follow wheel hubs without spinning. Check both sides and repeated race entry.
3. Compare the top-view shadow at the same terrain/lighting; ensure a stock car's
   shadow is unchanged. Live model-key/bounds admission is still unqualified.
4. Listen under acceleration, coast, neutral and gear changes; check AI and race
   exit/re-entry. Use `candidate-no-whine` for an audio A/B.
5. Confirm menu, wheel orientation, crew, reflections on/off, native damage and
   stop lights still behave as before. Offline replay/captures do not replace
   these tests.

No original executable/DLL edits, physics tuning, Randomizer changes, capacity
expansion, commits, pushes or publication were performed.
