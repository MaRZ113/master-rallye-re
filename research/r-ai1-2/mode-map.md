# Native mode and generation owners

All addresses refer to pristine retail SHA256
bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4.
Labels below are CONFIRMED_BY_EXE unless explicitly qualified.

| Mode / Race Type | Fresh roster boundary | Stock class / vehicle | Drivers | Storage / reuse |
|---|---|---|---|---|
| QuickRace / 2 | 47B780 -> 458090(first,count,class,human IDs) | Car0 registry class; T1 0..6, T2 7..13, T3 14..20 plus unlocked 21..24 | Native ten-driver pool/draw/publication | Race/CarN; Restart/loading reuse, new frontend generation rerolls |
| Challenge / 7 | 45EA60 -> 44FEC0(event) | Registry +570/+574+(event+25)*2C: fixed human/AI absolute IDs | Original shuffled driver pool; draw occurs before new vehicle hook | Race/CarN; current race/restart reuse |
| RallyeCup / 6 | 481722 (normal human branch) -> 45BE10 -> 45ABC0(1,3,class) | RaceData/VehicleClass; ordinary class cases with reward additions | Native ten-driver pool; Name and DriverID published independently | RaceData/CompetitorN; three-stage cup shares roster |
| Invitation / 8 | Frontend 462678 type8, class2/cup5 -> same 45BE10/45ABC0 | Special Cup=5 branch, core T3 IDs14..20 only | Same competition driver chooser | Same native three-stage event lifecycle, Race IDs36..38 |
| MasterRallye / 5 | 48157C -> 452590 -> 451DD0(1,3,class) | MasterRallye/VehicleClass; ordinary class cases/reward checks | Native ten-driver pool plus name publication | RaceData/CompetitorN -> MasterRallye/CarN; stage/save/load reuse |

The second-human branches are left Stock. Quick Race count comes from the
existing setup arguments, not an assumed 3. Common 449E90 sets normal
competition totals to four; R-AI1.2 does not change that.

Frontend single-player selection sets Type6 at 4625D9, Type5 at 462606,
Type7 at 462654 and Type8 at 462681. Invitation class2/cup5 initialization
is visible at 462688/4626A9. The 46D1D0 Type9+ path is a different owner;
it is NOT Challenge and is excluded.

## Safe seams

Quick: 45810B initial pool bookkeeping, 458379 per-AI draw, 4582D5 pool end.
Master: 451E90, 4520D2, 45202D.
Cup/Invitation: 45AC79, 45AF0F, 45AE66.
Challenge: 45010E fixed AI ID load in the one-human branch, before
45011F CarID and 45013D registry-derived CarClass publication.

Each non-Stock class rebuild uses the native pool cases, native vector clear/
erase, shuffle/draw, and downstream identity publication. It filters all prior
participant IDs, including the human. No CarClass patch after publication.

Master and Cup reuse their firstAI argument word for a temporary name pointer
after the first AI. The hook computes firstAI=end-count from the retained
loop-end register; on rebuilding, the dead argument scratch retains end.
Scratch is restricted to chosen-ID/driver locals before their draws, never
callee-saved register words. Native emulation checks register/stack/SEH return.

Cup does not write RaceData/CompetitorN/CarClass in 45ABC0. Active race identity
is derived from the chosen ID by 44A320 -> 44A710, which reads registry
class/family/colour independently per participant. A stale RaceData class
value is not evidence of active Race/CarN class normalization.
