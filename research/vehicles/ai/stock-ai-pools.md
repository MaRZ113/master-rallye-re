# Stock AI vehicle pools

## Current result

The pristine retail Quick Race chooser is **CONFIRMED_BY_EXE** to build explicit
vectors of absolute vehicle IDs. It does not select a class-local ordinal and
does not call the G.1 sparse T1 local-to-physical mapper.

| Class code | Candidate physical IDs | Construction | Conditional IDs |
|---:|---|---|---|
| 0 / T1 | 0–6 | absolute IDs 0 through 6 | none |
| 1 / T2 | 7–13 | absolute IDs 7 through 13 | none |
| 2 / T3 | 14–20 | absolute IDs 14 through 20 | 21, 22, 23, 24 behind their individual progress flags |
| 4 / alias | same arm as code 2 | shared switch arm | same as code 2 |

ID25 is absent from the stock T3 list. ID26 is absent from the stock T1 list
in retail. H.1 now appends it explicitly to Quick Race's native T1 pool and
is `CONFIRMED_BY_RUNTIME` for the supplied natural Quick Race result. H.2
extends the T1 source at the distinct dynamic Rallye Cup/Invitation and new
Master Rallye roster owners; those paths are
`READY_FOR_HUMAN_RUNTIME`, not yet runtime-confirmed. The machine-readable
form is [stock-ai-pools.json](stock-ai-pools.json).

## Selection behavior

`FUN_00458090` receives the selected class, the participant range, and up to two
excluded absolute CarIDs. Quick Race supplies the player's CarID; split-screen
also supplies the second player's ID. It copies candidate identities into a
working vector, selects and removes entries, and refills/shuffles the working
vector after exhaustion. The stock selection therefore avoids duplicate
vehicles during one working-pool cycle, while repeats can become possible
after the pool is exhausted. The candidate excludes the player's selected
vehicle when it is present in that class pool.

Every covered T1 input is a direct absolute-ID list. Extending an ordinal loop
from seven to eight would be incorrect: the neighboring absolute ID7 belongs
to T2, while the frontend's T1 local7 maps sparsely to physical ID26. H.1/H.2
append `26` explicitly at each verified dynamic T1 owner while leaving T2 IDs
7–13 and T3 unchanged.

## Evidence

The working tree's current Ghidra 12.1.4 export for retail
`FUN_00458090` shows the three switch arms and direct vector appends. The export
was checked against pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and the
bytes around the selected-ID publication site. The direct xrefs to the pool
builder are `0x0047B93D` and `0x0047B96E`, both inside
`FUN_0047B780`; the latter is the one-human Quick Race call used by the
diagnostic proof.

The H.1 Quick Race natural selection and Results identity are now
`CONFIRMED_BY_RUNTIME`. Cup, Invitation, and Master Rallye H.2 inclusion
remain static/candidate-ready; see [natural-t1-pool.md](natural-t1-pool.md),
[mode-aware-t1-eligibility.md](mode-aware-t1-eligibility.md), and
[runtime-results.md](runtime-results.md).
