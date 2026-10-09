"""Extract only this case's SVG assets from observed public bundles; never execute bundles."""
import re,json,urllib.parse,pathlib,base64,hashlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
app=pathlib.Path('/tmp/murdoku-app.js').read_text(); game=pathlib.Path('/tmp/murdoku-game.js').read_text()
raw=json.loads((root/'sources/24h-delivery.json').read_text()); records=[]
def literal(s,var):
 m=re.search(r'(?<![\w$])'+re.escape(var)+r'=("(?:[^"\\]|\\.)*")',s)
 if not m: raise ValueError(var)
 return json.loads(m[1])
def asset(s,key):
 m=re.search('"'+re.escape(key)+r'":([\w$]+)',s)
 if not m:return None
 v=literal(s,m[1]); records.append({'key':key,'source':v[:110] if v.startswith('data:') else 'https://murdoku.com'+v})
 data=urllib.parse.unquote(v.split(',',1)[1]) if v.startswith('data:') else subprocess.check_output(['curl','-fLsS','--max-time','25','--retry','2','--retry-all-errors','https://murdoku.com'+v]).decode()
 if '<svg' not in data:raise ValueError(key)
 return data
for kind,oid in [('bed',6),('chair',2),('table',4),('carpet',5),('box',42),('plant',1),('shrub',37)]:
 layers=[]
 for layer,suffix in enumerate(['','_02']):
  data=asset(app,f'./objects/obj_{kind}{suffix}.svg')
  if not data:continue
  color=int(float(raw['OBJECT'][f'obj_color_{layer}_{oid}']))
  rr,gg,bb=(color&255)/255,((color>>8)&255)/255,((color>>16)&255)/255
  encoded=base64.b64encode(data.encode()).decode()
  layers.append(f'<filter id="color{layer}" color-interpolation-filters="sRGB"><feColorMatrix values="{rr} 0 0 0 0 0 {gg} 0 0 0 0 0 {bb} 0 0 0 0 0 1 0"/></filter><image href="data:image/svg+xml;base64,{encoded}" width="100" height="100" preserveAspectRatio="none" filter="url(#color{layer})"/>')
 (root/f'public/assets/objects/{kind}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'+''.join(layers)+'</svg>')
palettes={}
for kind,var in [('skin','r0'),('hair','d0'),('clothes','h0')]:
 body=re.search(var+r'=\{([^}]+)\}',app)[1];palettes[kind]={int(k):v for k,v in re.findall(r'(\d+):"(#[a-f0-9]+)"',body)}
c=raw['CHARACTERS']
for i,ident in enumerate('ABCDEV'):
 n=lambda k:int(float(c.get(f'char_{k}_{i}',0)))
 sex='woman' if n('sex') else 'man'; body=n('body'); theme=n('theme'); parts=[]
 for layer,number,color in [('hairback',n('hair'),palettes['hair'][n('haircolor')]),('body',body,palettes['skin'][n('skincolor')]),('clothes',n('clothes'),palettes['clothes'][n('clothescolor')]),('hair',n('hair'),palettes['hair'][n('haircolor')]),('facial',n('facial'),palettes['hair'][n('haircolor')]),('hat',n('hat'),None),('accessory',n('accessory'),None)]:
  if layer in ['hat','facial','accessory'] and number==0:continue
  folder='hair' if layer=='hairback' else layer
  suffix=f'back_{number:03}' if layer=='hairback' else f'{number:03}'
  data=asset(game,f'../../portraits/theme-{theme}/{sex}/{folder}/{sex}_{folder}_{suffix}.svg')
  if not data and layer=='hairback':data=asset(game,f'../../portraits/theme-{theme}/{sex}/hair/{sex}_hair_{number:03}_back.svg')
  if not data:continue
  encoded=base64.b64encode(data.encode()).decode(); filt=''; definition=''
  if color:
   r,g,b=[int(color[j:j+2],16)/255 for j in [1,3,5]]
   definition=f'<filter id="{layer}" color-interpolation-filters="sRGB"><feColorMatrix values="{r} 0 0 0 0 0 {g} 0 0 0 0 0 {b} 0 0 0 0 0 1 0"/></filter>';filt=f' filter="url(#{layer})"'
  sx,sy,dy=1,1,0
  if layer!='body' and sex=='man' and body==2:sx,sy,dy=1.21,1.05,-6 if layer=='clothes' else 0
  transform=f'translate({50-50*sx} {dy}) scale({sx} {sy})'
  parts.append(f'{definition}<g transform="{transform}"><image width="100" height="100" preserveAspectRatio="xMidYMin meet" href="data:image/svg+xml;base64,{encoded}"{filt}/></g>')
 (root/f'public/assets/portraits/{ident}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'+''.join(parts)+'</svg>')
(root/'sources/manifest.json').write_text(json.dumps({'source':'https://murdoku.com/play_puzzles/en/puzzle-24h-delivery-easy.json','retrieved':'2026-10-07','sha256':hashlib.sha256((root/'sources/24h-delivery.json').read_bytes()).hexdigest(),'assets':records},ensure_ascii=False,indent=2))
print('Prepared 7 objects and 6 portraits')
