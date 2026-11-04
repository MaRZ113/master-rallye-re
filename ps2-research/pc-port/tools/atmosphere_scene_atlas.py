"""Private, exact source-draw atlas for scoped static course lighting.
Category labels are an explicit authored allowlist; unknown textures stay native.
Live admission additionally requires exact triangle geometry/prelight/UV hash,
source texture content, current course/owner, shader state and original world matrix.
"""
from pathlib import Path
import argparse,hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3]
# Reviewed original course material labels, not filename substring classification.
POLICY={
 1:('road','road_dirt','f_roadfill','gravel','sandroad','sand_road','asphalt','dirt_left','dirt_right','grass_left','grass_right','f_grass_2_gravel_l','f_grass_2_gravel_r'),
 2:('grass','rock','rock01','rock02','rocks','grass_rock_lft','grass_rock_rht','grass-treedirt','treedirt','cliff','ground','sand','sand01','sand02','mud'),
 3:('pinetree','solidtree1','solidtree2','2dtree1','2dtree2','2dtree3','bush01','bark','treewall1','pinerowleft','pinerowright','tree','tree01','tree02','bush','palmtree'),
 4:('wall','wood_01','gate01','bridge','canalwall','castle01','castle02','castle03','church','f_conc','f_railmisc1','house','house01','house02','building','building01','stonewall','roof')}

# Explicit per-course authoring reviewed against original texture pixels.
# These labels select source records only; live geometry, texture, normal and
# fixed-function admission remain mandatory. Ambiguous boats/tyres/water and
# reflective secondary materials are deliberately absent.
COURSE_POLICY={
 'Turkey2':{
  1:('sandtrack_lft','sandtrack_rht','sandtrack','mudtar_road','mud_road','mud road tran','gravel_road','mud tran b','light brown gravel with track','light brown gravel with track b','new roadblend','end of tar','gravel dirt to road','gravel dirt to road 2'),
  2:('basegrass','dryland','neu rocky','basemud','neu grass to rock','neu grass to rock2','mud_to_grass','grass_to_mud','mud to ro1','mud to ro','light brown gravel','dirt_shrub_blend_rht','dirt_shrub_blend_lft','quad blend','new4way blend','dirt to gravel'),
  3:('green shrub','shrubtrig2','pinerow','plant1','plant2','plant3','plant4'),
  4:('new wall','concrete','i2a_planks2')},
 'Turkey3':{
  1:('gravel_road','mud_road','bedroad','mud road tran','mud tran b','gravel dirt to road','gravel dirt to road 2'),
  2:('neu rocky','base1','basegravel','basemud','mud to ror','mud to ro1','mud to ro','grass to roc1','grass to roc2','grass to grav2','grass to grav','neubeddirt','bed to mud2','bed to wall','bedlef','neubedrig','mutlirgd','g to m2','bed to mud multi','grav to ro1','bed to wall2','bed to mud','bed to mud gravel','neu grass to rock','neu grass to rock2'),
  3:('shrub','shrub1','shrubtrig2','plant1','plant2','plant3','plant4'),
  4:('new wall','i2a_planks2','hut_01','fence_02')}}

def category_for(course,name):
 if course not in ('France1','Turkey2','Turkey3'):return 0
 categories={}
 for policy in (POLICY,COURSE_POLICY.get(course,{})):
  for category,names in policy.items():
   for label in names:
    key=label+'-tga'
    if key in categories and categories[key]!=category:raise ValueError('ambiguous material category '+key)
    categories[key]=category
 return categories.get(name,0)
def sha(b):return hashlib.sha256(b).hexdigest()
def fixed(s,n):
 b=s.encode('ascii')
 if len(b)>=n:raise ValueError('field too long')
 return b+bytes(n-len(b))
def main():
 sys.path.insert(0,str(ROOT/'src'))
 from master_rallye.dx_course import parse_course_dx
 from master_rallye.dxt import parse_dxt
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--registry',type=Path);ap.add_argument('--additional-source',type=Path,action='append',default=[]);a=ap.parse_args()
 out=a.output.resolve();src=a.source.resolve()
 if out.exists() or src==out or src in out.parents or out in src.parents:raise ValueError('fresh disjoint output required')
 out.mkdir(parents=True);entries={};report=[];skipped={}
 for source_variant,src in enumerate([src]+[p.resolve() for p in a.additional_source]):
  for course in ('France1','Turkey2','Turkey3'):
   folder=src/course;path=folder/(course.lower()+'.dx');m=parse_course_dx(path)
   if m.diagnostics.errors or not m.course_render_validated:raise ValueError(f'{course}: draw validation failed')
   textures={};rows=[]
   for draw in m.physical_draws:
    if not draw.index_count:continue
    name=draw.texture_tuple[0];category=category_for(course,name)
    if not category:skipped[name]=skipped.get(name,0)+1;continue
    texture=folder/(name+'.dxt')
    if not texture.exists() and source_variant:texture=a.source.resolve()/course/(name+'.dxt')
    if not texture.exists():continue
    if name not in textures:
     tex=parse_dxt(texture);opaque=bytearray(tex.bgra);opaque[3::4]=bytes([255])*(tex.width*tex.height)
     textures[name]=(tex,sha(tex.bgra),sha(opaque),sha(texture.read_bytes()))
    tex,texture_sha,opaque_sha,file_sha=textures[name];canonical=bytearray();normals=bytearray()
    for index in m.local_indices[draw.index_start:draw.index_start+draw.index_count]:
     v=draw.vertex_base+index;p=m.vertices.positions[v];uv=m.uv_sets[0].values[v];color=m.vertices.colors[v*4:v*4+4]
     canonical+=struct.pack('<3f',*p)+color+struct.pack('<2f',*uv)
     normals+=struct.pack('<3f',*m.vertices.normals[v])
    geometry=sha(canonical);key=(course,geometry,texture_sha)
    row={'course':course,'record':draw.record_path,'category':category,'material':name,'source_shader_contract':'base_noise' if 'noise-tga' in draw.texture_tuple else 'base/modulate (live proof required)','triangles':draw.triangle_count,'expanded_vertices':draw.index_count,'geometry_sha256':geometry,'texture_bgra_sha256':texture_sha,'texture_opaque_bgra_sha256':opaque_sha,'texture_file_sha256':file_sha,'normal_sha256':sha(normals),'normals_source':'original DX normal array; not synthesized lighting/shadows'}
    if key in entries:
     if entries[key][1]!=normals:raise ValueError('ambiguous source normals')
     continue
    entries[key]=(row,normals);rows.append(row)
   report.append({'source_variant':source_variant,'course':course,'source':str(path),'source_sha256':sha(path.read_bytes()),'draw_parser':'complete-disjoint index coverage; structural global/trailing reconstruction not claimed','warnings':m.diagnostics.warnings,'records':rows})
 data=bytearray(struct.pack('<4sII',b'ATS2',1,len(entries)))
 for row,normals in entries.values():
  data+=fixed(row['course'],32)+struct.pack('<II',row['category'],row['expanded_vertices'])+fixed(row['material'],64)+fixed(row['geometry_sha256'],65)+fixed(row['texture_bgra_sha256'],65)+fixed(row['texture_opaque_bgra_sha256'],65)+normals
 (out/'scene.atlas').write_bytes(data)
 (out/'provenance.json').write_text(json.dumps({'schema':1,'evidence':'SOURCE_EXACT_CATEGORY_AUTHORING_LIVE_ADMISSION_REQUIRED','atlas_sha256':sha(data),'records':len(entries),'policy':POLICY,'course_policy':COURSE_POLICY,'sources':report,'unclassified_native':skipped},indent=2)+'\n')
 if a.registry:a.registry.write_text('#pragma once\n// Exact private source atlas produced by tools/atmosphere_scene_atlas.py.\nnamespace gfx2::atmosphere { inline constexpr char kSceneAtlasSha[]=\"'+sha(data)+'\"; inline constexpr unsigned kSceneAtlasRecords='+str(len(entries))+'; }\n')
 print(f'{len(entries)} exact course records; {len(data)} private atlas bytes')
if __name__=='__main__':main()
