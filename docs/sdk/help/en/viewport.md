# 3D viewport and diagnostics

The embedded GPU capture and interactive Previewer share SDK decoding. They are
diagnostics, not proof of identical gameplay rendering or physics.

Interactive navigation: left mouse rotates/selects; middle mouse pans; mouse
wheel zooms. F focuses the selection, Home resets the camera. Keys 1 through 6
select presets. Ctrl+1..6 saves views; Shift+1..6 recalls them.

R reloads generated resources. Tab cycles variants. A switches raw/assembled
wheels. E toggles reflections, B brake state, W wireframe, K culling, Z depth,
L material layer and 0 all layers. F3 toggles diagnostic HUD.

Wheel fitting here is a preview rest pose. It does not tune suspension, handling
or race wheel attachment. Physics and camera profiles remain separate CLI data.

When checking a defect compare race/frontend models, both sides, reflections on
and off, alpha and individual layers. Retain a gameplay test for native damage,
light triggers and draw ordering.
