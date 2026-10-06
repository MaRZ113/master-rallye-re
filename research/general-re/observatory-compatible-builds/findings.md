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
unsafe. The exact R-AI1 NULL-safe walker fingerprint is recognized as
`native_hardened-r-ai1-v1`; only that exact bounded walker window reports
post-Results Dump safe. Unknown walker bytes disable native Dump and remain
unknown for post-Results safety.

## Cache and package

The local profile cache uses schema 2 and audit version `retail-broker-v1.1`.
Every resolution rereads the executable and recomputes SHA, size, PE layout,
anchors, capabilities, registry fingerprint, and audit fingerprint. A schema-1
cache does not grant trust; the current audit rewrites a matching profile after
revalidation.

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
