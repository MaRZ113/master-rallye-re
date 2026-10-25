"""Launch the local Windows Rally Workshop application."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
if __name__=='__main__':
    try:
        from master_rallye.workshop.gui import main
        main()
    except Exception as e:
        import ctypes,traceback
        error=traceback.format_exc();folder=Path(__file__).resolve().parents[1]/'.research-output/rally-workshop';folder.mkdir(parents=True,exist_ok=True);(folder/'startup-error.txt').write_text(error,encoding='utf-8')
        if sys.platform=='win32':ctypes.windll.user32.MessageBoxW(None,str(e)+'\n\nSee .research-output/rally-workshop/startup-error.txt','Rally Workshop',0x10)
        raise
