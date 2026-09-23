# R4E findings and decision

R4D.1 M1-M4 runtime observations were integrated before the published R4E checkpoint. R4E adds conservative source-byte DX attribute/material patching, same-size DXT authoring, exact texture dependencies, staging, a high-level mod build, and ZIP-compatible SMA helpers. The original R3 positions-only path remains.

Automation: 78/78 real DX and 6,960/6,960 DXT zero edits were byte-identical; 78/78 collision and topology hashes were preserved; 74 synthetic tests passed. Blender 5.2.2 synthetic attribute edits and seam rejection passed; its full 78-resource zero-edit attribute export was byte-identical. The existing 22-resource real Blender import/save/reload suite passed. E1-E4 candidates each preserve collision/topology and contain only field-authorized bytes. E5 full archive passed ZIP CRC/member hashes. E1, E3, E4 and E5 are now confirmed by human runtime observation; E2 is inconclusive.

R4E human closeout: **E1 PASS, E2 INCONCLUSIVE, E3 PASS, E4 PASS, E5 PASS**. See runtime-results.md/json. R4E.1 targets only normal writing and the environment feature bit. Topology-changing DX writing remains outside this phase.
