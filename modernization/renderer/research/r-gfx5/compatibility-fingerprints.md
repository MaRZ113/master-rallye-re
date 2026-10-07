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
