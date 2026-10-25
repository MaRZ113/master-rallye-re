"""Blender (headless) contact-sheet builder used by vmesh_preview.py: ``blender -b --python this -- out cols files...``."""
import sys

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
out, cols, files = a[0], int(a[1]), a[2:]
W, H = 480, 270
rows = (len(files) + cols - 1) // cols
sheet = np.ones((rows * H, cols * W, 4), dtype=np.float32)
for i, f in enumerate(files):
    im = bpy.data.images.load(f)
    im.scale(W, H)
    px = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)
    r, c = divmod(i, cols)
    y = (rows - 1 - r) * H
    sheet[y:y + H, c * W:(c + 1) * W] = px
im = bpy.data.images.new("s", cols * W, rows * H, alpha=True)
im.pixels = sheet.ravel()
im.filepath_raw = out
im.file_format = "PNG"
im.save()
