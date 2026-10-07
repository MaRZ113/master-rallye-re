# R-OBS3 — Adaptive Research Observatory

## Status

The existing compatible-family live-capture workflow is
**CONFIRMED_BY_RUNTIME** across multiple locally audited hashes. The R-OBS3
degraded-capability route and ordinary-entrypoint smoke for the supplied
R5V-H forced-ID26 AI build are **READY FOR HUMAN RUNTIME**. The existing GRID8
research candidate also remains statically compatible. The public Observatory
v0.1.0-beta remains frozen and pristine-only. No executable or game data was
modified.

## Resolution and rejection

The internal `mr_observe.py` previously used only `match_profile(SHA256, size)`.
The R-OBS2 audit accepted the AI build structurally, but the ordinary UI
rejected it before process discovery. This was a routing split, not a Broker
layout mismatch.

The internal resolver now checks committed exact profiles first, then performs
the known retail Broker family audit, then admits a degraded profile only when
the PE32 retail layout and passive Debug-sink core pass. If no safe read core is
proved, it rejects the executable. There is no filename, size-only, nearest
hash, or `--allow-any` path. SHA256 and size remain mandatory provenance and
cache keys; exact research patch builders retain their strict source hashes.

The supplied AI proof file and its adjacent build manifest report SHA256
`688653245b916ae7aae2a8e22fd47e76963f3afb1c23936b47b57bb40c76f0c5`. The
handoff text expected `dc821c096dea1db00c91ddf41e85cfac1f5369eaf56bd821ed0b904cbe246e13`;
that expected value does not match the supplied file. The file actually present
was audited directly. All ten retail-broker-v1 family anchors match, the
independent registry fingerprint is `merc-id26`, and the family profile
resolves to Broker read, Broker Editor, and native Dump enabled. The exact
profile remains unknown and is cached locally as `local-audited-688653245b91`.
The second resolution reused the cache after recomputing and re-auditing the
file.

The ordinary verifier reproduced the old unsupported-SHA refusal before the
change. After the change, the same file resolves through the ordinary runtime
profile path. The GRID8 candidate also passes the current family audit without
an exact-SHA source edit.

## Capability boundaries

Passive Broker read requires the known PE32 retail RVA layout plus the
`debug_logger`, `debug_sink_vtable`, and `debug_sink_global` anchors. Runtime
capture then checks the same file hash and size, x86 module base and extent,
live logger/vtable code fingerprints, sink object/vtable, helper HWND, buffer
pointer ordering and capacity, and repeated stable metadata/bytes.

Native Dump additionally requires the exact Broker local Dump route, singleton
accessor, manager ownership anchor and native walker. Before a Dump command,
the live process route, accessor, and walker bytes are checked against the
resolved profile. A failure disables the command without disabling passive
read/recovery when that core still audits.

The `WM_COMMAND 0x27` Broker Editor opener has no standalone fingerprint in the
current family map. It is enabled only for a full family match plus the local
Dump route and the existing main-window/menu signature. A degraded profile may
use an already-open, signature-checked editor when native Dump is independently
proven. Flow Builder remains disabled for locally audited family profiles.

The Attract/loading anchor is informational to passive Broker read. The
resource-loader and main-loop anchors remain full-family evidence, but neither
is a requirement of the minimal Broker read core. Registry recognition is
independent of Observatory compatibility and may remain `unknown` without
blocking generic Broker observation.

Stock native Dump walker is recognized as `native_stock`; post-Results Dump is
unsafe. At the initial R-OBS3 audit, only the exact R-AI1 NULL-safe walker fingerprint was recognized. The v0.2.2 extension below also recognizes the separately audited two-trampoline implementation.
`native_hardened-r-ai1-v1`; it reports post-Results Dump safe. Unknown walker
bytes still disable native Dump and remain
unknown for post-Results safety.

## Cache and package

The current local profile cache uses schema 3 and audit version
`retail-broker-v1.2`. Every resolution rereads the executable and recomputes
SHA, size, PE layout, anchors, capabilities, registry fingerprint, and audit
fingerprint. Older cache schemas do not grant trust; the current audit rewrites
a matching profile after revalidation.

`tools/build_observatory_research.py` creates the separate ignored
`Master Rallye Observatory Research` package at
`.research-output/general-re/observatory-research-r-obs3-final/`. Its archive
SHA256 is `d17f6be6067a61bb45dafbcac54b032ecc89f1c13b63b446c9aa0a3c62b26f94`
(52,732 bytes). It includes the runtime resolver and only the minimum research
profile/registry evidence, and contains no game executable. Its CMD launcher
was smoke-tested through the Python fallback because the installed `py`
launcher reported no registered interpreter. The public beta package was not
replaced or modified.

## Evidence limit

This phase establishes source-level resolver behavior, synthetic capability
isolation, deterministic package construction, and static compatibility for the
AI/GRID8 candidate files. The live process reader still requires human
validation against a running candidate; static admission is not a capture or
gameplay runtime pass.

## Observatory v0.2.2 hardened-walker recognition

The forced-ID26 hardened runtime package (`9255c9d7cb27336d0a5324bd193719c768f09f5bb7d37e30bab384031b0de0e7`, 3,121,214 bytes) initially failed full-family admission because its native Dump walker used two bounded NULL-safe trampolines rather than the already-known inline R-AI1 hardened window. Its other Broker anchors and retail PE layout matched.

The v0.2.2 audit recognizes this implementation structurally. It checks hashes for every unchanged segment of the 0x600-byte walker, verifies the two exact hook locations redirect to distinct executable `.text` stubs, checks the StringList and XmlData null tests precede their stock dereference/call sequences, and requires both branches to reach the audited stock null and continuation paths. This is not an executable-SHA allowlist. A one-byte change in an unchanged segment, a malformed jump, an incomplete stub, or an unexpected target remains incompatible.

On a match, the local profile is classified `hardened`, sets `hardened_dump=true` and `broker_dump_variant=native_hardened`, and enables the existing verified Broker Editor/native Dump path. The process is still re-read and its resolved native walker bytes are checked before the command is sent. Flow Builder remains disabled for locally audited builds. This is static executable verification; no live-process runtime result is claimed here.
