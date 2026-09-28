# SFL / FL / SF correlation (R5T-B)

R5T-B did not assign new meaning to SFL. The local `inputs/` corpus contains
no raw `.sfl`, `.fl`, or `.sf` files, and the old-demo TGA visualizations are
not available as source bytes in this phase's inputs. R5T-A's committed
structural analysis remains the current evidence: retail SFL is a 20-byte
header plus `width*height` bytes; scanned older FL/SF candidates use 20-byte
headers plus four bytes per cell. Direct cell correspondence and all unknown
header-field meanings remain unresolved.

The RaceTest XML marker overlay can be viewed with course render geometry, but
it does not register the SFL raster. No origin/spacing/orientation transform
has been inferred from the still-unknown SFL header floats. A normalized
stretch-to-bounds image would be a display assumption, so no such Blender
overlay was added.
