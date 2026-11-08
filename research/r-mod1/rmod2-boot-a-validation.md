# R-MOD2 BOOT-A validation record

## Candidate

Build output: `.research-output/r-mod2/boot-a-2026-10-10-r6/` (final reproducible build).
Candidate: `r-mod2-boot-a-dinput8-forwarding-test`.
The release ZIP contains only `dinput8.dll` and `README.txt`; no MRallye.exe,
runtime core, assets, raw capture, or development harness is included.

The proxy is PE32/I386 and has six exports matching the tested system
`C:\Windows\SysWOW64\dinput8.dll` exactly by name and ordinal:

| Ordinal | Export |
|---:|---|
| 1 | `DirectInput8Create` |
| 2 | `DllCanUnloadNow` |
| 3 | `DllGetClassObject` |
| 4 | `DllRegisterServer` |
| 5 | `DllUnregisterServer` |
| 6 | `GetdfDIJoystick` |

The proxy has no static import of its own `dinput8.dll`. It resolves the
architecture-matched system library through the absolute system directory,
then validates the loaded module path to reject recursive self-resolution.

## Automated and Windows validation

- Focused Python suite: `python -m unittest discover -s tests/synthetic -p test_r_mod2_dinput8.py -v` — **4 passed**.
- Full synthetic suite: `python -m unittest discover -s tests/synthetic -v` — **636 passed, 1 skipped, 0 failed**. The single skip is the opt-in real suspended-process preflight test (`RMOD1_RUN_WINDOWS_PREFLIGHT=1`), which is unrelated to the forwarding-only DLL.
- `python -m compileall src tools tests` — **passed**.
- MSVC x86 `/W4 /WX` proxy and harness compile — **passed**. The linker reports informational LNK4104 warnings for standard COM exports that are intentionally exported by name and ordinal; the final PE export auditor verifies the six ordinals.
- Windows x86 forwarding harness — `DINPUT8_FORWARD_PASS named=6 ordinal=6 directinput8create=system-match joystick-format=system-match`.
- Proxy PE export parser — all 6 required names and ordinals matched the current SysWOW64 system DLL.
- Proxy import audit — no self-import of `dinput8.dll`.
- `git diff --check` — **passed**; Git emits only LF-to-CRLF working-copy advisories for pre-existing dirty files.
- Retail input identity — **SHA256 BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4**, verified from `D:\Game\Master Rallye\corpora\retail\MRallye.exe` (3,121,214 bytes).
- Release package and source review ZIP were rebuilt from this worktree; builder refuses to overwrite an existing output directory.

The test harness loaded the proxy in a non-game process and compared safe
DirectInput/COM calls against the system DLL. It did not launch Master Rallye.
No Windows game startup, real keyboard/gamepad, renderer, race, Results,
shutdown, second-launch or `d3d8.dll` coexistence test has yet passed.

## Runtime limit

BOOT-A forwards only; it activates no R-MOD gameplay behavior. BOOT-B must
reuse the generated F3 native operation plan, omit `oep-bootstrap`, prove the
first-DirectInput initialization boundary in a real game process, and provide
safe preflight/rollback before it is a launcher-free Randomizer candidate.
The known seven-AI T1/T2 same-class crash remains unqualified; a package that
continues to expose it must remain BETA or limit advertised configurations.
