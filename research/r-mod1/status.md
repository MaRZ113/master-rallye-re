# R-MOD1-F checkpoint status

**Branch:** `research/r-mod1`  
**Source HEAD at closeout:** `ea3012a1481cf1d2f8ed3401eedc995c96dbcfb9`  
**Supported retail:** `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`  
**On-disk retail EXE modified:** No

## Separate deliverables

| Result | Candidate | Scope | Operation count | Static status | Runtime status |
|---|---|---|---:|---|---|
| R-MOD1-F1 | `first-integrated-candidate-v14-f1-r3` | Config V2 and live Quick Race policy reload at a new roster boundary | 7 | `STATICALLY_VERIFIED; WINDOWS_PREFLIGHT_PASS` | `PENDING_HUMAN_RUNTIME` |
| R-MOD1-F2 | `first-integrated-candidate-v15-f2` | F1 plus new Rallye Cup, Invitation and Master Rallye generation owners | 13 | `STATICALLY_VERIFIED; WINDOWS_PREFLIGHT_PASS` | `PENDING_HUMAN_RUNTIME` |
| R-MOD1-F3 | `first-integrated-candidate-v16-f3` | F2 plus Challenge preview/race identity cache | 17 | `STATICALLY_VERIFIED; WINDOWS_PREFLIGHT_PASS` | `PENDING_HUMAN_RUNTIME` |

F1, F2 and F3 remain separate test candidates. F2 cumulatively contains F1;
F3 cumulatively contains F2. This packaging relationship does not transfer a
human runtime result from one candidate to another. No new mode or checkpoint
has runtime PASS from the static work in this closeout.

## Exact identities

| Candidate | Launcher SHA256 | Runtime DLL SHA256 | Native plan SHA256 | Template plan SHA256 |
|---|---|---|---|---|
| F1 | `51dfacee84f03344c4ff1f302e4a3bdd10e9af5d9c0a9b5e4b1c1ab39def5b33` | `cf743e356e3198cadd68ce750ff9f8c2cce5cb7caa965a4ee64d40c75f442da3` | `1d609a0f989ebb350a42a0c264c04756ad358d10f81d97496d2f80f43a117989` | `06597e1ea451df7427482fde97fbc707b5b7f48e12ad4ffc87acb5f421dac049` |
| F2 | `5da905fe5fd03b88fe819625356063e021359d0feea6f3a8c0ca7f493d5d96a6` | `cf743e356e3198cadd68ce750ff9f8c2cce5cb7caa965a4ee64d40c75f442da3` | `2b9c0aa9eee34b9436a342879ed104978b12faec8114382905954599863e84f6` | `c972078639f9b76c7e3eb9aa4d6729aa85709248fed232df0389b2c73d3e0d98` |
| F3 | `3849d57dcf57532b8ac9ca74c214f8643fec2bbe24d31ae9e77531dc4eab978a` | `cf743e356e3198cadd68ce750ff9f8c2cce5cb7caa965a4ee64d40c75f442da3` | `8d03c12e1f50779da43b185865f95acb0ddd2c6a67961fe3e402297ad1a3ddf4` | `3c760a475b854fd1435584f04450eada4dd90647ed7bbb7144fbf101e375d89d` |

All three use INI SHA256 `b47affdffa4748f337c405169d46b3b3763e1946931c0fdbd87bb5dc5b6eaacd`.
Each candidate contains 17 manifest-listed package files. Rebuild directories
were compared against their corresponding candidates: all 17/17 file
hash/size rows and template plan identities matched for F1, F2 and F3.

## Evidence boundary

The unchanged seven-operation v13 plan remains the parent operation set. F2
adds mode-specific class-selector hooks only at new roster generation. F3
adds Challenge preview preparation/reset and race consumption. Static plan,
negative-path, package and preflight checks passed. The known v11 four-AI
runtime confirmation and historical R-AI patched-build results remain limited
to their original candidates. Do not call F1/F2/F3 gameplay-qualified until
the owner tests them separately.

See [runtime-handoff.md](runtime-handoff.md) for the checkpoint tests and
`validation-f1-f3.md` for commands, counts and verification output.

## R-MOD2 BOOT-A

The launcher-free x86 DirectInput forwarding proxy is implemented as a
separate BOOT-A test artifact. It forwards six audited name/ordinal exports
through the absolute System32/SysWOW64 path and passes the local Windows
forwarding harness. It installs no gameplay hooks. Human game startup, input,
and `d3d8.dll` coexistence remain pending; do not label the DLL path supported
until those tests pass. See [rmod2-boot-a.md](rmod2-boot-a.md).

The first BOOT-B human run failed closed before runtime loading. Its log
identified the live mapped `.text` comparison as the blocker. The verifier had
compared `SizeOfRawData` including alignment padding after startup. The updated
candidate validates executable virtual extents, emits first-difference
diagnostics, rejects differences at selected hook ranges, and retains exact
preimage checks for every selected operation. The F3 runtime core and operation
plan remain unchanged; the OEP operation remains omitted in-process. Static
build/tests and Windows synthetic image-difference harness pass. The corrected
candidate is READY FOR HUMAN RUNTIME; BOOT-B startup, both renderer
configurations, race, live reload, Results and shutdown are still pending. See
[rmod2-boot-b.md](rmod2-boot-b.md) and its validation record.

The next BOOT-B test reached `HOST_VERIFIED`, `RUNTIME_LOADED`,
`CONFIG_ACCEPTED`, and `IMAGE_DIFFERENCES_NONCONFLICTING`, then failed because
the installer treated generated allocation-relative `kConfigOffset` and
`kDllPathOffset` as absolute addresses. The correction removes the redundant
in-process configuration staging: `MRConfigureBlobV1` already receives the
INI, and the omitted OEP bootstrap is the only generated reader of those
reserved offsets. The corrected candidate passes exact-retail host-qualified
startup-preflight, selected-operation preimage checks, x86 build, and synthetic
validation. Human retest is pending; no BOOT-B runtime pass is claimed.

The next Start hotfix makes non-mode-2 contexts pass through the original
native Start path while retaining the mode-2 Quick Race count and capability
checks. The candidate INI uses QuickRace=T1 and MaxOpponents=7. Practice and
Checkpoint runtime confirmation is required before release packaging resumes;
the DLL package is not human-qualified.
