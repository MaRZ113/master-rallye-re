# SMA structural packaging

The original Data.sma is ZIP-compatible and has three top-level roots: DataGame, DataGx and DataScene. The Python pack helper accepts exactly these roots, deterministic sorted file order and fixed ZIP timestamps, validates CRC and each member hash, and refuses source overwrite. The optional override map replaces one member while reading all others from the original unpacked tree. The unpack helper rejects extra-root entries and checks CRC before extraction.

The E5 archive was packed from the full unpacked original tree with only Astero/car.dx replaced by E1. It has 7,595 file members; the original ZIP also includes directory entries. E5 is `STRUCTURALLY_VALID`. Original-game acceptance remains `RUNTIME_CONFIRMATION_PENDING`.

The high-level build refuses a full-archive output without ~--sma-root~. It packages all unchanged original members plus the staged overrides. A standalone ~pack-sma~ of a sparse staging tree is only a structurally valid partial archive and is not represented as a complete game replacement.
