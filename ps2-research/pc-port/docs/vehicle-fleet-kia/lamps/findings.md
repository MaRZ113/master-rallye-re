# Kia rear OFF lamp: exact missing conditional reflection

Original PS2 `KIASPORTAGE/CAR.PSM` has two distinct kbl/perspex sources.
`root.13` is an unconditional30-face carshiny/mode3 mesh already present in
the private CAR and marked mixedReflection=true. It is not the missing12-face
conditional patch. Its PC record21 also contains other original geometry;
this audit does not invent a one-to-one30-face native record alias.

The missing patch is `root.25.0.0`, original node190551, **12faces**, explicit
`$shader(carshiny)`, primary kbl and authored secondary perspex. Original
carshiny processing selects mode3 and substitutes its secondary render target.
Native PC compiled source30 (`record_path28`,20vertices) is independently
matched triangle-by-triangle within0.001 original position and exactUV.

| source | position geometry SHA256 | position+UV corner SHA256 |
|---|---|---|
| OFF30 |36c7ae35f499923af99bc317cb0402b183d9d24e162a4d2918c9981322d03f54|559102637af617f9ccbe2c9c6025d5c07189bf580d046a436c7b30317abd2edb|
| ON31 |36c7ae35f499923af99bc317cb0402b183d9d24e162a4d2918c9981322d03f54|3bfdba6278a48d057ca7508e9db3b4dc2ed3155b8075d173ee4f61376d1e0687|

ON is a separate selected `root.25.1.0`,12faces, original breaklightson/lightshine.
The explicit primary override produces final mode1; the unknown literal
carbrakelights is not an alias for carshiny. Glow is separate
`root.25.1.1`,32faces, final mode14 through breaklightsonglow. Preserve its
established RGB-fade ONE/ONE transaction. Neither should be admitted by the
OFF reflection hash. **Geometry alone cannot separate OFF from ON.**

## Current runtime observation

PID10052 F10frame3336 contains the20v/12f OFF-shape native draw at sequence1018
`(4,4560,20,14952,12)`, FVF0x152/36, shared-world caller0x17707E,
VEHICLE_BODY, nativeHRESULT0, forwarded=true. The logical stock renderer labels
it reflection_candidate=true / stock_mode; these labels do not describe the
independent Mode4 extension. Frames3911 and3913 instead contain16v/12f
ON-shape0x102/20 records, nativeHRESULT0. Historical draw sequences and resource
IDs are observations, never persistent identities. No raw upload is present
in these F10s, so current source SHA must still be checked by integration.

The implementation gap is explicit: fleetCAR conversion excludes conditional
roots; existing standalone reflection registry has no Kia12f/20v OFF identity.
The private unconditional root13 is already correctly mixed-reflective. Fixing
its material cannot cover the independently submitted conditional OFF patch.

## Smallest justified integration

Reuse the existing standalone X-Trail/Terrano OFF Mode4 mechanism for this exact
Kia source: add12f/20v layout admission, require the exact geometry SHA **and**
the OFF position+UV SHA, current buffer generation/revision, current owner,
native WORLD and state dependencies. Retain one native draw and exact native
state restoration. Do not place a geometry-only lamp entry into a blanket
registry. Explicitly reject ON UV and glow geometry. No new model or texture
asset is required; this does not replace native braking selection.

Unsupported damaged OFF geometry remains Stock until independently mapped.
Do not broaden its hash, reflect the complete rear lamp assembly, add glow to
OFF geometry, or modify the successful unconditional CAR material.

Four focused evidence tests pass. Ignored local fixture
`.assets/vehicles/kia-off-on-glow-native.bin` contains original OFF152/36,
ON102/20 and glow102/20 snapshots, SHA
`96dd25e7ed86bb88242d839c2b44d4145a49304b839eada641d6a938b4bf9720`.
It supports native positiveOFF/negativeON/glow/corruption tests; these are
original-source fixtures, not captured live upload bytes.

Runtime acceptance: same rear camera, OFF -> held brake -> OFF, all three F10;
OFF patch reflects surroundings, ON core and additiveglow remain independent,
release restores OFF reflection; no whole-lamp emission or glow reflection.
Check windowReset and MSAA4x. The already-confirmed full Kia CAR/glow and body
reflections must remain unchanged. This audit edits no renderer or build files.
