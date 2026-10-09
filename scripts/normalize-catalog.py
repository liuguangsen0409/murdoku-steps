"""Normalize public source files using statically inspected official decoder semantics.
No answer fields are copied into the playable map. Original source keeps answers separate.
"""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CORE=Path('/tmp/murdoku-core.js').read_text()
OBJECTS={int(i):{'name':name,'occupiable':int(occ)==1,'file':file or None} for i,name,occ,file in re.findall(r'c\((\d+),"([^"]+)",(-?\d+)(?:,"([^"]+)")?\)',CORE)}
OBJECTS[142]={'name':'Unknown object 142','occupiable':True,'file':None,'unverified':True}
TEXTURES={int(i):name for i,name in re.findall(r'(\d+):"(texture_floor_[^"]+)"',Path('/tmp/murdoku-app.js').read_text())}
AVAILABLE_TEXTURES=set(re.findall(r'"\./textures/([^"]+)":',Path('/tmp/murdoku-app.js').read_text()))
DEFAULTS={int(k):' '.join(v.split()) for k,v in re.findall(r'(\d+):`([^`]+)`',CORE[CORE.index('hn={'):CORE.index('function we')])}
def num(v,default=0):
 try:return int(float(v))
 except (ValueError,TypeError):return default
def color(v,default='#e7e5df'):
 if str(v).startswith('#'):return v
 if v is None:return default
 n=num(v);return '#'+''.join(f'{(n>>i)&255:02x}' for i in [0,8,16])
def slug(q):return re.sub(r'-(?:very-easy|easy|medium|hard|expert)$','',re.sub(r'^puzzle[-_]','',q['id'])).replace('_','-')
def localize(result,q):
 path=ROOT/'sources/catalog'/(q['id']+'-zh_hans.json')
 if not path.exists():return result
 tr=json.loads(path.read_text());c=tr.get('CHARACTERS',{});g={**tr.get('GRID',{}),**c};p=tr.get('PROPERTIES',{})
 for i,ch in enumerate(result['characters']):
  zh=' '.join(c.get(f'char_{part}_zh_hans_{i}','').strip() for part in ['quote','subquote']).strip()
  if zh:ch['clueZh']=zh
 for room in result['rooms']:room['label']=g.get(f"room_name_{room['id']}",room['label'])
 for label in result['roomLabels']:label['label']=g.get(f"room_name_{label['id']}",label['label'])
 raw=json.loads((ROOT/'sources/catalog'/q['file']).read_text());props={**raw.get('GRID',{}),**raw['PROPERTIES']}
 mapping={props.get(k):v for k,v in p.items() if k.startswith('clue_custom_text') and v and props.get(k)}
 for clue in result['generalClues']:
  if clue['text'] in mapping:clue['text']=mapping[clue['text']]
 return result

def normalize(q):
 raw=json.loads((ROOT/'sources/catalog'/q['file']).read_text());p=raw['PROPERTIES'];v2=num(p.get('puzzle_version'))==2;c=raw['CHARACTERS'];g=raw.get('GRID',c);allg={**p,**c,**g};w=num(p['grid_w']);h=num(p['grid_h']);sid=slug(q)
 def at(prefix,r,col):return num(g.get(f'{prefix}_{r}_{col}' if v2 else f'{prefix}_{col}_{r}'))
 def cell(r,col):return f'R{r+1}C{col+1}'
 coords=[(r,col) for r in range(h) for col in range(w)];regions={xy:at('room_code',*xy) for xy in coords};sub={i:num(allg.get(f'room_subroom_mainroom_{i}',i)) if num(allg.get(f'room_subroom_{i}')) else i for i in set(regions.values())};room={xy:sub[i] for xy,i in regions.items()};origin={xy:at('room_objects',*xy) for xy in coords};obj=origin.copy();objects=[]
 def add_object(r,col,oid,ow,oh,ship=False):
  covered=[(rr,cc) for rr in range(r,min(h,r+oh)) for cc in range(col,min(w,col+ow))];meta=OBJECTS[oid];kind=(meta['file'] or ('obj_'+meta['name'].lower().replace(' ','_')+'.svg'))[4:-4]
  for xy in covered:
   if obj[xy]==0:obj[xy]=oid
  objects.append({'id':f'{"ship" if ship else "object"}-{r+1}-{col+1}','kind':kind,'cells':[cell(*xy) for xy in covered],'asset':f'/assets/catalog/{sid}/objects/{kind}.svg','x':col,'y':r,'width':ow,'height':oh,'objectId':oid})
 for (r,col),oid in origin.items():
  if not oid:continue
  ow,oh=(2,1) if oid in [6,119,21,22,90] else (3,1) if oid==56 else (1,2) if oid in [7,120] else (2,2) if oid==54 else (1,1)
  add_object(r,col,oid,ow,oh)
 for r,col in coords:
  oid=at('ship_objects',r,col)
  if oid:
   if oid not in [73,74,111]:raise ValueError(('unsupported ship',sid,oid))
   ow,oh={73:(2,1),74:(3,2),111:(4,3)}[oid];add_object(r,col,oid,ow,oh,True)
 floors={i:num(allg.get(f'room_texture_{i}' if v2 else f'floor_type_{i}'),9) for i in regions.values()}
 fills={i:color(allg.get(f'room_color_{i}' if v2 else f'room_color_0_{i}')) for i in regions.values()}
 cells=[]
 for r,col in coords:
  xy=(r,col);oid=obj[xy];reg=regions[xy];carpet=at('carpet_objects',r,col)==5 or oid==5;label=allg.get(f'room_name_{reg}','').strip().lower();path=oid==140 or label=='path';water=(floors[reg] in [12,23] and not path) or label in ['water','sea','lake','river'] or oid==34
  cells.append({'id':cell(r,col),'row':r+1,'col':col+1,'roomId':room[xy],'regionId':reg,'occupiable':oid==0 or OBJECTS[oid]['occupiable'],'carpet':carpet,'water':water,'objectIds':([oid] if oid else [])+([5] if carpet and oid!=5 else []),'fill':fills[reg],'texture':TEXTURES.get(floors[reg],'texture_floor_plain.svg').removeprefix('texture_floor_').removesuffix('.svg'),'textureAsset':'/assets/catalog/textures/'+TEXTURES[floors[reg]] if TEXTURES.get(floors[reg]) in AVAILABLE_TEXTURES else None,'floorType':floors[reg],'puddle':oid==34,'path':path,'sand':oid==24 or floors[reg]==11})
 for item in cells:
  if item['carpet'] and 5 not in [origin[(item['row']-1,item['col']-1)]]:
   objects.insert(0,{'id':'carpet-'+item['id'],'kind':'carpet','cells':[item['id']],'asset':f'/assets/catalog/{sid}/objects/carpet.svg','x':item['col']-1,'y':item['row']-1,'width':1,'height':1,'objectId':5,'carpet':True})
 ids=list('ABCDEFGHIJKLMNO')[:num(p.get('total_chars',p.get('total_char')))-1]+['V'];chars=[]
 for i,k in enumerate(ids):
  clue=' '.join(' '.join(str(c.get(f'char_{part}_en_{i}','')).split()) for part in ['quote','subquote']).strip()
  chars.append({'id':k,'name':c[f'char_name_{i}'],'portrait':f'/assets/catalog/{sid}/portraits/{k}.svg','clueId':k+'-clue','clueEn':clue,'clueZh':clue,'sex':num(c.get(f'char_sex_{i}'))})
 general=[DEFAULTS[num(v)] for k,v in allg.items() if re.fullmatch(r'clue_\d+',k) and num(v) in DEFAULTS]
 custom=[allg.get(f'clue_custom_text{i}','').strip() for i in range(1,4)];custom=[x for x in custom if x]
 if not custom:custom=[allg.get(f'general_clue_{i}','').strip() for i in range(10) if allg.get(f'general_clue_{i}','').strip()]
 general=list(dict.fromkeys(general+custom));labels=[]
 for i in sorted(set(regions.values())):
  label=allg.get(f'room_name_{i}',f'Area {i}');first=next(xy for xy in coords if regions[xy]==i);x=first[1]+.5;y=first[0]+.85
  if f'room_name_xpos_{i}' in allg:
   x=(float(allg[f'room_name_xpos_{i}'])-float(p.get('grid_rx',0)))/float(p.get('cellsize',100));y=(float(allg[f'room_name_ypos_{i}'])-float(p.get('grid_ry',0)))/float(p.get('cellsize',100))
  labels.append({'id':i,'label':label,'x':x*100,'y':y*100,'mainRoomId':sub[i],'isSubarea':sub[i]!=i})
 rooms=[{'id':i,'label':allg.get(f'room_name_{i}',f'Area {i}'),'labelEn':allg.get(f'room_name_{i}',f'Area {i}'),'cells':[cell(*xy) for xy in coords if room[xy]==i],'fill':fills.get(i,'#e7e5df')} for i in sorted(set(room.values()))]
 edges=[]
 for direction in ['h','v']:
  for key,value in g.items():
   m=re.fullmatch(r'room_windows_'+direction+r'_(\d+)_(\d+)',key)
   if m and num(value):
    a,b=map(int,m.groups());edges.append({'direction':direction,'row':a if v2 else b,'col':b if v2 else a,'objectId':num(value)})
 result={'id':sid,'width':w,'height':h,'cells':cells,'objects':objects,'rooms':rooms,'roomLabels':labels,'objectNames':{i:OBJECTS[i]['name'] for i in sorted(set(obj.values())-{0})},'characters':chars,'generalClues':[{'id':f'general-{i+1}','text':t,'textEn':t} for i,t in enumerate(general)],'metadata':{'sourceId':q['id'],'sourceFile':q['file'],'version':2 if v2 else 1,'coordinateOrder':'row_col' if v2 else 'col_row','roomLabels':labels,'edges':edges,'unsupportedObjectIds':sorted(set(obj.values())&{142}),'titleEn':q['title_en_'],'titleZh':q.get('title_zh_hans_',q['title_en_'])}}
 result=localize(result,q)
 out=ROOT/'src/case/data';out.mkdir(exist_ok=True);(out/(sid+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
 entries=json.loads((ROOT/'sources/catalog/available.json').read_text());results=[normalize(q) for q in entries if slug(q) not in ['24h-delivery','frontier-town','the-zoo']];print('Normalized',len(results),'public maps;',sum(len(r['cells']) for r in results),'cells')
