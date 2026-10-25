# Texture Studio

RGB shows color without transparency. RGBA composites over the checkerboard.
Alpha shows the alpha channel as grayscale. Original compares the imported
baseline with the current working resource.

Mouse wheel zooms around the cursor; pan with the image viewer controls. Actual
size maps one texel to one display pixel. Filtered fractional zoom uses
premultiplied alpha; pixel mode uses nearest-neighbor sampling. Rasterization is
bounded to the viewport. These operations never change native texture bytes.

Whole-texture multipliers and same-size PNG replacement affect all listed
draws using the shared image, including baked logos, decals and glass. Review
the impact warning first. They are different from assigning an existing image
to one surface. PNG replacement preserves the established FEED BGRA orientation
and dimensions. Undo/Restore removes the override.
