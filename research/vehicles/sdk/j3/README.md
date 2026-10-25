# R5V-J.3 — Vehicle SDK v1 productization

**Implementation status: J.3-A authoring and J.3-B static runtime compiler implemented; GlacierSprint is READY FOR HUMAN RUNTIME, not runtime-qualified or a public release.**

This is the user-facing donor-based Option A workflow. It reuses the existing
Vehicle Authoring SDK (`VehicleProject`, DX/DXT tools and validators) and adds
an addon identity/configuration project. It does not enable unrestricted
Blender import or new cooker/material/collision formats.

Start with the [Quick Start](quick-start.md), then see [authoring a donor
vehicle](authoring.md), [manifest settings](manifest.md), [physics family
generation](physics.md), [build limits](build-and-install.md), [save and
removal policy](saves.md), [troubleshooting](troubleshooting.md), and
[release gates](release-boundary.md). The high-level work plan is in
[plan.md](plan.md).

The compiler can produce a deterministic offline plan, validated model/texture
payload, and (when supplied the pinned retail Data.sma plus matching unpacked
root) independent DataGame family XML overlays. J.3-B now adds
collection-specific native operations, a verified external resource bundle,
and a build of the existing J.1/J.2 launcher. The exact GlacierSprint bundle
passes static verification and is ready for a human runtime test; compilation
does not qualify its new identity.

Current runtime-qualified addon identities remain ID26/T1 Mercedes and
ID27/T2 R5VQualifier. Another identity that resolves to one of those slots is
only synthetically planned until separately runtime-qualified. There is no
new additive T3 slot, unlimited-ID claim, ID28 work, or custom ordering.

The independent [Glacier Sprint T2 example](../examples/glacier-sprint-t2.json)
is metadata-only. Its local retail-Navara smoke build was performed from the
user's corpus and is not included in the repository or review archive.

See [validation](validation.md) for J.3-A results and the new
[J.3-B compiler](runtime-compiler.md), [runtime validation](runtime-validation.md),
and [human handoff](runtime-handoff.md). Create the compact source-only review package with
`python tools/package_j3_review.py`; it writes to ignored `.research-output`
and verifies its per-file SHA256 index.
