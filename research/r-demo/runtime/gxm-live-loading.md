# GXM live loading: human runtime evidence

The user reports testing a structurally identified Vector C position in `demo-8.4.1:DataGx/Vehicles/Trooper/car.gxm` in the original demo. A small coordinate edit visibly changed the expected body geometry while primary vehicle collision remained present. This identifies Vector C as participating in **live runtime position geometry** for that path (**CONFIRMED_BY_RUNTIME**, human report). The exact tested file hash and changed component were not supplied with this new report; the earlier ignored one-float candidate is a documented structural candidate, not independently identified here as the tested bytes.

The resource-removal matrix separately shows that `car.gxm` is required for the tested race body and its primary collision, `complete.gxm` for the presentation/menu model, and `wheel.gxm` for visual wheels. This is **CONFIRMED_BY_RUNTIME** for Trooper in demo 8.4.1 only. It does not isolate `$chull` from other `car.gxm` content and does not identify the role of DX files at the file-access level.

The demo did not appear to expose retail-style external procedural body damage in this test. Missing retail-style deformation is not evidence against the visible GXM position edit.

The isolated `$chull` source-position candidate later **CRASHED_IN_RUNTIME** in both demos. This leaves the exact dependency/failure stage unknown; see `research/r-demo2/chull-crash.md`.
