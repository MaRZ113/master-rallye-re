# Native private damaged-mesh ownership

Exact retail EXE bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4, REA/Ghidra12.1.4 fresh read-only analysis of function0054c9d0. Compact evidence and original independently PE-mapped byte window accompany this note.

The original renderer does NOT always dispatch model+18. At54caf4 it assigns render instance+8c=this compiled model. At54caee it reads instance+90; when nonzero,54cafe dereferences this private list's sentinel and54cb00 reads sentinel+4 first node. It walks sibling+8 and invokes each node virtual+30 with the same render instance. Only when private list iszero does54cb20 use model+18, same sentinel+4/sibling+8 convention. This is exact original consumer evidence for private damaged-copy ownership, not permission to accept arbitrary nearby pointers.

Minimal correct identity should select the same current native source list, retain that source-list identity in the certificate, walk verified root/child layouts with count/type/cycle bounds, and require the current emitted mesh to belong to that selected tree. Recheck source-list selection immediately before suppression. Do not readbothlists and acceptaunion, or discard source hashes/generations/WORLD.

A bounded current READ/QUERY attempt for PID47284 failedOpenProcess WinError87. Process inventory confirmed no running MRallye atthatmoment, therefore no current private list count/membership has been established here. Fresh same-session capture plus optional read_current_owner.py can close this remaining runtime gate. The helper requires explicit currentPID, currentcapture and independently selected instance, verifies packet+74 backreference/currentmodel, reads atmost32 siblingroots perlist and64KiBoverall via established reader. It writes metadata only; no game memory mutation or native invocation.

This proves the correct native selection contract, not yet that the current damagedXtrail private tree contains27roots or exactexpectedgeometry. Those remain explicit runtime admission tests.

## Fresh same-session runtime closure

User supplied fresh damaged owner session PID40592. At capture age approximately30seconds, read/query-only join verified instance0x21328258, packet backreference and unchanged compiled model. instance+90=0x1f13dc50 selects private root0x1f163618 (vtable0x6921b0). Its child list contains exactly27 terminated siblings. All18 captured current emitted meshes for this owner belong to those27 private children. None belongs to the original model's27 children. Original model and private roots share expected group dispatch; membership differs because meshes were cloned. `current-private-root.json` records pointer observations strictly as same-session evidence, never persistent identities.

This closes the missing native list-selection contract for the observed XTrail damaged instance. Full source geometry/hash/material validation remains required; selecting the correct owner tree does not authorize arbitrary deformed geometry.
