"""Clue-driven finite-domain solver and proof recording; no solution fields in deductions."""
import json,itertools,copy,re,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OBJ={'chair':[2,122],'bed':[6,7,119,120],'car':[21,22],'table':[4],'tree':[10,11,69,99,100],'plant':[1],'shelf':[13],'tv':[3],'statue':[20,105,114],'boulder':[43,75],'shrub':[37],'box':[42],'horse':[15,137],'flowers':[80],'cart':[71],'boat':[25,73,74,76,77,110,111,112,113,124],'flag':[58],'barrel':[32,133],'puddle':[34],'path':[140],'sand':[24]}
class Model:
 def __init__(self,slug):
  self.slug=slug;self.p=json.loads((ROOT/f'src/case/data/{slug}.json').read_text());self.cells={c['id']:c for c in self.p['cells']};self.ids=[c['id'] for c in self.p['characters']];self.people={c['id']:c for c in self.p['characters']};self.free={c['id'] for c in self.p['cells'] if c['occupiable']};self.dom={k:set(self.free) for k in self.ids};self.rules=[];self.globals=[];self.local={k:[] for k in self.ids};self.events=[];self.names={r.get('labelEn',r['label']).lower():r['id'] for r in self.p['rooms']};self.rooms=set(self.names.values());self.nodes=0
 def at(self,p):return self.cells[p]
 def room(self,p):return self.at(p)['roomId']
 def row(self,p):return self.at(p)['row']
 def col(self,p):return self.at(p)['col']
 def compat(self,p,q):return self.row(p)!=self.row(q) and self.col(p)!=self.col(q)
 def has(self,p,o):return bool(set(self.at(p)['objectIds'])&set(OBJ.get(o,[o])))
 def near(self,p,o):return any(self.has(q,o) and self.room(p)==self.room(q) and abs(self.row(p)-self.row(q))+abs(self.col(p)-self.col(q))==1 for q in self.cells)
 def inroom(self,p,*names):return self.room(p) in [self.names[n.lower()] for n in names]
 def floor(self,p,kind):return self.at(p).get(kind,False) or (kind in ['puddle','path','sand'] and self.has(p,kind))
 def corner(self,p):
  c=self.at(p);wall=lambda dr,dc:not any(q['row']==c['row']+dr and q['col']==c['col']+dc and q['roomId']==c['roomId'] for q in self.cells.values())
  return (wall(1,0) or wall(-1,0)) and (wall(0,1) or wall(0,-1))
 def U(self,k,pred,label=None):self.dom[k]={p for p in self.dom[k] if pred(p)};self.local[k].append(label or self.people[k]['clueZh'])
 def R(self,a,b,pred,label=None):self.rules.append((a,b,pred,label or f"{self.people[a]['name']} 与 {self.people[b]['name']} 的关系线索"))
 def alone(self,k):
  for t in self.ids:
   if t!=k:self.R(k,t,lambda p,q:self.room(p)!=self.room(q),f'{self.people[k]["name"]} 独处，其他人必须在不同区域')
 def pair(self,k,t,alone=False):
  self.R(k,t,lambda p,q:self.room(p)==self.room(q),f'{self.people[k]["name"]} 与 {self.people[t]["name"]} 在同一区域')
  if alone:
   for o in self.ids:
    if o not in [k,t]:self.R(k,o,lambda p,q:self.room(p)!=self.room(q),f'{k}/{t} 两人独处，不能容纳第三人')
 def count(self,pred,n,label):
  self.globals.append((label,lambda d:sum(all(pred(k,p) for p in d[k]) for k in self.ids)<=n<=sum(any(pred(k,p) for p in d[k]) for k in self.ids)))
 def occupied(self,mode):
  def feasible(d):
   forced={self.room(next(iter(v))) for v in d.values() if len({self.room(p) for p in v})==1};possible={self.room(p) for v in d.values() for p in v}
   if mode=='nonempty':return self.rooms<=possible
   if mode=='oneempty':return len(forced)<=len(self.rooms)-1<=len(possible)
   if mode=='nosingle':return all(not any(all(self.room(p)==r for p in d[k]) for k in self.ids) or sum(any(self.room(p)==r for p in d[k]) for k in self.ids)>=2 for r in self.rooms)
  self.globals.append(({'nonempty':'每个区域都必须有人','oneempty':'恰好一个区域为空','nosingle':'任何区域都不能只有一个人'}[mode],feasible))
 def exists(self,k,eligible,predicate,label,exactroom=None,witnessalone=False):
  eligible=[t for t in eligible if t!=k]
  def feasible(d):
   for p in d[k]:
    for t in eligible:
     for q in d[t]:
      if not self.compat(p,q) or not predicate(p,q):continue
      if witnessalone and any(all(self.room(z)==self.room(q) for z in d[o]) for o in self.ids if o!=t):continue
      if exactroom is not None:
       if sum(all(self.room(z)==self.room(p) for z in d[o]) for o in self.ids if o not in [k,t])+2>exactroom:continue
      return True
   return False
  self.globals.append((label,feasible))
 def solo_count(self,k,total,label):
  def feasible(d):
   for p in d[k]:
    r=self.room(p);lo=1+sum(all(self.room(q)==r for q in d[t]) for t in self.ids if t!=k);hi=1+sum(any(self.room(q)==r for q in d[t]) for t in self.ids if t!=k)
    if lo<=total<=hi:return True
   return False
  self.globals.append((label,feasible))
 def build(self):
  s=self.slug;U=self.U;R=self.R;near=self.near;has=self.has;room=self.inroom;floor=self.floor;row=self.row;col=self.col;pair=self.pair;alone=self.alone;ids=self.ids;male=[k for k in ids if self.people[k]['sex']==0];female=[k for k in ids if self.people[k]['sex']==1];N=self.p['height'];W=self.p['width'];ex=self.exists
  def only(k,pred):
   for t in ids:U(t,pred if t==k else lambda p:not pred(p))
  def nearU(k,o):U(k,lambda p:near(p,o))
  def on(k,o):U(k,lambda p:has(p,o))
  def inside(k,*rs):U(k,lambda p:room(p,*rs))
  def ground(k,f):U(k,lambda p:floor(p,f))
  def delta(a,b,axis,n):R(a,b,lambda p,q:(row(p)-row(q) if axis=='row' else col(p)-col(q))==n)
  def north(a,b):R(a,b,lambda p,q:row(p)<row(q))
  def west(a,b):R(a,b,lambda p,q:col(p)<col(q))
  def someone(k,eligible,pred,label,exact=None):ex(k,eligible,pred,label,exact);self.solo_count(k,exact,label) if exact else None
  if s=='the-french-restaurant':
   inside('A','Dining Room');[U(k,lambda p:not room(p,'Dining Room')) for k in male if k!='A'];ground('B','carpet');nearU('C','table');nearU('D','shelf');U('D',lambda p:not room(p,'Kitchen'));inside('E','Entrance');inside('F','Kitchen');nearU('F','table');nearU('G','plant');only('H',lambda p:has(p,'chair'))
  elif s=='the-picnic':
   ground('A','carpet');inside('B','Gazebo');on('B','chair');inside('C','Picnic Area');nearU('D','flowers');nearU('D','tree');on('E','chair');inside('F','Pond');north('F','E')
  elif s=='the-panic-room':
   nearU('A','statue');on('B','chair');inside('C','Guest Bedroom');nearU('D','shelf');inside('E','Panic Room');nearU('F','tv');someone('G',ids,lambda p,q:row(p)==row(q)+1 and floor(q,'carpet'),'G 恰在一名地毯上的人南边一行');inside('H','Dining Room');someone('H',female,lambda p,q:self.room(p)==self.room(q),'H 与一名女性同在餐厅');someone('I',female,lambda p,q:col(p)==col(q)+2,'I 恰在一名女性东边两列')
  elif s=='the-terracotta-courtyard':
   nearU('A','plant');U('B',lambda p:any(has(q,'shelf') and row(q)==row(p) for q in self.cells) and any(has(q,'shelf') and col(q)==col(p) for q in self.cells));inside('C','Garage');on('D','car');alone('E');west('E','D');U('F',lambda p:not floor(p,'carpet'));on('G','bed');on('H','chair')
  elif s=='fireside-beach':
   north('C','A');inside('B','Woods');U('B',lambda p:not near(p,'tree'));U('C',lambda p:col(p)==W);nearU('D','boulder')
  elif s=='the-retirement-community':
   ground('A','carpet');inside('B','Condo A','Condo B');alone('B');nearU('C','tree');on('D','chair');on('E','bed');on('F','cart');U('G',lambda p:row(p)==1);someone('H',male,lambda p,q:row(p)==row(q)+1 and has(q,'cart'),'H 北边恰好一行处有一名男性坐在球车里');inside('I','Pickleball Court');U('I',self.corner)
  elif s=='midnight-rain':
   only('A',lambda p:floor(p,'puddle'));nearU('B','shelf');alone('C');nearU('C',150);someone('D',male,lambda p,q:col(q)==col(p)+1 and has(q,'car'),'D 东边恰好一列有一名男性在车里');U('E',lambda p:not near(p,'puddle'));U('F',lambda p:col(p)==W)
  elif s=='the-garage-band':
   nearU('A',145);U('B',lambda p:has(p,'car') or has(p,'bed'));nearU('C','shelf');U('D',lambda p:not near(p,'box'));on('E','chair');nearU('F','tree')
  elif s=='the-donut-house':
   on('A','bed');alone('A');ground('B','carpet');nearU('C','tv');inside('D','Kitchen');alone('E');nearU('F','plant');nearU('G','shelf');someone('H',male,lambda p,q:row(p)==row(q)+2 and has(q,'chair'),'H 北边恰好两行有一名男性坐椅子');self.occupied('oneempty')
  elif s=='the-wine-cellar':
   U('A',lambda p:not near(p,'table'));U('B',lambda p:row(p)==N);nearU('C','shelf');west('B','D');U('D',lambda p:not near(p,'table'));inside('E','Basement');U('E',lambda p:not near(p,'tv'));alone('F');on('F','chair');inside('G','Bathroom');nearU('H','table');self.count(lambda k,p:has(p,'bed'),1,'恰好一人在床上');self.count(lambda k,p:has(p,'chair'),2,'恰好两人坐椅子');self.occupied('nonempty')
  elif s=='neighbour-dispute':
   U('A',lambda p:any(room(p,r) for r in self.names if 'arnold' in r));alone('A');U('B',lambda p:any(room(p,r) for r in self.names if 'brie' in r));on('C','bed');someone('D',male,lambda p,q:self.room(p)==self.room(q),'D 与一名男性独处',2);ground('E','carpet');nearU('F','tree');nearU('G','tv');self.count(lambda k,p:has(p,'chair'),1,'恰好一人坐椅子')
  elif s=='the-pigsty':
   inside('A','Pigsty');U('B',lambda p:not floor(p,'puddle'));nearU('C','table');inside('D','Pasture')
  elif s=='the-bus-stop':
   someone('A',ids,lambda p,q:col(p)==col(q)+1 and has(q,'car'),'A 恰在车内人物东边一列');on('B',56);inside('C','Yard');U('C',lambda p:not near(p,'tree'));pair('C','D');on('E','chair');R('F','A',lambda p,q:self.room(p)!=self.room(q))
  elif s=='piano-lesson':
   inside('A','Closet');nearU('B','statue');someone('C',ids,lambda p,q:row(q)<row(p) and self.room(p)==self.room(q),'C 的同区有人在她北方');someone('D',ids,lambda p,q:row(q)==row(p)+1 and near(q,86),'D 南边恰一行处有人在钢琴旁');on('E','chair');self.count(lambda k,p:floor(p,'carpet'),1,'恰好一人在地毯上')
  elif s=='main-street':
   pair('A','I',True);north('A','I');on('B','chair');someone('C',ids,lambda p,q:col(q)==col(p)-3 and has(q,'car'),'C 西边恰三列处有人在车里');inside('E','Elevator A','Elevator B');someone('E',female,lambda p,q:self.room(q)!=self.room(p) and room(q,'Elevator A','Elevator B'),'E 所在电梯之外的另一部电梯还有一名女性');U('F',lambda p:has(p,'car') or has(p,56));U('G',lambda p:col(p) in [1,2]);nearU('H','plant');pair('H','B');inside('I','South Sidewalk','North Sidewalk');west('D','I');inside('J','South Sidewalk','North Sidewalk');alone('J');someone('K',ids,lambda p,q:row(q)==row(p)-2 and near(q,'statue'),'K 北边恰两行处有人在雕像旁')
   def emptywall(d):
    for p in d['D']:
     neighbors={self.room(q) for q in self.cells if abs(row(p)-row(q))+abs(col(p)-col(q))==1 and self.room(q)!=self.room(p)}
     if any(all(any(self.room(q)!=r for q in d[k]) for k in ids) for r in neighbors):return True
    return False
   self.globals.append(('D 靠墙且墙另一侧的区域为空',emptywall))
  elif s=='lake-fishing':
   on('A','boat');inside('B','Dock');nearU('C','shrub');R('D','B',lambda p,q:row(p)>row(q) and col(p)<col(q));U('E',lambda p:not near(p,'tree'));nearU('F','boulder');someone('G',male,lambda p,q:self.room(p)==self.room(q),'G 与另一名男性同区');self.occupied('nosingle')
  elif s=='outdoor-painting':
   U('A',lambda p:col(p)==1);delta('B','D','row',1);R('B','D',lambda p,q:self.room(p)!=self.room(q));nearU('C','boulder');nearU('D',81);on('E','chair')
  elif s=='river-crossing':
   nearU('A',9);on('B','chair');nearU('C','tree');on('D',90);on('F','horse');nearU('G','boulder');alone('H');ex('E',[k for k in ids if k not in ['E','H','V']],lambda p,q:row(p)==row(q)+6,'亡命徒独处，E 恰在其南方六行',witnessalone=True)
   self.globals.append(('最顶行或最底行为空',lambda d:all(any(row(p)!=1 for p in d[k]) for k in ids) or all(any(row(p)!=N for p in d[k]) for k in ids)))
  elif s=='horse-with-no-name':
   nearU('A',16);U('B',lambda p:not room(p,'Desert'));R('B','A',lambda p,q:abs(row(p)-row(q))==abs(col(p)-col(q)));north('C','A');nearU('D','table');nearU('E','boulder');self.count(lambda k,p:k!='V' and has(p,'horse'),1,'有一名非死者的亡命徒在马背上')
  elif s=='remote-village':
   someone('A',female,lambda p,q:row(q)==row(p)+1 and has(q,'car'),'A 南边恰一行处有女性在车里');nearU('B','tree');north('C','E');[R('D',k,lambda p,q:self.room(p)!=self.room(q),'D 的区域没有男性') for k in male];someone('E',female,lambda p,q:self.room(p)==self.room(q),'E 所在区域至少有一名女性');ground('F','carpet');U('G',lambda p:col(p)==5);nearU('H','shrub');self.count(lambda k,p:has(p,'chair'),1,'恰好一人坐椅子')
  elif s=='minigolf':
   someone('A',ids,lambda p,q:row(p)==row(q)+1 and has(q,'flag'),'A 北边恰一行有人站在旗标上');on('B','chair');U('C',lambda p:not self.corner(p));only('D',lambda p:floor(p,'path'));ground('E','sand');alone('F');U('G',lambda p:row(p)==1);nearU('H','flowers');inside('I','The Desert');self.solo_count('I',2,'I 与另一人在沙漠区独处');self.count(lambda k,p:near(p,'table'),1,'恰好一人在桌旁');self.count(lambda k,p:near(p,'barrel'),1,'恰好一人在桶旁')
  elif s=='grizzly-night':
   inside('A','Tent A','Tent C');U('B',lambda p:not floor(p,'carpet') and row(p) in [1,N]);only('C',lambda p:near(p,'shrub'));on('D','bed');only('E',lambda p:has(p,'car'));U('F',lambda p:col(p)==W);north('C','F');on('G','chair');inside('H','Woods');someone('H',ids,lambda p,q:near(q,53),'H 之外另有人在熊旁');self.count(lambda k,p:floor(p,'carpet'),1,'恰好一人在地毯上')
  elif s=='book-club':
   nearU('A','plant');north('C','B');ground('C','carpet');only('D',lambda p:has(p,'chair'));inside('E','Library');U('E',lambda p:not near(p,'shelf'))
  elif s=='the-flower-store':
   nearU('A',44);inside('B','Preparation');ground('C','carpet');on('D','chair');U('E',lambda p:col(p)==1);inside('F','Store Floor');someone('F',male,lambda p,q:self.room(p)==self.room(q),'F 在商店区与一名男性同区')
  elif s=='a-messy-situation':
   alone('A');R('B','A',lambda p,q:row(p)>row(q) and col(p)>col(q));R('B','H',lambda p,q:row(p)<row(q) and col(p)<col(q));ground('C','puddle');pair('C','D',True);nearU('E','tree');ground('F','puddle');on('G','chair');delta('G','F','row',-1);U('H',lambda p:not near(p,'table'));self.occupied('nonempty')
  elif s=='the-riding-lesson':
   nearU('A','shrub');nearU('B','table');someone('C',female,lambda p,q:col(p)==col(q)-1 and has(q,'horse'),'C 恰在骑马女性西边一列');U('D',lambda p:col(p)==5);inside('E','Stable');on('F','horse');inside('F','Training Ring');inside('G','Tool Shed');pair('G','B');ground('H','puddle')
  elif s=='white-wedding':
   nearU('A','table');nearU('B','flowers');U('C',lambda p:col(p)==5);inside('D','Porch');R('E','C',lambda p,q:row(p)<row(q) and col(p)>col(q));U('F',self.corner);someone('G',ids,lambda p,q:self.room(p)==self.room(q) and near(q,'tree'),'G 的同区另有人在树旁');on('H','chair');self.count(lambda k,p:room(p,'Altar') and k in male,1,'祭坛恰有一名男性');self.count(lambda k,p:room(p,'Altar') and k in female,1,'祭坛恰有一名女性')
  elif s=='the-beach':
   nearU('A','boulder');ground('B','carpet');on('C','chair');U('C',lambda p:not room(p,'Beach'));inside('D','Beach');nearU('E','chair');inside('F',"Lifeguard's Tower");alone('F')
  elif s=='surprise-visitors':
   nearU('A','tv');on('B','bed');U('C',lambda p:col(p)==W);nearU('D','table');only('E',lambda p:near(p,'plant'));nearU('F','shelf');nearU('G','bed');on('H','chair');self.count(lambda k,p:floor(p,'carpet'),1,'恰好一人在地毯上')
  elif s=='the-abandoned-museum':
   delta('A','G','col',-1);on('B','chair');someone('B',male,lambda p,q:self.room(p)==self.room(q),'B 与一名男性独处',2);U('C',lambda p:col(p)==1);north('A','C');nearU('D','table');someone('E',male,lambda p,q:self.room(p)==self.room(q) and has(q,'chair'),'E 的区域里有一名男性坐在椅子上');nearU('F','statue');U('G',lambda p:near(p,'statue') or near(p,23));nearU('H',23);U('H',lambda p:not room(p,'Lobby'))
  elif s=='preppers':
   U('A',lambda p:not near(p,'box') and any(has(q,'box') and self.room(q)==self.room(p) for q in self.cells));inside('B','Bedroom');someone('C',male,lambda p,q:self.room(p)==self.room(q) and has(q,'bed'),'C 的区域里有一名男性在床上');someone('D',ids,lambda p,q:self.room(p)==self.room(q) and near(q,'shelf'),'D 的区域里另有人在书架旁');U('E',lambda p:row(p)==N);nearU('F','tv');on('G','chair');inside('H','Bathroom')
  elif s=='netflix-and-kill':
   nearU('A','shelf');on('B','bed');only('C',lambda p:has(p,'chair'));inside('D','Kitchen');nearU('E','tv')
  elif s=='car-repair':
   on('A','car');on('B',138);on('C','chair');inside('D','Waiting Area');alone('D');nearU('E','shelf')
  elif s=='backyard-garden':
   inside('A','Living Room');pair('A','E');inside('B','Shed');nearU('C','tree');inside('D','Bedroom','Sunroom');on('E','chair');ground('F','carpet');inside('G','Garden');alone('H')
  else:raise ValueError(s)
  self.solo_count('V',2,'死者与凶手独处，所在区域恰好两人')
  # Build combined binary tables; row and column exclusions always apply.
  self.tables={};self.labels={}
  for a,b in itertools.combinations(ids,2):
   rs=[(f,label,False) for x,y,f,label in self.rules if x==a and y==b]+[(f,label,True) for x,y,f,label in self.rules if x==b and y==a]
   self.tables[a,b]={p:{q for q in self.dom[b] if self.compat(p,q) and all(f(q,p) if reverse else f(p,q) for f,label,reverse in rs)} for p in self.dom[a]}
   self.tables[b,a]={q:{p for p in self.dom[a] if q in self.tables[a,b][p]} for q in self.dom[b]}
   self.labels[a,b]=self.labels[b,a]='；'.join(dict.fromkeys(label for f,label,reverse in rs)) or '每行、每列最多一人'
  return self
 def project(self,d,k,p):
  return {t:({p} if t==k else {q for q in d[t] if q in self.tables[k,t].get(p,set())}) for t in self.ids}
 def reduction(self,d):
  for a in self.ids:
   if not d[a]:return a,set(),'没有可用位置',[]
   for b in self.ids:
    if a==b:continue
    keep={p for p in d[a] if self.tables[a,b][p]&d[b]}
    if keep!=d[a]:return a,keep,self.labels[a,b],[a,b]
  # Hall subsets: k people in k rows/columns reserve those axes.
  for axis,fn in [('行',self.row),('列',self.col)]:
   sets={k:{fn(p) for p in d[k]} for k in self.ids}
   for n in range(2,min(5,len(self.ids))):
    for group in itertools.combinations(self.ids,n):
     axes=set().union(*(sets[k] for k in group))
     if len(axes)<n:return group[0],set(),f'{n} 个人只有 {len(axes)} {axis}可用',list(group)
     if len(axes)==n:
      for k in self.ids:
       if k in group:continue
       keep={p for p in d[k] if fn(p) not in axes}
       if keep!=d[k]:return k,keep,f'{"、".join(group)} 共 {n} 人锁定第 {"、".join(map(str,sorted(axes)))} {axis}',[k,*group]
  for label,feasible in self.globals:
   if not feasible(d):return self.ids[0],set(),label+'无法满足',self.ids
   for k in self.ids:
    if len(d[k])==1:continue
    keep=set()
    for p in d[k]:
     trial=self.project(d,k,p)
     if all(trial.values()) and feasible(trial):keep.add(p)
    if keep!=d[k]:return k,keep,label,[k]
  return None
 def propagate(self,d,record=False):
  d={k:set(v) for k,v in d.items()}
  while True:
   change=self.reduction(d)
   if not change:return d,None
   k,keep,label,focus=change
   if record:self.events.append({'character':k,'before':sorted(d[k],key=self.sort),'after':sorted(keep,key=self.sort),'reason':label,'focus':focus,'state':{t:sorted(keep if t==k else v,key=self.sort) for t,v in d.items()}})
   d[k]=keep
   if not keep:return None,label
 def sort(self,p):return self.row(p),self.col(p)
 def search(self,d,limit=2):
  solutions=[]
  def visit(ds):
   self.nodes+=1
   if self.nodes>200000:raise RuntimeError('search budget exceeded')
   ds,fail=self.propagate(ds)
   if ds is None:return
   if all(len(v)==1 for v in ds.values()):solutions.append({k:next(iter(v)) for k,v in ds.items()});return
   k=min((k for k in self.ids if len(ds[k])>1),key=lambda k:len(ds[k]))
   for p in sorted(ds[k],key=self.sort):
    visit({**ds,k:{p}})
    if len(solutions)>=limit:return
  visit(d);return solutions
 def solve(self):
  initial=copy.deepcopy(self.dom);d,fail=self.propagate(initial,True)
  if not d:raise ValueError('contradiction '+str(fail))
  while any(len(v)>1 for v in d.values()):
   # Test hypotheses independently of stored official answers.
   k=min((k for k in self.ids if len(d[k])>1),key=lambda k:len(d[k]));before=set(d[k]);keep=set();reject=[];branch_proofs=[]
   for p in sorted(before,key=self.sort):
    checkpoint=len(self.events)
    trial,why=self.propagate({**d,k:{p}},True)
    trace=self.events[checkpoint:];del self.events[checkpoint:]
    if trial is None:
     reject.append((p,why));branch_proofs.append({'assumption':p,'events':[{x:e[x] for x in ['character','before','after','reason','focus']} for e in trace]});continue
    sols=self.search(trial,1)
    if sols:keep.add(p)
    else:reject.append((p,'继续结合全部线索后，无法为每个人安排互不冲突的位置'))
   if keep==before:raise ValueError('multiple supported positions remain '+k+str(keep))
   self.events.append({'character':k,'before':sorted(before,key=self.sort),'after':sorted(keep,key=self.sort),'reason':'逐个假设并排除矛盾','focus':[k],'branches':reject,'branchProofs':branch_proofs,'state':{t:sorted(keep if t==k else v,key=self.sort) for t,v in d.items()}});d[k]=keep;d,fail=self.propagate(d,True)
   if not d:raise ValueError(fail)
  result={k:next(iter(v)) for k,v in d.items()};return initial,result

def main():
 targets=sys.argv[1:] or [p.stem for p in (ROOT/'src/case/data').glob('*.json') if p.stem not in ['24h-delivery','frontier-town','the-zoo','the-ceos-office','the-golf']]
 report=[]
 for slug in targets:
  started=time.time()
  try:
   m=Model(slug).build();initial,result=m.solve()
   # Answer data is read only after clue-based deduction has finished.
   catalog=json.loads((ROOT/'sources/catalog/available.json').read_text());q=next(q for q in catalog if re.sub(r'-(very-easy|easy|medium|hard|expert)$','',q['id'].removeprefix('puzzle-'))==slug);raw=json.loads((ROOT/'sources/catalog'/q['file']).read_text());c=raw['CHARACTERS'];pr=raw['PROPERTIES'];official={}
   for i,k in enumerate(m.ids):
    if f'solution_x_{i}' in c:col=int(float(c[f'solution_x_{i}']))+1;row=int(float(c[f'solution_y_{i}']))+1
    else:col=int((float(c[f'letter_xpos_{i}'])-float(pr['grid_rx']))/float(pr['cellsize']))+1;row=int((float(c[f'letter_ypos_{i}'])-float(pr['grid_ry']))/float(pr['cellsize']))+1
    official[k]=f'R{row}C{col}'
   assert result==official,('solution mismatch',result,official)
   out=ROOT/'analysis/generated';out.mkdir(parents=True,exist_ok=True);(out/f'{slug}-proof.json').write_text(json.dumps({'initial':{k:sorted(v,key=m.sort) for k,v in initial.items()},'events':m.events,'final':result,'officialMatch':True},ensure_ascii=False,indent=2))
   report.append({'slug':slug,'ok':True,'events':len(m.events),'branches':sum('branches' in e for e in m.events),'nodes':m.nodes});print('OK',slug,len(m.events),'events',m.nodes,'nodes',round(time.time()-started,2),flush=True)
  except Exception as e:report.append({'slug':slug,'ok':False,'error':str(e)});print('FAIL',slug,str(e),flush=True)
 (ROOT/'analysis/catalog-solver-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
