# R4E findings and decision

R4D.1 M1-M4 runtime observations were integrated in the amended, still-unpublished R4D.1 commit. R4E adds conservative source-byte DX attribute/material patching, same-size DXT authoring, exact texture dependencies, staging, a high-level mod build, and ZIP-compatible SMA helpers. The original R3 positions-only path remains.

Automation: 78/78 real DX and 6,960/6,960 DXT zero edits were byte-identical; 78/78 collision and topology hashes were preserved; 74 synthetic tests passed. Blender 5.2.2 synthetic attribute edits and seam rejection passed; its full 78-resource zero-edit attribute export was byte-identical. The existing 22-resource real Blender import/save/reload suite passed. E1-E4 candidates each preserve collision/topology and contain only field-authorized bytes. E5 full archive passed ZIP CRC/member hashes. Their in-game effects remain pending.

Verdict: **MORE WORK NEEDED — R4E.1 runtime confirmation**. E1-E5 require human original-game validation before calling UV/normal/color/material flag writing and Python SMA packaging runtime-safe. Topology-changing DX writing remains outside this phase.
