"""Offline stock resource copy-on-write authoring; never installs into retail data."""
import argparse,json
from pathlib import Path
from master_rallye.addon_sdk.stock_project import create,build,conflicts,restore
p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
a=s.add_parser('create');a.add_argument('--source',type=Path,required=True);a.add_argument('--project',type=Path,required=True);a.add_argument('--family',required=True);a.add_argument('--car-id',type=int,required=True)
a=s.add_parser('build');a.add_argument('--project',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
a=s.add_parser('conflicts');a.add_argument('manifests',type=Path,nargs='+')
a=s.add_parser('restore');a.add_argument('--project',type=Path,required=True);a.add_argument('--relative',required=True)
a=p.parse_args();d=vars(a);cmd=d.pop('command')
print(json.dumps(conflicts([json.loads(x.read_text()) for x in d['manifests']]) if cmd=='conflicts' else {'create':create,'build':build,'restore':restore}[cmd](**d),indent=2))
