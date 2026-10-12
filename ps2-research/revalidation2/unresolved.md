# Unresolved questions and proof boundaries

## Original PS2 execution

* Which specific France1 frame route and mesh instance reaches the treeblend queue drain?
* What are the live TEX0 base/format, CLUT, TEXA, ZTE, DATE/DATM, FRAME and other inherited GS values for that bush?
* What source-alpha value reaches the GS per pixel after texture conversion, texture/diffuse modulation and VU output?
* Is the embedded VU program resident and selected in the observed France1 runtime? Its upload producer and CPU packet contract are static-confirmed; live micro-RAM residency is unknown.
* What later PS2 draw groups, if any, overlap the bush and how do they interact with `ZMSK=1`?
* Does actual PS2 gameplay show this exact bush with the inferred static state contract? No controlled PCSX2 capture was made.

## PC pilot

* The current F10 format identifies native draw arguments, source mirror hash and resource generations, but lacks per-pixel output/depth snapshots.
* The target is the same API draw and buffer generations across the four supplied frames, but this does not prove that every prior 5,364 identity event in older logs is a distinct intended instance or establish a universal classifier outside these verified sessions.
* The logs/screenshot pairing is ordinal with timestamp support; mode is not embedded in JPEG metadata.
* The supplied frames are comparable snapshots with the same bookmark slot selected; exact camera matrix equality is unknown.
* No later draw has been correlated with the pixels that cover the bush. Draw order alone cannot establish overdraw.
* The runtime texture's actual D3D format and addressed texels are unknown; the white-card artifact is not yet attributed to alpha contents, stage state, diffuse alpha, or conversion.

## ELF and analysis tooling

The original ELF header labels `e_machine=EM_MIPS`; processor identity comes from the explicit Ghidra EER language and Rabbitizer `InstrCategory.R5900`, not that generic ELF field. Ghidra pseudocode is a navigation aid. Its low-64-bit temporary surrogates for some EE `LQ/SQ` instructions are not semantic proof. All checked instruction bytes are compared to the canonical file.

The queue proves ascending bucket order inside one `0x0031cd98` drain. It does not prove a whole-frame opaque-before-transparent order. The 12-byte queue-key stride uses an EE three-register `MULT` at `0x0031d70c`; Rabbitizer R5900 decoding confirms its three operands.

## Status

Static PS2 material-to-GS contract: independently byte-revalidated. PC four-mode execution and native restoration: confirmed by supplied F10 sessions. Pixel-level failure cause: unresolved. PS2 runtime visual parity: not tested. Overall phase remains PARTIAL.
