# Minimal loader evolution check: demo 9.3.1

Status: **PREPARED; not run**. This is a separate build. Do not inherit the Trooper 8.4.1 loader result without testing.

Use a separate clean runnable scratch copy of demo 9.3.1. Restore each case from its own scratch baseline. `demo-9.3.1:DataGx/Vehicles/Trooper/car.gxm` SHA256 is `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642`; same-build `car.dx` SHA256 is `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1`. Its `Black-tga.gxi` and `black-tga.dxt` happen to have the same bytes/hashes as the named 8.4.1 pair, but this is an explicit cross-build comparison, not a fallback.

1. With `car.gxm` and `car.dx` present, show Trooper and enter a race. Record body/collision and any Debug window title/control tree.
2. Restore baseline, remove only scratch `car.dx` and repeat. Restore, then remove only scratch `car.gxm` while keeping `car.dx` and repeat. Record visual body, wheels, collision and file-access events. This tests whether GXM remains live; do not infer the role of complete/wheel from car alone.
3. Restore baseline, remove only scratch `black-tga.dxt` while keeping `Black-tga.gxi`, trigger Trooper texture loading and exit. Hash any new DXT. Run the same three-way tool with `--corpus-id demo-9.3.1` and the 9.3.1 corpus root.
4. If a Debug window appears, run `tools/runtime/demo_debug_capture.py --list-windows` and capture a short session; compare message templates with 8.4.1. A small ProcMon trace can distinguish file opens from visual equivalence.

The static EXE contains the same GXI/DXT cache message family and a symmetric caller branch; see `targeted-exe-xrefs.md` (**CONFIRMED_BY_EXECUTABLE**). No 9.3.1 live loader result is claimed here.
