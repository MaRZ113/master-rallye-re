"""Create/rebuild independent Source Fidelity and Classic Workshop versions."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.workshop.service import WorkshopProject
from master_rallye.workshop.classic import rebuild_classic,approve_classic


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='operation',required=True)
    for command in ('init','rebuild'):
        a=sub.add_parser(command);a.add_argument('--project',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
        a.add_argument('--style',choices=['Source Fidelity','Classic MR Style'],default='Classic MR Style');a.add_argument('--recipe',type=Path,default=ROOT/'research/vehicles/vsdk4b1/lancer-classic-profile.json');a.add_argument('--stock-root',type=Path)
        a.add_argument('--paint-mode',choices=['preserve_source','regenerate_fields'],help='Override recipe paint policy; decal selection remains independent')
    a=sub.add_parser('approve');a.add_argument('--project',type=Path,required=True);a.add_argument('--report-sha256',required=True)
    a=p.parse_args()
    if a.operation=='approve':
        approve_classic(WorkshopProject(a.project),a.report_sha256);print('Exact Classic report approved for builds');return
    if a.operation=='init' and a.style=='Source Fidelity'and not(a.project/'workshop-project.json').is_file():
        result=WorkshopProject.create(a.project,a.output);print(json.dumps({'project':str(result.root),'style':'Source Fidelity'},indent=2));return
    if (a.project/'workshop-project.json').is_file():project=WorkshopProject(a.project)
    else:
        if a.operation!='init':p.error('rebuild requires an existing Workshop project')
        project=WorkshopProject.create(a.project,a.output.with_name(a.output.name+'-source-import'))
    if a.style=='Source Fidelity':
        if a.output.exists():p.error('Choose a fresh output folder')
        from master_rallye.workshop.classic import source_project
        origin=source_project(project);result=WorkshopProject.create(origin.data['source'],a.output)
        print(json.dumps({'project':str(result.root),'style':'Source Fidelity'},indent=2));return
    if a.stock_root is None:p.error('--stock-root must point to local DataGx/Vehicles')
    c,s,r=rebuild_classic(project,a.recipe,a.stock_root,a.output,paint_mode=a.paint_mode)
    print(json.dumps({'classic':str(c.root),'source_fidelity':str(s.root),'report':c.data['classic_generation'],'before':r['before'],'after':r['after'],'manual_layers':r['manual_layers'],'build':'PENDING_OWNER_REPORT_APPROVAL'},indent=2))


if __name__=='__main__':main()
