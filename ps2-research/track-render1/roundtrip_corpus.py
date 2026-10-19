"""Round trip of every retail course DX through master_rallye.course_render_writer (W2 step 1)."""
import glob, hashlib, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from master_rallye.course_render_writer import CourseRender
res = {}
for p in sorted(glob.glob('D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Course/*/*.dx')):
    t = time.time(); data = open(p, 'rb').read()
    try:
        r = CourseRender.from_bytes(data, p)
        out = r.serialize()
        res[Path(p).name] = {'identical': out == data, 'bytes': len(data), 'draws': sum(1 for _ in r.draws()), 'batches': len(r.batches), 'uv_sets': len(r.uv_sets), 'seconds': round(time.time() - t, 1)}
    except Exception as e:
        res[Path(p).name] = {'error': f'{type(e).__name__}: {e}'[:200]}
    print(Path(p).name, res[Path(p).name], flush=True)
Path(sys.argv[1]).write_text(json.dumps(res, indent=1))
print(sum(1 for v in res.values() if v.get('identical')), 'of', len(res), 'identical')
