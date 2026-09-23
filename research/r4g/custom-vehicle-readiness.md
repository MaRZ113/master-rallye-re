# Custom vehicle readiness audit

| Modder goal | Automated status | Exact limit or runtime gate |
|---|---|---|
| Completely different body topology | YES WITH LIMITATION | Existing donor draw/material identities; every draw remains nonempty and faces are triangulated |
| Different vertex count | YES | Existing-draw uint16 local-index capacity applies |
| Different triangle count | YES | Existing draw set remains fixed |
| Different UVs | YES | Donor UV-set count is fixed |
| Different normals | YES | Source-space normals; valid generated normals required |
| Different vertex colors | YES | Existing four-channel vertex field |
| Different textures | YES WITH LIMITATION | Same-dimension DXT content replacement; no new texture string or slot |
| Body beyond donor bounds | YES WITH LIMITATION | Writer and B1 candidate structurally validated; B1 runtime pending |
| Different collision dimensions | YES WITH LIMITATION | Finite existing tag101 per-axis scale; C1 runtime pending; no new hull topology |
| Different wheel geometry | YES WITH LIMITATION | Existing wheel draw/material set; W1 runtime pending |
| Different presentation geometry | YES WITH LIMITATION | Existing complete draw/material set; P1 runtime pending |

All earlier same-topology capabilities and the F1 race-car topology edit have human runtime evidence. The full custom-vehicle SDK v1 freeze still requires B1, C1, P1 and W1 in the original game. New draw/material identities, collision from scratch, extra EXE slots and track support remain future optional work, not claims of this baseline.
