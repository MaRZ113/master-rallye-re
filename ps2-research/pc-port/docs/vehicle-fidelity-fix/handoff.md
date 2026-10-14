# Vehicle fidelity fix — runtime handoff

Status: IMPLEMENTED_PENDING_USER_RUNTIME. Starting HEAD: fb26d69daf96066b65e6963f52dd050801e45b4f. No original renderer or game assets changed.

The Terrano lamp exclusion from the preceding release was too broad. It is removed: the original 58-face reflection record remains reflective. The separate six-face OFF lamp surface is admitted only by exact source geometry, UV/topology and current native guards; the ON surface uses a different FVF and is excluded.

BrakeGlowMode=1 now requires the verified original PS2 RGB-fade texture. The old PC texture has red RGB=255 even at alpha zero; ONE+ONE discarded its alpha fade and exposed the polygon edges. The PS2 texture has fading RGB and constant alpha zero. Its RGB is preserved, not premultiplied by zero alpha. This corrects a texture/blend mismatch, not a demonstrated MSAA failure. Native selected brake draw remains authoritative; no brake/input polling is introduced.

Terrano bumper deformation fallback requires native VEHICLE_BODY proof, current generations and complete mirrored geometry, exact source UV and index topology, and Mode 4. It permits finite XYZ/normal deformation only. Unknown UV/topology remains Stock. New-game runtime confirmation is pending.

## Manual A/B

Keep the same Terrano, course, Free Camera bookmark, lighting and MSAA settings. Preserve your existing reflection configuration. Use ReflectionMode=4, ReflectionCoverage=1 and RaceModelMode=1. BrakeGlowMode=0 provides the stock glow comparison; BrakeGlowMode=1 selects the PS2-source glow pilot.

Manually copy the locally extracted `.assets/reflection/PS2BrakeGlow.gxi` beside PS2Port.ini and set BrakeGlowAsset=PS2BrakeGlow.gxi. The file is deliberately excluded from the archive. Missing/wrong bytes fail closed to stock glow. To regenerate from your original canonical PS2 corpus, run `python ps2-research/pc-port/tools/prepare_brake_glow_asset.py`.

Enable BrakeGlowDiagnostics=1 and ReflectionDiagnostics=1 for this test. Capture OFF brake and held brake at the same view; verify soft RGB falloff, no hard glowing plate, and restored reflections on the lamp surrounds. Check the separate brake ON surface is not blanket-reflected. Damage the bumper, capture before/after F10, and check whether reflections persist. The new bounded reflection record reports `exact_unique_source_uv_topology_on_deformed_native_body` with the measured current geometry and stable source key. If this record is absent, do not infer admission from the screenshot alone.

Then reset the window, restart the race and switch cars. Watch for missing reflections, persistent texture bindings, changed body/decal glass, MSAA changes, HUD/menu stalls or illumination while brake is released. Stop and retain logs if any appear. No automatic deployment is performed.

## Frontend and models

X-Trail COMPLETE: both new frames match 24/24 compiled records, share coherent native transforms, and demonstrate rotation. Current owner/cache-to-upload admission is still missing. No full frontend or race mesh replacement is included; wheel model differences remain deferred until that path is proven. See frontend/findings.md for the exact bounded observation point.

## Reproduction and validation

Run `python ps2-research/pc-port/overlay/build_overlay.py`. It stages immutable renderer Git objects, validates exact patches, and builds baseline then PS2-enabled Win32 Release with `--parallel 1` in the canonical reusable directories. For private asset upload native tests, set MRR_PS2_GLOW_GXI to the original local GXI and MRR_XTRAIL_GLASS_ASSET to the existing private headlight asset before the build.

Baseline CTest 24/24; PS2-enabled CTest 33/33; Python port suite 133/133; additional source/frontend evidence tests 6/6 PASS. Proxy exports and repeated interface generation PASS. Native tests cover the replacement texture bind/restore, Reset release/recreate, missing asset fallback, deformation identity, rejected UV changes, invalid indices, unknown body owner and stale generations. These are automated checks, not visual acceptance.

Frozen renderer tree: e33386bcf682db6983380c499e4928726c758fe0. Baseline DLL SHA-256: 011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138.
PS2 DLL SHA-256: 5377842c9b8cd0e62de640e5740c6ff387979fb8c1da305eb6440d15b5f5cc21.

Source, tests, source evidence, both DLLs, build report and SHA manifest are included in the clean handoff. Proprietary textures/models and large runtime captures are excluded. Existing unrelated worktree changes are preserved. No push.

Next: validate this Terrano OFF/ON/damaged A/B before further material tuning; frontend requires one current owner/cache consumer join before replacement.
