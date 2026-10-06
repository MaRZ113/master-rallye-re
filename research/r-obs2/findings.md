# R-OBS2 — Compatible Build Families

## Status

**AUDITOR IMPLEMENTED; mercv2 STATIC FAMILY/REGISTRY AUDIT PASS; READY FOR HUMAN OBSERVATORY CAPTURE.** Exact known builds remain accepted by their committed profiles. Unknown retail-family hashes are admitted only after the PE/layout and every required exact anchor fingerprint pass; the resulting local profile is SHA-bound and does not broaden capabilities. The user-provided `MRallye.exe` matches the stated mercv2 SHA and has a locally audited `retail-broker-v1` profile with registry `merc-id26`.

## Model

Build identity has four independent dimensions:

1. exact file SHA-256 and size;
2. audited Broker/Debug compatibility family;
3. vehicle registry profile, which may remain `unknown`;
4. capability flags derived from the family and specific fingerprints.

The first family is `retail-broker-v1`. The current audited family retains x86 PE32, ImageBase `0x00400000`, the same image size/entry point and section table, and the retail section RVAs/raw extents/flags. `.text` VirtualSize may vary inside its raw section without overlapping `.rdata`. All listed family anchors use exact bounded SHA-256 fingerprints. No fuzzy matching, filename trust, or size-only trust is used.

The exact committed profiles remain `retail-pristine` and `retail-merc-id26`. A different SHA that passes the family audit becomes `locally_audited`; the exact SHA, size, family, registry result, audit fingerprint, and capability set are cached under ignored `.research-output/observatory/build-profiles/`. Every reuse recomputes the file SHA and structural audit. Invalid cache entries are not trusted.

Unknown registry identity does not block generic Broker structure checks. Registry-aware ID/class/type checks fail with `UNKNOWN_REGISTRY_PROFILE` until independent mapping fingerprints identify a committed registry profile. This prevents Broker ABI support from being mistaken for vehicle-ID semantics.

## Verified evidence

- The tracked `inputs/MRallye_merc.exe` has SHA-256 `1fb0a1f1ba02cd05fa25f0c94558cf1b281fd12affcdc37bb3c1ca538e6c65af` and passes the family/registry audit as `retail-broker-v1` / `merc-id26`.
- A synthetic cosmetic change outside all anchors gets a local exact profile without adding its SHA to source. A subsequent launch reuses the cache after recomputing the same audit.
- Changed critical anchors, wrong machine type, invalid section layout, and incompatible cache identity fail closed.
- Stock native Dump walker fingerprints set Results Dump safety to false. `flow_builder` and `hardened_dump` remain false. The legacy loading-to-Attract failure-path fingerprint is reported separately.
- Public Observatory v0.1.0-beta and the pinned external Observatory files are unchanged. Research compatibility is confined to the internal adapter and remains read-only.

The test target is the user-provided `MRallye.exe`: SHA-256 `1fbb3489208de9bc0af3802902a8611ea9a149c245031d1563960bd91b430c14`, size 3,121,214, family `retail-broker-v1`, registry `merc-id26`. All ten configured family anchors and layout gates passed. The local SHA-bound profile is under ignored `.research-output/observatory/build-profiles/`; the source candidate was read only from the sibling vehicle worktree and is not committed.

## Safety boundary

The tool reads the EXE file and uses the existing pinned Observatory implementation. Runtime interaction remains process query/read plus normal native `WM_COMMAND`. No `WriteProcessMemory`, injection, debugger, process suspension, executable patching, or `--allow-any` path was added. Passing a family audit permits only the listed observation capabilities; it does not enable Flow Builder or research patch workflows.

See [family definition](compatibility-family.md), [profile schema](build-profile-schema.md), [audit behavior](structural-audit.md), [registry profiles](registry-profiles.md), [mercv2 status](mercv2.md), and [human handoff](runtime-handoff.md).
