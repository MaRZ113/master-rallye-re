# SUPERSEDED: stack-only candidate is crash-free but ID27 still restores as Navara.
# Use root-cause/human-retest.md and the root-cause-candidate directory.

# J.2 Vehicle Select re-entry human test — prior candidate

This is the remaining J.2 human gate. The 2026-10-09 capture archive already
confirms the simultaneous ID26/ID27 SplitScreen state, Rallye Cup stage reuse,
and Master Rallye fresh-process roster persistence. This candidate only adds
the narrowly scoped Vehicle Select re-entry synchronization described in
[`frontend-reentry-fix.md`](frontend-reentry-fix.md).

## Candidate and preflight

The candidate is under the canonical vehicle checkout's ignored research
output. It uses the unchanged retail executable and the J.2-specific external
launcher:

```powershell
$exe = 'D:\Game\Master Rallye\MRallye.exe'
$root = 'D:\Game\Master Rallye\master-rallye-re-vehicles'
$candidate = Join-Path $root '.research-output\vehicles\sdk\j2-reentry\runtime-candidate'
$loader = Join-Path $candidate 'mr-runtime-launcher.exe'
$bundle = Join-Path $candidate 'bundle'

Get-FileHash -Algorithm SHA256 $exe
Get-FileHash -Algorithm SHA256 $loader
& $loader --verify $exe $bundle
if ($LASTEXITCODE -ne 0) { throw 'J.2 candidate preflight failed; do not launch' }
```

Expected values:

| Artifact | SHA256 / value |
|---|---|
| On-disk retail EXE | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` (3,121,214 bytes) |
| J.2 external launcher | `c10c27a72387004a3696a1eab3d25f24e777ea2c566bf0a5f642f68e1085765c` (141,312 bytes) |
| J.0 two-addon semantic plan | `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989` |
| J.2 native patch manifest | `53c5b1deccfaee1e798a7ff271db8232028eab501060186b582b04974e41b489` |
| J.2 native operation payload | `945012567528fbe1b2794ed48b6d17473bcca340cc4e35d60d41a0fdd1c4fd9e` |
| Runtime resource index | `2fc7121c3d4f66c407cedbcb47dc223c580301971e3d12d16aa197c7a70a3384` |
| Native reconstructed image (analysis only) | `aee7439cdc00897b23984042b26e566629156330f908e6c03533bfd1bfe6255e` |

Preflight should report 243 verified resources and 248 native patch operations.
The resource root is `bundle\resource-root`; the original EXE is never written.
After the test, recheck the retail EXE SHA. Do not run if any expected identity
or inventory check differs.

## Test sequence

Launch the candidate only after `--verify` passes:

```powershell
& $loader --integrated $exe $bundle
```

Use an isolated/test profile if available. Do not overwrite stock files or
reuse a valuable save for failure testing. Keep the loader log separate from
Observatory captures. For each capture, record active `PlayerID`, stored
QuickRace Car0/Car1, `VehicleSelect/CarModel`, `selectedCar`, class, and
`UI/XYButton/XValue`/`YValue` separately.

1. **ID27 / T2:** select and commit R5VQualifier, complete a short race,
   return through normal Results/frontend flow, and reopen player 0 Vehicle
   Select without navigating. Capture `j2-reentry-id27`. Expected: physical
   CarModel 27, T2/YValue 1, local XValue 7, and R5VQualifier identity.
2. **ID26 / T1:** repeat the return/reopen test for Mercedes. Capture
   `j2-reentry-id26`. Expected: physical CarModel 26, T1/YValue 0, local
   XValue 7, and Mercedes identity.
3. **Stock ID7:** deliberately choose Navara and repeat. Capture
   `j2-reentry-stock-id7`. Expected: CarModel 7, T2/YValue 1, XValue 0, and
   normal stock selection behavior.
4. **SplitScreen independence:** where the native mode allows it, set player 0
   to ID27 and player 1 to ID26, leave/reopen each selector, and verify each
   follows its own stored vehicle and local ordinal. Capture
   `j2-reentry-splitscreen`.
5. **Locked ID27:** with the stock unlock predicate false, verify its locked
   presentation remains locked and accept cannot commit it. This is a
   regression check; do not infer commit from `selectedCar` alone.

The expected class/local map is ID27 -> T2/local 7, ID26 -> T1/local 7, and
ID7 -> T2/local 0. No physical ID should alias another. Stop on a wrong
CarModel, wrong class/local value, failed lock, crash, missing resource,
profile mutation, or EXE hash change. No further J.3 or ID28 work is in scope.

## Evidence classification

The existing 19-pair archive is already verified and summarized in
`runtime-evidence-2026-10-09.json`. It confirms the prior gameplay and
persistence results; it does not itself test this newly built J.2 re-entry
hook. A successful preflight is only package/static evidence. The human screen
and in-game result plus Broker state are required before marking the re-entry
fix runtime-confirmed or closing J.2.
