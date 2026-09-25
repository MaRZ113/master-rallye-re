# Retail PE patch design

## Verified input and mapped region

Exact retail source SHA-256: bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4. PE32 x86 image base 0x400000, section/file alignment 0x1000, four sections. The executable .text section has RVA 0x1000, raw offset 0x1000, raw size 0x28E000, original VirtualSize 0x28D294, characteristics 0x60000020 (read/execute/code). The next .rdata begins at RVA 0x28F000. No extra section or file growth is used.

The original mapped .text content ends at VA 0x68E294; the source's raw alignment tail from 0x68E294 onward is zero. Stub VA 0x68E2A0 (file offset 0x28E2A0) to 0x68E2F5 fits in that tail. Changing .text VirtualSize to 0x28D300 declares the entire stub mapped while staying below the next section. This is section-owned padding beyond the original VirtualSize, not assumed padding between live functions. The patcher requires the exact source hash, PE headers and zero original bytes before use.

## Control flow

Retail registry constructor 0x458CD0 default-constructs 26 records, calls 0x458E70 to initialize IDs 0–24, then has mov ecx,esi; call 0x4598D0 at 0x458D3D–0x458D43. The five-byte call at 0x458D3F is replaced with a call to the stub. The stub receives ECX=registry, preserves ESI, constructs an owned temporary from existing literal VA 0x6B3CB4, pushes Astero float bits and semantic integers, calls full initializer 0x45A0B0 on registry+0x518 (record25), calls original 0x4598D0 with the same ECX, restores ESI and returns to 0x458D44. 0x45A0B0 consumes twelve stack dwords with ret 0x30; 0x4D11D0 consumes its literal pointer with ret 4. The stub disassembles to the expected calls and balanced stack on the normal path.

The relative calls target existing functions and are computed from VA in the patcher. The original image already uses fixed absolute addresses and its relocation directory is empty; this patch introduces no new relocation expectation. patch-plan.json records every original/replacement byte, VA/RVA where applicable and file offset.

## Other two executable gates

- 0x480A65 (file offset 0x80A65) changes only the class-2 count byte from 0B to 0C in mov dword [esi+0x28],11.
- Switch table 0x45A298 has a unique entry for ID25 targeting 0x45A282. At 0x45A282, the first four bytes 6A 0F E8 87 become B0 01 5E C3 (mov al,1; pop esi; ret). Cases 0–24 target other addresses. The untouched bytes after the new return are unreachable through the case25 entry. This override is test-only; the inspected Bonus2 unlock state is false.

No normal vehicle initializer byte from 0x458E70 through 0x4598CF changed. The diff audit found 88 changed bytes, all within the five declared patch ranges. This establishes static preservation of original initializers, not runtime proof of all 25 original vehicles.