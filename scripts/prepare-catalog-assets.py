"""Compose local SVGs from the already observed public bundles, without executing JS."""
import json,re,urllib.parse,base64,subprocess,hashlib,importlib.util,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('normalizer',ROOT/'scripts/normalize-catalog.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
APP=Path('/tmp/murdoku-app.js').read_text();GAME=Path('/tmp/murdoku-game.js').read_text();URLS={}
for text in [APP,GAME]:
 values={}
 for k,v in re.findall(r'(?<![\w$])([\w$]+)=("(?:[^"\\]|\\.)*")',text):
  decoded=json.loads(v)
  if decoded.startswith(('data:image/svg','/play/assets/')):values[k]=decoded
 for key,var in re.findall(r'"((?:\./objects/|\./textures/|\.\./\.\./portraits/)[^"]+)":([\w$]+)',text):URLS[key]=values.get(var)
CACHE=ROOT/'public/assets/catalog/.source-cache';CACHE.mkdir(parents=True,exist_ok=True)
def asset(key):
 url=URLS.get(key)
 if not url:return None
 if url.startswith('data:'):return urllib.parse.unquote(url.split(',',1)[1])
 dest=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.svg')
 if not dest.exists():subprocess.run(['curl','-fLsS','--max-time','30','--retry','3','--retry-all-errors','https://murdoku.com'+url,'-o',str(dest)],check=True)
 return dest.read_text()
def layer(data,ident,color=None,transform=''):
 enc=base64.b64encode(data.encode()).decode();f='';defs=''
 if color:
  color=N.color(color);r,g,b=[int(color[i:i+2],16)/255 for i in [1,3,5]]
  defs=f'<filter id="{ident}" color-interpolation-filters="sRGB"><feColorMatrix values="{r} 0 0 0 0 0 {g} 0 0 0 0 0 {b} 0 0 0 0 0 1 0"/></filter>';f=f' filter="url(#{ident})"'
 return defs+f'<g transform="{transform}"><image width="100" height="100" preserveAspectRatio="none" href="data:image/svg+xml;base64,{enc}"{f}/></g>'
def svg(parts):return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'+''.join(parts)+'</svg>'
PALETTES={}
for name,var in [('skin','r0'),('hair','d0'),('clothes','h0')]:PALETTES[name]={int(k):v for k,v in re.findall(r'(\d+):"(#[a-f0-9]+)"',re.search(var+r'=\{([^}]+)\}',APP)[1])}
def run(q):
 sid=N.slug(q);data=json.loads((ROOT/'src/case/data'/(sid+'.json')).read_text());raw=json.loads((ROOT/'sources/catalog'/q['file']).read_text());c=raw['CHARACTERS'];allg={**raw.get('GRID',{}),**c,**raw.get('OBJECT',{})};out=ROOT/'public/assets/catalog'/sid
 for folder in ['objects','portraits']:(out/folder).mkdir(parents=True,exist_ok=True)
 missing=[]
 for o in {o['kind']:o for o in data['objects']}.values():
  oid=o['objectId'];file=N.OBJECTS[oid]['file'];parts=[]
  if file:
   for ix,suffix in enumerate(['','_02']):
    key='./objects/'+file.replace('.svg',suffix+'.svg');a=asset(key)
    if a:parts.append(layer(a,'object'+str(ix),allg.get(f'obj_color_{ix}_{oid}',allg.get(f'obj_color_{"base" if ix==0 else "overlay"}_{oid}'))))
  if not parts and oid==142:parts=['<g/>'];missing.append('unknown_object_142: transparent')
  if not parts and oid==72:parts=['<rect width="100" height="100" fill="#86bfd0"/><path d="M8 30q10 -8 20 0t20 0t20 0t20 0M8 65q10 -8 20 0t20 0t20 0t20 0" fill="none" stroke="#568fa4" stroke-width="2"/>']
  if not parts and oid in [8,33]:parts=['<rect width="100" height="100" fill="#2c3030"/>']
  if not parts:
   missing.append(o['kind']);parts=['<rect x="8" y="8" width="84" height="84" rx="15" fill="#ddd5c8"/><text x="50" y="58" text-anchor="middle" font-size="24" fill="#675c4b">'+str(oid)+'</text>']
  (out/'objects'/(o['kind']+'.svg')).write_text(svg(parts))
 for i,ch in enumerate(data['characters']):
  def n(key):return N.num(c.get(f'char_{key}_{i}'))
  sex='woman' if n('sex') else 'man';body=n('body');theme=n('theme');parts=[]
  def paint(kind):return c.get(f'char_{kind}color_hex_{i}') or PALETTES[kind].get(n(kind+'color'),PALETTES[kind][0])
  for name,number,col in [('hairback',n('hair'),paint('hair')),('body',body,paint('skin')),('clothes',n('clothes'),paint('clothes')),('hair',n('hair'),paint('hair')),('facial',n('facial'),paint('hair')),('hat',n('hat'),None),('accessory',n('accessory'),None)]:
   if name in ['hat','facial','accessory'] and number==0:continue
   folder='hair' if name=='hairback' else name;prefix='wildwest_' if number>=1000 else '';number%=1000;suffix=f'{prefix}back_{number:03}' if name=='hairback' else f'{prefix}{number:03}';key=f'../../portraits/theme-{theme}/{sex}/{folder}/{sex}_{folder}_{suffix}.svg';a=asset(key)
   if not a and name=='hairback':a=asset(f'../../portraits/theme-{theme}/{sex}/hair/{sex}_hair_{prefix}{number:03}_back.svg')
   if not a:
    if name in ['body','clothes','hair']:missing.append(ch['id']+':'+key)
    continue
   sx,sy,dy=1,1,0
   if name!='body' and sex=='man' and body in [1,2]:sx,sy,dy=(1.2 if body==1 else 1.21),1.05,-6 if name=='clothes' else 0
   if name!='body' and sex=='man' and body==3:sx=.9
   if name!='body' and sex=='woman' and body==1:sx,dy=1.15,-8 if name=='clothes' else 0
   parts.append(layer(a,name,col,f'translate({50-50*sx} {dy}) scale({sx} {sy})'))
  (out/'portraits'/(ch['id']+'.svg')).write_text(svg(parts))
 return {'id':sid,'missing':missing}
if __name__=='__main__':
 entries=[q for q in json.loads((ROOT/'sources/catalog/available.json').read_text()) if N.slug(q) not in ['24h-delivery','frontier-town','the-zoo']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  results=[]
  for r in pool.map(run,entries):results.append(r);print(r,flush=True)
 (ROOT/'public/assets/catalog/manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
