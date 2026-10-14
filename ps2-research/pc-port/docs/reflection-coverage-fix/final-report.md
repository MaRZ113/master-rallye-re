# Reflection coverage correction

Status: **PARTIAL_COVERAGE_FIX_PENDING_RUNTIME**.

Repository: `master-rallye-re-general`, branch `master`.
Starting HEAD: `485288f29eebd01d8b2e0d89b8abfd5f01aa56ef`.
Ending source commit: recorded in the handoff's `release-provenance.json`.
Frozen renderer tree: `e33386bcf682db6983380c499e4928726c758fe0`.
Immutable staging source: `0bddf7c7bc5e95831f98714ff6231da05ab073ea`.
Baseline source and both integration patches: unchanged.
No original assets, Course SDK, deployment or push changes.

## Findings and correction

The user's thirteen affected families were investigated through original source
geometry, material ownership, current D3D8 captures and screenshots. These are
separate evidence layers. The screenshots confirm the user's visual concern;
they do not identify a draw or prove a shader cause by themselves.

The registry grows from **174 to 212 exact PC geometry signatures**. All previous
174 records remain unchanged. The 38 additions consist of:

* 26 complete nondegenerate-triangle or strictly coplanar surface joins against
  unconditional, original PS2 `carshiny` material geometry;
* four source-position/material joins (Jump1/2, Bruno5, IceCream4), explicitly
  **not** promoted to emitted-triangle equivalence;
* eight single-root material correspondences whose nondegenerate PC faces differ
  slightly from PS2 positions, with a maximum corner displacement of .005
  model-local source units (Forester10/12/14, Navara3/4, Patrol1/2, Kamaz13).

The runtime signature remains exact for the original PC stream. The .005
threshold is only an offline material-correspondence test; runtime matching has
not acquired a positional epsilon. PC UVs, normals and geometry are unchanged.
Original UV differences are recorded in `modified-material-correspondence.json`.
All additions were checked for family uniqueness across 78 retail vehicle DX
files. Three alpha/conditional candidates remain excluded.

The previous registry omitted groups because it prefiltered secondary texture
names, expected one PS2 mesh per PC draw, or compared raw PC triangle counts to
nondegenerate PS2 faces. These omissions are distinct from runtime admission.

For the thirteen listed families, Mode4 now permits a registered source-material
identity with a verified current native material context, without requiring the
legacy four-wheel constellation. This addresses a structural limitation for UFO
and static-camera views. It does not waive the exact current geometry digest,
resource generations/revisions, live race certificate, opaque environment stage,
normal-bearing FVF, rigid world transform or native/effective state checks.
The native world matrix must match the effective tracked matrix byte-for-byte.
Other families retain the previous admission path. New signatures and this
alternative admission are Mode4-only; Stock remains the default.

No blend coefficients, environment images, capture timing, MSAA resolve path,
texture coordinates, state tracker, grass, water, HUD or physics code changed.
The original target is still drawn once and its HRESULT is preserved. Existing
native state transactions and Reset handling remain in use.

## Forester corresponds to WOOLDAND

The user's alias is supported independently: 1,814/1,845 PC Forester triangles
match PS2 WOOLDAND at .001, compared with 669/1,845 for PS2 FORESTER. The two
original model names remain distinct. This correction is recorded in new
evidence; historical reports have not been rewritten.

Three principal PC Forester body groups now have single PS2 WOOLDAND carshiny
material correspondences. Rear/lights groups coalesce shiny and untyped PS2
materials and are deliberately not treated as uniform carshiny. The original
`$shader(crashiny)` typo is not normalized. See `wooldand/findings.md`.

## Native evidence and limits

REA/Ghidra rechecked the canonical retail x86 executable, SHA-256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Function `0x576970..0x577087` contains the native indexed draw at `0x577078`,
returning to `0x57707e`. This is a shared compiled-model emitter, not a car-only
identity. Short original bytes and instruction references are preserved in
`rea-draw-evidence.json`; callsite identity alone never activates this feature.

Pre-fix UFO F10 candidates use FVF0x152 and the ordinary environment stage, but
fail the legacy body constellation test. A bounded early session event also
failed the live-race certificate before the later F10 frame. That cold failure
must not be presented as proof that the later frame had no active race.
`runtime-evidence.json` preserves original log hashes and these limitations.

**Unresolved:** several large LandCruiser, Xtrail, Bruno, ChevyBlazer and
SeatBuggy groups still lack complete uniform source-material correspondence.
FVF0x142/stride24 has no normal input or supported original environment stage
for this path. Mixed/conditional groups remain unresolved. The implementation
does not manufacture normals, extend texture-only admission, or override every
draw belonging to a car. A source registry entry can still be rejected by a
current native state or layout gate.

Consequently no whole-body success or PS2 visual parity is claimed. Post-fix
game testing is **NOT_PERFORMED**, pending the user's controlled A/B.
`vehicle-coverage.md` gives all thirteen outcomes. `whole-model-feasibility.md`
records the user's requested PS2 model fallback.

## Deliverables and validation

Baseline DLL SHA-256:
`011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138`.
PS2-enabled DLL SHA-256:
`abf005f8ff2f9535a2abb644e2066a224fc389734dc5f36fbdec5694ff37f48a`.

Both Win32 Release builds PASS using the canonical serial, incremental overlay.
Baseline CTest 24/24; PS2 CTest 30/30; port unittest115/115; pytest115 with470
subtests. Both proxy export checks and repeated interface generators PASS.
Source-audit tests5/5; WOOLDAND tests5/5. Additional material-report checks,
compileall, diff-check and isolated handoff checks are in `validation.md`.
These checks establish code/artifact integrity, not in-game visual acceptance.

Existing unrelated dirty documentation/configuration was preserved and excluded
from this commit. The handoff contains committed sources, tests, metadata,
exact patches and both DLLs; no original model arrays, textures or raw captures.

Next action: run the controlled Mode0/Mode4 comparison in `runtime-ab.md`, first
on UFO, IceCream, Tata and Forester. If current normal-less or coalesced body
regions remain uncovered, assess one WOOLDAND visual-body replacement pilot
against the explicit ownership gates, rather than loosening draw identity.
