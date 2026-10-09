"""Derive the expert lesson from clues; consult stored answers only at the end."""
import json,copy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
raw=json.loads((root/'sources/the-zoo.json').read_text());g=raw['GRID'];ids=list('ABCDEFGHIJKLMNOV');cells=[(r,c) for r in range(1,17) for c in range(1,17)];n=lambda k:int(float(g[k]));sub={i:n(f'room_subroom_mainroom_{i}') if n(f'room_subroom_{i}') else i for i in range(14)}
region={p:n(f'room_code_{p[1]-1}_{p[0]-1}') for p in cells};room={p:sub[region[p]] for p in cells};obj={p:n(f'room_objects_{p[1]-1}_{p[0]-1}') for p in cells}
for p in [q for q in cells if obj[q]==54]:
 if obj[p]==54:
  for dr,dc in [(0,1),(1,0),(1,1)]:obj[(p[0]+dr,p[1]+dc)]=54
free={p for p in cells if obj[p] in [0,2]};water={p for p in cells if region[p] in [2,10,11,12,13]};hab={1,2,3,5,6,8};animals={26,47,52,53,54,55}
def beside(p,ps):return any(q in ps and room[q]==room[p] for q in [(p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1)])
def near(p,os):return beside(p,{q for q in cells if obj[q] in os})
def compatible(p,q):return p[0]!=q[0] and p[1]!=q[1]
d={k:{p for p in free if room[p] not in hab} if k<'I' else set(free) for k in ids}
d['B']={p for p in d['B'] if room[p]==9};d['D']={p for p in d['D'] if room[p]==0};d['E']={p for p in d['E'] if near(p,{4}) and obj[p]!=2};d['F']={p for p in d['F'] if near(p,{2})};d['G']={p for p in d['G'] if obj[p]==2};d['I']={p for p in free if near(p,animals)};d['J']={p for p in free-water if beside(p,water)};d['L']={p for p in free&water if not near(p,animals)};d['M']={p for p in free if p[1]==2};d['N']={p for p in free if near(p,{10,11})};d['O']={p for p in free if near(p,{43})};placed={}
def show():
 for k in ids:print(k, placed.get(k) or sorted(d[k]))
def place(k):
 assert len(d[k])==1,(k,d[k]);p=next(iter(d[k]));placed[k]=p;d[k]=set()
 for t in ids:
  if t not in placed:d[t]={q for q in d[t] if compatible(p,q)}
def cell(p):return f'R{p[0]}C{p[1]}'
def fmt(ps):return '、'.join(map(cell,sorted(ps)))
initial=copy.deepcopy(d);previous=copy.deepcopy(d);lastplaced={};steps=[];proofs=[]
def emit(title,text,focus,highlights,rule,details,blocks=()):
 global previous,lastplaced
 num=len(steps)+1;refs=[k+'-clue' for k in ids]+['general-roles','general-habitats'];reason={'ruleId':rule,'clueRefs':refs,'dependsOn':[f'zoo-{num-1}'] if num>1 else []};actions=[]
 for k in ids:
  if num==1:actions.append({'type':'setCandidates','character':k,'cells':list(map(cell,sorted(d[k])))})
  else:
   for p in sorted(previous[k]-d[k]):
    if placed.get(k)!=p:actions.append({'type':'removeCandidate','character':k,'cell':cell(p),'reason':reason})
  if k in placed and k not in lastplaced:actions.append({'type':'placeCharacter','character':k,'cell':cell(placed[k]),'reason':reason})
 if blocks:actions.append({'type':'blockCells','cells':list(map(cell,sorted(blocks))),'reason':reason})
 steps.append({'id':f'zoo-{num}','title':title,'explanation':text,'focusCharacters':focus,'highlightCells':list(map(cell,sorted(highlights))),'clueRefs':refs,'actions':actions,'rule':rule,'details':details})
 proofs.append({'step':num,'placements':{k:cell(p) for k,p in placed.items()},'candidates':{k:list(map(cell,sorted(v))) for k,v in d.items()}});previous=copy.deepcopy(d);lastplaced=placed.copy()
def restrict(k,predicate):d[k]={p for p in d[k] if predicate(p)}
emit('先认身份，不急着落位','A–H 是 8 名游客，I–O 和 V 是 8 名饲养员。游客不能进入栖息地；6 个栖息地都至少有一名饲养员。',['M','J','L'],[],'先处理全局条件',['16 人对应 16 行、16 列，最终每行每列恰好一人。死者 V 也计入人数。','蓝色水域是所在栖息地的一部分，不是额外房间；水岸不算区域墙。','旁边指同一区域的上下左右邻格。大象占 2×2 格，这四格都不能站人。','M 在第 2 列；J 不在水里但紧邻水；L 在水里且不靠动物。可以先点击他们查看原始候选。'])
for k in ['G','H']:restrict(k,lambda p:room[p] in [4,7])
for k in ids:
 if k not in ['G','H']:restrict(k,lambda p:room[p] not in [4,7])
emit('两名独处游客，占据栈道和入口','D 已在主游览区，B 与另一名游客在小卖部。因此独处的 G、H 只能分别在栈道和入口，暂时不知道谁在哪边。',['G','H','B','D'],d['G']|d['H'],'先确定区域，再确定格子',['游客能去的只有主游览区、小卖部、栈道、入口。','G 和 H 都独处，不能与 D 同区，也不能进入已有 B 和同伴的小卖部。','两人不能同区，所以恰好一人占栈道、一人占入口；其他人都不能去这两个区域。'])
blocks={p for p in free if room[p]==1 and p[1]>=14}
for k in ids:d[k]-=blocks
assert {room[p] for p in d['N']}=={6}
emit('三个人锁住最右三列','小卖部的两人和入口的一人，都只能使用 C14–C16。三列被他们占满，熊栖息地的这三列全部排除，N 只能在鳄鱼区的树旁。',['N','B','H','G'],blocks,'三个人锁定三列',['小卖部所有可站立格均在 C14、C15、C16，入口也只在这三列。','三个人不能同列，因此恰好用满三列，无需先确定各自的位置。','N 在树旁的原始候选只分布于熊区和鳄鱼区。熊区候选恰好全在被保留的三列。','N 还剩 '+fmt(d['N'])+'，都在鳄鱼栖息地。'],blocks)
for k in ids[8:]:restrict(k,lambda p:room[p] in hab)
for k in ['I','J','K','L','M','O']:restrict(k,lambda p:room[p]!=6)
emit('八名饲养员，只有两对能同区','K 与 M 是一对；V 与凶手是另一对。8 人要覆盖 6 个栖息地，这两对正好用完多出的 2 人。因此其他饲养员之间不能同区。',['K','M','V','N'],[],'用人数预算限制同区关系',['8 名游客中，栈道、入口各 1 人，小卖部 2 人，剩下 4 人只能在主游览区。','K、M 要两人独处，V 也要与凶手独处；四个游客区域都容不下这些组合，所以两对必须在栖息地。','6 个栖息地各放 1 人，再给 K/M 和 V/凶手各加 1 人，恰好需要全部 8 名饲养员。因此凶手也是饲养员。','除 K/M 外，任意两名非 V 的饲养员不能同区。N 在鳄鱼区，所以 I、J、K、L、M、O 均不能进鳄鱼区；V 此时仍有可能与 N 同区。'])
assert {p[1] for p in d['J']}=={8}
for k in ids:
 if k!='J':restrict(k,lambda p:p[1]!=8)
for k in ids:
 if k!='M':restrict(k,lambda p:p[1]!=2)
emit('Jim 锁第 8 列，Mara 锁第 2 列','J 的临水陆地候选只剩 R2C8、R9C8；M 的线索直接指定第 2 列。其他人物都不能再使用这两列。',['J','M'],d['J'],'一列被锁定，不必等人物落位',['J 的熊区候选在已保留的 C14、C16，鳄鱼区候选又与 N 同区，均不成立。','所以 J 只能在企鹅区 R2C8 或大象区 R9C8：行未定，列已定。','M 在 C2 是原始线索。两次列排除都对所有其他人物有效。'])
assert d['E']=={(10,14)};place('E')
emit('确定 Eloise：R10C14','E 要在桌旁，但不能坐椅子。排除第 2、8 列以及由 G/H 独占的入口后，只剩小卖部的 R10C14。',['E'],[placed['E']],'把全局限制带回个人线索',['桌旁的椅子不符合“没有坐着”，先排除。','主游览区的桌旁空格 R6C2、R15C8 分别被 M、J 占列。','入口由 G/H 中的一人独占，所以 E 不能在那里。','小卖部唯一不坐椅子的桌旁空格为 R10C14，E 正是与 B 同区的那名游客。'])
assert d['G']=={(12,1)};place('G');restrict('H',lambda p:room[p]==4)
emit('确定 Gordon，Henry 留在入口','E 占 C14，入口的两把椅子都失效。G 只能坐栈道的 R12C1；H 因而独处于入口。',['G','H'],[placed['G']],'区域二选一也会连锁落定',['G 原来能坐栈道 R12C1，或入口 R12C14、R16C14。','入口两把椅子都与 E 同列，因此排除。','G 独占栈道，H 只能在入口。栈道其余格可以全部打叉。'],{p for p in free if room[p]==7 and p!=placed['G']})
assert d['L']=={(1,9)};place('L')
for k in ['I','J','K','M','N','O']:restrict(k,lambda p:room[p]!=room[placed['L']])
emit('确定 Langston：R1C9','L 需要在水里且不靠动物。结合 N 的区域限制、保留列和已占行列，唯一剩下的是企鹅区 R1C9。',['L','N'],[placed['L']],'水域条件与区域人数一起用',['熊区水域在已被游客保留的 C14–C16，不能用。','鳄鱼区已有 N；L 不能与另一名非 V 饲养员同区。','大象区符合“不靠动物”的水格都在 J 锁定的 C8。','鲨鱼区符合条件的水格都在 G 占用的 C1；企鹅区只剩 R1C9。'])
assert d['J']=={(9,8)};place('J')
emit('确定 Jim：R9C8','企鹅区已有 L，J 不能与 L 同区。因此他的两个临水陆地候选只剩大象区 R9C8。',['J','L'],[placed['J'],placed['L']],'同区限制区分最后两个候选',['J 原有 R2C8、R9C8 两个候选。','J 与 L 既不是 K/M 组合，也没有 V，不能成为同区的一对。','排除企鹅区 R2C8，J 落位后占第 9 行。'])
assert d['B']=={(8,16)};place('B')
emit('确定 Barry：R8C16','小卖部里，E 已占第 10 行、第 14 列，J 又占第 9 行。B 只能在 R8C16。',['B','E','J'],[placed['B']],'区域内筛选剩余行列',['小卖部的第 11 行只有 C14 能站人，但该列已被 E 占据。','第 9 行被 J 占，第 10 行被 E 占。','第 8 行有 C14、C16 两把椅子；C14 被排除，只剩 C16。'])
assert d['N']=={(7,3)};place('N')
emit('确定 Nancy：R7C3','N 在鳄鱼区的四个树旁候选，已有三个被第 8、9、10 行排除，只剩 R7C3。',['N'],[placed['N']],'追踪连续落位带来的行排除',['四格原本是 R7C3、R8C3、R9C4、R10C3。','B 占第 8 行，J 占第 9 行，E 占第 10 行。','因此 N 不需要试放，直接落在第 7 行。'])
assert d['H']=={(14,15)};place('H')
emit('确定 Henry：R14C15','H 独处入口。E 和 B 占了 C14、C16，而 C15 上剩余可用格只有 R14C15。',['H'],[placed['H']],'先筛列，再筛可站立格',['入口位于 C14–C16。C14 属于 E，C16 属于 B，所以 H 必须在 C15。','C15 的其他入口格是桌子；唯一空格为 R14C15。'])
assert d['O']=={(2,13)};place('O')
emit('确定 Oliver：R2C13','把“巨石旁”与已占行列叠加，O 只剩熊栖息地的 R2C13。',['O'],[placed['O']],'每次落位后，重新扫描局部线索',['当前已占第 1、7、8、9、10、12、14 行和第 1、3、8、9、14、15、16 列。','O 也不能进入已有 N 的鳄鱼区或已有 L 的企鹅区。','剩余巨石旁空格中，唯一同时避开占用行列的是 R2C13。'])
for k in ['I','K','M']:restrict(k,lambda p:room[p] not in {room[placed[t]] for t in ['J','L','N','O']})
for k in ['A','C','D','F']:restrict(k,lambda p:room[p]==0)
restrict('I',lambda p:any(a[0]+1==p[0] and compatible(a,p) for a in d['A']))
assert d['I']=={(4,5)};place('I');restrict('A',lambda p:p[0]+1==placed['I'][0]);assert d['A']=={(3,7)};place('A')
emit('相邻两行，确定 Ivan 与 Alfred','I 只能在狮子区或鲨鱼区的动物旁。A 必须在他正北一行且位于主游览区，这只支持 I 在 R4C5、A 在 R3C7。',['I','A'],[placed['I'],placed['A']],'关系线索需要双方都可落位',['J、L、N、O 各占一个栖息地，I 不能与他们同区，所以只检查狮子区和鲨鱼区。','A 是游客；入口和栈道已独占，小卖部是 B/E，因此 A 必在主游览区。','逐个查看 I 的动物旁候选：其上一行必须有 A 能用的主游览区格，还要避开已占行列。','只有 R4C5 上一行的 R3C7 成立。“北一行”不要求同列；同行同列规则反而禁止两人同列。'])
for k in ['K','M']:restrict(k,lambda p:room[p]!=room[placed['I']])
assert d['K']=={(15,4)};place('K');restrict('M',lambda p:room[p]==room[placed['K']])
emit('确定 Kaiden：R15C4','狮子区已有 I，其他四个栖息地也已有非 V 饲养员。K/M 这一对只能进入鲨鱼区，K 只剩 R15C4。',['K','M'],[placed['K']],'用覆盖全部区域的要求收束位置',['K 与 M 必须独处于同一栖息地。','除了鲨鱼区，其余五个栖息地都有其他非 V 饲养员，不能再容纳 K/M。','M 锁定 C2；扣除其他已占行列和动物、巨石，K 只剩 R15C4。'])
restrict('C',lambda p:any(p[0]+1==q[0] and compatible(p,q) for q in d['D']));restrict('D',lambda q:any(p[0]+1==q[0] and compatible(p,q) for p in d['C']))
assert {p[0] for p in d['C']}=={5} and {p[0] for p in d['D']}=={6}
for k in ids:
 if k not in ['C','D'] and k not in placed:restrict(k,lambda p:p[0] not in [5,6])
emit('Carolyn 与 Deborah 锁住第 5、6 行','C 恰在 D 北一行。两人都在主游览区，剩余候选中只有第 5、6 行这一组相邻行成立，先把这两行保留给她们。',['C','D'],d['C']|d['D'],'相邻关系可以先锁行，不急着锁格',['C、D 都是剩余游客；其他三个游客区域已经人数满额，所以两人都在主游览区。','扣除已占用的行，只有 C 在第 5 行、D 在第 6 行能满足“恰好北一行”。','C 还有 '+fmt(d['C'])+'；D 还有 '+fmt(d['D'])+'。','即使具体列未定，其他人物也不能使用第 5、6 行。'])
assert d['F']=={(16,10)};place('F')
emit('确定 Flavia：R16C10','F 要在椅子旁。第 5、6 行被 C/D 保留后，最后可用的椅子旁格是主游览区 R16C10。',['F'],[placed['F']],'保留行也能排除其他人的候选',['已经占用的行列筛掉了大部分椅子旁格。','入口、栈道和小卖部不能再容纳 F，因此只检查主游览区。','第 5、6 行的候选最后被 C/D 的连续两行关系排除。'])
assert d['M']=={(13,2)};place('M')
emit('确定 Mara：R13C2','M 与 K 同在鲨鱼区，并且必须在 C2。F 占第 16 行后，M 只剩 R13C2。',['M','K'],[placed['M']],'把同区和指定列交叉使用',['K 已在鲨鱼区 R15C4，因此 M 也必须进入鲨鱼区。','C2 上符合行列约束的最后两格为 R13C2、R16C2。','F 落在第 16 行，排除后者。'])
assert d['C']=={(5,6)};place('C');assert d['D']=={(6,11)};place('D')
emit('确定 Carolyn 与 Deborah','F 占第 10 列，C 只能落在 R5C6；随后第 6 列被占，D 只剩 R6C11。',['C','D'],[placed['C'],placed['D']],'锁行之后，再用列完成落位',['C 的两个候选原为 R5C6、R5C10；F 的 C10 排除后者。','D 原为 R6C6、R6C10、R6C11。F 占 C10，C 占 C6，故 D 在 C11。'])
assert d['V']=={(11,12)};place('V')
emit('确定死者 Vlad：R11C12','15 人已经落位，最后空着的是第 11 行和第 12 列。V 位于交点 R11C12，在大象栖息地。',['V'],[placed['V']],'最后一行与最后一列相交',['死者同样占用一行、一列。','R11C12 可站立，没有被大象覆盖；大象位于 R10–R11 的 C10–C11。','落位后 16 行和 16 列各恰好一人。'])
assert {k for k,p in placed.items() if room[p]==room[placed['V']]}=={'J','V'}
emit('Jim 是凶手，回看整条证据链','大象栖息地里只有 J 和死者 V，符合死者“与凶手独处”的线索。因此凶手是 Jim。',['J','V'],[placed['J'],placed['V']],'身份结论来自独处关系',['最终区域人数：狮子 I；企鹅 L；熊 O；鳄鱼 N；鲨鱼 K/M；大象 J/V。六个栖息地均有人。','游客区域：栈道 G；入口 H；小卖部 B/E；主游览区 A/C/D/F。','整条主线只使用线索、区域人数与行列排除，没有试猜位置。'])
# Keep the population overview legible; clicking a person still reveals their candidates.
steps[2]['candidateCharacters']=['N']
steps[3]['candidateCharacters']=[]
p=raw['PROPERTIES'];official={k:(int((float(raw['CHARACTERS'][f'letter_ypos_{i}'])-float(p['grid_ry']))/float(p['cellsize']))+1,int((float(raw['CHARACTERS'][f'letter_xpos_{i}'])-float(p['grid_rx']))/float(p['cellsize']))+1) for i,k in enumerate(ids)}
assert placed==official,(placed,official);assert ids[int(float(p['murderer']))]=='J'
(root/'src/tutorial/data/the-zoo.json').write_text(json.dumps(steps,ensure_ascii=False,indent=2))
(root/'analysis/zoo-proof.json').write_text(json.dumps({'initial':{k:list(map(cell,sorted(v))) for k,v in initial.items()},'snapshots':proofs,'final':{k:cell(p) for k,p in placed.items()},'officialMatch':True},ensure_ascii=False,indent=2))
# Preserve subroom colors without introducing walls or an extra logical room.
def color(v):
 v=int(float(v));return '#'+''.join(f'{(v>>s)&255:02x}' for s in [0,8,16])
labels={0:'主游览区',1:'熊栖息地',2:'鲨鱼栖息地',3:'狮子栖息地',4:'入口',5:'大象栖息地',6:'鳄鱼栖息地',7:'栈道',8:'企鹅栖息地',9:'小卖部'}
kinds={2:'chair',4:'table',10:'tree',11:'palmtree',26:'shark',37:'shrub',43:'boulder',47:'lion',52:'crocodile',53:'bear',54:'elephant',55:'penguin'}
names={2:'椅子',4:'桌子',10:'树',11:'棕榈树',26:'鲨鱼',37:'灌木',43:'巨石',47:'狮子',52:'鳄鱼',53:'熊',54:'大象',55:'企鹅'}
zh=['他恰好在 Ivan 北边一行。','他在小卖部，与一名游客独处。','她恰好在 Deborah 北边一行。','她在主游览区。','她在桌子旁，没有坐着。','她在椅子旁边。','他坐在椅子上，独处。','他独处。','他在动物旁边。','他不在水里，但在水旁。','她与 Mara 独处。','他在水里，不在动物旁边。','她在第 2 列。','她在树旁边。','他在巨石旁边。','死者。他与凶手独处。']
objects=[]
for r,c in cells:
 oid=n(f'room_objects_{c-1}_{r-1}')
 if oid:
  size=2 if oid==54 else 1
  objects.append({'id':f'object-{r}-{c}','kind':kinds[oid],'cells':[cell((r+dr,c+dc)) for dr in range(size) for dc in range(size)],'asset':f'/assets/zoo/objects/{kinds[oid]}.svg','x':c-1,'y':r-1,'width':size,'height':size})
rooms=[{'id':i,'label':labels[i],'fill':color(g[f'room_color_0_{i}']),'cells':[cell(q) for q in cells if room[q]==i]} for i in labels]
positions={0:(1050,1585),1:(1380,687),2:(165,1585),3:(250,487),4:(1450,1585),5:(1010,1385),6:(285,1085),7:(580,1585),8:(900,387),9:(1460,1085)}
puzzle={'id':'the-zoo','width':16,'height':16,'cells':[{'id':cell(q),'row':q[0],'col':q[1],'roomId':room[q],'occupiable':q in free,'carpet':False,'objectIds':[obj[q]] if obj[q] else [],'fill':color(g[f'room_color_0_{region[q]}']),'texture':'water' if q in water else ('grass' if room[q] in hab else 'woodentile'),'water':q in water} for q in cells],'objects':objects,'rooms':rooms,'roomLabels':[{'label':labels[i],'x':positions[i][0],'y':positions[i][1]} for i in labels],'objectNames':names,'characters':[{'id':k,'name':raw['CHARACTERS'][f'char_name_{i}'],'portrait':f'/assets/zoo/portraits/{k}.svg','clueId':k+'-clue','clueZh':zh[i],'clueEn':' '.join(raw['CHARACTERS'].get(f'char_{part}_en_{i}','') for part in ['quote','subquote']),'role':'游客' if i<8 else '饲养员'} for i,k in enumerate(ids)],'generalClues':[{'id':'general-roles','text':'A–H 为游客，I–O 与 V 为饲养员；仅饲养员能进栖息地。'},{'id':'general-habitats','text':'6 个栖息地，每个都至少有一名饲养员。'}]}
(root/'src/case/data/the-zoo.json').write_text(json.dumps(puzzle,ensure_ascii=False,indent=2))
md=['# The Zoo 专家题逐步推理','来源：https://murdoku.com/play/puzzle-the-zoo-expert','原始提示只作推理方向参考，候选由地图与线索计算。最后才读取答案字段交叉核对。','']
for i,s in enumerate(steps,1):md+=['## '+str(i)+'. '+s['title'],s['explanation'],'']+['- '+t for t in s['details']]+['']
(root/'analysis/zoo-walkthrough.md').write_text('\n'.join(md))
print(len(steps),'main steps',sum(len(s['details']) for s in steps),'details. All forced placements match source.')
