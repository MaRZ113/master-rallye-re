"""Versioned Workshop adapter for the shared, immutable-source Classic stage."""
import copy
import json
import shutil
from pathlib import Path
from ..classic_style import convert,digest,json_bytes,rebase_mechanics,draw_attributes,draw_material
from ..dx import parse_dx_bytes
from ..topology_writer import source_geometry
from ..vehicle_project import VehicleProject
from .service import WorkshopProject,write_json,plain_tree


def source_project(project):
    """Always return the original import, never a previous lossy output."""
    seen=set()
    while project.data.get('classic_generation'):
        if str(project.root)in seen:raise ValueError('Classic source cycle')
        seen.add(str(project.root));project=WorkshopProject(project.data['classic_generation']['source_root'])
    project.verify_inputs();return project


def preserve_shadow(before,after,profile):
    """Reuse the existing exact footprint/bounds guard; no shadow tuning."""
    from ..addon_sdk.vehicle_shadow import rebase_unchanged_footprint
    return rebase_unchanged_footprint(before,after,profile)


def _transfer_layers(parent,child,mapping):
    """Reapply exact-compatible overrides; preserve incompatible recipes verbatim."""
    conflicts=[];applied=[]
    child._record()
    previous=None;generation=parent.data.get('classic_generation',{})
    if generation.get('version_style')=='Classic MR Style':
        raw=Path(generation['report']).read_bytes()
        if digest(raw)!=generation['report_sha256']:raise ValueError('Previous Classic ownership report changed')
        previous=json.loads(raw)
    child.data['color_presets']=copy.deepcopy(parent.data.get('color_presets',{}))
    # Store all snapshots independently, including those not currently selected.
    write_json(child.root/'source-manual-layers.json',parent._state())
    for name,edit in parent.data.get('edits',{}).items():
        if child.data['inputs'].get(name)!=parent.data['inputs'].get(name):conflicts.append({'kind':'texture','name':name,'reason':'Classic changed or omitted its immutable texture baseline'});continue
        (child.root/'overrides').mkdir(exist_ok=True)
        shutil.copyfile(parent.root/'overrides'/(edit['output_sha256']+'.dxt'),child.root/'overrides'/(edit['output_sha256']+'.dxt'))
        child.data['edits'][name]=copy.deepcopy(edit);applied.append({'kind':'texture','name':name})
    for model,edits in parent.data.get('surfaces',{}).items():
        a,b=(parse_dx_bytes((p.baseline/model).read_bytes())for p in(parent,child));ga,gb=source_geometry(a),source_geometry(b)
        old_to_source=None
        if previous and model in previous['geometry']:
            if parent.data['inputs'][model]!=previous['after']['models'][model]['sha256']:raise ValueError('Previous Classic baseline differs from its ownership report')
            old_to_source={int(new):int(old)for old,new in previous['geometry'][model]['draw_map'].items()}
        for old,edit in edits.items():
            old=int(old);source_id=old_to_source.get(old)if old_to_source is not None else old
            target=mapping[model].get(source_id)if model in mapping else source_id
            if target is None:conflicts.append({'kind':'surface','model':model,'draw':old,'reason':'Its original source owner was omitted by Classic'});continue
            if any(child.data['inputs'].get(stem+'.dxt')!=parent.data['inputs'].get(stem+'.dxt')or stem+'.dxt'not in child.data['inputs']for stem in edit.get('bindings',{}).values()):conflicts.append({'kind':'surface','model':model,'draw':old,'reason':'Manual binding target changed or was omitted by Classic'});continue
            if target not in gb or draw_attributes(ga[old])!=draw_attributes(gb[target])or draw_material(a.physical_draws[old])!=draw_material(b.physical_draws[target]):conflicts.append({'kind':'surface','model':model,'draw':old,'reason':'Classic changed geometry, texture binding or material ownership'});continue
            patch={**edit,'draw_id':target};child.data.setdefault('surfaces',{}).setdefault(model,{})[str(target)]=patch;applied.append({'kind':'surface','model':model,'old_draw':old,'new_draw':target})
    for name,region in parent.data.get('paint_regions',{}).items():
        texture=region['texture']
        if child.data['inputs'].get(texture)!=parent.data['inputs'].get(texture):conflicts.append({'kind':'paint_region','name':name,'reason':'Classic changed or omitted the texture baseline'});continue
        mask=parent.root/'paint-masks'/(region['mask_sha256']+'.png')
        if not mask.exists():conflicts.append({'kind':'paint_region','name':name,'reason':'Qualified mask file unavailable'});continue
        child.register_paint_region(name,texture,mask,region['evidence']);applied.append({'kind':'paint_region','name':name})
    if parent.data.get('crew'):conflicts.append({'kind':'crew','reason':'Original exact-hash vertex selectors retained in source-manual-layers.json; requalification required for Classic topology'})
    if parent.data.get('shadow'):conflicts.append({'kind':'shadow','reason':'Author controls retained in parent and source-manual-layers.json; inspect the new emitted body in Shadow Studio before reapplying. Original donor profile is separately rebased by the qualified footprint guard.'})
    child.materialize();child.save()
    return {'applied':applied,'conflicts':conflicts,'preserved_original':str(parent.root),'saved_layers':'source-manual-layers.json'}


def rebuild_classic(parent,recipe_path,stock_root,output,*,material_roles=None,paint_mode=None):
    """Create two buildable variants, leaving source and owner edits untouched."""
    parent.verify_inputs();origin=source_project(parent);output=plain_tree(output).resolve()
    if origin.data['kind']!='addon':raise ValueError('Classic conversion currently requires a qualified imported SDK addon')
    if output.exists():raise ValueError('Classic rebuild requires a fresh version folder')
    if output.is_relative_to(origin.root)or output.is_relative_to(parent.root):raise ValueError('Classic output must be outside existing source/Classic projects')
    recipe=json.loads(Path(recipe_path).read_text(encoding='utf-8'));stock_root=plain_tree(stock_root).resolve()
    if paint_mode is not None:
        if paint_mode not in ('preserve_source','regenerate_fields'):raise ValueError('Unknown Classic paint mode')
        if recipe.get('version')==2:
            if paint_mode!='preserve_source':raise ValueError('Semantic recipe preserves its source colorway; use a separate qualified Paint layer')
        else:recipe['paint']['mode']=paint_mode
    import re
    for key in ('stock_wheel_family','stock_brake_family'):
        if not isinstance(recipe[key],str)or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',recipe[key]):raise ValueError('Reference family must be a local MR family name')
    if material_roles is not None:
        if set(material_roles)!={'tyres','glass'} or any(type(v)is not bool for v in material_roles.values()):raise ValueError('Invalid Classic role selection')
        for role,enabled in material_roles.items():
            if role in recipe.get('semantic_materials',{}):recipe['semantic_materials'][role]['enabled']=enabled
    stock_wheel=(stock_root/recipe['stock_wheel_family']/'wheel.dx').read_bytes();stock_brake=(stock_root/recipe['stock_brake_family']/'car.dx').read_bytes()
    resources={n:(origin.baseline/n).read_bytes()for n in origin.data['inputs']}
    from ..classic_materials import references
    converted,report,mapping=convert(resources,recipe,stock_wheel,stock_brake,references(recipe,stock_root))
    original_spec=json.loads((origin.root/'original-author.json').read_text())
    donor=VehicleProject.load(origin.working/'vehicle-project.json').source_vehicle_dir
    output.mkdir(parents=True)
    write_json(output/'recipe.json',recipe)
    # Source Fidelity is the original import, with its own editable author copy.
    author=output/'source-author';shutil.copytree(origin.working,author)
    origin.audio_restore_author_baseline(author)
    origin.vehicle_restore_author_baseline(author)
    write_json(author/'vehicle-project.json',original_spec)
    for immutable,name in [('original-mechanical.json','mechanical-attachments.json'),('original-shadow.json','shadow-profile.json')]:
        if (origin.root/immutable).exists():shutil.copyfile(origin.root/immutable,author/name)
    fidelity=WorkshopProject.create(author,output/'source-fidelity')
    fidelity.audio_inherit(parent)
    fidelity.vehicle_inherit(parent)
    author=output/'classic-author';shutil.copytree(origin.working,author)
    origin.audio_restore_author_baseline(author)
    origin.vehicle_restore_author_baseline(author)
    generated=output/'generated';generated.mkdir()
    for name,raw in converted.items():(generated/name).write_bytes(raw)
    # Retain the read-only donor grammar as validation templates, separate from
    # the converted candidate. Ship only its texture dependencies and the new
    # referenced closure, rather than all discarded GT4 atlases.
    source=output/'source'/donor.name;source.mkdir(parents=True)
    from ..assets import AssetResolver
    resolver=AssetResolver(donor)
    for f in donor.glob('*.dx'):
        shutil.copyfile(f,source/f.name)
        for d in parse_dx_bytes(f.read_bytes()).physical_draws:
            for stem in d.texture_tuple:
                if stem.casefold()!='null':
                    texture=resolver.resolve_texture(stem)
                    if texture is None:raise ValueError('Missing donor template dependency')
                    shutil.copyfile(texture,source/texture.name)
    for n,v in converted.items():
        if n.endswith('.dxt'):(source/n).write_bytes(v)
    spec=copy.deepcopy(original_spec);spec['source_vehicle_dir']=str(source);spec['texture_edits']={};spec['texture_replacements']={}
    spec['resources']={n:{'source_sha256':digest((source/n).read_bytes()),next((k for k in ('native_brake_scene_candidate','native_state_scene_candidate')if n=='car.dx'and k in original_spec['resources'].get(n,{})),'scene_candidate'):str(generated/n)}for n in('car.dx','complete.dx','wheel.dx')}
    write_json(author/'vehicle-project.json',spec)
    if (origin.root/'original-mechanical.json').exists():
        from ..addon_sdk.mechanical_attachments import build_mechanical_resources
        old=json.loads((origin.root/'original-mechanical.json').read_text());new=copy.deepcopy(old)
        new['definition']=rebase_mechanics(resources['car.dx'],converted['car.dx'],old['definition'],mapping['car.dx'])
        write_json(author/'mechanical-attachments.json',new)
        a=build_mechanical_resources(resources['car.dx'],resources['wheel.dx'],old['definition'],stock_brake_template=stock_brake)[0]
        b=build_mechanical_resources(converted['car.dx'],converted['wheel.dx'],new['definition'],stock_brake_template=stock_brake)[0]
        if any(a[n]!=b[n]for n in a if n!='car.dx'):raise ValueError('Classic altered protected mechanical resources')
        report['protected_mechanics']={n:digest(a[n])for n in a if n!='car.dx'}
        if (origin.root/'original-shadow.json').exists():
            old_shadow=json.loads((origin.root/'original-shadow.json').read_text());new_shadow=preserve_shadow(a['car.dx'],b['car.dx'],old_shadow)
            write_json(author/'shadow-profile.json',new_shadow);report['shadow']={'before':old_shadow,'after':new_shadow,'reason':'existing strict unchanged footprint and native bounds rebase; parameters unchanged'}
    classic=WorkshopProject.create(author,output/'classic')
    # New versions remain editable, but old lossy output never becomes a source.
    classic.data['appearance']='Classic MR Style'
    classic.audio_inherit(parent)
    report['vehicle_authoring']=classic.vehicle_inherit(parent)
    report['manual_layers']=_transfer_layers(parent,classic,mapping)
    report['protected_author_files']={f.name:digest(f.read_bytes())for f in author.iterdir()if f.is_file()and f.name in('addon.json','physics-profile.json','audio-profile.json','ui-assets.json','camera-profile.json')}
    report_path=output/'classic-report.json';report_path.write_bytes(json_bytes(report))
    links={'Source Fidelity':str(fidelity.root),'Classic MR Style':str(classic.root)}
    for p,style in ((classic,'Classic MR Style'),(fidelity,'Source Fidelity')):
        p.data['appearance']=style;p.data['style_versions']=links;p.data['build_settings']=copy.deepcopy(parent.data.get('build_settings',{}))
        p.data['classic_generation']={'source_root':str(origin.root),'recipe':str(output/'recipe.json'),'report':str(report_path),'report_sha256':digest(report_path.read_bytes()),'approved_report_sha256':None,'version_style':style}
        p.save()
    return classic,fidelity,report


def approve_classic(project,report_sha256):
    g=project.data.get('classic_generation')
    if not g or digest(Path(g['report']).read_bytes())!=g['report_sha256']or report_sha256!=g['report_sha256']:raise ValueError('Review the current exact Classic report before approval')
    g['approved_report_sha256']=report_sha256;project.save()


def require_classic_approval(project):
    g=project.data.get('classic_generation')
    if g and g['version_style']=='Classic MR Style':
        if digest(Path(g['report']).read_bytes())!=g['report_sha256']or g.get('approved_report_sha256')!=g['report_sha256']:raise ValueError('Classic build blocked: preview and explicitly approve its exact conversion report first')
