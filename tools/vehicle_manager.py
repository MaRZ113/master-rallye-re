"""Vehicle SDK entry point for the integrated native Vehicle Manager."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye.workshop.roster.vehicle_manager import main
if __name__=='__main__':
    if '--qt' in sys.argv:
        import argparse
        from PySide6 import QtWidgets as W
        from master_rallye.workshop.qt_roster import RosterDialog
        from master_rallye.workshop.qt_editor import STYLE
        p=argparse.ArgumentParser();p.add_argument('--qt',action='store_true');p.add_argument('--game',type=Path)
        a=p.parse_args();app=W.QApplication([]);d=RosterDialog();d.setStyleSheet(STYLE)
        if a.game:d.folder.setText(str(a.game.resolve()));d.open()
        d.show();raise SystemExit(app.exec())
    main()
