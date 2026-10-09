# Landscape contact and initial placement

Manager initialization resolves a landscape entity and installs it in the collision path. The same concrete backend **2e3270** routes convex-versus-BSP pairs through **2470f8**. Landscape/prop contact therefore uses a proved shape dispatch, rather than visual landscape triangles inferred as contact triangles.

`16df68` registers the body and invokes **16f2f0** for bounded initial intersection correction. When its gate16f040 permits, it repeatedly tests the prop against landscape through interface virtual+34. Correction uses an accumulating vertical increment: the increment grows by .01 on successive iterations and the accumulated value is added to body Y. It stops when the relevant contact disappears or reaches a 1000-iteration guard/warning. This is not a single fixed .01 lift, a new mesh or general terrain deformation.

During update, **173d98** clears contacts and invokes **16e498**; **173df0** follows the contact-group solver path. Relevant position, force and velocity state writers are present, but BSP narrowphase geometry, full penetration policy, terrain material coefficient mixing and contact persistence are not exhaustively reconstructed.

The initial authored Row3 is an input pose. Initial placement and later physics can change it. Neither Row3 nor source render-mesh bounds alone proves the live contact pose.

Runtime required for friction, settling and selected contact footprint: see [runtime-capture-plan.md](runtime-capture-plan.md). No collision structures were modified.
