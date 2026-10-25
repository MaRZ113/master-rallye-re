# J.3-B human runtime handoff — GlacierSprint

This is a narrow first real runtime-compiler test. It uses the original retail
executable and a separately compiled external launcher. The bundle contains
the Mercedes/ID26 baseline and GlacierSprint/ID27 collection; the exact bundle
and launcher are in ignored `.research-output` and are not part of Git or the
source review ZIP.

## Candidate identities

- Original retail EXE expected SHA256:
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
- Bundle: `.research-output/vehicles/sdk/j3b/glacier-sprint-runtime-final`
- Bundle addon-plan SHA256:
  `1a242651f78fbe7d528d1f078be35573a37fb78abb955c53ad5d438af1b20dff`
- Bundle native manifest SHA256:
  `539ec636e7294eda561a819c89c416d15fb0aee49cd64f9dad37c048840e4a47`
- Bundle RVP SHA256:
  `3f18db5ab4f3d635f743868d3649b4f5b41d5198f31d26fb8f2e7a7be3076e0e`
- Bundle resource inventory: 187 files, index SHA256
  `137d44afd6c2dc93723d340d8a59371b19a64c79b78f2543ea028ab246aba156`
- Launcher:
  `.research-output/vehicles/sdk/j3b/glacier-sprint-launcher/mr-runtime-launcher.exe`
  (SHA256 `f93cb2c1dc92285fb268a99ff462dce63276c0be772fbba41be653fc6f473d1b`).

The pristine EXE must remain at its normal game installation path. Do not copy
the bundled reconstructed image over it. First run from the worktree to verify
the exact retail file and staged resources:

```powershell
$retail = '<full path to the original MRallye.exe>'
$launcher = '.research-output/vehicles/sdk/j3b/glacier-sprint-launcher/mr-runtime-launcher.exe'
$bundle = '.research-output/vehicles/sdk/j3b/glacier-sprint-runtime-final'
& $launcher --verify $retail $bundle
```

Expected output includes:

```text
RESOURCE_ROOT_VERIFIED files=187 index=137d44afd6c2dc93723d340d8a59371b19a64c79b78f2543ea028ab246aba156
RUNTIME_BUNDLE_VERIFIED patch_operations=247 plan_sha256=1a242651f78fbe7d528d1f078be35573a37fb78abb955c53ad5d438af1b20dff
```

Only after that preflight succeeds, launch the integration:

```powershell
& $launcher --integrated $retail $bundle
```

The launcher refuses unqualified local DLL proxies beside the executable and
starts the exact executable suspended, installs the complete validated patch
set, checks the resulting process image, then resumes it. The game current
directory is the bundle's `resource-root`. Launch directly without the
external launcher to disable the mod. Remove only the external bundle and
launcher after the game exits; keep all save/profile files.

## Test sequence

1. Record `Get-FileHash $retail -Algorithm SHA256` before launch.
2. Run `--verify`; require both success lines above.
3. Run `--integrated`; verify Vehicle Select still operates, then choose
   Vehicle Select T2 local7 and confirm `NORTHSTAR / GLACIER SPRINT`.
4. Start one short single-player T2 Quick Race with a stock T2 player.
5. Through Observatory, capture `Race/Car0` when GlacierSprint is player, or an
   active AI only if naturally selected. The player case must report
   `CarID=27`, `CarClass=1`, `CarType=GlacierSprint`, and
   `WheelType=GlacierSprint`. The configured marker is
   `[0.1,0.75,0.35,1.0]`; vehicle paint and marker are independent channels.
6. Confirm the visible vehicle loads and drives; note any renderer, collision,
   physics, lock-state, or return-to-menu issue. Do not infer untested AI or
   persistence behavior from the launcher log.
7. After exit, hash the original EXE again. It must remain the expected retail
   SHA. Save both hashes, launcher log, Observatory JSON/raw pair, and human
   observations outside Git; report the exact candidate hashes with them.

This candidate is ready for a human runtime test, not runtime-qualified. No
new human capture is fabricated here. The previous ID27 re-entry issue is
covered by the unchanged `C7 46 18 07` mapping and a statically verified
collection-specific republisher at the cave address named in the native
patch manifest; same-player re-entry remains part of the observed test.
