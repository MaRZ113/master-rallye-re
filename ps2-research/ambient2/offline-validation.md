# Offline reconstruction and independent evidence

`tools/bird_runtime.py` reuses `spline_runtime.Corpus`/typed XML helpers, `tngtool` PackFS, `psbtool` PSB/GXI and `foliage_runtime` GS field decoding. No second archive/PSB parser, general renderer or PC feature is added. Modes are `inventory`, `resources`, `trace`, `contract`; output must be a **new** path below ignored`data/ambient2/`.

Inventory retains exact property types/spelling/order/duplicates, absent-versus-empty lists and order hashes. It does not write source point arrays to committed JSON. Resource mode reports original PSB/GXI metadata and consumer provenance, not texture images. Contract mode emits the bounded static GS/CPU/VU contract. Trace mode evaluates one explicitly synthetic FlyBird plus its separately ordered image switcher; it does not simulate the unknown course scheduler, global RNG call interleaving, owner registry or a complete live population.

The committed `synthetic-flight-trace.json` uses origin(0,10,0), observer(100,10,0), explicit RNG state12345 and15 owner invocations. These inputs are synthetic, even though12345 also happens to be the original process constructor seed. Its timing/source-point labels explicitly state synthetic origin and unknown wall-clock cadence. Identical inputs reproduce identical output. Original course coordinates, point maps and larger traces remain ignored.

## Independent numerical checks

- The RNG's first1000 positive states are checked against modular `(48271*s)%2147483647`, independently of the Schrage implementation; low24/2^24 output is separately checked.
- `instruction-probes.json` contains original rise and speed/travel instruction windows. A small fail-closed interpreter executes the original LUI/MTC1/LWC1/DIV.S/ADD.S/SWC1 sequence on synthetic memory. It agrees with the evaluator while preserving update order.
- Canonical integration verifies the original byte windows and re-extracts all36 source resources against frozen counts/hashes/references. Marker-list stride/position fields also reuse AMBIENT1's independently recovered loader contract.
- Original banks are re-read by established PSB/GXI parsers and compared with frozen key/triangle/texture metadata.
- Uploaded VU program hashes independently match prior frozen chunk hashes; tests explicitly distinguish MPG command address from instruction payload+4.
- Synthetic tests cover full/local nearest windows, source order/ties, XZ-only distance, end clamping, strict annulus, conditional RNG call count, current direction×total travel, animation counter boundary, camera-basis fallback and known-versus-inherited GS fields.

Arithmetic is FLOAT32_RECONSTRUCTION; integer recurrence/bit-field masks are exact integer operations. Host sqrt/div and MIPS-surrogate decompilation are not PS2 FPU/GS pixel simulation. A green test is not a runtime bird/frame PASS.

## Format/query limits

Canonical ELF addresses map to file offset VA-0xff000 in the established load segment. Newest installed local Ghidra12.1.4 and installed ghidra-bridge exporter query the existing project read-only. Temporary LQ/SQ low64, EE SQRT operand and explicit audited EE MULT low32 surrogates are rolled back. No binary/project patch is saved. The `--ee-scalar` HI/LO guard remains; explicit MULT sites are validated as aligned nonzero-rd MULT instructions. Their HI/LO side effects are not modeled, so only audited sites whose side effects are unused support conclusions.

RNG's MFLO/MFHI occur before the two audited MULTs; no later HI/LO consumer relies on them. The PSB key-lookup DIVU/MFHI is preserved while selected vertex-stride MULTs are normalized. Function starts are grounded by original calls/vtables; rejected interior guesses330168/3302c8/1af770 are excluded from the function inventory. An unsupported later packet-builder instruction does not license inventing its tail.

## Visual diagnostics

Original FRANCE1/SPAINW/TURKEY3 X/Z point maps are ignored SVGs under`data/ambient2/`. They show disconnected origins with source bounds; no invented routes, screenshot-derived positions or live visibility. A separate synthetic60-invocation trajectory SVG is generated from the proved evaluator with the same explicit origin/observer/state and clearly labeled synthetic. Neither is a gameplay capture.

Reproduction commands, external roots and actual/exemplar status are in [HANDOFF.md](HANDOFF.md) and `command-log.md`. Optional runtime validation is described in [runtime-capture-plan.md](runtime-capture-plan.md).
