# Demo 9.10.0 France1 course cook workflow

Evidence: `CONFIRMED_BY_RUNTIME` for the owner's runtime selection/load result;
`CONFIRMED_BY_BINARY` for parsed DX and resource hashes.

The cooker trigger was launching the original Demo 9.10.0 runtime and choosing
France1. No separate cooker program or CLI invocation was observed. The user
provided screenshot logs in the ignored local directory
`inputs/9.10.0_France1_log-screens/`.

The two repeatability runs used only `.research-output/r5t_b/cooker-lab/`, an
isolated clone whose runtime EXE hash matched the user's Demo 9.10.0 EXE. The
France1 folder contained the 8.4.1 source GXM/TXT and 104 GXI resources. Before
each user selection the clone's `france1.dx` and 66 DXT outputs were removed.
The original installation and source inputs were not changed.

The screenshots show the runtime noticing an invalid/missing cache, reading
`france1.gxm`, building the DX model, welding vertices, building the course
BSP/land database/render draw planes, saving the cached DX, then loading the
RaceTest scene successfully. The log also reports repeated render-sort BSP
candidate/plane errors. Those messages do not identify the separate tag100
payload.

The 8.4.1 source directory had 172 non-DX resources: 66 DXT, 104 GXI, one GXM,
one TXT. The before-first-run scratch snapshot confirms 104 GXI + GXM + TXT and
no DX/DXT; each forced cook emitted one DX and 66 DXT. The 172 non-DX output
files matched the source and each other byte-for-byte in both runs. DX output
was revision 135 but varied structurally. Exact per-run hashes and section
measurements are in [`cooker-baseline.json`](cooker-baseline.json).

The report can be reproduced when local inputs and ignored scratch results are
present with `python tools/r5t_b_report.py`. It writes derived JSON only.
