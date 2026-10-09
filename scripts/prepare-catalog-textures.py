"""Extract observed official floor texture assets without executing the bundles."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('assets',ROOT/'scripts/prepare-catalog-assets.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
out=ROOT/'public/assets/catalog/textures';out.mkdir(exist_ok=True)
used={c['floorType'] for p in (ROOT/'src/case/data').glob('*.json') for c in json.loads(p.read_text())['cells'] if 'floorType' in c};manifest={}
for floor in sorted(used):
 name=a.N.TEXTURES.get(floor)
 if not name:manifest[floor]={'asset':None,'status':'untextured' if floor==9 else 'not-defined-in-official-registry'};continue
 data=a.asset('./textures/'+name)
 if data:(out/name).write_text(data)
 manifest[floor]={'name':name,'asset':'/assets/catalog/textures/'+name if data else None,'status':'available' if data else 'missing-asset'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
