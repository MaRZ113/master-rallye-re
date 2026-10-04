# Count failure and replacement

The previous Quick Race proof received `firstAI,count,class,excluded human
IDs` from 47B780 at 47B93D/47B96E. The old 68E300 shim checked count==3 at
68E324 and current slot<=3 at68E33B. One/two/four-AI setup took its Stock
fallback. Player/course/difficulty independence did not imply count coverage.

The new loop hook receives current ESI, immutable end and actual count; first
is end-count. Zero AI has no loop callback. Counts1..4 affect exactly Car1..N,
with existing native pool/draw/publication and prior-ID exclusion. Unknown
mode, first!=1, split/network or count outside1..4 returns Stock. The DLL
does not create participants or write NumCars.

The four-car package keeps the native frontend maximum of three AI. Four AI
require the separate, unchanged R-AI2 five-car shim. Its previously audited
research guard is ID0/T1, Track10/ItalyS4, Race, one human, ghost off and visible
Opponents3. That guard is a capacity-proof restriction, not an R-AI1.2 class
selection restriction. Native composed tests execute the real47B780 owner,
the five-car setup shim and real458090 chooser through all four AI slots.

Old randomizer68E300..approximately68E463 and capacity68E300..68E383 overlap.
They are never overlaid. New selectors start68E400/68E700/68EA00; loader and
Challenge fit below68F000. [Build summary](build-summary.json) records exact
disjoint ranges, hashes and unchanged capacity composition.
