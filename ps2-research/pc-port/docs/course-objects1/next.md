# Expansion boundary

After the Turkey3 layer A/B, extend one bounded **static scene model + verified
placement + material** through this asset/transaction path. Keep model-local and
course-world coordinates separate, preserve original transforms/provenance and
check whether PC already has baked equivalent geometry before adding it.

The current schema admits one original landscape-world surface family and one
preview material. A model-local/placed-object schema should be separately
versioned and fail closed for unknown node grammar, transforms, materials or
conditional ownership. Dynamic spline poses, birds and rigid-body controllers
remain independent later work. No physics or population spawning was started.
