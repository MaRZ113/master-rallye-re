"""Qualify a private Classic pilot: exact resources, protected layers and GPU views.

Requires user-owned assets. Does not approve a Classic report or run the game.
"""
import argparse,json,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.classic_style import convert,digest,json_bytes,draw_attributes,draw_material
from master_rallye.workshop.service import WorkshopProject,write_json
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.preview_scene import logical_cases,stage_vehicle
from master_rallye.addon_sdk.native_brakes import validate_brake_scene


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','classic','recipe','stock-root','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--viewer',type=Path);p.add_argument('--exe',type=Path);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=WorkshopProject(a.source);classic=WorkshopProject(a.classic);source.verify_inputs();classic.verify_inputs()
    recipe=json.loads(a.recipe.read_text());resources={n:(source.baseline/n).read_bytes()for n in source.data['inputs']}
    sw=(a.stock_root/recipe['stock_wheel_family']/'wheel.dx').read_bytes();sb=(a.stock_root/recipe['stock_brake_family']/'car.dx').read_bytes()
    from master_rallye.classic_materials import references
    refs=references(recipe,a.stock_root)
    first,report,mapping=convert(resources,recipe,sw,sb,refs);second,r2,map2=convert(resources,recipe,sw,sb,refs)
    assert first==second and json_bytes(report)==json_bytes(r2)and mapping==map2,'Non-deterministic conversion'
    assert all((classic.baseline/n).read_bytes()==raw for n,raw in first.items()),'Candidate differs from reproducible Core output'
    result={'status':'RUNNING','deterministic_all_output_bytes':True,'deterministic_report':True,'comparison':{'before':report['before'],'after':report['after']},'protected':{},'captures':[],'boundary':'Offline DX/DXT, original-instruction CPU replay and real Windows D3D9 captures. No D3D8 gameplay claim.'}
    for model in ('car.dx','complete.dx','wheel.dx'):
        old,new=resources[model],first[model];x,y=parse_dx_bytes(old),parse_dx_bytes(new);gx,gy=source_geometry(x),source_geometry(y)
        assert old[x.trailing.offset:x.collision.unparsed_offset]==new[y.trailing.offset:y.collision.unparsed_offset],'Collision changed'
        if recipe.get('version')==2:
            changed={step['draw']for step in recipe.get('geometry',[])if step['resource']==model}
            if model=='wheel.dx':changed.update(recipe.get('wheel',{}).get('rim_draws',[]))
        else:changed=set(recipe['wheel']['rim_draws'])if model=='wheel.dx'else set(recipe['models'][model]['radial_covers'])|set(recipe['models'][model]['paint_draws'])
        if model=='complete.dx'and recipe.get('wheel'):changed.update(g['draws'][i]for g in recipe['wheel']['embedded_groups']for i in recipe['wheel']['rim_draws'])
        def semantic_owners(role):
            if not isinstance(role,dict)or role.get('enabled',True)is not True:return
            changed.update(role.get('draws',{}).get(model,[]))
            for child in role.get('additional_atlases',[]):semantic_owners(child)
        for role in recipe.get('semantic_materials',{}).values():semantic_owners(role)
        indices=mapping.get(model,{i:i for i in gx});unchanged=[]
        for i,j in indices.items():
            if i not in changed:
                assert draw_attributes(gx[i])==draw_attributes(gy[j]),(model,i,'Unselected geometry changed')
                assert draw_material(x.physical_draws[i])==draw_material(y.physical_draws[j]),(model,i,'Unselected material changed')
                unchanged.append(i)
        cases,_=logical_cases(x);other,_=logical_cases(y)
        assert {indices[i]:v for i,v in cases.items()}==other,'Controller cases changed'
        result['protected'][model]={'unchanged_draws':unchanged,'collision_preserved':True,'logical_switches_preserved':True,'shader_alpha_states_preserved':all(tuple(x.physical_draws[i].flags_0x20)==tuple(y.physical_draws[j].flags_0x20)for i,j in indices.items())}
    brake_groups=[g for g in parse_dx_bytes(first['car.dx']).draw_groups if g.root.group_label=='blight']
    result['native_brakes']=validate_brake_scene(sb,first['car.dx'])if brake_groups else {'status':'NOT PRESENT','boundary':'Source pilot has no native brake controller; automatic importer native features are qualified separately.'}
    assert classic.validate()['status']=='PASS';assert source.validate()['status']=='PASS'
    if a.exe:
        from validate_vehicle_damage_native import validate
        from master_rallye.addon_sdk.mechanical_attachments import build_mechanical_resources
        definition=json.loads((classic.root/'original-mechanical.json').read_text())['definition']
        body=build_mechanical_resources(first['car.dx'],first['wheel.dx'],definition,stock_brake_template=sb)[0]['car.dx']
        native,control,adapted=validate(a.exe.read_bytes(),body);result['native_damage']=native
    if a.viewer:
        si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
        views=[('front',0,5),('rear',180,5),('left',90,5),('right',270,5),('three-quarter',40,15),('top',0,89)]
        for label,project in [('source',source),('classic',classic)]:
            scene=out/(label+'.mrpv');stage_vehicle(project.assets/'car.dx',scene)
            jobs=[(v,'frontend',az,el,[])for v,az,el in views]
            jobs.extend([('race-brake-off','race',140,10,[]),('race-brake-on','race',140,10,['--brake']),('paint-reflection-mask','frontend',40,15,['--material-mode','reflection-mask']),('reflections-off','frontend',40,15,['--no-reflections']),('alpha-base','frontend',140,15,['--material-mode','base']),('wireframe','frontend',40,15,['--wireframe'])])
            for name,model,az,el,extra in jobs:
                path=out/(label+'-'+name+'.bmp');subprocess.run([str(a.viewer.resolve()),'--scene',str(scene),'--source',str(project.assets/'car.dx'),'--capture',str(path),'--model',model,'--azimuth',str(az),'--elevation',str(el),'--zoom','.7',*extra],startupinfo=si,check=True,timeout=60);result['captures'].append({'name':path.name,'sha256':digest(path.read_bytes())})
            wheel=out/(label+'-wheel.mrpv');stage_vehicle(project.assets/'wheel.dx',wheel)
            for name,az in [('outside',270),('oblique',240),('inside',90)]:
                path=out/(label+'-wheel-'+name+'.bmp');subprocess.run([str(a.viewer.resolve()),'--scene',str(wheel),'--source',str(project.assets/'wheel.dx'),'--capture',str(path),'--model','wheel','--azimuth',str(az),'--elevation','5','--zoom','.7'],startupinfo=si,check=True,timeout=60);result['captures'].append({'name':path.name,'sha256':digest(path.read_bytes())})
    result['status']='PASS_OFFLINE_CLASSIC';write_json(out/'validation.json',result);print(result['status'])


if __name__=='__main__':main()
