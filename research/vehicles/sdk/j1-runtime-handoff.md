# R5V-J.1 human runtime handoff

## Candidate identity

Use these paths from the `master-rallye-re-vehicles` checkout:

```text
retail executable:
D:\Game\Master Rallye\MRallye.exe

launcher:
D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\sdk\j1\launcher-release-final\mr-runtime-launcher.exe

runtime bundle:
D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\sdk\j1\reference-runtime-final

effective external resource root for integrated launch:
D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\sdk\j1\reference-runtime-final\resource-root
```

Pinned retail EXE SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
(3,121,214 bytes).

Launcher SHA256: `9d4a98d01166362933974f8c376f3a42323feecfdfd021af7df0a3b1aceb31b5`
(141,312 bytes; MSVC x64). Native patch manifest SHA256:
`78c1070f2e656677f02d22f5d4fdff457e43c7ba74c67bb4e5a5c1488ca53179`.
RVP1 operation table SHA256:
`f4938b1a997364e371af6b1aee4798ca1865d67b22752bead9849c5d216a34ce`.
The two-addon J.0 plan remains byte-identical with SHA256
`357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`.
The reference reconstruction hash is
`dd03adbd9f45c679e59d09e0a9f09337bd99c787d81f4ce018edb654c1cec881`; it is
not a hash of the mapped process address space and no patched EXE file is
included or emitted.

## Preflight

Close any running game. In PowerShell, from the vehicle checkout:

```powershell
$exe = 'D:\Game\Master Rallye\MRallye.exe'
$loader = '.research-output\vehicles\sdk\j1\launcher-release-final\mr-runtime-launcher.exe'
$bundle = '.research-output\vehicles\sdk\j1\reference-runtime-final'

Get-FileHash -Algorithm SHA256 $exe
& $loader --verify $exe $bundle
if ($LASTEXITCODE -ne 0) { throw 'J.1 runtime bundle verification failed' }
```

Expected result: retail hash above, then `RESOURCE_ROOT_VERIFIED files=243`
and `RUNTIME_BUNDLE_VERIFIED patch_operations=246`. The candidate has one
file-only PE-header record that is never written to the mapped process, 244
byte-changing process-memory ranges, and one identical-byte no-op canary.

The verifier does not copy or replace `MRallye.exe`. It does not remove or
overwrite game-generated runtime profile files. Only `DataGame/PlayerState.xml`,
`DataGame/PlayerState.xml#`, and `DataGame/options.xml#` are allowed as separate
runtime state beneath `resource-root`; preserve them. All other unindexed files
cause a verification failure.

## Test A — ordinary retail startup

First launch the retail EXE normally, outside the J.1 launcher. Confirm the
usual frontend opens and exits normally. Capture the on-disk SHA before and
after; both must match the pinned retail SHA. This is a human control test.

## Test B — external bootstrap only

Run:

```powershell
& $loader --bootstrap-only $exe
```

The launcher verifies the exact image, creates it suspended, checks the
mapped x86 image identity/base and mapped bytes, resumes it without installing
any game operation, then waits for normal exit. Expected log includes
`BOOTSTRAP_PREFLIGHT_PASS`, `PROCESS_IMAGE_VERIFIED`, and
`PROCESS_EXIT ... retail_exe_sha256=<pinned SHA>`. Confirm normal frontend
behavior and capture the EXE hash again.

## Test C — no-op process-memory canary

After Test B passes, run:

```powershell
& $loader --canary-only $exe $bundle
```

This installs only the exact same four bytes (`File`) at the audited mapped
`.rdata` import-name location, verifies readback, restores the original page
protection, and resumes. It must print `IN_MEMORY_CANARY_VERIFIED` before
normal frontend startup. The canary has no semantic gameplay effect; report it
as a launcher memory-write exercise, not an addon or hook runtime pass.

## Test D — integrated Mercedes addon

Only after A-C behave normally, make a copy of any unlocked test profile into
the external `resource-root/DataGame/PlayerState.xml` if ID26 is locked in the
fresh external profile. Copy; do not move, edit, or reset the original save.
The default runtime bundle intentionally contains no user profile. The
launcher preserves the external profile files and the verifier excludes them
from the asset inventory.

Before starting, ensure no unqualified adjacent graphics/input/audio proxy
DLL is present. The current launcher fails closed if it sees one of its
known proxy names; wrapper coexistence has not been proven. Then run:

```powershell
& $loader --verify $exe $bundle
if ($LASTEXITCODE -ne 0) { throw 'J.1 runtime bundle verification failed' }
& $loader --integrated $exe $bundle
```

The EXE remains at the retail path. The child CWD is the external `resource-root`.
The game has not yet been proven to resolve all resources from this separated
root, so abort on an unexpected load error. Check Observatory's process image
path and `Resource Root` field; they must identify the retail EXE and external
root respectively.

Select Mercedes ID26 and verify in the active race:

* `Race/Car0/CarID = 26`
* `Race/Car0/CarClass = 0`
* `Race/Car0/PlayerType = 1`
* `Race/Car0/CarType = Mercedes`
* `Race/Car0/WheelType = Mercedes`
* `Vehicles/Car0/*` reports the expected Mercedes runtime family.

Human observation should separately confirm the Mercedes model, wheels,
frontend identity, controls, and stable movement. Do not use launcher logs as
proof of the rendered model or gameplay. Capture the loader log and Broker
snapshot as separate evidence; record whether a race was entered/completed.
After normal exit, verify `MRallye.exe` still has the pinned SHA.

## Safe failure check

The compiled native launcher has already been run against
`C:\Windows\System32\notepad.exe` in `--bootstrap-only` mode. It exited 1
with `FAIL_CLOSED: retail executable SHA256 mismatch` before creating a game
process. No failure-injection run was made against a real game process.

If any test fails, preserve the launcher output, resource root and any runtime
profile files for diagnosis. Do not begin J.2, ID28, or UI ordering from this
handoff.
