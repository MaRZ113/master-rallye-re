"""Optional PySide6 Widgets pilot; legacy rally_workshop.py remains supported."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
if __name__=='__main__':
    try:from master_rallye.workshop.qt_editor import main
    except ImportError as error:
        raise SystemExit('Use an isolated Python3.11+ environment with the versions in requirements-workshop2.txt: '+str(error))
    raise SystemExit(main())
