# R5V-J.2 stack hotfix — minimal human retest

Use only the repaired candidate. The earlier `runtime-candidate` is
`FAILED_BY_HUMAN_RUNTIME` and must not be launched again.

## Exact candidate

```powershell
$root = 'D:\Game\Master Rallye\master-rallye-re-vehicles'
$exe = 'D:\Game\Master Rallye\MRallye.exe'
$candidate = Join-Path $root '.research-output\vehicles\sdk\j2-reentry\repaired-candidate'
$loader = Join-Path $candidate 'mr-runtime-launcher.exe'
$bundle = Join-Path $candidate 'bundle'
```

Expected launcher SHA256:
`4a91217c7fcb1e78f2165d12634ee7fd1746ae28a5855c9698f10b8904a0afd4`.
Derived runtime candidate identity SHA256:
`22c8f428b8e1508091e3b447b1f4d9c5851aca64ca4475b0d70abf9d9c545eb7` (canonical
component record in `runtime-candidate-identity.json`).

Expected bundle identities:

* Retail EXE: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
* Addon plan: `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`
* Native patch manifest: `09d2852ff8c439bb102d5b6a351860101fc7094175ab79bd2faeefe79c9b891c`
* Native operation table: `aac0f887227c64ca4a591f542d9eda8a170b8b76f16687145c23e33664d57c17`
* Repaired stub: `f39f33838e0e7d3d276fbec03af0439c6c36a4807224ebe8cfc7ce14e70324ee`

The repaired candidate's `bundle\resource-root` contains two optional runtime
state files copied from the J.1 reference bundle. The integrated process uses
this candidate root as its working directory; the J.1 parent and installed
game files remain separate. Leave these candidate files in place, and do not
launch the failed `runtime-candidate` directory.

Before launching, verify the stock EXE and let the native launcher verify the
bundle. Do not continue unless the command prints `RUNTIME_BUNDLE_VERIFIED`
and returns zero:

```powershell
Get-FileHash -Algorithm SHA256 $exe
Get-FileHash -Algorithm SHA256 $loader
& $loader --verify $exe $bundle
if ($LASTEXITCODE -ne 0) { throw 'Hotfix preflight failed; do not launch' }
```

## Short test

Start a fresh process through the external launcher:

```powershell
& $loader --integrated $exe $bundle
```

1. Open Vehicle Select while a stock car is selected. It must open without a
   crash.
2. Switch T1 -> T2 -> T3 and back. Each transition must remain stable.
3. Select/commit ID27, leave Vehicle Select, then reopen the same player's
   selector. It must not crash and must restore ID27 as T2/local 7.
4. Repeat with ID26. It must restore ID26 as T1/local 7 without a crash.
5. Record active `PlayerID`, stored QuickRace Car0/Car1, `CarModel`, class,
   `selectedCar`, and XYButton X/Y values separately. The prior snapshots had
   different active PlayerIDs, so compare the same player this time.
6. A Broker capture of the ID27 re-opened state is sufficient for this initial
   hotfix qualification. Human observations cover the stock screen and ID26.
7. Exit normally and recheck that the on-disk EXE still has the exact retail
   SHA above.

If the game still crashes, stop. Do not try another candidate or add a patch.
Capture the exception code, faulting EIP, ESP, call stack, and currently loaded
runtime bundle identity for diagnosis.

Report each result as PASS/FAIL. This bounded retest does not repeat the Cup,
Master Rallye or SplitScreen capture suite. J.2 remains open pending this
human result.
