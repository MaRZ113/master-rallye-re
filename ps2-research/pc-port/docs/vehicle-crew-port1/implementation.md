# PS2-VEHICLE-CREW-PORT1 implementation

Starting branch master, HEAD `707085fa961237c413cfd0d2e95ec9d628460e55`. Work is confined to the independent PS2 port; neither staged integration patch nor frozen renderer source needed modification. The baseline renderer tree remains `e33386bcf682db6983380c499e4928726c758fe0`, staged from immutable commit `0bddf7c7bc5e95831f98714ff6231da05ab073ea`.

Static crew is restored from the existing pinned XTRAIL-CAR asset, without animation, new native objects or a new asset format. Explicit RacePS2CrewMode=1 requires the existing race model and parts selectors. Faces, bodies and helmets replace their own current verified native submissions. The PC17 topology audit proves its first38 faces are crew inserts, while its four separate trim faces retain their existing private replacements. The existing main chassis remains crew-filtered so the new per-part path cannot duplicate it. Both face records share counts but have different complete geometry digests; lookup resolves the digest rather than selecting by shape alone. Current native queue, compiled model, buffer generations/revisions, WORLD and race lifetime are rechecked. No historical pointer is a persistent identity.

FrontendModelMode=2 uses 20 pinned source profiles and the already accepted COMPLETE conversion/draw transaction. Every profile names its exact asset SHA/counts, all PC compiled source signatures and source-derived mixed-reflection decisions. A globally unique geometry anchor selects a candidate; full owner tree, all source records, previous-frame warmup, native bindings/matrices and current upload generations admit suppression. Resource files are opened only at family selection; one selected family is retained. Missing/corrupt assets are negatively cached, with a fixed 64-entry rejected-probe bound and per-profile failure bits. No startup load of the full fleet exists. Unknown modes/materials/files fail Stock. Owner/cache arrays have capacity32; admitted sources require at most26 slots. Existing Mode1 is retained.

Frontend audit covers all29 PS2 COMPLETE/CAR sources and26 PC pairings. The native decoder correctly rejected two initially converted profiles with missing primary bindings (Kia/Tata explicit mode3). Their ignored intermediate files are preserved but excluded from the runtime registry. Other explicit gaps are in coverage.md. Full generic CAR replacement is **not** activated: conditional/native glow records and family-specific mixed crew/interior suppression remain uncertified. This is a precise implementation boundary, not a parser failure or a claim that no other CAR can be ported. X-Trail chassis, parts and wheel pilots remain enabled through their accepted selectors.

Rear OFF X-Trail lamp reflection uses the existing ReflectionMode4 native draw transaction, with full geometry AND position/UV corner SHA. ON geometry has identical positions but different UV, so it cannot inherit OFF reflection. No private conditional mesh, reordered draw or repeated native target draw is introduced. Brake glow profiles cover20 exact native geometry+UV joins; Terrano also retains its original stronger full-vertex signature. The remaining eight PS2 glow meshes lack an exact PC join and stay Stock; the forklift has no corresponding source glow. Native brake branch selection remains authoritative.

An independent review exposed inherited SetRenderState notification slot57 in GlassTransaction. All three apply/restore notification sites now use actual D3D8 slot50. New tests update a real effective Shadow under successful/partial-failure glass and glow transactions and confirm full restoration while logical Shadow remains unchanged. No native material policy was changed by that correction.

Tests distinguish original-source fixtures from runtime observations. Ignored native lamp fixtures contain20 original PC glow uploads plus X-Trail OFF/ON; native tests verify positives, UV/position mutations, stale generations, unsupported modes and OFF/ON discrimination. Source fixtures are hash-pinned and excluded from the source handoff. Existing native state failure/rollback, resource lifetime, Reset, Stock, reflection capture/MSAA, proxy and overlay generator tests remain applicable. New appearance/performance/Reset behavior still requires the user runtime recipe.

Rebuild from the repository root (uses the canonical roots and serial MSBuild):

```powershell
python ps2-research/pc-port/docs/vehicle-crew-port1/lamps/prepare_native_fixtures.py
$env:MRR_FRONTEND_MODEL_ASSET=(Resolve-Path 'ps2-research/pc-port/.assets/vehicles/XTRAIL-COMPLETE.ps2model').Path
$env:MRR_RACE_MODEL_ASSET=(Resolve-Path 'ps2-research/pc-port/.assets/vehicles/XTRAIL-CAR.ps2model').Path
$env:MRR_WHEEL_MODEL_ASSET=(Resolve-Path 'ps2-research/pc-port/.assets/vehicles/XTRAIL-WHEEL-DRAW.ps2model').Path
$env:MRR_NATIVE_LAMP_FIXTURES=(Resolve-Path 'ps2-research/pc-port/.assets/vehicles/crew-port1-native-lamps.bin').Path
python ps2-research/pc-port/overlay/build_overlay.py
```

Both builds use `--parallel 1`, exact Git-object staging, strict patch hashes and repeat interface generation. Private fleet conversion is reproducible with `fleet/convert_fleet_complete.py`; it requires the previously prepared source-derived inputs and original default texture. The copied runtime frontend registry must equal its generated metadata draft. `lamps/generate_runtime_registry.py --check` verifies glow registry reproducibility. Nothing deploys into the game directory or pushes Git.
