"""Register explicit local projects/families in a private Workshop library.

Optional onboarding helper. Normal users can use the equivalent GUI file pickers.
No bundled paths/assets or guessed stock vehicle identities.
"""
from pathlib import Path
import argparse,json,sys,uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.workshop.service import WorkshopProject,write_json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--project',type=Path,action='append',default=[]);p.add_argument('--family',type=Path,action='append',default=[]);a=p.parse_args()
    workspace=a.workspace.resolve();workspace.mkdir(parents=True,exist_ok=True);path=workspace/'library.json'
    entries=json.loads(path.read_text()) if path.exists() else []
    for project in a.project:
        root=str(WorkshopProject(project).root)
        if root not in entries:entries.append(root)
    for family in a.family:
        source=str(family.resolve())
        if any(WorkshopProject(e).data['source']==source for e in entries):continue
        project=WorkshopProject.create(family,workspace/'projects'/uuid.uuid4().hex[:12],kind='family');entries.append(str(project.root))
    write_json(path,entries);print(json.dumps({'library_entries':len(entries),'workspace':str(workspace)}))

if __name__=='__main__':main()
