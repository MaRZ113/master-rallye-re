"""Private reversible ATMOSPHERE2 candidate packaging, never deployment/publication."""
from pathlib import Path
import argparse,hashlib,json,re,shutil
PORT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--sky',type=Path,required=True);ap.add_argument('--atlas',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 report_path=PORT/'dist/current/build-report.json';r=json.loads(report_path.read_text())
 for name,digest in r['ps2_source_sha256'].items():
  if sha(PORT/name)!=digest:raise ValueError('stale source '+name)
 for name,digest in r['patch_sha256'].items():
  if sha(PORT/'overlay/patches'/name)!=digest:raise ValueError('stale patch '+name)
 dll=PORT/'.build/ps2-enabled/Release/d3d8.dll'
 if sha(dll)!=r['builds']['ps2-enabled']['dll_sha256']:raise ValueError('DLL/report mismatch')
 sky=json.loads((a.sky/'provenance.json').read_text());atlas=json.loads((a.atlas/'provenance.json').read_text())
 if sha(a.atlas/'scene.atlas')!=atlas['atlas_sha256']:raise ValueError('atlas/provenance mismatch')
 registry=(PORT/'renderer/atmosphere_scene_registry.hpp').read_text()
 identity=re.search(r'kSceneAtlasSha\[\]="([0-9a-f]{64})"',registry)
 count=re.search(r'kSceneAtlasRecords=(\d+)',registry)
 if not identity or identity[1]!=atlas['atlas_sha256'] or not count or int(count[1])!=atlas['records']:
  raise ValueError('atlas does not match compiled DLL source registry')
 out=a.output.resolve()
 if out.exists():raise ValueError('fresh output required')
 out.mkdir(parents=True);runtime=out/'runtime-overlay';runtime.mkdir();shutil.copy2(dll,runtime/'d3d8.dll')
 assets=runtime/'Atmosphere2';assets.mkdir();shutil.copy2(a.atlas/'scene.atlas',assets/'scene.atlas');shutil.copy2(a.atlas/'provenance.json',assets/'scene-provenance.json');shutil.copy2(a.sky/'provenance.json',assets/'sky-provenance.json')
 for course in sky['courses']:
  dest=assets/'sets'/course['course'];dest.mkdir(parents=True)
  for item in course['resources']:
   source=a.sky/'sets'/course['course']/(item['name']+'.dxt')
   if sha(source)!=item['sha256'] or item['alpha_sha256']!=item['native_alpha_sha256']:raise ValueError('sky source/alpha mismatch')
   shutil.copy2(source,dest/source.name)
 profiles=out/'profiles';profiles.mkdir();stock=(PORT/'Atmosphere.ini').read_text();original=stock.replace('Enabled=0','Enabled=1').replace('SkyPreset=Auto','SkyPreset=3')
 original+='\nLightingPreset=Original\nSceneAtlas=Atmosphere2/scene.atlas\nCustomSkyUScale=1\nLightingStrength=1\nFogEnabled=0\nSunDisk=0\nSunHalo=0\n'
 (profiles/'original.ini').write_text(original);(profiles/'disabled-classic.ini').write_text(stock);(profiles/'native-auto.ini').write_text(original.replace('SkyPreset=3','SkyPreset=Auto'))
 for course in sky['courses']:
  fog='0x'+''.join(f'{v:02x}' for v in course['fog_rgb'])
  base=original.replace('CustomSet=\n','CustomSet=Atmosphere2/sets/'+course['course']+'\n').replace('CustomSkyUScale=1','CustomSkyUScale=0.5')
  (profiles/(course['course']+'-sky-only.ini')).write_text(base)
  golden=base.replace('WorldLighting=0','WorldLighting=1').replace('LightingPreset=Original','LightingPreset=GoldenHour').replace('FogEnabled=0','FogEnabled=1')+'FogColor='+fog+'\nFogStrength=1\nExposure=1.05\nAmbientStrength=0.8\nAmbientR=0.62\nAmbientG=0.70\nAmbientB=0.88\nSunlightStrength=0.95\nSunlightR=1.4\nSunlightG=1.02\nSunlightB=0.64\nSunDirX=-0.65\nSunDirY=0.45\nSunDirZ=0.61\n'
  (profiles/(course['course']+'-golden-hour.ini')).write_text(golden)
  if course['course']=='r_deepforest':
   shutil.copy2(profiles/(course['course']+'-golden-hour.ini'),runtime/'Atmosphere.ini')
   (profiles/'golden-world-only.ini').write_text(golden.replace('CustomSet=Atmosphere2/sets/r_deepforest','CustomSet='))
   (profiles/'scene-diagnostic.ini').write_text(golden.replace('CustomSet=Atmosphere2/sets/r_deepforest','CustomSet=')+'SceneDiagnostics=1\n')
   (profiles/'sun-depth-diagnostic.ini').write_text(golden.replace('SunDisk=0','SunDisk=1').replace('SunHalo=0','SunHalo=1').replace('SunFlare=0','SunFlare=1'))
 (profiles/'day.ini').write_text(original.replace('WorldLighting=0','WorldLighting=1').replace('LightingPreset=Original','LightingPreset=Day')+'Exposure=1\n')
 rollback=out/'rollback';rollback.mkdir();bl1=PORT.parents[1]/'.research-output/atmosphere-bl1/candidate-first-load-v2/d3d8.dll'
 if sha(bl1)!='f2b51e0d41adeadf245bbd87c2e5f6362eb9b5324bfef5eae934bfdc0f9717ba':raise ValueError('BL1 rollback identity mismatch')
 shutil.copy2(bl1,rollback/'d3d8.dll');shutil.copy2(profiles/'original.ini',rollback/'Atmosphere.ini')
 shutil.copy2(report_path,out/'build-report.json')
 (out/'RUN_TEST_RU.md').write_text("""# ATMOSPHERE2: отдельный тестовый кандидат, RUNTIME_PENDING

Это новая source-bound версия, не candidate-verified. Начать с France1 PS2-Off.
1. Закрыть игру. Сохранить текущие d3d8.dll, Atmosphere.ini, PS2Port.ini и существующий
   каталог Atmosphere2 (если есть) в отдельную резервную папку Atmo-copy.
2. Из runtime-overlay скопировать d3d8.dll и каталог Atmosphere2 в корень Atmo-copy.
   EXE, архивы, сохранения, dinput8.dll и MRRRenderer.ini не менять. PS2Port.ini
   оставить прежним Baseline/PS2-Off; принятые отражения проверим отдельным проходом.
3. profiles/original.ini -> Atmosphere.ini. Новый процесс, France1, тот же автомобиль,
   камера, точка на старте: F10 + локальный скриншот; закрыть.
4. profiles/r_deepforest-golden-hour.ini -> Atmosphere.ini. Новый процесс France1:
   первая гонка F10/скриншот -> Restart F10 -> меню/France1 F10 -> закрыть.
5. profiles/r_grandvalley-golden-hour.ini -> Atmosphere.ini. Новый процесс France1:
   F10/локальный скриншот -> закрыть. Написать «Сделал»; нужны новые логи Atmo-copy.

Оба пресета используют нативный Cloud3 как защищённый base-контракт BL1. Atlas
содержит точные исходные draw records France1/Turkey2/Turkey3. Неизвестные записи,
неподтверждённые transform/материалы и специальные проходы остаются native.
Второй reflection pass не создаётся, mapping/Reflection4/VehicleLighting1 не меняются.
Прямой цвет кузова пока исключён: сначала отдельно проверяется влияние окружения.
SunDisk/Halo/Flare не рисуются без current-frame occlusion; отдельный diagnostic
профиль пишет причину подавления. Здесь нет готовой ночи, фар или динамических теней.

После первого разбора — такие же Original/Golden сравнения Turkey2/Turkey3, затем
MSAA/Reset/FOV/FreeCam и отдельно PS2-on/отражения/трава/вода/HUD/glass/glow/props.
Исходные sky-only/world-only/Day/Auto/Disabled профили помогают разделять причины.
Числа Exposure/Ambient/Sunlight регулируют только доказанные материалы, не экран.

Откат: закрыть игру и вернуть сохранённые DLL/INI. rollback/d3d8.dll — точный BL1 v2;
rollback/Atmosphere.ini — Original, без новых эффектов. Не удалять чужие файлы:
добавленные ресурсы Atmosphere2 при выключении просто не используются.
""",encoding='utf-8')
 manifest={'status':'OFFLINE_VALIDATED_RUNTIME_PENDING','dll_sha256':sha(dll),'source_head':r['current_head'],'files':{p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(out,sha(dll))
if __name__=='__main__':main()
