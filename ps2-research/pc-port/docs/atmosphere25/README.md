# ATMOSPHERE2.5 — instanced props, LiveTuning, GT3-style sun, Turkey3 fixes

Status: build-verified (CTest), gameplay checks per candidate in `.research-output/atmosphere25`.

## Material metadata (reproducible)
`Atmosphere25/materials.lsm` = `export_lighting_metadata(sources, [France1, Turkey2, Turkey3], roles.json)`
followed by `add_common_records(lsm, DataGx)`. Sources, in order:
`Data.sma_unpacked/DataGx/Course` (retail) and the test install `DataGx/Course` (PS2 delta courses).
With the 002 roles the export reproduces the 002 LSM byte for byte (f019c6b5…).
`roles.json` adds `Turkey3/newtex-tga = static`: the PS2 Turkey3 caravan body/windows/door/wheel
atlas (caravan-tga is only its wooden/metal base).

## Runtime findings (Turkey3, sessions 52188 and 48748)
- Checkpoint boards: one mesh drawn per board with a non-identity WORLD matrix; the resolver
  rejected all such draws. Instances are now lit in world space; LSM falls back to `Common`.
- Caravan: visible part is `newtex-tga` (was Deny), see above.
- Bridge rails / thin paired props: shared vertices for front and back faces always used the
  sun-facing normal. Non-vegetation ambiguous vertices now mix 35 % lit / 65 % shadow colour.
- LiveTuning: file-time detection missed profiles copied over Atmosphere.ini (copy keeps the
  source time). Detection is now by content every 30 frames; Ctrl+Alt+R forces a reload.

## Sun keys (degrees of view, additive intensities)
`SunCoreSize SunGlowSize SunBloomSize SunRaySize SunRays Sun{Core,Glow,Bloom,Ray,Flare}Intensity
SunCore{R,G,B} SunGlow{R,G,B} SunBloom{R,G,B}`. Reference look: GT3 blue-Miata shots on the
Deep Forest Reverse sky (user's ShareX `2026-11/Atmo/miot1..3.png`).

## Runtime-004 follow-up
- Bridge rails are `boat2-tga` (the boat atlas, ~100 m along the bridge); A/B pixels were identical,
  i.e. never lit. `boat` is no longer a hard SDK exclusion (still Deny without a role); roles.json
  sets the four Turkey3 boat materials static. A material bound by plain AND noise passes with one
  category now merges the pass flags instead of becoming Deny (boat2: Noise|Plain).
- PS2 source-point grass and rigid props (tumbleweeds, barrels, bales) are proxy draws; their private
  vertices now get the same world lighting (grass: up normal; props: outward face normal). Their fog
  colour is still the native one.
- Sun: 72 soft spokes of pseudo-random length/strength + faint radial haze; optional
  `SunRaysTexture=` sprite made with `tools/atmosphere_sun_sprite.py` (no GT3 asset shipped).

## Open
Only France1/Turkey2/Turkey3 have metadata. Fleet body materials only for Patrol/Tata.
