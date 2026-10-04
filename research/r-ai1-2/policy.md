# Stock / Mixed / Diverse

Stock returns -1 from the policy callback and replays the displaced native
instructions. No native class RNG draw, pool rewrite, DriverID rewrite, count
write or persistence conversion is introduced. Missing module/export follows
the same path. Existing research hardening and the optional R-AI2 capacity
shim are separate components, so this is Stock **randomizer** behavior.

Mixed selects one eligible class per newly generated AI with the game's
4D1E90 singleton / 4D1DF0 integer range [0,n). Class duplicates are allowed.
This describes separate selection calls, not statistically proven RNG
independence, uniformity or exact class probabilities.

Diverse Fisher-Yates shuffles the eligible class list using the same native
range API, consumes it before repeating, and starts another shuffled cycle
when exhausted. With three classes and four AI, the first three cover
T1/T2/T3 and the fourth starts a new cycle. Player class is not excluded.
One/two eligible classes and an empty set are handled without out-of-range
indexing; empty/invalid outputs return Stock.

Core stock pools contain seven IDs per class. T3 additionally admits ID21
through progress key11, ID22/key12, ID23/key13 and ID24/key14. Frontend
class-unlock reachability is separate from AI core vehicle eligibility.
Normal pool cases do not filter the core seven by human frontend unlocks.

Invitation intentionally permits opt-in class replacement of its stock
T3-only selection rule; it retains its core-only T3 pool and does not add
reward IDs21..24. Other selected classes use normal core T1/T2 cases.
This changes balance; event/rules/progression are untouched.

For Quick/Cup/Master, the native pool is rebuilt per randomized AI and all
earlier IDs are erased. With total<=5, every core class retains vehicles.
Stock driver pool initialization/shuffle/draw and identity publication remain
native. Additional RNG calls can affect later native draws; exact DriverID
equality to a separately generated Mixed-vs-Stock race is not promised.
The mod does not select or rewrite drivers.

Challenge has one AI in the supported path. Opt-in selects class then a
valid, unlocked, non-human ID from the established stock eligibility set,
using native range calls. Its fixed event constructor has no ordinary
class-pool chooser to reuse. This narrow replacement is before native ID/class
publication, after the existing driver draw. Multi-human Challenge is Stock.

Mode identity, first/count/slot and network guard failures return Stock.
Replay/Attract/network/multi-human owners are not hooked. Mode identities
outside Types2/5/6/7/8 are unsupported. Max active indices are Car0..Car4.
