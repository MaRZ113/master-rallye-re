"""Standalone Brake Glow-ON editor (the panel of the Material & Glow Studio). Needs PySide6 and the Vehicle SDK.

py -3.11 tools/brake_lamp_studio.py --host <host> [--family Trooper | --spec tools/brake_lamps/specs/Trooper.brake_lamps.json]
py -3.11 tools/brake_lamp_studio.py --host <host> --workshop <workspace dir>   (Rally Workshop with a Brake Glow-ON tab)
"""
import argparse
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host', type=Path, required=True)
    p.add_argument('--family')
    p.add_argument('--spec', type=Path)
    p.add_argument('--sdk', type=Path, default=TOOLS.parents[1] / 'master-rallye-re-vehicles')
    p.add_argument('--screenshot', type=Path, help='render the window once to a PNG and exit (smoke test)')
    p.add_argument('--workshop', type=Path, help='open Rally Workshop 2.0 (SDK qt_editor) on this workspace and add the tab there')
    p.add_argument('--viewer', type=Path, help='Workshop previewer exe (default: the SDK rally-workshop build)')
    a = p.parse_args()
    sys.path.insert(0, str(a.sdk.resolve() / 'src'))
    from PySide6 import QtCore, QtWidgets as W
    from brake_lamps.studio_panel import BrakeGlowPanel
    app = W.QApplication(sys.argv)
    if a.workshop:
        from master_rallye.workshop.qt_editor import Editor
        from brake_lamps.studio_panel import add_to_workshop
        app.setStyle('Fusion')
        viewer = a.viewer or a.sdk / '.research-output/rally-workshop/bin/mr-vehicle-previewer.exe'
        window = Editor(a.workshop, viewer); window.show()
        panel = add_to_workshop(window, a.host, a.family or 'Trooper')
        if a.spec:
            panel.load_spec(a.spec)
    else:
        window = W.QMainWindow(); window.setWindowTitle('Material & Glow Studio - Brake Glow-ON'); window.resize(1400, 860)
        panel = BrakeGlowPanel(a.host, a.family or 'Trooper', a.spec)
        window.setCentralWidget(panel); window.show()
    if a.screenshot:
        a.screenshot.parent.mkdir(parents=True, exist_ok=True)

        def grab():
            window.grab().save(str(a.screenshot)); app.quit()
        QtCore.QTimer.singleShot(1500, grab)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
