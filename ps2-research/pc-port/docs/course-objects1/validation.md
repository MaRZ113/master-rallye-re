# Validation and evidence boundary

| Check | Result |
|---|---|
| Independent baseline Win32 Release /CTest | PASS;24/24 |
| Independent PS2 Win32 Release /CTest | PASS;28/28 |
| Focused Python | PASS;41/41;0 failures/skips |
| New synthetic artifact cases | PASS;10 Python cases |
| New native transaction cases | PASS; all capture/apply/restore slot failure positions |
| Course/frame/owner/target/recording rejection | PASS; pure native admission cases |
| Original local artifact upload/Reset case | PASS; explicitly enabled external input |
| Original reflection image Reset case | PASS; existing regression retained |
| Exact patch application | PASS; separate fresh check staging |
| Generator repeatability | PASS; twice per variant, locked output hashes |
| Proxy exports | PASS; baseline and final PS2 outputs |
| Compileall /diff-check /frozen tree integrity | PASS |
| Old F10 render boundary | Confirmed for supplied frame94470; course identity not embedded |
| New layer actual game rendering /Reset | NOT_PERFORMED |
| Handoff CRC/checksum/repeated serialization | PASS |
| Extracted handoff tests | 41/41 PASS; external verified staging, no original corpus |

The fixed transaction tests attempt mutation even on failed native setters.
They cover every captured slot's failure, every apply slot's rollback, every
restoration slot's failed retry, simultaneous apply/rollback failure, null bindings,
UP stream0 side effects, held getter references, equal-state optimization and
one additional submission with preserved original native-call result. No target,
viewport, index-buffer or state-block mutation occurs.

Admission rejects unsupported builds, wrong courses/cameras, missing typed UI
consumer, stale frame/device/reset/race/owner, missing gameplay camera sites,
missing subsequent world draw, changed target/depth/viewport, unsupported native
dependencies and active state-block recording. Repeated boundary consumption
cannot draw the layer twice in the same frame/race/reset scope.

Private-image integration uses MRR_COURSE_OBJECT_TEST_ASSET and was actually run
with the exact ignored canonical artifact. Without that environment the subcase
prints NOT_PERFORMED explicitly; synthetic tests still run. Source image bytes
and full geometry are not test fixtures in Git or the handoff.

Independent review identified camera-attempt, state-recording, surface-reference,
depth-clear and scene-transition gaps. Each was closed in the final source; target
switches also invalidate depth proof. The final PS2 safety build repeated all28
CTest and41 Python cases. Initial compile failure was a scoped UI identity variable;
it was corrected in staging and is not counted as a final PASS without rebuild.

Source preparation twice yielded identical70,384-byte artifacts after canonical
hash checks. Existing PackFS/PSM/GXI parsing was reused; no second parser was
introduced. Old PILOT1.4 and reflection archive hashes are preserved in the build
report. Broad unrelated suites, PCSX2 work, physics and whole-course migration
were not started. Static/native/package passes do not establish live visibility
or PS2 material equivalence.
