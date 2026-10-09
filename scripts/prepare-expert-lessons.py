"""Auditable expert lessons: domains from maps, justified reductions, answers checked last."""
import json,copy,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IDS=list('ABCDEFGHIJKLMNOV')
def pos(s):return tuple(map(int,re.findall(r'\d+',s)))
def cell(p):return f'R{p[0]}C{p[1]}'
def fmt(ps):return '、'.join(map(cell,sorted(ps)))
def compatible(a,b):return a[0]!=b[0] and a[1]!=b[1]
class Lesson:
 def __init__(self,slug):
  self.slug=slug;self.raw=json.loads((ROOT/f'sources/catalog/puzzle-{slug}-expert.json').read_text());self.map=json.loads((ROOT/f'src/case/data/{slug}.json').read_text());self.cells={pos(c['id']):c for c in self.map['cells']};self.free={p for p,c in self.cells.items() if c['occupiable']};self.room={p:c['roomId'] for p,c in self.cells.items()};self.obj={p:set(c['objectIds']) for p,c in self.cells.items()};self.d={k:set(self.free) for k in IDS};self.placed={};self.steps=[];self.snapshots=[];self.previous={k:set() for k in IDS};self.last={};self.reservations=[];self.forced=[]
 def near(self,p,kind):return any(q in self.cells and self.room[q]==self.room[p] and kind in self.obj[q] for q in [(p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1)])
 def keep(self,k,pred):self.d[k]={p for p in self.d[k] if pred(p)};assert self.d[k] or k in self.placed,(self.slug,k)
 def block(self,ps,excepts=()):
  for k in IDS:
   if k not in excepts:self.d[k]-=set(ps)
 def reserve_row(self,r,excepts=()):self.block({p for p in self.free if p[0]==r},excepts)
 def reserve_col(self,c,excepts=()):self.block({p for p in self.free if p[1]==c},excepts)
 def put(self,k):
  assert len(self.d[k])==1,(self.slug,len(self.steps),k,sorted(self.d[k]));p=next(iter(self.d[k]));self.forced.append({'step':len(self.steps)+1,'character':k,'domainBeforePlacement':[cell(q) for q in sorted(self.d[k])],'cell':cell(p)});self.placed[k]=p;self.d[k]=set()
  for t in IDS:
   if t not in self.placed:self.keep(t,lambda q:compatible(p,q))
  return p
 def emit(self,title,text,focus,details,rule='候选与行列交叉排除',high=None):
  n=len(self.steps)+1;refs=[k+'-clue' for k in IDS]+[c['id'] for c in self.map['generalClues']];reason={'ruleId':rule,'clueRefs':refs,'dependsOn':[f'{self.slug}-{n-1}'] if n>1 else []};actions=[]
  for k in IDS:
   if n==1:actions.append({'type':'setCandidates','character':k,'cells':list(map(cell,sorted(self.d[k])))})
   else:
    for p in sorted(self.previous[k]-self.d[k]):
     if self.placed.get(k)!=p:actions.append({'type':'removeCandidate','character':k,'cell':cell(p),'reason':reason})
   if k in self.placed and k not in self.last:actions.append({'type':'placeCharacter','character':k,'cell':cell(self.placed[k]),'reason':reason})
  if high is None:high=set().union(*(self.d[k] or {self.placed[k]} for k in focus)) if focus else set()
  self.steps.append({'id':f'{self.slug}-{n}','title':title,'explanation':text,'focusCharacters':focus,'candidateCharacters':focus,'highlightCells':list(map(cell,sorted(high))),'clueRefs':refs,'actions':actions,'rule':rule,'details':details})
  self.snapshots.append({'step':n,'placements':{k:cell(v) for k,v in self.placed.items()},'candidates':{k:list(map(cell,sorted(v))) for k,v in self.d.items()}});self.previous=copy.deepcopy(self.d);self.last=self.placed.copy()
 def finish(self,killer,extra={}):
  assert len(self.placed)==16 and len({p[0] for p in self.placed.values()})==16 and len({p[1] for p in self.placed.values()})==16
  replay_d={k:set() for k in IDS};replay_p={}
  for step,expected in zip(self.steps,self.snapshots):
   for a in step['actions']:
    if a['type']=='setCandidates':replay_d[a['character']]=set(a['cells'])
    elif a['type']=='removeCandidate':replay_d[a['character']].discard(a['cell'])
    elif a['type']=='placeCharacter':
     assert replay_d[a['character']]=={a['cell']},(step['id'],a['character'],replay_d[a['character']])
     replay_p[a['character']]=a['cell'];replay_d[a['character']]=set()
   assert replay_p==expected['placements']
   assert all(replay_d[k]==set(expected['candidates'][k]) for k in IDS)
  g=self.raw['CHARACTERS'];official={k:(int(g[f'solution_y_{i}'])+1,int(g[f'solution_x_{i}'])+1) for i,k in enumerate(IDS)}
  assert self.placed==official,(self.slug,self.placed,official);assert IDS[int(self.raw['PROPERTIES']['murderer'])]==killer
  companions={k for k,p in self.placed.items() if self.room[p]==self.room[self.placed['V']]};assert companions=={'V',killer},companions
  (ROOT/f'src/tutorial/data/{self.slug}.json').write_text(json.dumps(self.steps,ensure_ascii=False,indent=2))
  (ROOT/f'analysis/generated/{self.slug}-proof.json').write_text(json.dumps({'method':'地图与线索建立候选，每次落位均断言域仅一格；最后才读取 solution 字段。','snapshots':self.snapshots,'forcedPlacements':self.forced,'officialMatch':True,'killer':killer,'victimRoomOccupants':sorted(companions),**extra},ensure_ascii=False,indent=2))
  lines=[f'# {self.slug} 逐步推理','所有落位先用候选唯一性断言，最终才与源答案核对。','']
  for i,s in enumerate(self.steps,1):lines += [f'## {i}. {s["title"]}',s['explanation'],'']+['- '+t for t in s['details']]+['']
  (ROOT/f'analysis/generated/{self.slug}-walkthrough.md').write_text('\n'.join(lines));print(self.slug,len(self.steps),'steps;',sum(len(s['details']) for s in self.steps),'details')

def golf():
 s=Lesson('the-golf');d=s.d;room=s.room
 hole={r['id']:int(r['labelEn'].split()[-1]) for r in s.map['rooms']};h=lambda p:hole[room[p]]
 men=set('CDGHKLOV');women=set(IDS)-men
 s.keep('A',lambda p:s.near(p,72));s.keep('B',lambda p:h(p)==4 and s.near(p,10));s.keep('C',lambda p:p[1] not in [1,16]);s.keep('D',lambda p:s.near(p,58));s.keep('E',lambda p:58 in s.obj[p] and h(p)%2==0);s.keep('G',lambda p:78 in s.obj[p]);s.keep('J',lambda p:78 in s.obj[p] and h(p) in [6,7,8]);s.keep('M',lambda p:58 in s.obj[p] and h(p) in [3,4,5]);s.keep('N',lambda p:s.cells[p]['sand']);s.keep('O',lambda p:p[0]==1 and s.near(p,10))
 for k in men-{'G'}:s.keep(k,lambda p:78 not in s.obj[p])
 s.emit('先区分旗杆、发球台和沙坑','偶数洞必须有偶数人，奇数洞必须有奇数人；死者也计入。先建立个人线索候选。',['H','M','J'],['旗杆可以站人，发球台也可以站人；树与水格不可站立。','“旁边”指同洞的上下左右；I 在 F 西北，要求行号和列号都更小。','G 是唯一站发球台的男性，其他男性均不能站发球台。','16 人对应 16 行、16 列，最终每行每列恰好一人。'])
 carts={p for p in s.free if 71 in s.obj[p]};s.keep('H',lambda p:h(p)<4 and any(h(q)==h(p) for q in carts));assert {h(p) for p in d['H']}=={1}
 wc={p for p in carts if h(p)==1};assert wc=={(12,1),(12,4)}
 s.reserve_row(12,women)
 s.emit('Harry 在 1 号洞，车上的女性占第 12 行','B 在 4 号洞且洞号比 H 大。前三洞中，只有 1 号洞有球车，因此 H 和一位女性都在 1 号洞。',['H','M'],['1 号洞的球车只有 R12C1、R12C4。女性必占第 12 行，身份暂未确定。','车上的女性不可能是 H；其他男性因此不能用第 12 行。','M 在 3/4/5 号洞旗杆，不可能兼任这名 1 号洞女性，所以 M 的第 12 行也排除。'])
 s.keep('M',lambda p:p[0]!=12);s.put('M');s.keep('K',lambda p:h(p)==h(s.placed['M']));s.keep('K',lambda p:p[0]==2)
 # M in row3; O occupies row1. Hole3 only rows1-4, row4 exclusively water; K must row2.
 s.emit('Mona 落在 3 号洞，Kent 锁第 2 行','M 只剩 R3C15 的旗杆。K 要与她同洞，避开 M 的第 3 行和 O 锁定的第 1 行，只能在第 2 行。',['M','K'],['M 的另外两面旗杆在 R12C10、R12C15，均被球车女性占行。','3 号洞可站立格仅在第 1–3 行；第 4 行只有水。','O 的线索锁定第 1 行，所以 K 只能占第 2 行。'])
 s.reserve_row(2,['K']);s.reserve_row(1,['O']);s.keep('O',lambda p:h(p)==3);s.put('O')
 s.emit('3 号洞的奇数人数，确定 Oscar','3 号洞已有 M 和 K，需要第三人；仅剩第 1 行能容纳第三人，所以 O 必须进入 3 号洞，落在 R1C12。',['O','K','M'],['同洞可站立格只有三行，不能容纳五人。奇数人数且至少两人，故恰好三人。','第三人必须使用剩余的第 1 行，而 O 已锁定该行。','O 在树旁的两个 3 号洞候选中，R1C10 是发球台，只有 G 能作为男性站发球台；故 O 只能 R1C12。'])
 assert d['J']=={(11,5),(14,9)}
 blocked={p for p in s.free if all(not compatible(p,q) for q in d['J'])};s.block(blocked,['J'])
 s.emit('Jana 两个候选，共同排除交叉格','J 只剩 R11C5、R14C9。无论她在哪一格，其他人都不能占 R11C9 或 R14C5。',['J','E'],['7 号洞发球台为 R11C5，6 号洞发球台为 R14C9。','8 号洞发球台 R6C12 与 O 同列，已被排除。','对角两候选的交叉格，在任意分支都会与 J 同行或同列。'])
 s.put('E');s.emit('确定 Edna：R13C5','E 必须在偶数洞旗杆。第 2、12 行和交叉格限制之后，只剩 6 号洞的 R13C5。',['E'],['2 号洞旗杆 R2C7 被 K 锁行；4 号洞旗杆 R12C15 被球车女性锁行。','8 号洞旗杆 R11C9 是刚刚证明不能使用的交叉格。'])
 s.put('J');s.emit('确定 Jana：R14C9','E 占第 5 列，排除 J 的 R11C5，因此 J 落在 6 号洞 R14C9。',['J'],['6 号洞现在至少有 E、J 两人，满足偶数人数，但仍需证明是否还有人。'])
 # Holes4/5 both confined to right four columns after M C15 and O C12? hole4 min C12 but C12 occupied; C13-16, C15 occupied, so 3 cols.
 right={13,14,16};assert all(p[1] in right for p in s.free if h(p) in [4,5] and all(compatible(p,q) for q in s.placed.values()) and p[0] not in [1,2,12])
 s.keep('K',lambda p:p[1] not in right);s.put('K')
 s.emit('右侧三列的人数预算，确定 Kent','4 号洞有 B，偶数人数至少 2 人；5 号洞奇数人数至少 1 人。这三人必须用满 C13、C14、C16，K 因而只能在 R2C11。',['K','B'],['O、M 已占 C12、C15；其他已占行也不再可用。','4/5 号洞所有剩余可站立格都在 C13、C14、C16。','两洞人数下限合计三人，上限也为三列，所以恰好 2+1 人；其他洞不能使用这三列。'])
 s.block({p for p in s.free if p[1] in right and h(p) not in [4,5]})
 # hole5 rows15/16 due current occupancy, hole6 12/15/16 but row12 cart ->15/16
 s.block({p for p in s.free if p[0]==12 and h(p)!=1})
 s.block({p for p in s.free if h(p)==6})
 s.emit('6 号洞恰好两人，5 号洞占第 16 行','5 号洞唯一的人只能在第 15 或 16 行；6 号洞若再加两人，也要占这两行，产生冲突。因此 6 号洞只有 E/J。',['E','J'],['6 号洞人数必须为偶数；已有两人后，新增人数至少为二。','排除第 12 行的球车女性后，6 号洞剩余可用行只有第 15、16 行。','5 号洞至少一人，也必须用其中一行，故 6 号洞不能再加两人。','第 16 行的 1 号洞全是树，6 号洞又已满员，所以第 16 行只能由 5 号洞的人占据；第 15 行则在 1 号洞。'])
 s.block({p for p in s.free if h(p)==5 and p[0]!=16});s.block({p for p in s.free if p[0]==16 and h(p)!=5});s.block({p for p in s.free if p[0]==15 and h(p)!=1})
 s.put('G');s.emit('确定 Gerald：R5C2','G 的发球台候选逐一排除后，只剩 2 号洞 R5C2。',['G'],['3 号洞第 1 行已有 O；1 号洞第 14 行已有 J。','4 号洞 C15 已被 M 占；8 号洞 C12 已被 O 占。','7 号洞 C5 已被 E 占；5 号洞只能在第 16 行，发球台在第 15 行。'])
 # Cart woman identity: A/B/E/J/M/N cannot; I cannot since northwest of F same hole requires a column beyond4? inspect supported I/F.
 cart_options={k:{q for q in wc if q in d[k]} for k in women if k not in s.placed};cart_options={k:v for k,v in cart_options.items() if v}
 s.keep('I',lambda p:any(h(p)==h(q) and p[0]<q[0] and p[1]<q[1] for q in d['F']));s.keep('F',lambda q:any(h(p)==h(q) and p[0]<q[0] and p[1]<q[1] for p in d['I']))
 cart_options={k:{q for q in wc if q in d[k]} for k in women if k not in s.placed};cart_options={k:v for k,v in cart_options.items() if v};assert set(cart_options)=={'F'},cart_options
 s.d['F']&=wc;s.put('F');s.keep('I',lambda p:h(p)==1 and p[0]<12 and p[1]<4);s.keep('H',lambda p:p[0]==15);s.put('H')
 s.emit('球车女性是 Flor，Harry 落在 R15C1','只剩 F 能坐 1 号洞球车，且 I 必须在她西北。F 因而在 R12C4，H 在 R15C1，I 锁定第 3 列。',['F','H','I'],['A 必须靠水，B 必须在 4 号洞，N 必须在沙坑，E/J/M 已落位，都不可能是车上女性。','I 若在球车 R12C4，F 必须在其东南且同洞，但 1 号洞没有更东的可用格；R12C1 又被第 15 行唯一空格 R15C1 锁列。','F 若在 R12C1，I 没有更西的列，因此 F 在 R12C4。','第 15 行只能在 1 号洞：R15C2 被 G 占列，R15C3 是树，所以 R15C1 必有人。','1 号洞的可用列只剩 C1、C3、C4，至多三人；H、F、I 已经是三名不同的人，所以不能再加入第四人。F 在第 12 行，I 在她北方，第 15 行因此只能是 H。'])
 s.reserve_col(3,['I'])
 # even hole2 needs companion only row4 after occupied rows1 2 3 5 ; rows6 candidate C1 blocked, C2 tree, thus row4C6 after columns1..5 etc
 available={p for p in s.free if h(p)==2 and all(compatible(p,q) for q in s.placed.values()) and p[1]!=3};assert available=={(4,6)},available
 s.block({p for p in s.free if (p[0]==4 or p[1]==6) and p!=(4,6)})
 s.emit('2 号洞需要一位同伴，保留 R4C6','G 在偶数的 2 号洞，不能独处。排除已占行列和 I 锁定的第 3 列后，该洞只剩 R4C6 能再放一人。',['G','D'],['2 号洞需要偶数人数，已有一人，至少再有一人。','现存空格只有 R4C6，因此这一格必有人；身份尚未确定。','其他人物不能使用第 4 行或第 6 列的别处，先利用位置确定带来的排除。'])
 s.put('D');s.emit('确定 Drew：R10C10','旗杆旁候选结合已占行列与 R4C6 的保留后，D 只剩 8 号洞 R10C10。',['D'],['D 是旗杆旁，不是站在旗杆上。','只计算同洞的上下左右邻格；水域边界不是洞与洞的分界。'])
 s.put('I');s.emit('确定 Iris：R11C3','D 占第 10 行后，I 在 F 西北的候选只剩 R11C3。',['I','F'],['I、F 都在 1 号洞；I 的行号 11 小于 F 的 12，列号 3 小于 F 的 4。'])
 s.put('A');s.emit('确定 Anna：R9C7','I 占第 11 行及第 3 列后，A 靠水的候选只剩 7 号洞 R9C7。',['A'],['水旁的格子必须仍是可站立陆地，并且在同洞中与水上下左右相邻。'])
 s.keep('N',lambda p:h(p)!=2);s.keep('N',lambda p:h(p)<8);s.put('N')
 s.emit('Naomi 不能去 2 或 8 号洞','F 在 1 号洞，且她的洞不能恰好比 N 小 1，故 N 不在 2 号洞；L 又必须在 N 后面的洞，所以 N 不在 8 号洞。N 只剩 R7C8。',['N','F','L'],['N 的沙坑候选分别受地形、行列和洞号限制。','排除 2、8 号洞之后，只剩 7 号洞沙坑 R7C8。'])
 s.put('B');s.emit('确定 Breta：R8C13','N 占第 7 行和第 8 列，B 在 4 号洞树旁只剩 R8C13。',['B'],['B 的洞号 4 大于 H 的洞号 1，满足最开始使用的关系线索。'])
 s.keep('L',lambda p:h(p)>h(s.placed['N']));s.put('L');s.emit('确定 Lars：R6C14','N 在 7 号洞，L 洞号更大，只能在 8 号洞；剩余格唯一为 R6C14。',['L','N'],['大于 7 的洞号只有 8。','D 与 L 在 8 号洞，构成偶数的两人。'])
 s.put('C');s.emit('确定 Carson：R4C6','C 不能在首列或末列。剩余位置中，5 号洞与 4 号洞的末列均不符，只有先前保留的 R4C6。',['C','G'],['R4C6 是为 G 的同伴保留的位置；现在通过 C 的列限制确定身份。'])
 # remaining V and ? remaining 5 hole person inspect
 for k in IDS:
  if k not in s.placed:
   s.put(k);s.emit(f'确定 {s.map["characters"][IDS.index(k)]["name"]}：{cell(s.placed[k])}','剩余行列与所在洞的人数约束相交后，候选只剩这一格。',[k],['每次落位都删除其他人物的同行、同列候选。','该步落位前的候选域由脚本验证恰好一格。'])
 killer=next(k for k,p in s.placed.items() if k!='V' and room[p]==room[s.placed['V']])
 counts={i:sum(h(p)==i for p in s.placed.values()) for i in range(1,9)};assert all(v%2==i%2 for i,v in counts.items())
 s.emit('按实际同洞关系判定凶手','死者 V 与 Breta 独处于 4 号洞，因此凶手是 B。官方末条提示中的“与 D 独处”是字母笔误。',['B','V'],['最终逐洞人数为：'+ '；'.join(f'{i} 号洞 {v} 人' for i,v in counts.items())+'。','D 实际位于 8 号洞，与 L 同洞，不能用提示里误写的字母替代地图证据。','最终凶手由 V 所在逻辑洞的全部人物计算，再与源 murderer 字段交叉核对。'])
 assert s.near(s.placed['A'],72) and s.near(s.placed['B'],10) and h(s.placed['B'])==4 and h(s.placed['H'])<4
 assert s.placed['C'][1] not in [1,16] and s.near(s.placed['D'],58)
 assert 58 in s.obj[s.placed['E']] and h(s.placed['E'])%2==0
 assert h(s.placed['F'])!=h(s.placed['N'])-1
 assert {k for k in men if 78 in s.obj[s.placed[k]]}=={'G'}
 assert any(71 in s.obj[s.placed[k]] and h(s.placed[k])==h(s.placed['H']) for k in women)
 assert h(s.placed['I'])==h(s.placed['F']) and all(a<b for a,b in zip(s.placed['I'],s.placed['F']))
 assert 78 in s.obj[s.placed['J']] and h(s.placed['J']) in [6,7,8]
 assert h(s.placed['K'])==h(s.placed['M']) and h(s.placed['L'])>h(s.placed['N'])
 assert 58 in s.obj[s.placed['M']] and h(s.placed['M']) in [3,4,5]
 assert s.cells[s.placed['N']]['sand'] and s.placed['O'][0]==1 and s.near(s.placed['O'],10)
 s.finish(killer,{'allPersonalAndParityCluesVerified':True,'holeCounts':counts,'sourceHintCorrection':'hint_8 writes V with D but actual same-hole pair is B/V; murderer=1 agrees with B.'})


def office():
 s=Lesson('the-ceos-office');d=s.d;room=s.room;offices={3,4,5,6,7};women=set('ABEFIJMN');men=set(IDS)-women
 s.keep('A',lambda p:s.near(p,14) and room[p] in offices);s.keep('B',lambda p:room[p]==2);s.keep('C',lambda p:room[p]==5 and 2 not in s.obj[p]);s.keep('D',lambda p:s.near(p,1));s.keep('E',lambda p:2 in s.obj[p] and room[p] in offices-{5});s.keep('G',lambda p:p[0]==1 and 2 in s.obj[p]);s.keep('I',lambda p:room[p]==0);s.keep('K',lambda p:s.near(p,13) and room[p]!=2);s.keep('L',lambda p:p[0]==16 and 2 not in s.obj[p]);s.keep('M',lambda p:room[p]==1);s.keep('N',lambda p:room[p]!=2);s.keep('O',lambda p:room[p]==8)
 for k in IDS:
  if k!='M':s.keep(k,lambda p:room[p]!=1)
 s.keep('F',lambda p:room[p]!=2)
 s.emit('五个办公室，五位未知业主','每间办公室都有且只有一位本室业主，其中包括 CEO。A 必须与唯一的女业主同区；C 必须与 CEO 同区。',['A','C','J'],['业主是身份，不是地图中的额外人物；五位业主分别在 A、B、C、D、CEO 五间办公室。','A 与唯一女业主是两个不同的人，所以 A 自己不是业主。','C 与 CEO 是两个人，所以 C 自己不是 CEO。','M 独占会议室；B 在工位区，且 F、K 不能进入工位区。'])
 s.keep('J',lambda p:room[p]==8 and 2 in s.obj[p]);s.emit('Omar 的同伴只能是 Jolly','O 在厨房，与坐椅子的 A 或 J 同区。A 必须在女业主的办公室，所以不能在厨房；因此 J 在厨房椅子上。',['O','J','A'],['厨房不是五间办公室之一，任何业主都不可能在那里。','J 的厨房椅子候选为 '+fmt(d['J'])+'。'])
 # For each J candidate, find a west cell in exactly 3 distinct offices.
 support={q:{r:{p for p in s.free if room[p]==r and p[1]<q[1] and compatible(p,q)} for r in offices} for q in d['J']}
 s.keep('J',lambda q:sum(bool(ps) for ps in support[q].values())>=3);s.put('J')
 s.emit('确定 Jolly：R10C9','J 西边必须有三位业主，且他们来自三间不同办公室。厨房椅子中只有 R10C9 的西侧能容纳三间办公室的业主。',['J'],['R8C5、R10C5 的西边只涉及办公室 C；R10C7 的西边也无法覆盖三间办公室。','R10C9 的西边恰好涉及办公室 A、C、D。','“西边”只比较列号，三位业主不需要与 J 同行；同行反而不允许。'])
 owners={r:{p for p in s.free if room[p]==r and compatible(p,s.placed['J']) and (p[1]<9 if r in [3,6,7] else p[1]>9)} for r in offices}
 assert {p[1] for p in owners[6]}=={8};owners[3]={p for p in owners[3] if p[1]!=8};assert owners[3]=={(4,7)}
 s.block({p for p in s.free if p[1]==8 and room[p]!=6});s.block({p for p in s.free if (p[0]==4 or p[1]==7) and p!=(4,7)})
 s.emit('匿名业主也能锁列、锁格','办公室 D 的业主必须在 C8；办公室 A 的业主只能在 R4C7。先保留这些位置，暂不指定身份。',['A','E'],['J 西侧的三位业主分别来自办公室 A、C、D。','D 办公室在 J 西边的格子全在 C8，因此 C8 不再给其他区域使用。','A 办公室西侧可用格为 R1C8、R3C8、R4C7、R4C8；去掉被 D 业主锁定的 C8，只剩 R4C7。','R4C7 因而是业主的位置，其余第 4 行和第 7 列格子全部不可用。'])
 s.put('G');s.emit('确定 Grant：R1C14','G 坐在最上面一行。会议室由 M 独占，办公室 A 的 C9 又被 J 占用，只剩办公室 B 的 R1C14。',['G'],['G 是办公室 B 业主的有力候选，但此时先只确定其坐标；身份需要后续关系证明。'])
 s.reserve_row(16,['L']);s.keep('E',lambda p:p[0]!=16);assert {p[0] for p in d['E']}=={13};s.reserve_row(13,['E'])
 s.emit('Leroy 锁底行，Esther 锁第 13 行','L 在第 16 行且不坐椅子。E 的办公室椅子排除第 1、4、16 行和 J 的第 9 列后，只剩第 13 行。',['L','E'],['L 的线索直接保留第 16 行。','E 不能在 CEO 办公室，其剩余椅子位于办公室 C 或 D，第 13 行尚不能确定具体列。','其他人物不能使用第 13、16 行。'])
 s.keep('I',lambda p:p[0]>=14);s.emit('Irene 只能在第 14 或 15 行','I 在走廊，且其南边恰好一位业主。办公室 C、D 的业主都在第 13 行以南，所以 I 不能在走廊第 11、12 行。',['I'],['两间南侧办公室 C、D 都必须各有一位业主。','如果 I 在第 11 或 12 行，两位业主都会在其南边，违反“恰好一位”。','第 13 行留给 E，第 16 行留给 L，所以 I 只剩第 14、15 行。'])
 # Lower four rows: E + another owner + partner (A if E owner else E partner) and I.
 s.keep('C',lambda p:p[0]<13)
 for k in IDS:
  if k not in s.placed:s.keep(k,lambda p:not(room[p]==5 and p[0]>=13))
 s.emit('四个人填满南侧四行，CEO 室下半部为空','办公室 C/D 至少共三人，加上走廊的 I，正好占满第 13–16 行。CEO 办公室只能使用第 11、12 行。',['C','E','I'],['C、D 两间办公室各要一位业主。E 已在这两间办公室之一。','若 E 不是业主，她是在两位业主之外的第三人；若 E 是女业主，A 必须与她同室，仍然至少三人。','再加走廊里的 I，共至少四人，而只有第 13、14、15、16 四行可用。','因此这四行恰好满额，CEO 办公室在这四行不可能再放人。'])
 ceo_options=set().union(*(v for k,v in d.items() if k!='C'))
 s.keep('C',lambda p:any(room[q]==5 and compatible(p,q) for q in ceo_options))
 s.put('C');s.emit('确定 Carter，并保留 CEO 的位置','C 不坐椅子，只能在 CEO 办公室 R12C13。CEO 则必须占 R11C15 的椅子。',['C'],['CEO 室第 11 行原有 R11C13、R11C14、R11C15；第 12 行仅 R12C13 可站立。','C 不能坐 R11C15；G 已占 C14，且若 C 占 R11C13，CEO 将无可用第 12 行，因为唯一格与 C 同列。','所以 C 在 R12C13；CEO 避开 C13、G 的 C14，只能在 R11C15。'])
 # Preserve the anonymous CEO's forced row and column.
 s.block({p for p in s.free if (p[0]==11 or p[1]==15) and p!=(11,15)})
 # F owner relation: owners rows 1..4 or13..16. F cannot rows14 lower (capacity), row4 owner reserved conflicts A nonowner, row2 G.
 s.keep('F',lambda p:p[0]==2);s.put('F')
 s.emit('Flora 只能在 Grant 南一行','F 不可能落在南侧四行，也不可能自己占据 R4C7 的业主位置。因此 F 在 G 南一行，落在 R2C10；G 随之确认为办公室 B 业主。',['F','G'],['F 恰在某位业主南一行；CEO 在第 11 行，下一行已被 C 占。','先排除 F 在南侧四行：E、I、L 已必须在那里。若 E 是业主，A 也要来，加入 F 就是五人。若 E 不是业主，则两间办公室的业主只能由 F 和 L 担任；但 F 是女性，A 仍须加入，又是五人。因此 F 无论有没有业主身份，都不能在南侧四行。','若 F 在 R4C7，她是办公室 A 业主且是唯一女业主，A 必须同室在垃圾桶旁。但 A 的 R3C8 已被办公室 D 业主锁列，其他垃圾桶旁格被占行列，无法满足。','北侧唯一可行是 F 在第 2 行、业主在第 1 行。第 1 行已有 G，所以 G 是业主；第 2 行除 R2C10 外可用格均在 M 独占会议室或被占列。'])
 s.keep('M',lambda p:p[0]==3);s.reserve_row(3,['M']);s.keep('A',lambda p:p!=(4,7));s.put('A')
 s.emit('确定 Aylin：R14C12','第 1、2、4 行已经占用，M 只能在第 3 行。A 不能占业主格 R4C7，所以她在办公室 D 的 R14C12。',['A','M'],['会议室只跨第 1–4 行，M 独处其中，只剩第 3 行。','A 是女业主的同伴，不能把自己同时当作那个女业主。','垃圾桶旁、办公室内的其他候选均被占用行列排除，唯一剩余 R14C12。'])
 s.keep('E',lambda p:room[p]==6 and p[1]<9);s.put('E');s.emit('确定 Esther：R13C8，她是唯一女业主','A 在办公室 D，唯一女业主也必须在这里。E 已锁第 13 行，必须是该业主，并位于 J 西边的 R13C8。',['E','A'],['南侧四行的人数预算恰好为 A、E、I、办公室 C 业主。','若 E 不是女业主，还要在 D 办公室加入另一位女业主，超出四行容量。','D 办公室业主必须在 C8，所以 E 在 R13C8。'])
 s.keep('L',lambda p:room[p]==7);s.put('L');s.emit('确定 Leroy：R16C6，他是办公室 C 业主','南侧四行已由 A、E、I、L 占满，办公室 C 仍必须有一位业主，因此 L 就是该业主，落在 R16C6。',['L','E','A','I'],['A 在办公室 D，E 是 D 业主，I 在走廊；只有 L 能承担办公室 C 业主身份。','底行不坐椅子，再排除已占列，办公室 C 唯一剩余格为 R16C6。'])
 s.put('I');s.emit('确定 Irene：R15C2','A 占第 14 行，L 占第 16 行，I 只能在走廊第 15 行的 R15C2。',['I','L'],['她的南边只有第 16 行的 L 一位业主，符合恰好一位的条件。'])
 s.put('O');s.emit('确定 Omar：R8C5','行列限制更新后，厨房只剩 R8C5 可以放 O。',['O','J'],['O 与 J 同在厨房，J 坐在 R10C9 的椅子上，满足两人的关联线索。'])
 s.put('K');s.emit('确定 Kaleb：R7C3','K 不能与 B 同在工位区。结合已占行列，剩余书架旁候选只有前台的 R7C3。',['K'],['隔着区域墙的书架不算“旁边”；只检查同一区域上下左右。'])
 s.put('M');s.emit('确定 Monica：R3C4','K 占第 3 列，会议室第 3 行剩余候选只剩 R3C4。',['M'],['M 独占会议室；第 3 行的其他椅子和空格已被占列。'])
 # N cannot ownerA female; remaining room B? map candidates inspect
 s.keep('N',lambda p:p not in [(4,7),(11,15)]);s.put('N');s.emit('确定 Nina：R9C1','N 不在工位区；她也不能占 R4C7 的业主位置，因为唯一女业主已经是 E。剩余候选为前台 R9C1。',['N','E'],['R11C15 是 CEO 的业主位置，N 同样不能成为第二位女业主。','因此所有办公室业主保留格都不能给 N，结合个人线索只剩前台。'])
 s.put('D');s.emit('确定 Dillard：R6C16','N 占第 9 行和第 1 列，D 的植物旁候选只剩 R6C16。',['D'],['D 的落位随后会约束 H 的列：H 不能在相邻的第 15 列。'])
 s.put('B');s.emit('确定 Beatriz：R5C11','工位区内剩余满足行列的格子只有 R5C11，B 落位。',['B'],['F 在办公室 A，K 在前台，二者均不与 B 同区。'])
 s.keep('H',lambda p:abs(p[1]-s.placed['D'][1])!=1);s.put('H');s.emit('确定 Hans：R4C7','H 不能在 D 的相邻列。D 在 C16，所以 H 不能去 C15 的 CEO 位置，只能成为办公室 A 的业主。',['H','D'],['剩下两个匿名业主位置是 R4C7 和 R11C15。','H 的列不与 D 相邻，排除后者。'])
 s.put('V');s.emit('确定死者 Vincent：R11C15','最后一个位置是 CEO 的 R11C15，所以死者 V 就是 CEO。',['V','C'],['16 人全部落位，每行每列恰好一人。','五位业主为 H（A 办公室）、G（B）、L（C）、E（D）、V（CEO）。唯一女业主是 E。'])
 s.emit('Carter 是凶手','CEO 办公室只有 C 和死者 V，满足死者与凶手独处。因此凶手为 Carter。',['C','V'],['C 与 CEO 同区的线索和 V 与凶手独处的线索，在最终地图上指向同一组两人。','所有业主身份来自房间、性别与人数预算；没有把原始答案里的身份当作前提。'])
 owner_ids=set('HGLEV');assert sum(k in women for k in owner_ids)==1
 assert {room[s.placed[k]] for k in owner_ids}==offices
 assert room[s.placed['A']]==room[s.placed['E']] and s.near(s.placed['A'],14)
 assert room[s.placed['B']]==2 and room[s.placed['F']]!=2 and room[s.placed['K']]!=2
 assert room[s.placed['C']]==5 and 2 not in s.obj[s.placed['C']]
 assert s.near(s.placed['D'],1) and 2 in s.obj[s.placed['E']] and room[s.placed['E']]!=5
 assert any(s.placed['F'][0]==s.placed[k][0]+1 for k in owner_ids)
 assert s.placed['G'][0]==1 and 2 in s.obj[s.placed['G']]
 assert abs(s.placed['H'][1]-s.placed['D'][1])!=1
 assert room[s.placed['I']]==0 and sum(s.placed[k][0]>s.placed['I'][0] for k in owner_ids)==1
 assert sum(s.placed[k][1]<s.placed['J'][1] for k in owner_ids)==3
 assert s.near(s.placed['K'],13) and s.placed['L'][0]==16 and 2 not in s.obj[s.placed['L']]
 assert {k for k in IDS if room[s.placed[k]]==1}=={'M'} and room[s.placed['N']]!=2
 assert room[s.placed['O']]==8==room[s.placed['J']] and 2 in s.obj[s.placed['J']]
 s.finish('C',{'allPersonalAndOwnerCluesVerified':True,'owners':{'Office A':'H','Office B':'G','Office C':'L','Office D':'E','CEO':'V'}})

if __name__=='__main__':
 golf();office()
