# Bounded original WORLD and queue contract

Queue erratum: the original recommendation below to find the entire body in the current manager+44/+48 pointer vector was disproved by the original two-pass consumer. Use `queue-two-pass-correction.md` and its exact backing-vector union contract. The WORLD proof and record+8 material-subindex interpretation remain valid.

Original PC executable SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. REA Ghidra 12.1.4, read-only original x86 analysis; retained evidence `ev_edc1915f4652cf2d7fe82bf400e676a477806e04cb8a85dbd8efca019fa1133b`. Compact full-function assembly/pseudocode is in `world-setter-evidence.json`. Pseudocode is an interpretation; the instruction windows below establish the narrow runtime checks.

The previously retained `vehicle-damage-fix1/damage-owner/atomic-leaf-descriptors.json` instruction window 005769CF–005769EC reads the current instance from the emitter stack, packet from instance+B0, then pushes packet+6C, packet+68, packet+5C and instance+44 before calling 00561A40. No mesh-specific transform is an argument.

00561A40 accepts that 64-byte instance matrix. Its packet-type parameter is tested at 00561A7D/00561A87 and 00561B03/00561B07. Packet type 0/2 enters the native view setup; packet+6C values 1/2 then enter billboard matrix mutation, and packet type 2 also replaces matrix translation. For the deliberately narrow gate `packet+5C == 0 && packet+6C == 0`, those matrix mutations are bypassed. The runtime need not reproduce any matrix math: read instance+44, require it finite and byte-equal to the current native WORLD, and recheck it with both packet fields immediately before suppression.

The end of the function compares/copies all 16 float words to its transform cache, then 00561DC9–00561DDA pushes the source matrix pointer and transform type 0x100, calling the D3D8 device virtual slot+94 (SetTransform). Thus admitted same-instance source leaves use this identical unchanged WORLD matrix. Reject leaf+44 optional preparation callbacks, as already required by `race_descriptors`; no unknown callback may invalidate this argument.

The existing byte-backed 00562560 queue producer constructs a 24-byte record `[instance, mesh, material_subindex, ...]`. `atomic-descriptors.md` already records +8 as subindex. `frontend_queue_owner` proves the active pointer-vector at manager+44/+48 and the saved current index; use the same bounded pointer-vector contract for a complete preflight scan. For every selected source mesh require exactly one record, with the current instance and subindex 0. Reject duplicate source submissions and multi-material records before drawing any private body. This proves submission membership/multiplicity, not a blanket exclusion of later camera passes.

For separate render passes, include current render-target identity, VIEW, PROJECTION and viewport with WORLD/frame/owner in the submission cohort key. A queue may be reused for another camera. Do not suppress a second pass using only `drawn_frame`. A precommit gate failure can select whole-cohort Stock; a postcommit failure cannot truthfully be described as an atomic Stock fallback, because GPU submissions cannot be undone.

These are static engine contracts with live validation requirements. They do not constitute new runtime fleet acceptance.
