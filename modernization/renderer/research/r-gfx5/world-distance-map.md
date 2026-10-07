# Distance/fog/culling/LOD — prototype DEFERRED

Current pristine read-only query **VA0x0056D020/RVA0x0016D020** confirms renderer environment block+0x54. Near+0x70(block+0x1C)=0.2; ViewDist class0/1/2 ->+0x74(block+0x20)=300/400/500. Span+0x6C clamps0..1; enabled fog start+0x78=end*(1-span),otherwise=end. CONFIRMED_BY_EXE, consistent with [prior fog](../../../renderer-recon/fog.md).

| Limit | VA / RVA | Evidence/scope |
|---|---|---|
| Far clip | 0x005614A0 / 0x001614A0 | Ordinary2*distance=600/800/1000,special100000;near0.2. Requeried EXE. |
| Fog | 0x00576970 / 0x00176970 | Linear vertex fog/global env +instance enable0xAA; existing EXE research |
| Sky/env | 0x004B1180 / 0x000B1180 | Sky palette,span0.9,ViewDist class; existing EXE research |
| Sphere CPU culling | 0x004F2380 / 0x000F2380 | Distance/behind-camera/side planes; R-GFX4 synchronizes FOV planes, leaves distance |
| Hierarchy visibility | 0x0054C9D0 / 0x0014C9D0 | Bounds/hierarchy plus caller distance scalar; existing EXE research |
| Submission | 0x00576910 / 0x00176910;0x00562560 / 0x00162560 | Model/object submission, not distinct terrain proof |
| Terrain sectors/chunks | UNKNOWN | End-to-end data/visibility/draw owner not established |
| Vegetation thresholds/LOD | UNKNOWN | Separate limit not established |
| Model LOD switch | UNKNOWN | No validated coherent override seam |

Span0.9 gives start30/40/50,end300/400/500; far twice end. Enlarging far cannot restore objects already removed by distance/hierarchy/sector submission. Fog is not terrain visibility; palette is not sun color.

No ViewDistanceScale or far5000 patch. Future experiment needs fixed-camera visibility/submission/LOD measurements and coherent fog/far/CPU/terrain thresholds. No blanket highestLOD. Current viewport and FOV/frustum behavior preserved; mapped/deferred is the evidence-backed result.
