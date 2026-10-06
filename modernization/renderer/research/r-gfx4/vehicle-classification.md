# D3D-boundary classification

## Observed renderer seam

CONFIRMED_BY_EXISTING_RESEARCH: shared owner VA0x00576970 /RVA0x00176970, DrawIndexedPrimitive CALLVA0x00577078 /RVA0x00177078 and returnVA0x0057707E /RVA0x0017707E. Frozen draw-owners.md and exact-build callmap identify this shared world/vehicle tail. Alternate owner VA0x0057F9A0 /RVA0x0017F9A0 is intentionally outside the first tracker. Production has no Broker dependency, no child COM wrappers, no geometry byte reads and no native Get* calls per draw.

Only canonical SHA and exact principal return PC in the main EXE are observed. Race context is evaluated from the successful game-requested projection at returnVA0x0053FA75 /RVA0x0013FA75: symmetric finite LH, reconstructed source90 within0.01 degrees. Logical original projection is used even when R-GFX3 delivers effective80. HUD/ortho and source45 preview are outside race context. This does not prove replay/split-screen equivalent.

Signature: FNV64 over method/caller, VB/IB last successful creation serial, stride, index base, full draw args, FVF, texture0/1 serials, stage COLOR/ALPHA ops and args, TCI/transform flags, active stage1 texture matrix bits, depth/alpha-test/alpha-blend state. WORLD is excluded. Unknown nonnull resource generations reject a signature; no raw pointer is a persistent identity. This is a process/device-local fingerprint, not an asset content hash; collision and shared-resource geometry ambiguity preclude visual proof.

## Temporal state

Fixed128 WORLD groups/frame,64 signatures/group and128 previous tracks. Near-identical rigid WORLDs merge (translation squared<1e-6, orientation squared<1e-8). A full static WORLD group is marked saturated/unknown without poisoning other groups. More than128 groups invalidates the whole frame's classification. Signature sets are sorted once per Present and merged linearly during association, rather than quadratically compared. No per-frame heap allocation, matrix inverse, or per-draw serialization. F10 copies compact facts into the existing bounded buffer; normal frame summaries remain compact.

Across adjacent Present frames, signature overlap plus translation/orientation proximity proposes matches; mutual unique nearest association is required. Max squared translation100 and orientation difference2; cost ties within1e-6 restart cold/ambiguous. New IDs are assigned in WORLD lexicographic order, never draw order. Same geometry at distinct WORLDs remains separate. Motion accumulates after translation>.05 game units or orientation squared>.0001; age>=4 and at least2 motion observations mark dynamic. Stopping/pause retains a previously dynamic track while observed. A missing group restarts cold on return. These thresholds are STATIC_INFERENCE heuristics, not measured car kinematic bounds.

Successful Reset clears resources/tracks/context; failed Reset preserves them. Failed Present clears tracks. Resource pointer re-creation or registry capacity invalidation clears tracks; an epoch guards earlier F10 records from reassociation to a newer group at the same index. A frame without tracked race geometry clears previous associations (frontend/scene gap). There is no proven scene-manager hook; an instantaneous same-resource race restart without a gap remains a limitation. Raw resource Release is not observed; existing serials mean last observed creation, not proven complete lifetimes. These limitations independently block a visual override.

## Confidence and exclusions

UNKNOWN: missing build/context/owner/generation/rigid matrix, overflow or ambiguity. CANDIDATE: valid associated world group, including static groups. DYNAMIC_ENV_OBJECT: demonstrated motion plus exact active stock env signature. Reasons independently record normal FVF and opaque depth-writing state. Alpha, no-normal, particles/trails/sky/UI and preview never become a visual-positive vehicle. Dynamic env objects remain unproven vehicles, even when opaque.

Offline Broker validation reproduces five unique transform groups for Tata. Wheels use translation plus directed local-X axle; full spinning basis and fixed wheel order are deliberately not required. This snapshot does not supply a production identity whitelist. No VEHICLE_REFLECTION_CANDIDATE is emitted yet. Requested ViewDependent2D is forced Stock with BLOCKED_BY_CLASSIFICATION. Required next evidence: a warmed Stock F10, static-world negative controls, and targeted Broker pairing only if the D3D observations cannot establish which dynamic tracks are vehicles.
