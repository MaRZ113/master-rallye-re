# R-MOD2 BOOT-B — in-process activation through the DirectInput proxy

## Scope

BOOT-B reuses the existing F3 runtime core and native operation planner. It
changes the activation route: the local x86 `dinput8.dll` forwards to the real
Windows DirectInput DLL, then attempts one startup installation on the first
`DirectInput8Create` call. No Randomizer policy or native callback was rewritten
for this route. The OEP bootstrap operation is deliberately omitted because
the entry point has already run. The generated F3 code/data templates and
operation preimages remain the source of native patch bytes.

The unchanged retail executable remains pinned to SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and
3,121,214 bytes. The runtime core is pinned to the accepted F3 SHA256
`cf743e356e3198cadd68ce750ff9f8c2cce5cb7caa965a4ee64d40c75f442da3`.

## Startup ordering evidence

Exact-build static call-chain inspection places the first DirectInput call at
`0x00570E21` under `FUN_00652F50` / `FUN_005AFB20`; that initialization returns
before control enters the long-running `FUN_005AFE30` frontend loop. F3's
Quick Race/Cup/Master selector sites, opponent list and Start handlers, and
Challenge preview sites are reached through later user-driven frontend/mode
actions. Thus the first DirectInput call is the selected pre-hook boundary.
This is static executable evidence, not proof of Windows runtime scheduling;
the BOOT-B human launch test remains mandatory.

The DirectInput wrapper resolves and verifies the genuine architecture-matched
system DLL before invoking BOOT-B. Initialization is guarded by `INIT_ONCE`;
the proxy's `DllMain` remains inert. Concurrent exports cannot reinstall the
patch plan. Initialization failure is logged but ordinary DirectInput
forwarding continues; if transactional rollback cannot be proven, the process
is terminated rather than resumed with partial hooks.

## Transaction

Before any native image write the installer verifies the process image path,
on-disk retail hash and size, x86 PE32 fixed image base, mapped PE headers,
`MEM_IMAGE`/committed allocation ownership, and each executable section's
virtual extent. It verifies the adjacent runtime DLL hash and x86
format, checks all required F3 exports, parses the game-directory ConfigVersion
2 INI through the same `core.hpp` parser, calls the existing configuration
export, and selects operations from the generated F3 feature masks.

The first human BOOT-B attempt failed because live `.text` was compared through
`SizeOfRawData` after startup. Retail `.text` has RVA `0x1000`,
`VirtualSize=0x28D294`, and `SizeOfRawData=0x28E000`; the trailing 3436 bytes are
file-alignment padding outside the audited virtual code extent. The corrected
verifier validates committed `MEM_IMAGE` mapping across the virtual extent and
diagnoses the first mapped-code difference there. Logs include section, RVA,
absolute VA, expected/actual byte window, page protection, and whether the
difference overlaps an operation selected for this configuration.

A difference outside selected operation ranges is diagnostic evidence, not
proof that an unknown third-party modification is harmless. A difference at a
selected hook range fails closed. Independently, every selected native
operation must match its complete exact retail preimage, expected image mapping
and protection, and pass a second preimage check after other threads are
quiesced. The complete on-disk retail SHA256 and size gate is unchanged.

The code/data regions must be free at their audited fixed addresses. The
installer fills the existing generated templates and callback slots, verifies
read-back and code protection, then suspends every other game thread at the
early startup boundary. While those threads are quiescent it rechecks native
preimages, opens only the verified image pages, applies all selected operations,
verifies read-back, flushes the instruction cache and restores original page
protection. A recoverable transaction failure restores original bytes before
threads resume. If reopening pages or byte restoration fails, the process is
terminated. Fixed-address conflicts and incompatible preimages fail closed.

The installer does not install a second set of gameplay hooks. It applies the
same generated F3 operations and callback table. In-process installation is
separate from the suspended launcher because OEP replay is invalid after the
entry point has executed.

## Candidate profile and logs

The first profile enables only the existing Quick Race T1 randomizer policy,
keeps AI count at three, disables add-on discovery, and enables diagnostics.
ConfigVersion 2's existing shared mode hooks preserve its generation-boundary
live policy reload. The package includes `dinput8.dll`,
`MRallyeRandomizerRuntime.dll`, `MRallyeRandomizer.ini`, and a README. It
contains no executable or game assets. The original graphical `d3d8.dll` is
not included or modified.

`MRallyeRandomizer-boot.log` records the proxy/system-DLL stage, host image
verification, runtime load, config decision, installed native operation count,
and `BOOT_B_READY` or `BOOT_B_FAILED`. A loaded proxy alone does not mean the
Randomizer initialized.

The source builder derives its plan from the exact retail executable and the
unchanged F3 core build. Review metadata distinguishes the full plan operation
table (which includes the excluded OEP record) from the selected in-process
operation set for the sample INI.

## BOOT-B offset correction (2026-10-10)

The first human attempt reached `CONFIG_ACCEPTED` and
`IMAGE_DIFFERENCES_NONCONFLICTING`, then failed with
`config blob overlaps generated F3 runtime data`. The root cause was a unit
confusion: `kConfigOffset=0x100` and `kDllPathOffset=0x1200` are offsets within
the generated allocation, but the in-process installer subtracted
`kDataBase=0x70010000` as if they were absolute VAs.

The staging operation was also unnecessary in BOOT-B. `MRConfigureBlobV1`
already consumes the local length-prefixed INI buffer, while the only generated
reader of `CONFIG_BLOB` and `DLL_PATH` is the OEP bootstrap, which the proxy
path explicitly omits. The fix removes only the second copy and its invalid
bounds check. The generated constants and F3 gameplay code are unchanged.
Absolute callback-slot VAs continue to be translated once through a checked
VA-to-allocation-offset helper. The same production helpers now prepare code
and data templates, validate selected operation ranges/overlap, and verify
exact native preimages.

The Windows host-qualified preflight harness verifies the pinned retail file
SHA from disk, materializes generated templates, checks callback-slot
translation, exercises empty/default, ConfigVersion 2 and maximum 4096-byte
INI cases, and checks the selected operation preimages against retail PE bytes
plus a deliberate negative mismatch. It is a startup-preflight test, not a
live game or renderer qualification. Human testing must still confirm the log
reaches `NATIVE_INSTALL_COMPLETE` and `BOOT_B_READY` before testing Quick Race
or hot reload.

## Non-Quick-Race Start pass-through hotfix (2026-10-10)

The DLL runtime loaded successfully, but Practice and Checkpoint Start were
denied when the configured Quick Race ceiling was seven. The shared native
Start hook is also reached from other frontend contexts; those calls are not
evidence of Quick Race mode. The previous `plan_quick_race()` returned
`allowed=false` for every mode except 2, which caused the callback to cancel
the original Start action.

The corrected policy admits every `mode_id != 2` as a native pass-through with
`use_extension=false`, zero Quick Race participant counts, and the diagnostic
reason `Native mode passthrough; no Quick Race opponent extension applied`.
It does not interpret unknown mode values (including -1) as Practice or
Checkpoint identifiers and does not use stale Quick Race count values to make
the decision. Only mode 2 enters the Quick Race count, max-opponents and
extended-AI checks. The exported callback calls the same shared evaluator used
by the callback-path regression tests.

The generated x86 Start hook and its displaced call remain byte-identical:
one callback check, exactly one `FUN_0047B780` setup call on the admitted path,
the existing blocked epilogue, and continuation `0x0047AD11`. No hook, stack,
register, or ABI changes were made. The F3 Randomizer selector, Challenge
preview, live configuration reload, DirectInput forwarding and renderer
boundary are retained. The candidate INI keeps QuickRace=T1 and
MaxOpponents=7. Human retest must first confirm Practice and Checkpoint each
start normally with that configuration; static tests are not runtime proof.

## Runtime gate and limitations

Automated build and synthetic checks cannot prove game startup, input, graphics,
race, Results, live reload, shutdown or repeated launch. BOOT-B must first pass
the owner's disposable-folder test with the original executable launched
normally in separate copies with and without the existing graphical proxy.
Preserve both logs to determine whether renderer coexistence correlates with
the first diagnostic mismatch. The known
seven-AI T1/T2-player crash remains unqualified; the first candidate stays a
bounded test package, not a release. Vehicle SDK and addon resources are not
loaded or required.
