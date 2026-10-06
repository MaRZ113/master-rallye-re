# Vehicle DX importer

The Master Rallye Blender add-on imports one vehicle DX file or all direct DX
children in a vehicle folder. It accepts the observed vehicle revisions 127,
131, and 135. See [Multi-revision vehicle DX import](vehicle-multirevision.md)
for grammar, validation, and corpus evidence.

## Import

Use **File > Import > Master Rallye DX (.dx)** for one resource, or **Master
Rallye Vehicle Folder** for a folder. Enable strict validation to reject
malformed or structurally unsafe geometry. Structurally valid revision-135
files with a different stored index order are imported with a warning after
per-draw oriented triangle equivalence is proven.

Folder import creates one mesh per direct `*.dx` file and labels known roles
from the filename: `car.dx` (RACE BODY), `complete.dx` (PRESENTATION), and
`wheel.dx` (WHEEL TEMPLATE). Other names are imported as AUXILIARY resources.
Each object stores its header revision and validation profile.
The object panel distinguishes structurally valid import from the exact
revision-135 writer profile and disables DX/collision authoring controls for
legacy or order-divergent files.

## Preview and source preservation

All UV sets use the established direct-source-V Blender policy. Preview
textures are resolved beside the source and decoded through the existing DXT
path, including the established vertical PNG row flip. Blender-calculated
display normals are used; source normal values remain available as mesh
attributes and metadata.

Revision-127/131 render-prefix bytes are retained raw. Their material flag
semantics remain unknown, so the preview uses conservative first-texture
materials without revision-135 alpha/helper interpretation. This preview is
not a claim of runtime material parity.

Imports and previews do not write source DX, DXT, sidecar, or game files. The
existing writers remain revision-135 and exact-validation gated; structural
import support for older generations does not imply writer support.
