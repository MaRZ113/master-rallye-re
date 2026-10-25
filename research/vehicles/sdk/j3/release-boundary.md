# SDK v1 status and compatibility boundary

## Current status after J.3-B

| Area | Status |
|---|---|
| Donor VehicleProject edit/validation | Reuses the existing donor-authoring baseline. |
| Manifest v1 and deterministic addon identity plan | Implemented and regression-tested. |
| Third independent author identity | Glacier Sprint T2 compiles to ID27/T2/local7 as a synthetic plan. |
| DX/DXT dependency staging | Reuses existing parsers and deterministic resource inventory. |
| Independent donor physics-family XML | Implemented for the exact pinned retail Data.sma; donor rows are cloned without edits. |
| Native operation/resource bundle for the exact ID26 + ID27/T2 layout | Implemented and statically verified; other layouts fail closed. |
| GlacierSprint native and resource collection compilation | Built and reproducibly verified from the author project; runtime identity not yet qualified. |
| External launcher build and bundle preflight | Built with MSVC and passed native `--verify`; integrated game launch remains a human gate. |
| Original retail executable on disk | Exact SHA required; compiler never writes or packages a replacement executable. |
| Independent Glacier Sprint runtime | READY FOR HUMAN RUNTIME; not runtime-qualified. |

## Qualified target

Retail EXE SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

Runtime-qualified added identities remain ID26/T1 Mercedes and ID27/T2
R5VQualifier. The current profile supports one extra T1 slot and one extra T2
slot; T3 has no new additive slot. The ID27/T2 slot can be planned for another
identity, but only R5VQualifier has runtime identity qualification. Synthetic
allocation to ID27 does not add a new qualified identity.

## Deferred or blocked

- Native collection layouts outside ID26/T1 plus one ID27/T2 addon.
- T2-only layouts; rejected to avoid silently enabling Mercedes ID26.
- Frontend/native policies beyond the qualified VehicleSelect, Results, unlock,
  audio and mode-pool boundaries encoded by the current profile.
- Save collection compatibility warnings and lockfile persistence.
- Public installer/uninstaller and broader runtime conflict matrix.
- Human integrated run of the independently named GlacierSprint addon.
- Broad demo donor build-profile qualification.
- Custom materials, arbitrary Blender import, new collision topology, new
  audio authoring, UI ordering, ID28 and additive T3.

**J.3-A:** PASS for offline donor project/identity compilation. Its semantic
offline plan remains separate from the J.3-B runtime artifact.

**J.3-B:** IMPLEMENTED / READY FOR HUMAN RUNTIME for the bounded two-slot
layout. A collection compiler now creates ID27's native record and audited
operations from the supplied manifest, composes the corrected J.2 re-entry
hook, builds the effective VehicleSelect/DataGame/resource-root outputs, and
verifies the whole bundle through the existing external launcher format. The
exact J.2 reference pair retains its operation table and reconstructed image.
GlacierSprint has a separate bundle and launcher preflight, but has not been
run in-game. The compiler rejects T2-only input rather than silently adding
ID26. This is not arbitrary-layout or arbitrary-N runtime support.

**J.3-C:** NOT STARTED. SDK v1 is not release-ready; a human GlacierSprint
runtime pass and broader install/removal/conflict qualification remain.
