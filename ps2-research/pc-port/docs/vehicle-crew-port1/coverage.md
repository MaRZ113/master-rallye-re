# Integrated vehicle coverage

Source verification and implementation coverage are separate from in-game confirmation. All new crew/fleet/lamp changes below await the user A/B. Previously confirmed X-Trail Mode 1 frontend, race body and wheels remain available.

| PS2 family | PC family | COMPLETE | CAR / crew / wheels | Brake glow |
|---|---|---|---|---|
|ASTERO|Astero|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|BRUNO|Bruno|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|CHEVYBLAZER|ChevyBlazer|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|FORESTER|NONE|NO_VERIFIED_PC_COUNTERPART|No verified PC counterpart|Stock: no complete original-PC geometry+UV join|
|FORKLIFT|forklift|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|No source glow|
|FRONTERA|Frontera|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Stock: no complete original-PC geometry+UV join|
|ICECREAM|IceCream|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|JUMP|Jump|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Stock: no complete original-PC geometry+UV join|
|KAMAZ|Kamaz|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|KANGOO|Kangoo|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|KIASPORTAGE|KiaSportage|Missing primary for explicit shader: node 379852 mode 3|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|LANDCRUISER|LandCruiser|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|MATTSERATI|Mattserati|Unimplemented material mode 2|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Stock: no complete original-PC geometry+UV join|
|MEGANE|megane|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|MOONBUGGY|NONE|NO_VERIFIED_PC_COUNTERPART|No verified PC counterpart|Stock: no complete original-PC geometry+UV join|
|NAVARA|Navara|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|NEWRAV|NewRav|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|PAJERO|Pajero|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|PATROL|Patrol|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|RMONSTER|RMonster|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Stock: no complete original-PC geometry+UV join|
|SEATBUGGY|SeatBuggy|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|SIMMBUGGHINI|Simmbugghini|Unimplemented material mode 2|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|TANK|NONE|NO_VERIFIED_PC_COUNTERPART|No verified PC counterpart|Stock: no complete original-PC geometry+UV join|
|TATA|Tata|Missing primary for explicit shader: node 349913 mode 3|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Stock: no complete original-PC geometry+UV join|
|TERRANO|Terrano|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|UFO|Ufo|Unproved explicit shader: $shader(carbrakelight)|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|WILDCAT|WildCat|Mode 2 implemented; runtime pending|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|WOOLDAND|Forester|Unproved explicit shader: $shader(crashiny)|Stock: per-family current compiled owner + complete crew/interior/conditional suppression not certified|Exact source profile implemented; runtime pending|
|XTRAIL|Xtrail|Mode 2 implemented; runtime pending|X-Trail chassis/parts/wheels retained; new static crew implemented, runtime pending|Exact source profile implemented; runtime pending|

20 COMPLETE profiles, 20 native glow profiles, 29 PS2 families audited. No additional CAR family is claimed as ported. See `fleet/car-candidates.json` for record-level negative controls and `fleet/coverage.md` for authored face counts.

Specific next CAR gate: prove one family's complete current compiled source/owner set and crew/interior suppression partition, then independently certify each native wheel owner/WORLD. PC tag 2 alone is insufficient: it also contains native glow records. Do not reuse X-Trail masks.
