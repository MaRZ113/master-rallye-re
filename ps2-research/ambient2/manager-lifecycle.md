# Registration, layout, spawning and lifetime

Canonical class string `472b78` is `gaAnimals_BirdManager`. Shared factory entry `15b190` contains the exact audited BirdManager allocation: JAL allocator at`15d29c`, delay-slot size0xb0 at`15d2a0`, constructor call`15d2a4 ->1ae8b8`. The original window is in `instruction-probes.json`; the full factory size is not asserted. Constructor installs vtable`473c10`. Clone`1cec68` allocates a fresh0xb0 manager and calls the constructor; it does not copy a previous prototype's mutable bird state.

The complete essential field table is [bird-runtime-layout.json](bird-runtime-layout.json). Important vectors are pointer arrays with begin/end/capacity triples: free+38, ground+44, flying+50, pending milling+5c, pending takeoff+68. Their counts are `(end-begin)/4`, separately from capacity+34 and source point counts. +74..+7c is the current distance observer position. +80/+84 start at-1 and cache milling/flight nearest indices.

Config`1af0b0` reads list names, four distances and two random bounds. Bounds are clamped only above10. Negative/corrupt values are not repaired by the diagnostic. The call`1af150 ->1e2b98` is a Boolean writer: the helper constructs/appends a Value. This preserves the fresh +94 brown default instead of reading authored False. `1af1c0` contains a White-bank branch when +94 is0, but this is not proof that False in the canonical XML reaches that branch.

Initialization`1af1c0` resolves both names. If both pointers are NULL it schedules owner removal. Otherwise it optionally queries the global broker for `Animals/MaxBirds`, allocates the pool via`1af460`, and appends image keys0/1/2/3 to the first free entity's visual commands. A possible preload purpose is STATIC_INFERENCE, not a proved invisible warm-up; the visible consequence of this initialization-only command list needs capture. Constructor capacity is16; no MaxBirds override was found in the bounded46 non-RaceTest XML search. Its effective live value and producer remain UNKNOWN. A nonpositive capacity would make the inspected first-entry access unsafe; the offline tool does not invent a valid zero-capacity initialization.

Each pooled entity is0x7c bytes, named `Burdy%d`, priority byte+48=1. Entity ctor`21e290` registers it with the global entity manager and creates a0x80 en3d carrier at+50. `1af460` creates a0x90 en2d visual (`205bf8`) at entity+4c and applies uniform scale0.1. No bird PSM mesh is assigned to the carrier in this path. `21e620` attaches AI owners and invokes their initialization.

Manager update`1af330` resolves names again and requires **both** non-NULL pointers. It copies XYZ from the first entry of singleton`201350`, at entry+c0/c4/c8, then calls flight burst`1afa20`, flying retirement`1b01f8`, and periodic ground takeoff`1afc88`. It subsequently loops registry entries using count+10 and invokes near-ground takeoff`1afdd8`, converts one pending bird via`1affe0`, then mirrors active carrier translations via`1b0508` when +9c is set. The first-entry distance observer is not substituted with camera position or a `Car0` broker name; the precise live entry identity remains a capture dependency. Constructor Car0..Car3 strings are not read by this update.

For an eligible flight-burst invocation:

1. Free pool, FlightList pointer and nonempty FlightList must exist.
2. Draw `u=U(0.1,1)`, add float32`0.003` to +1c, test `u<clock*0.1`.
3. On success reset the clock, draw `R(0,RndFly)`, cap by free-pool size. Zero is possible.
4. Full nearest XZ selection initially; later scan `[max(0,previous-5),min(count,previous+5))`. Cache the nearest base, add `R(0,3)`, clamp to the source list.
5. Require strict `MinFlyDist² < XZdistance² < MaxFlyDist²`.
6. Pop that many free entities, write **the same selected marker XYZ** into each carrier, enqueue at+68.

`1affe0` converts at most one pending entity per invocation: clear old AI slots, attach0x30 FlyBird in slot0 (`1b0138`), configure bank/animation (`1b0410`), append flying vector. `1b01f8/1b0238` retires a flying entity at horizontal distance **greater than** MaxFlyDist², clears image commands/owners, resets carrier and returns it to the free vector. Equality remains active in this test. Observer positions can affect later direction initialization because pending conversion follows the all-entry loop; they must not be replaced with a synthetic camera implicitly.

The ground vector can move to pending takeoff when an observer is closer than MinMilDist, or through the periodic +24 clock. That clock adds0.001 and tests `U(0.1,1)<clock*0.01`; its random count uses hardcoded10. Miller allocation/attachment`1b0060` and plane-walking code exist, but **UNKNOWN LINK: normal producer that populates grounded birds**. Selected normal update does not call that producer. Ground spawn totals/activation are not inferred.

Destructor`1aec50` clears the five vectors, frees their buffers, nulls list pointers and optionally frees the manager. It does not individually delete registered pooled entities in the traced body. Global entity lifetime, race-reset/retained registry behavior, menu/replay activity and exact scheduler timing remain open. Generic `21f088` virtual update dispatch is reused from AMBIENT1; `/30` does not establish30 live calls per second.
