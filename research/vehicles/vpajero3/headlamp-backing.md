# Pajero front backing cleanup

The previous explicit MR housing approximation joined source glass and lens bounds into an axis-aligned box. Four sidewalls per lamp were not constrained to the sloping front fascia contour. These generated surfaces could therefore show as flat black protrusions from oblique views; they are not recovered GT4 body polygons.

The approved replacement opts into `source_housings[].mode = "rear_cap"`. It retains the rear black plane behind each lamp and removes the four generated box sidewalls. The existing wheelwell keepout, source lens, glass, UVs, reflections and textures remain unchanged. Default `open_box` behavior remains compatible for existing profiles; mode validation rejects unknown values.

Each body model loses 16 generated triangles: two rear caps now contain four triangles instead of twenty housing triangles. This is a documented MR approximation, not a claim to recovered GT4 housing geometry.

Private evidence: `.research-output/vehicles/vpajero3/build-rear-cap/conversion-report.json`, `cap-left.bmp`, `cap-right.bmp`, `source-profile-rear-cap.json`. Both front-oblique preview captures were inspected: symmetric backing remains, with no projecting sidewall. Gameplay views still require human confirmation.

Validation: three synthetic keepout/housing tests pass, covering unchanged source data, default output, rear-only planar output, source hash rejection, missing selectors, morph rejection and invalid modes. Both converted body DX files pass structural validation; wheel SHA remains `51a7f705a2f940568860580b2b6e22172278c5a9d48341703d6c2839becd46fc`.
