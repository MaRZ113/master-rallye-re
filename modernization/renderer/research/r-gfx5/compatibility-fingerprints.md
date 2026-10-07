# R-GFX5-3 feature-local owner authorization

Whole-image SHA remains provenance, not a global permission switch. No new whole-SHA profile was added. Generic display/AF/MSAA remain generic. Freeze and orthographic UI retain their unique decoded scanned owners. Stock shadow stays exact-profile gated.

FOV/culling, frontend preview, vehicle semantics and packet margins now have conservative **fixed-layout local fingerprints**. The entire required owner bytes, instruction-length recipes and E8 callees are checked, including absolute globals and relative operands. These coupled features require ImageBase 0x00400000 and original owner RVAs; relocated/rebased owners are intentionally unsupported. This is useful for EXEs patched elsewhere, not arbitrary modified-EXE support. Full bytes have no wildcard normalization for these groups.

| Capability | Required owner VAs (RVA = VA - 00400000) |
|---|---|
| Camera foundation / frontend preview | 004E3DD0 camera-manager allocation/layout/global 006F94DC; 0053EED0 renderer holder; 004F2350 authored angle; 005614A0 camera view/projection; 0053F9E0 final cached SetTransform return0053FA75 |
| GameplayFOVCulling | Foundation + complete scheduler00653080 (including submit CALL006532DD and holder006F9CF0) + submit00509680 |
| VehicleSemantics | Foundation + complete shared-world owner00576970, including DrawIndexedPrimitive return0057707E |
| PreserveMargins | Complete packet consumer0056D110, including point layout, modes, native draw path |

Loaded-image validation also requires both camera-manager/renderer-holder globals to lie within readable+writable non-executable image sections. Missing/changed component disables the dependent feature only. validated_owner_rvas distinguishes component checks from scanned match counts. Installers still immediately validate their patch-site bytes; unsupported image/camera runtime shapes remain Stock.

FOV retains count/index/pointer/current-camera/rigid/source90 runtime checks before any widening. Vehicle capability only admits the D3D discovery route; four-wheel dynamic/structural proof, learned signature generation lifetime, race context and strict current opaque FVF0x152 env/TCI gate remain required. Wheels0x112, lamps0x102, alpha/glass and unproven static geometry stay Stock. The historical bit1 EXACT_BUILD alias now means VEHICLE_SEMANTICS_CAPABILITY; F10 names it explicitly. Unknown SHA alone never learns vehicles; frame headers record the validated capability for offline analysis.

Read-only file audit of hardened MRallye-hard.exe SHA391d5d864699b6e945eed43fd8e7bc28b28639b24b222428ab79231e7cc3a819 passes all seven FOV and six vehicle owners. That is static SUPPORTED, not modified-build runtime acceptance. See owner recipes and current compatibility audit. Pristine remains canonical.

## Historical R-GFX5-2 record (superseded where stated above)

# Feature-local compatibility - R-GFX5-2

The image SHA remains provenance and a known-profile shortcut. An unknown SHA no longer disables D3D-generic features. This is a compatibility change requested by the continuation; the former all-Stock unknown-build assertions have been replaced with generic-enabled / game-owner-fail-closed assertions.

| Class | Features | Authorization |
|---|---|---|
| A: generic | Display, MSAA, AF, presentation tracing | Intercepted D3D/Win32 contracts and actual native caps/results. No game SHA dependency. |
| B: fingerprinted | MenuFreezeFix, Centered4x3 UI projection | Unique `.text` anchor, complete decoded instruction recipe, control-flow shape and resolved callee-prefix validation. Current UI matrix also passes semantic checks. |
| C: exact profile | Gameplay FOV/culling, PreserveMargins packet hook, shadow suppression, vehicle semantics/reflections | Pristine disk hash and retained owner/layout checks. Coupled camera globals, packet layouts and vehicle ownership are not safely generalized here. |

`compatibility.hpp/cpp` reads the loaded main PE32/I386 image with guarded copies, bounds its executable `.text` to 64 MiB, and never writes while discovering capabilities. Recipes retain absolute globals and require the original base `0x00400000`; rebased owners are unsupported locally. Generic forwarding/display/AF/MSAA remains available.

`tools/generate_fingerprints.py` accepts only the canonical pristine SHA. Capstone decodes every owner instruction; Ghidra 12.1.4 read-only exports identify the semantics. [Recipes](fingerprint-recipes.json) contain instruction offsets/lengths, bytes and 12-byte callee prefixes. The runtime matcher is a restricted instruction-recipe validator: it accepts the recovered encodings, not arbitrary x86 instructions or guessed instruction lengths. It is not a general detour engine.

Only decoded `E8 rel32` operands are normalized. Each resolved CALL must remain in executable `.text` and match its expected callee prefix. Absolute global operands, constants, ModRM/operand encodings and short branches remain exact. The sole branch variant is the documented MenuFreezeFix `75 11` / `75 00`. A normalized block hash is not used; diagnostics report it as null. No arbitrary wildcard mask or broad first-match patching.

Known profile: validate the known local owner first. A changed/missing known owner is unsupported even with a trusted disk hash. Scan for uniqueness as an additional check. Unknown profile: scan the section for exactly one anchor, then validate the complete owner and decoded call targets. Zero matches, multiple anchors, byte/instruction mismatch or changed callee fails only the affected feature. Ambiguity never selects the nearest RVA.

| Owner | Pristine VA / RVA | Validated structure |
|---|---|---|
| MenuFreezeFix | context `0x005B015A / 0x001B015A`; target `0x005B015C / 0x001B015C` | TEST EDI,EDI; JNE short; original arguments; CALL render scheduler; increment; TEST BL,BL. 23 bytes plus scheduler prefix. |
| WidescreenUI | block `0x00561DF0 / 0x00161DF0`; return `0x00561ED3 / 0x00161ED3` | 227-byte block: original 640/480 ortho arguments, cached 16-dword matrix comparison/copy, PROJECTION argument 3, indirect CALL `[EAX+0x94]`. All four direct CALL targets checked. |

Startup `compatibility_capabilities` records image SHA, known-build boolean, each feature's compatibility method/status/reason, fast-path candidate, scan count, candidate RVA, byte and instruction validation. MenuFreezeFix revalidates loaded ownership immediately before an enabled install and reports `ALREADY_PATCHED` without a write/ownership. FOV and packet installers retain their separate immediate checks.

[Native file audit](compatibility-audit.json): pristine owners pass through the unknown-profile discovery path too. The supplied historical `MRallye_patched.exe` is **not** treated as compatible: freeze resolves to a different scheduler prefix; UI anchor is absent. Its generic capabilities remain independent. Synthetic fixtures prove unknown images with unrelated mutations, relocated owner/callee positions, missing/ambiguous/changed owners, malformed recipes, out-of-section targets and already-patched branches. These are static/synthetic results, not modified-game runtime confirmation.
