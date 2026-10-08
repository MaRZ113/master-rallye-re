# Build and capability compatibility

The current capability profile pins the pristine retail executable SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and size
3,121,214. The capability file declares reserved stock IDs 0..25, supported
addon IDs 26 and 27, class maps, observed class slot limits, and the audited
VehicleRecord/RaceTest layout constants.

The I.0 formula is independent of a literal record count, but runtime-qualified
identity/presentation behavior is only demonstrated for IDs26 and 27. The
compiler rejects IDs outside the selected capability set and reports runtime
qualification independently from schema validity. It does not declare 28 a
generic maximum or infer support for ID28. Extending a capability profile
requires a new static audit and separate human runtime qualification.

Unknown retail hashes, unsupported audio IDs, reserved-ID collisions, class
overflow, family/resource collisions, malformed paths, and unknown policies
fail validation. The capability file is versioned and hashed into every
build manifest.
