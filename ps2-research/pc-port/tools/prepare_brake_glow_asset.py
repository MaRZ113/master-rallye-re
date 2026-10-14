"""Extract the verified original PS2 RGB-fade glow into ignored private storage."""
from pathlib import Path
import importlib.util,hashlib
PORT=Path(__file__).resolve().parents[1]
def main():
 spec=importlib.util.spec_from_file_location('asset_common',PORT/'docs/full-coverage/vehicles/audit.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);a.w.verify_inputs(a.PS2);manifest,_=a.t.load_pak(a.PS2/'TNG.PAK');entry=next(e for e in manifest['entries'] if e['path'].upper().endswith('COMMONTEXTURES\\BREAKLIGHTSONGLOW-TGA.GXI'));raw,_=a.t.read_payload(entry,a.PS2/'TNG.000');digest=hashlib.sha256(raw).hexdigest()
 if len(raw)!=1032 or digest!='b6350f92f674bf2b63200ce4bb39c0c26f03fd99856ac0b89e7fc0797861af09':raise ValueError('Canonical glow identity failed')
 target=PORT/'.assets/reflection/PS2BrakeGlow.gxi'
 if target.is_symlink() or target.parent.is_symlink():raise ValueError('Private output link rejected')
 if target.exists() and target.read_bytes()!=raw:raise ValueError('Existing unique asset preserved')
 target.write_bytes(raw);print(digest)
if __name__=='__main__':main()
