# Custom vehicle readiness audit

| Modder goal | SDK v1 status | Exact limit or runtime evidence |
|---|---|---|
| Completely different body topology | YES WITH LIMITATION | Existing donor draw/material identities; every draw remains nonempty and faces are triangulated |
| Different vertex count | YES | Existing-draw uint16 local-index capacity applies |
| Different triangle count | YES | Existing draw set remains fixed |
| Different UVs | YES | Donor UV-set count is fixed |
| Different normals | YES | Source-space normals; valid generated normals required |
| Different vertex colors | YES | Existing four-channel vertex field |
| Different textures | YES WITH LIMITATION | Same-dimension DXT content replacement; no new texture string or slot |
| Body beyond donor bounds | YES WITH LIMITATION | B1 runtime PASS; existing donor draw/material identity |
| Different collision dimensions | YES WITH LIMITATION | C1 runtime PASS on finite existing tag101; no new hull topology |
| Different wheel geometry | YES WITH LIMITATION | W1 runtime PASS on all four instanced wheels; existing draw/material set |
| Different presentation geometry | YES WITH LIMITATION | P1 runtime PASS in presentation/menu; existing draw/material set |

All earlier same-topology capabilities and the F1 race-car topology edit have human runtime evidence. B1, C1, P1 and W1 passed in the original game; MASTER RALLYE VEHICLE SDK v1 is now a RUNTIME-CONFIRMED BASELINE. New draw/material identities, collision from scratch, extra EXE slots and track support remain future optional work, not claims of this baseline.
