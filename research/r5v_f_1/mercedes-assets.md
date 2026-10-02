# Mercedes assets — deferred

Asset audit is intentionally deferred until cleanup P0 and P1 both pass.
There is no Mercedes model package, converted DX resource, collision result,
texture dependency list, or staged override from R5V-F.1.

The post-gate audit must inventory `complete.dx`, `car.dx`, `wheel.dx`, DXT
dependencies, bounds and tag101 collision; record source build, source revision,
conversion/cooker path, output revision and hashes; and use the existing Vehicle
SDK validators. Invalid collision or an unproven conversion route blocks a
Mercedes race candidate. Donor collision must not be described as authentic
Mercedes collision.
