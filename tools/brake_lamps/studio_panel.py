"""Brake Glow-ON panel for the Qt Material & Glow Studio (Rally Workshop 2.0, ``Material / Glow`` tab).

Mount into a running Workshop window with ``add_to_workshop(window, host)``, or run standalone:

    py -3.11 tools/brake_lamp_studio.py --host <host> --family Trooper [--spec tools/brake_lamps/specs/Trooper.brake_lamps.json]

Viewport: orthographic software view of the car (body grey, OFF lens amber, fitted core/halo coloured by the
penetration heat map: green = visible from all 8 rear views, red = hidden). Left drag orbits, right drag
moves the selected lamp in its lens plane (gizmo), wheel zooms, Shift+wheel changes the normal offset,
Ctrl+click toggles a face in the lamp's lens selection. ``Native preview`` renders the compiled car through
Direct3D 9 with the renderer states of BrakeGlow=0 (PC) and BrakeGlow=1 (PS2).
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets as W

from . import compile as C, preview
from .carmodel import face_ids, load as load_car
from .geometry import view_directions
from .spec import FITS, SOURCES, BODIES, normalise, SpecError


def heat_rgb(hidden, total=8):
    f = hidden / max(total, 1)
    return QtGui.QColor(int(255 * min(1, 2 * f)), int(255 * min(1, 2 * (1 - f))), 40)


class Viewport(W.QWidget):
    faceToggled = QtCore.Signal(object, int, str)   # (lens draw, draw index, face id)
    moved = QtCore.Signal(float, float)              # lens-plane du, dv (metres)
    normalNudged = QtCore.Signal(float)              # mm

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 420)
        self.setMouseTracking(True)
        self.yaw, self.pitch, self.zoom = 0.0, 8.0, 1.0
        self.show_on = True
        self.car = None
        self.fitted = []
        self.selected = None
        self.heat = {}
        self.centre = np.zeros(3)
        self._drag = None

    def set_scene(self, car, fitted, heat, selected):
        first = self.car is None or (car is not None and car is not self.car)
        self.car, self.fitted, self.heat, self.selected = car, fitted, heat, selected
        if first and car is not None:
            self.ids = {d.index: face_ids(d.mesh.positions, d.mesh.triangles) for d in car.draws if d.role in ('body', 'off_glass')}
        if first and car is not None:
            lens = car.mesh('off_glass')
            pts = lens.positions if len(lens.positions) else np.vstack([d.mesh.positions for d in car.draws])
            self.centre = pts.mean(axis=0)
            self.span = float(np.ptp(np.vstack([d.mesh.positions for d in car.draws]), axis=0)[:2].max())
        self.update()

    # camera: looking from behind (-Z) with yaw/pitch, orthographic
    def basis(self):
        yaw, pitch = math.radians(self.yaw), math.radians(self.pitch)
        back = np.array([-math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch)])  # toward camera
        right = np.cross(np.array([0, 1.0, 0]), back)
        right /= np.linalg.norm(right)
        up = np.cross(back, right)
        # The SDK geometry is right-handed: mirror X so lettering/sides read as in game.
        return -right, up, back

    def project(self, p):
        r, u, b = self.basis()
        s = min(self.width(), self.height()) / (self.span * .6) * self.zoom
        d = np.asarray(p) - self.centre
        return np.stack([self.width() / 2 + (d @ r) * s, self.height() / 2 - (d @ u) * s, d @ b], axis=-1)

    def paintEvent(self, _):
        g = QtGui.QPainter(self)
        g.setRenderHint(QtGui.QPainter.Antialiasing)
        g.fillRect(self.rect(), QtGui.QColor('#1b2027'))
        if self.car is None:
            g.drawText(self.rect(), QtCore.Qt.AlignCenter, 'open a car'); return
        polys = []
        lamp_draws = {d.index for d in self.car.draws if d.role in ('on_core', 'on_glow')}
        lens_ids = set()
        if self.selected is not None and self.selected.get('lens'):
            lens_ids = set(self.selected['lens']['faces'])
        for d in self.car.draws:
            if d.index in lamp_draws or d.role == 'hidden_state' or (d.role == 'off_glass_on'):
                continue
            q = self.project(d.mesh.positions)
            ids = self.ids.get(d.index)
            for k, t in enumerate(d.mesh.triangles):
                fid = ids[k] if ids else None
                if fid in lens_ids:
                    col = QtGui.QColor(255, 200, 60)
                elif d.role == 'off_glass':
                    col = QtGui.QColor(150, 60, 50)
                else:
                    col = QtGui.QColor(95, 102, 112)
                polys.append((q[t][:, 2].mean(), q[t], col, None))
        if self.show_on:
            for f in self.fitted:
                for name, layer in (('halo', f.glow), ('core', f.core)):
                    q = self.project(layer.positions)
                    hv = self.heat.get((f.id, name))
                    for k, t in enumerate(layer.triangles):
                        col = heat_rgb(int(hv[k])) if hv is not None else QtGui.QColor(255, 40, 40)
                        if name == 'halo':
                            col.setAlpha(110)
                        # Lamps sit 1-3 mm above the lens: draw them after the surface at equal depth.
                        polys.append((q[t][:, 2].mean() + 1e3, q[t], col, f.id))
        polys.sort(key=lambda p: p[0])
        for _, q, col, _ in polys:
            g.setPen(QtGui.QPen(col.darker(140), .5)); g.setBrush(col)
            g.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y, _ in q]))
        # Gizmo on the selected lamp: lens-plane axes (u red, v green) and normal (blue).
        sel = next((f for f in self.fitted if self.selected and f.id == self.selected['id']), None)
        if sel is not None:
            o = self.project(sel.frame.origin)
            L = .08
            for axis, colour in ((sel.frame.u, '#ff5050'), (sel.frame.v, '#50ff50'), (sel.frame.normal, '#5090ff')):
                e = self.project(sel.frame.origin + axis * L)
                g.setPen(QtGui.QPen(QtGui.QColor(colour), 2.5)); g.drawLine(QtCore.QPointF(o[0], o[1]), QtCore.QPointF(e[0], e[1]))
        g.setPen(QtGui.QColor('#e5b66a'))
        g.drawText(8, 16, f'{"ON (brake)" if self.show_on else "OFF"} | yaw {self.yaw:.0f} pitch {self.pitch:.0f} | '
                          'LMB orbit, RMB move lamp, Shift+wheel normal offset, Ctrl+click lens face')

    def mousePressEvent(self, e):
        if e.modifiers() & QtCore.Qt.ControlModifier and e.button() == QtCore.Qt.LeftButton:
            self.pick(e.position()); return
        self._drag = (e.button(), e.position())

    def mouseMoveEvent(self, e):
        if not self._drag:
            return
        button, start = self._drag
        dx, dy = e.position().x() - start.x(), e.position().y() - start.y()
        self._drag = (button, e.position())
        if button == QtCore.Qt.LeftButton:
            self.yaw = max(-89, min(89, self.yaw - dx * .4)); self.pitch = max(-60, min(80, self.pitch + dy * .4)); self.update()
        elif button == QtCore.Qt.RightButton:
            s = min(self.width(), self.height()) / (self.span * .6) * self.zoom
            self.moved.emit(-dx / s, -dy / s)   # screen right = -u after the mirror, screen up = +v

    def mouseReleaseEvent(self, _):
        self._drag = None

    def wheelEvent(self, e):
        steps = e.angleDelta().y() / 120
        if e.modifiers() & QtCore.Qt.ShiftModifier:
            self.normalNudged.emit(.5 * steps)
        else:
            self.zoom = max(.2, min(40, self.zoom * (1.15 ** steps))); self.update()

    def pick(self, pos):
        best = None
        for d in self.car.draws:
            if d.role not in ('body', 'off_glass') or d.alpha:
                continue
            q = self.project(d.mesh.positions)
            ids = self.ids[d.index]
            for k, t in enumerate(d.mesh.triangles):
                a, b, c = q[t]
                if _inside(pos.x(), pos.y(), a, b, c):
                    z = (a[2] + b[2] + c[2]) / 3
                    if best is None or z > best[0]:
                        best = (z, d, ids[k])
        if best:
            _, d, fid = best
            self.faceToggled.emit('blight' if d.role == 'off_glass' else 'any', d.index, fid)


def _inside(x, y, a, b, c):
    def s(p, q, r):
        return (p[0] - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (p[1] - r[1])
    p = (x, y)
    d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


class BrakeGlowPanel(W.QWidget):
    """Brake Glow-ON authoring panel. ``host``: game host folder (car.dx, textures, PS2 assets, registry)."""

    def __init__(self, host: Path, family: str | None = None, spec_path: Path | None = None, parent=None):
        super().__init__(parent)
        import brake_lamp_sdk as sdk
        self.sdk = sdk
        self.host = Path(host)
        self.resources = sdk.resources(self.host)
        self.spec_path = spec_path
        self.spec = None
        self.fitted = []
        self.raw = None
        self.car = None
        layout = W.QHBoxLayout(self)
        side = W.QVBoxLayout(); layout.addLayout(side, 0)
        self.viewport = Viewport(); layout.addWidget(self.viewport, 1)
        self.family = W.QComboBox(); self.family.setEditable(True)
        for f in ('Mercedes', 'Trooper', 'Rav4', 'Tomcat', 'HeritageNewRav', 'ForesterSTI', 'ImprezaProto', 'LancerEvo4', 'Evo2FourRunner'):
            self.family.addItem(f)
        side.addWidget(QLabel('Car')); side.addWidget(self.family)
        row = W.QHBoxLayout(); side.addLayout(row)
        for text, slot in (('Open json', self.open_spec), ('Auto spec', self.auto_spec), ('Save json', self.save_spec)):
            b = W.QPushButton(text); b.clicked.connect(slot); row.addWidget(b)
        self.lamps = W.QListWidget(); self.lamps.currentRowChanged.connect(self.select); side.addWidget(self.lamps)
        form = W.QFormLayout(); side.addLayout(form)
        self.fields = {}

        def spin(key, lo, hi, step, dec=3):
            s = W.QDoubleSpinBox(); s.setRange(lo, hi); s.setSingleStep(step); s.setDecimals(dec)
            s.editingFinished.connect(self.from_fields); self.fields[key] = s; return s
        self.source = W.QComboBox(); self.source.addItems(SOURCES); self.source.activated.connect(self.from_fields)
        self.fit = W.QComboBox(); self.fit.addItems(FITS); self.fit.activated.connect(self.from_fields)
        self.body = W.QComboBox(); self.body.addItems(BODIES); self.body.activated.connect(self.from_fields)
        form.addRow('Source', self.source); form.addRow('Fit', self.fit); form.addRow('Body set', self.body)
        for axis in 'xyz':
            form.addRow(f'Offset {axis} (m)', spin('offset_' + axis, -.5, .5, .002))
        for axis in 'xyz':
            form.addRow(f'Rotate {axis} (deg)', spin('rot_' + axis, -180, 180, 1, 1))
        for axis in 'xyz':
            form.addRow(f'Scale {axis}', spin('scale_' + axis, .05, 4, .02))
        form.addRow('Normal offset (mm)', spin('normal_offset_mm', -20, 20, .5, 1))
        form.addRow('Fit offset (mm)', spin('offset_mm', .5, 5, .5, 1))
        form.addRow('Halo size', spin('halo_size', .1, 4, .05, 2))
        form.addRow('Halo brightness', spin('halo_brightness', 0, 4, .05, 2))
        self.colour = W.QPushButton('Halo colour'); self.colour.clicked.connect(self.pick_colour); form.addRow(self.colour)
        self.mirror = W.QComboBox(); self.mirror.activated.connect(self.from_fields); form.addRow('Mirror of', self.mirror)
        row = W.QHBoxLayout(); side.addLayout(row)
        self.on = W.QPushButton('OFF / ON'); self.on.setCheckable(True); self.on.setChecked(True); self.on.toggled.connect(self.toggle_on); row.addWidget(self.on)
        b = W.QPushButton('Snap to lens'); b.clicked.connect(self.snap); row.addWidget(b)
        b = W.QPushButton('Re-fit'); b.clicked.connect(self.refit); row.addWidget(b)
        row = W.QHBoxLayout(); side.addLayout(row)
        for text, mode in (('Native BrakeGlow=0 (PC)', 'pc'), ('Native BrakeGlow=1 (PS2)', 'ps2')):
            b = W.QPushButton(text); b.clicked.connect(lambda _=False, m=mode: self.native(m)); row.addWidget(b)
        self.status = W.QPlainTextEdit(); self.status.setReadOnly(True); self.status.setMaximumHeight(140); side.addWidget(self.status)
        self.refit_timer = QtCore.QTimer(self); self.refit_timer.setSingleShot(True); self.refit_timer.timeout.connect(self.refit)
        self.viewport.faceToggled.connect(self.toggle_face)
        self.viewport.moved.connect(self.drag_move)
        self.viewport.normalNudged.connect(self.nudge_normal)
        self.family.activated.connect(lambda _: self.auto_spec())
        if spec_path:
            self.load_spec(Path(spec_path))
        elif family:
            self.family.setCurrentText(family); self.auto_spec()

    # ---------------------------------------------------------------- spec io
    def log(self, text):
        self.status.appendPlainText(text)

    def open_spec(self):
        path, _ = W.QFileDialog.getOpenFileName(self, 'brake_lamps.json', str(Path(__file__).parent / 'specs'), 'Brake lamps (*.json)')
        if path:
            self.load_spec(Path(path))

    def load_spec(self, path: Path):
        self.spec_path = path
        self.set_spec(json.loads(path.read_text(encoding='utf-8')))

    def save_spec(self):
        if self.spec is None:
            return
        path = self.spec_path or Path(__file__).parent / 'specs' / f'{self.spec["family"]}.brake_lamps.json'
        path, _ = W.QFileDialog.getSaveFileName(self, 'Save brake_lamps.json', str(path), 'Brake lamps (*.json)')
        if path:
            Path(path).write_text(json.dumps(normalise(self.spec), indent=1) + '\n', encoding='utf-8')
            self.spec_path = Path(path); self.log(f'saved {path}')

    def auto_spec(self):
        from .autospec import default_spec
        fam = self.family.currentText()
        raw = self.resources.read(f'DataGx/Vehicles/{fam}/car.dx')
        try:
            self.set_spec(default_spec(raw, fam, existing_rows=self.sdk.registry_rows(self.host),
                                       ps2_sources=self.sdk.FORESTER_PS2 if fam == 'ForesterSTI' else None))
        except ValueError as e:
            self.log(str(e))

    def set_spec(self, data):
        self.spec = normalise(data)
        self.family.setCurrentText(self.spec['family'])
        self.raw = self.resources.read(f'DataGx/Vehicles/{self.spec["family"]}/car.dx')
        self.car = load_car(self.raw, self.spec['family'])
        self.lamps.blockSignals(True); self.lamps.clear()
        for l in self.spec['lamps']:
            self.lamps.addItem(f'{l["id"]}  [{l["body"]}]  {l["source"]["kind"]}/{l["fit"]["mode"]}')
        self.lamps.blockSignals(False)
        self.mirror.clear(); self.mirror.addItem('-'); self.mirror.addItems([l['id'] for l in self.spec['lamps']])
        self.lamps.setCurrentRow(0)
        self.refit()

    # ---------------------------------------------------------------- editing
    def current(self):
        i = self.lamps.currentRow()
        return self.spec['lamps'][i] if self.spec and 0 <= i < len(self.spec['lamps']) else None

    def select(self, _row):
        l = self.current()
        if l is None:
            return
        t, f, h = l['transform'], l['fit'], l['halo']
        vals = {**{f'offset_{a}': t['offset'][k] for k, a in enumerate('xyz')}, **{f'rot_{a}': t['rotation'][k] for k, a in enumerate('xyz')},
                **{f'scale_{a}': t['scale'][k] for k, a in enumerate('xyz')}, 'normal_offset_mm': t['normal_offset_mm'],
                'offset_mm': f['offset_mm'], 'halo_size': h['size'], 'halo_brightness': h['brightness']}
        for k, v in vals.items():
            self.fields[k].blockSignals(True); self.fields[k].setValue(v); self.fields[k].blockSignals(False)
        for combo, value in ((self.source, l['source']['kind']), (self.fit, f['mode']), (self.body, l['body']),
                             (self.mirror, (l['mirror'] or {}).get('of', '-'))):
            combo.setCurrentText(value)
        self.redraw()

    def from_fields(self):
        l = self.current()
        if l is None:
            return
        F = {k: s.value() for k, s in self.fields.items()}
        l['transform'].update(offset=[F['offset_x'], F['offset_y'], F['offset_z']], rotation=[F['rot_x'], F['rot_y'], F['rot_z']],
                              scale=[F['scale_x'], F['scale_y'], F['scale_z']], normal_offset_mm=F['normal_offset_mm'])
        l['fit'].update(mode=self.fit.currentText(), offset_mm=F['offset_mm'], max_offset_mm=max(l['fit']['max_offset_mm'], F['offset_mm']))
        l['halo'].update(size=F['halo_size'], brightness=F['halo_brightness'])
        if self.source.currentText() != l['source']['kind']:
            l['source'] = {'kind': self.source.currentText()}
        l['body'] = self.body.currentText()
        m = self.mirror.currentText()
        l['mirror'] = None if m in ('-', l['id']) else {'of': m}
        self.refit()

    def pick_colour(self):
        l = self.current()
        if l is None:
            return
        c = W.QColorDialog.getColor(QtGui.QColor(*l['halo']['color']), self, 'PC halo tint (BrakeGlow=0)')
        if c.isValid():
            l['halo']['color'] = [c.red(), c.green(), c.blue()]; self.refit()

    def drag_move(self, du, dv):
        l = self.current(); f = self.fitted_of(l)
        if l is None or f is None:
            return
        d = f.frame.u * du + f.frame.v * dv
        l['transform']['offset'] = [a + b for a, b in zip(l['transform']['offset'], d)]
        self.select(None)
        self.refit_timer.start(300)   # debounce: one re-fit after the drag pauses

    def nudge_normal(self, mm):
        l = self.current()
        if l is not None:
            l['transform']['normal_offset_mm'] = max(-20, min(20, l['transform']['normal_offset_mm'] + mm)); self.select(None); self.refit()

    def snap(self):
        """Snap to lens: drop the manual transform and project the layer onto the glass again."""
        l = self.current()
        if l is None:
            return
        l['transform'] = {'offset': [0.0, 0.0, 0.0], 'rotation': [0.0, 0.0, 0.0], 'scale': [1.0, 1.0, 1.0], 'normal_offset_mm': 0.0}
        if l['fit']['mode'] in ('plane', 'none') and l['source']['kind'] != 'ps2':
            l['fit']['mode'] = 'project'
        self.select(None); self.refit()

    def toggle_face(self, draw, index, fid):
        l = self.current()
        if l is None or l['mirror']:
            return
        lens = l['lens']
        if draw != lens['draw'] and lens['draw'] == 'blight' and draw == 'any':
            lens['draw'] = 'any'   # adding painted faces around a small OFF lens
        faces = lens['faces']
        faces.remove(fid) if fid in faces else faces.append(fid)
        if not faces:
            faces.append(fid)
        self.log(f'{l["id"]}: lens faces {len(faces)} ({lens["draw"]})')
        self.refit()

    def toggle_on(self, on):
        self.viewport.show_on = on; self.viewport.update()

    def fitted_of(self, l):
        return next((f for f in self.fitted if l and f.id == l['id']), None)

    # ---------------------------------------------------------------- fit / preview
    def refit(self):
        if self.spec is None:
            return
        W.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            donor = self.resources.read('DataGx/Vehicles/Chevyblazer/car.dx')
            spec, self.fitted, ctx = C.fit_spec(self.raw, self.spec, donor_dx=donor)
            self.spec = spec
            self.heat = {}
            for f in self.fitted:
                for name in ('core', 'halo'):
                    raw = f.checks[name]['_raw']
                    tri = raw['triangle']; hv = raw['hidden_views']
                    layer = f.core if name == 'core' else f.glow
                    per = np.zeros(len(layer.triangles))
                    for t in range(len(layer.triangles)):
                        sel = hv[tri == t]
                        per[t] = sel.max() if len(sel) else 0
                    self.heat[(f.id, name)] = per
            msgs = [f'{f.id}: offset {f.offset_mm:.1f} mm, core hidden {f.checks["core"]["normal_hidden"]:.0%}, halo hidden {f.checks["halo"]["normal_hidden"]:.0%}'
                    + ('' if f.checks.get('evaluated', True) else ' (PS2 body: not evaluated)') + (' OK' if f.checks['buried'] == 0 else ' BURIED')
                    for f in self.fitted]
            self.log('\n'.join(msgs))
        except (SpecError, ValueError) as e:
            self.log(f'fit failed: {e}')
        finally:
            W.QApplication.restoreOverrideCursor()
        self.redraw()

    def redraw(self):
        self.viewport.set_scene(self.car, self.fitted, self.heat if hasattr(self, 'heat') else {}, self.current())

    def native(self, mode):
        """Compile the current description and render it through Direct3D 9 (renderer states of the chosen mode)."""
        if self.spec is None:
            return
        W.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            _, compiled = self.sdk.compile_one(self.host, self.spec)
            fam = self.spec['family']
            rt = lambda n: self.resources.read(f'DataGx/Vehicles/{fam}/{n}')
            sup = self.sdk.body_suppress(compiled.car_dx, compiled.rows, fam)
            yaw, pitch = math.radians(self.viewport.yaw), math.radians(self.viewport.pitch)
            direction = (math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch))
            cam = preview.lens_camera(self.car, +1, direction, width=640, height=480)
            out = Path(preview.ROOT / '.research-output/brake-lamps/studio' / f'{fam}-{mode}.png')
            preview.capture(preview.stage(compiled.car_dx, rt, mode, ps2_assets=self.sdk.ps2_assets(self.host), suppress=sup), cam, out)
        except Exception as e:  # shown to the author, never swallowed silently
            self.log(f'native preview failed: {e}'); return
        finally:
            W.QApplication.restoreOverrideCursor()
        dialog = W.QDialog(self); dialog.setWindowTitle(f'Native D3D9 preview - BrakeGlow={0 if mode == "pc" else 1}')
        label = W.QLabel(); label.setPixmap(QtGui.QPixmap(str(out))); W.QVBoxLayout(dialog).addWidget(label); dialog.show()


def QLabel(text):
    return W.QLabel(text)


def add_to_workshop(window, host, family=None):
    """Add the panel as a 'Brake Glow-ON' tab next to Material / Glow in a Rally Workshop main window."""
    tabs = window.findChild(W.QTabWidget)
    panel = BrakeGlowPanel(Path(host), family)
    index = next((i for i in range(tabs.count()) if tabs.tabText(i) == 'Material / Glow'), tabs.count() - 1)
    tabs.insertTab(index + 1, panel, 'Brake Glow-ON')
    return panel
