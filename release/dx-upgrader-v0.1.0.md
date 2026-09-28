# Master Rallye DX Upgrader v0.1.0

## What it does

Converts supported Master Rallye vehicle DX revision-131 files into the
revision-135 serialization accepted by the verified retail build. No game
files are included.

## Runtime validation

Trooper and Subaru Forester `car.dx`, `complete.dx`, and `wheel.dx` candidates
were loaded successfully in retail. Other corpus results are structural
validation, not individual runtime tests.

## Corpus validation

- 8 vehicle families; 36 DX file instances and 35 unique payloads.
- 20 unique revision-131 payloads converted and strictly validated.
- 10 verified same-source role pairs; all 135 paired draw records matched the
  conversion rule, with zero mismatches.
- All 10 generated candidates differed from official revision 135 only in
  local triangle ordering.

## Compatibility choice

The upgrader preserves the original revision-131 local triangle order. It does
not reproduce the official 9.10.0 triangle optimizer; runtime tests show that
the reorder is unnecessary for the tested Trooper and Forester resources.

## Not included

No game assets, demo files, executable patches, GXM cooker, or DXT converter.

## License

MIT for this project's original code and documentation. Master Rallye and its
game assets remain the property of their respective rights holders.
