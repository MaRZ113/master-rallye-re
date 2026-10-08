# Material to render binding

The executable-supported ownership chain is:

1. `391d38` tag2 creates mesh and reads its material/strip vector.
2. `391690 -> 3a6c58` writes that same mesh's mode+28, resource names+34/+38
   and auxiliary+24. No cross-table string matching is used to invent binding.
3. `3714e0` iterates model+44 meshes and resolves those two names with
   `2fd7d0`, writing handles mesh+dc/+e4.
4. Mesh vtable488328+5c selects `3bca80`. Its nonempty strip vector drives
   `361a58` cache preparation and renderer setters from the same mesh.
5. Renderer vtable4853f0+9c selects `31d230` (mode), +a4 selects `31d1f8`
   (two handles), +ac selects `31d250` (cached packet queue).
6. `31cd98` drains the queue, calls mode handler+bc=`312610`, first/second
   binders+c4/+cc=`311c50/312130`, state commit+dc=`31c438`, then links each
   geometry packet with `31e010`.

This proves a visual mesh/material/packet relationship beyond collision-source
ownership. The queue key includes material mode, handles and flags. Its entire
arithmetic is not reimplemented: a safe scalar query rejects HI/LO-consuming
code and the remaining bounds are explicitly unresolved in the inventory.
The queue's consumer fields and virtual targets independently establish the
necessary draw association.

Source material/group binding is **CONFIRMED_BY_BOTH**. CPU dispatch, lookup,
queue and packet production are **CONFIRMED_BY_EXE**. A particular live mesh
instance, current LOD and visible frame remain **UNKNOWN LINK** until captured.
No claim is made that every source mesh is submitted every frame.
