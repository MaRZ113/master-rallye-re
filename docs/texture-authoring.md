# Texture authoring (R4E)

Master Rallye DXT is a 20-byte header followed by bottom-up BGRA32 pixels. `export-texture` makes an upright RGBA8 PNG. `replace-texture` accepts a noninterlaced RGBA8 PNG of the original dimensions, preserves the entire header, reverses PNG rows independently of the Blender/glTF UV policy, and writes a new DXT. It requires the source SHA-256 and refuses to overwrite its inputs.

Example:
`py -3 tools/mrtool.py export-texture original.dxt --output edit.png`
`py -3 tools/mrtool.py replace-texture original.dxt edit.png --source-sha256 HASH --output staged.dxt`

The Blender panel offers export, validate, replace, and show-users operations for the selected primary material texture. Set an MR staging directory before replacement. No operation edits the original game DXT. Use `texture-users VEHICLE_DIR texture.dxt` before editing: one DXT can drive body and helmets or several chrome parts. Normal glass and active brake-glow alpha have human runtime support; arbitrary dimension changes are outside safe mode.
