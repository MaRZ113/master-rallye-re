# Offline diagnostic and independent evidence

`tools/rigid_runtime.py` exposes five bounded read-only modes:

| Mode | Input | Output / proof boundary |
|---|---|---|
| inventory | canonical PackFS root | all36 source scenes,83 rigid records, properties and matrix hashes |
| shapes | canonical PackFS +read-only SDK | selected visual metadata and independent strict tag101 convex summaries |
| pc | original PC root +PackFS +SDK | named scan, standalone collision agreement and baked draw candidates |
| contract | included compact JSON | documented static ownership/physics/pose contract |
| evaluate | explicit SYNTHETIC or CAPTURED_EXPLICIT_INPUT JSON | view-qualified gate, owner states, isolated linear RK4, derivative and pose |

Generated output paths must be new and inside ignored data/rigid1. No game writer or generic collision/PSM decoder is introduced. Unknown/malformed model inputs fail closed; original unusual finite parameters are preserved in authored inspection.

Independent checks include: original XML/PSM bytes; original ELF instruction windows and vtable target words; strict existing SDK parsing of PC and PS2 tag101; numerical model-local collision matching; synthetic Hamilton-product and constant-acceleration oracles. A small test interpreter evaluates the actual original straight-line derivative and gravity words. It is not a PS2 emulator and does not certify contact timing or FPU edge cases.

Committed synthetic-input.json and synthetic-expected.json contain explicitly synthetic vectors/poses only. The CLI is run twice for byte-identical JSON. An isolated mass500 half-step from zero yields Y=-0.001362500130198896 and Py=-81.75000762939453 with no contacts. This is a controlled math case, not an original object's trajectory.

Original operation words are **EXACT_ELF_OPERATION** evidence; evaluator finite host IEEE32 output is **FLOAT32_RECONSTRUCTION**. A reciprocal diagonal inertia is **MATHEMATICALLY_EQUIVALENT**. Full contact response, runtime initial states, exact PS2 SQRT/division and scheduler frequency remain UNKNOWN.
