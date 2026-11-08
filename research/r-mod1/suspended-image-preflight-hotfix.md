# R-MOD1-B suspended image preflight hotfix

## Scope

This hotfix replaces only suspended main-image discovery. The failed v4
candidate stopped at Toolhelp module enumeration before native patch
installation. The launcher no longer calls `CreateToolhelp32Snapshot` or
`Module32FirstW` for the suspended executable.

The pinned retail PE is I386/PE32, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, image
base `0x00400000`, `SizeOfImage=0x00311000`, and has relocations stripped. The
launcher uses the parsed and exact-build-checked `pe.image_base`; it does not
search for or accept another base. `VirtualQueryEx` must cover the complete
image extent with committed `MEM_IMAGE` regions whose `AllocationBase` is the
fixed image base. The mapped headers and each complete executable section are
then checked against the pinned on-disk file. Process path and x86 checks run
before this check. Native patch preimages, page protection/readback and the
seven-operation bundle are unchanged.

The portable implementation is in `src/native/rmod1/image_mapping.hpp` and is
used by the Win32 adapter in `launcher.cpp`. The native mock-memory harness
rejects absent or misplaced ranges, non-image allocations, uncommitted image
extent, altered PE headers, and altered executable-section bytes.

## Suspended-process test

`MRallyeRandomizerLauncher.exe --preflight --game-dir <game folder>` performs a
real `CreateProcessW(CREATE_SUSPENDED)` against the exact retail executable,
checks its process image path and x86 architecture, validates the map, makes
no process-memory writes, and terminates the child without resuming it. The
candidate builder and candidate checker run this test independently of the
file-only `--verify` mode. The opt-in
`tests/synthetic/test_r_mod1_suspended_preflight.py` runs the same Windows
test; it can be enabled with `RMOD1_RUN_WINDOWS_PREFLIGHT=1`.

In the current development environment, `CreateProcessW` fails with Windows
error 623 (`ERROR_ILLEGAL_DLL_RELOCATION`) for the pristine retail EXE before
returning a process handle. The same result occurred from a direct minimal
Win32 API probe; a suspended `cmd.exe` control process was created and
terminated normally. Therefore the map adapter was not reached by this live
preflight. Candidate v5 records
`PENDING_ENVIRONMENT_CREATEPROCESS_ERROR_623`; no workaround, resume, retry,
or alternate unverified base was added. A human test installation must pass
`--preflight` before the full launcher may be tested.

## Candidate v5 identity

Candidate: `.research-output/r-mod1/first-integrated-candidate-v5/`

| Artifact | SHA256 | Result |
|---|---|---|
| `MRallye.exe` input | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` | unchanged retail source |
| Launcher | `df22ff6f9e455977339358804f73112639686b798420d92baccb4acb7736a713` | rebuilt x64 |
| Runtime DLL | `432c72f4958bea4c9547799251e1c225df23a3e0ef032007fcebaa2f60a80fde` | byte-identical to v4 |
| Native patch plan | `e823fa7943f58aae16e8114c7ee46e11354d2d710f9eb8ec2ac32e80f8b83aaf` | same seven operations |
| Candidate manifest | `e6a631cca2188896b8e17915f78e8bfd23f6d11af0f5c5fc873f5a1bcc82e2bd` | preflight pending |

Plan template SHA256 remains
`1fd069633eae8713aa8cf2fbb0740a61170db57d36bf4683cdc30a1d79b9bc4f`.
INI bytes are unchanged from v4. The candidate contains no game EXE or game
assets. Package checks and exact-build `--verify` pass; Windows preflight is
blocked as described above, and gameplay is not qualified by this hotfix.

## Required human sequence

1. Run candidate `--verify` against the disposable exact-retail game folder.
2. Run `--preflight`; proceed only if it reports
   `SUSPENDED_PREFLIGHT_PASS` and `child_terminated_before_resume=1`.
3. If error 623 or any other preflight error occurs, stop before launching the
   regular launcher and provide the complete diagnostic output.
4. Only after the preflight passes, continue with the existing bounded v4
   gameplay handoff; do not change the INI, vehicle selection, grid limits, or
   seven-AI guards for this hotfix.

This hotfix does not claim a successful real mapped-image observation,
launcher runtime pass, or gameplay pass in the current development host.
