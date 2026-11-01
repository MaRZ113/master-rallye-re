# Definitive Demo vehicle shortlist

**Current V-DEF4:** owner accepts Forester, retail-physics RAV4 and33-record custom ordering. Early PRIVATEER TOMCAT32 now has a separate owner-test CMD candidate; no next restoration begins until its findings are reviewed. Historical ratings are in DEMO_FRONTEND_STATS.md. The dated snapshots below preserve earlier audit evidence.

**Current V-DEF2.1:** Forester remains owner accepted. RAV4 visuals/integration
are now owner accepted; the hybrid handling is rejected. A separate complete
retail Newrav physics candidate is prepared, with explicit remaining wheel-fit
WARN and editable REAL_FALLBACK Daniel Nebot. The eight-case historical
driver/marker matrix is `DEMO_DRIVER_COLOUR_EVIDENCE.md`; source-platform names
and inferred cross-version continuity are separate. No next import begins.
See `V_DEF2_1_RAV4_RESULTS.md`. The following V-DEF2 snapshot is retained history.

**V-DEF2 update,1 November2026:** corrected Forester is owner accepted. Canonical
Rav4 now has a manifest-driven independent CMD candidate, ID31/T2 local11;
source/automated/native-helper validation passes, owner gameplay pending.
See `V_DEF2_RAV4_RESULTS.md`. Historical unmatched icon candidates are not used;
Workshop generates matching CarSheet/SIDE HUD art. Driver remains unresolved.
No next shortlist vehicle is started before owner RAV4 review. The original
audit evidence/ranking below remains retained.

Audit recommendation,1 November2026. **No import or extra runtime slot is
allocated by this list.** Uniqueness and technical readiness are independent.
Complete native inputs do not imply qualified glass/brakes, registration or gameplay.

| Priority | Candidate and preferred source | Uniqueness evidence | Readiness / remaining work |
|---|---|---|---|
| 1 | Forester: original9.3.1 GXM/car/wheel; main PCG or Nov complete | Pink enclosed SUV versus retail Forester/WOOLDAND pickup. Main car exact decoded surface/UV/material match across local/shipped931;2459 vertices/1864 triangles | Complete local3-role DX/texture set. Review native glass/glow, artwork/driver and independent registration later. Preserve original931 provenance; avoid ambiguous Original/car.dx alternate. |
| 2 | Rav4: cooked PCG root, original9.3.1 provenance | White/blue historical MR SUV;1902tri versus retailNewRav1972, no exact retail/accepted car surface;RMS0.127260 toNewRav | All3 DX roles and27 matched GXI/DXT pairs.3-view assembled D3D9 preview. Preserve global-cache warning; native glass/brake controllers and physics association remain unqualified. |
| 3 | WildCat: PCG root, authenticated against original8.4.1 GXM | Early blue body/equipment, distinct from retail;1651 body triangles. Legacy one-triangle cache difference bounded | All3 native roles and textures. Complete D3D9 source preview works. Legacy125/127 draw/collision WARN and native event authoring remain. |
| 4 | NewRav: original corpora/demo-9.3.1/DataGx/Vehicles/NewRav | Early red body/livery:2029tri versus retail1972; zero exact triangle overlap, unscaled sampled RMS0.080853 | Original corpus has car/complete/wheel and textures. Nov lacks complete DX; use supplied originalcomplete, not guessed assembly. Native event states need qualification. |
| 5 | LandCruiser: PCG root + original841 GXM | Historical trim/roof/body/livery;1855 vs2323tri, overlap0.391304 / RMS0.054221 | Complete localnative set. Original841 Mercedes aliases the GXM: do not counttwice. Same real-world family, not a wholly new vehicle. |
| 6 | megane: PCG root + original841 GXM | Early body/livery;1922 vs2072tri, overlap0.504344 / RMS0.026493 | Complete localnative set;29 common texture filenames,25 decoded-pixel equal. Retain actual differences rather than repainting retail. |
| 7 | Tata: original9.3.1 | Historical bodyvariant;1973 vs2022tri, overlap0.511869 / RMS0.049757 | Original931 has3-role DX; Nov is GXM-only.81 common texturefiles/73 pixel-equal includes unreferencedresources, not81 boundmaterials. |
| Research priority | Rav4Alpha: original9.3.1 | Preserve its original source variant; do not infer identity solely from folder name | Original source only, no complete native assembly. Full Rav4 is now covered by the new PCG bake above. Keep both distinct from Michelin RAV4. |

## Defer or retain as variants

* **Mercedes / Copy of Mercedes:** main PCG body matches the accepted Mercedes
  resource namespace. Preserve source/artwork variants, not a duplicate newcar.
  The technical namespace is not a newly qualified manufacturer association.
* **Trooper:** sourcebody already represented by accepted Heritage. Preserve
  historic material/state variants rather than automatically making anothercar.
* **Jump:** overlap0.976605/RMS0.005331,1808 vs1838tri;23/25 common
  textures pixel-equal. Lower uniqueness. JumpAlpha DX remains unsupported.
* **Later KiaSportage:** overlap0.880758 but RMS0.000032,2261 vs2323tri;
 57/58 common texturefiles pixel-equal. Very similar positional shape with
  topology/material differences, not automatically a new silhouette.
* **Later Wildcat:** source1966 vs retail1998tri,overlap0.96046,RMS0;
 28/28 common textures pixel-equal. Preserve topology, lowerpriority.
* **Navara9.10:**2297 vs retail2366tri,RMS0.101387,88/89 commontexture
  files pixel-equal. Measurable variant; zero exact triangle overlap alone does
  not prove an independent uniquecar.
* **Simmbugghini9.10 / local Nov Wildcat:** renamed source correspondence and
  missing mastersticker133-tga prevent complete texturequalification.
* **Alpha aliases:** group identical GXM bodies, retain independent wheel and
  incompleteassembly evidence. Do not automatically allocate separate identities.

## Newly supplied Rav4 canonical evidence

All33 original GXM/GXI/TXT files match9.3.1. Use PCG Rav4 car/complete/wheel
DX only with their recorded hashes in DEMO_VEHICLE_AUDIT_RESULTS.md; no shipped
DX counterpart is available. Complete-role availability is not native staging
qualification. Never overwrite its source files to repair the global index cache.

## Forester canonical choice

Main PCG car.dx SHA256:
`fbe8d15af205a3cbe95773d5241372352729f7fbcef21e61386123209a80a423`.
Matching original car.gxm:
`3d27573a2358f379de1c1914fb6a17ac525a5a709bd62ab824736d05ac4c2535`.
Main complete.dx:
`72a3b98f616d55e66e43bf0bbc2702bdb5ff464406ae7e14338cc3c4a5a4ee15`.

PCG `Original/Forester/car.dx` shares sourceGXM and bodybounds but differs
measurably (91.9528% shared approximate triangles,RMS0.015046). Keep it as an
unresolved alternate bake. `Original/Forester/car111.dx` is byte-identical to
maincar, and its complete/wheel match the mainfiles. Original9.3.1 misspells
its complete GXM filename `comlplete.gxm`; do not invent an originalcomplete DX.

Next review selects one canonical snapshot and native systems plan. DLL/bootstrap,
extra independent record/class capacity, driver/artwork mapping and actual owner
gameplay remain separate gates. This audit changes none of them.
