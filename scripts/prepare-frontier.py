"""Source-based Frontier Town lesson. Answer fields are used only for final validation."""
import json,re,copy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
raw=json.loads((root/'sources/frontier-town.json').read_text());g=raw['CHARACTERS'];ids=list('ABCDEFGHIV')
cells=[(r,c) for r in range(1,11) for c in range(1,11)]
room={p:int(g[f'room_code_{p[0]-1}_{p[1]-1}']) for p in cells};obj={p:int(g[f'room_objects_{p[0]-1}_{p[1]-1}']) for p in cells}
free={p for p in cells if obj[p] in [0,2,6,15]}
def beside(p,kind):return any(q in obj and room[q]==room[p] and obj[q]==kind for q in [(p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1)])
def corner(p):
 r,c=p;wall=lambda q:q not in room or room[q]!=room[p]
 return (wall((r-1,c)) or wall((r+1,c))) and (wall((r,c-1)) or wall((r,c+1)))
def compatible(p,q):return p[0]!=q[0] and p[1]!=q[1]
def cell(p):return f'R{p[0]}C{p[1]}'
def fmt(ps):return '、'.join(cell(p) for p in sorted(ps))
d={k:set(free) for k in ids}
d['A']={p for p in free if beside(p,94)};d['B']={p for p in free if corner(p)};d['C']={p for p in free if obj[p]==2};d['D']={p for p in free if beside(p,2)};d['E']={p for p in free if room[p]==5};d['F']={p for p in free if obj[p]==15};d['G']={p for p in free if beside(p,16)};d['H']=d['C'].copy()
initial=copy.deepcopy(d);placed={};steps=[];previous={k:set() for k in ids};lastplaced={};proofs=[]
def partners(h):return [(k,p) for k in ids if k not in ['D','V','H','I'] for p in d[k] if room[p]==room[h] and beside(p,4) and compatible(p,h)]
def place(k,p):
 assert d[k]=={p},f'{k} not unique: {d[k]}'
 placed[k]=p;d[k]=set()
 for t in ids:
  if t not in placed:d[t]={q for q in d[t] if compatible(p,q)}
def emit(title,explanation,focus,highlights,rule,details,refs=None):
 global previous,lastplaced
 n=len(steps)+1;reason={'ruleId':rule,'clueRefs':refs or [k+'-clue' for k in focus],'dependsOn':[f'frontier-{n-1}'] if n>1 else []};actions=[]
 for k in ids:
  if n==1:actions.append({'type':'setCandidates','character':k,'cells':list(map(cell,sorted(d[k])))})
  else:
   for q in sorted(previous[k]-d[k]):
    if placed.get(k)!=q:actions.append({'type':'removeCandidate','character':k,'cell':cell(q),'reason':reason})
  if k in placed and k not in lastplaced:actions.append({'type':'placeCharacter','character':k,'cell':cell(placed[k]),'reason':reason})
 if n in [5,9,12]:
  blocks={5:[(10,9)],9:[(6,2),(5,5)],12:[(6,5),(1,3)]}[n]
  actions.append({'type':'blockCells','cells':[cell(q) for q in blocks],'reason':reason})
 steps.append({'id':f'frontier-{n}','title':title,'explanation':explanation,'focusCharacters':focus,'highlightCells':[cell(q) for q in highlights],'clueRefs':reason['clueRefs'],'actions':actions,'rule':rule,'details':details})
 proofs.append({'step':n,'candidates':{k:list(map(cell,sorted(v))) for k,v in d.items()},'placements':{k:cell(v) for k,v in placed.items()}});previous=copy.deepcopy(d);lastplaced=placed.copy()
emit('先分清两种身份','这里只有一名亡命徒，且他在桌子旁边；亡命徒不一定是凶手。Hazel 与亡命徒同区，Virgil 与凶手独处。先从 Hazel 的椅子入手。',['H'],list(d['H']),'身份关系也是线索',['旁边指同一区域内的上下左右邻格，斜角和隔墙不算。','south 只要求行号更大，不要求同一列；Ivy 还必须与 Hazel 不同区。','角落是两面垂直墙相交的格子，包括不规则区域的拐角。','每行、每列最多一人；10 人填入 10×10 地图，最终每行、每列恰好一人。'],['H-clue','D-clue','V-clue','general-outlaw'])
support={h:partners(h) for h in d['H']};valid={h for h,ps in support.items() if ps};assert valid=={(7,10)};d['H']=valid
emit('九把椅子都容不下同行者','Hazel 不只是坐椅子，还必须与一名“在桌子旁的亡命徒”同区。把这两个条件合起来，只有银行的 R7C10 成立。',['H'],list(initial['H']),'组合线索，排除整个分支',['户外 R4C3、门廊 R10C6：所在区域没有桌子，无法与桌旁的亡命徒同区。','牧师家 R2C1：可站立的桌旁格只有 R1C1、R2C2，分别与 Hazel 同列、同行。','杂货店 R9C2：桌旁可站立格只有 R9C4、R10C2，也分别同行、同列。','教堂的五把椅子：桌旁格为 R1C6、R1C7、R2C5、R2C8、R3C6、R3C7。A 不在收银机旁，B 不在角落，C 不在椅子上，E 不在银行，F 不在马背，G 不在仙人掌旁；I 必须与 H 不同区，D/V 明确不是亡命徒。所有身份都不成立。','银行 R7C10：Etta 能在 R8C9、R9C9 或 R10C8 的桌旁与她同区，分支可行。'],[k+'-clue' for k in ids]+['general-outlaw'])
place('H',(7,10));emit('确定 Hazel：R7C10','Hazel 坐在银行的椅子上。第 7 行和第 10 列从此不能再放其他人物。',['H'],[(7,10)],'落位后传播行列限制',['这不是猜测：上一阶段已排除其他九把椅子。','银行只有这一把椅子能满足 Hazel 的两个条件。'])
e={p for k,p in support[(7,10)] if k=='E'};assert {k for k,p in support[(7,10)]}=={'E'};d['E']&=e
emit('Etta 就是亡命徒','银行里，只有 Etta 的个人线索允许她站在桌子旁。她暂时有 R8C9、R9C9、R10C8 三个候选。身份确定了，位置还没有。',['E','H'],sorted(d['E']),'身份确定不等于位置确定',['逐人检查银行的桌旁格：A 需要收银机，B 需要角落，C 需要椅子，F 需要马，G 需要仙人掌，都不符。','Ivy 必须与 Hazel 不同区；Duke 和 Virgil 明确不是亡命徒。','Etta 的唯一位置条件是在银行，三个桌旁格都满足。'],[k+'-clue' for k in ids]+['general-outlaw'])
assert all(not compatible((10,9),p) for p in d['E']);d['A'].discard((10,9));assert d['A']=={(9,4)};place('A',(9,4))
emit('不用确定 Etta，也能确定 Abigail','R10C9 与 Etta 的三个候选全部冲突，因此 Abigail 不能在那里。另一处 R9C10 已被 Hazel 占列，Abigail 只剩 R9C4。',['A','E'],[(10,9),(9,4),(8,9),(10,8)],'候选交叉格排除',['如果 Etta 在 R8C9 或 R9C9，R10C9 与她同列。','如果 Etta 在 R10C8，R10C9 与她同行。','所以无论 Etta 最后选哪一格，其他人都不能站 R10C9。','Abigail 的原始候选为 R9C4、R9C10、R10C9。排除后只剩 R9C4。'])
d['I']={p for p in d['I'] if p[0]>7 and room[p]!=5};assert {p[0] for p in d['I']}=={8,10};assert {p[0] for p in d['E']}=={8,10}
for k in ids:
 if k not in placed and k not in ['E','I']:d[k]={p for p in d[k] if p[0] not in [8,10]}
emit('第 8、10 行，留给 Etta 和 Ivy','Ivy 在 Hazel 南方且不在银行；第 9 行已被 Abigail 占据。她和 Etta 都只能用第 8、10 行，因此这两行不再留给其他人。',['E','I'],sorted(d['E']|d['I']),'两个人锁定两行',['Hazel 在第 7 行，Ivy 的行号必须大于 7，所以原本只能是 8、9、10 行。','Abigail 占第 9 行；Etta 也只剩 R8C9、R10C8。','两人必须分处不同行，因此恰好占满第 8、10 行。暂时不必知道谁在哪一行。'])
assert d['F']=={(4,9)};place('F',(4,9));emit('确定 Frank：R4C9','四匹马逐一筛选后，只剩 R4C9。Frank 占据第 4 行和第 9 列。',['F'],[(1,10),(2,4),(4,9),(8,5)],'把已知行列限制带回个人线索',['R1C10 与 Hazel 同列。','R2C4 与 Abigail 同列。','R8C5 位于为 Etta、Ivy 保留的第 8 行。','所以 Frank 只能在 R4C9。'])
assert d['E']=={(10,8)};place('E',(10,8));d['I']={p for p in d['I'] if p[0]==8};emit('确定 Etta，并锁定 Ivy 的行','Frank 占第 9 列，Etta 的 R8C9 被排除，只剩 R10C8。她占第 10 行，因此 Ivy 必须在第 8 行。',['E','I'],[(10,8)]+sorted(d['I']),'二选一的连锁确定',['Etta 落位前只有 R8C9、R10C8 两个候选。','落位后 Ivy 只剩 R8C2、R8C5、R8C7；暂时保留三格。'])
assert d['G']=={(5,2),(6,5)}
for k in ids:
 if k not in placed and k!='G':d[k]-={(6,2),(5,5)}
emit('Garrett 的二选一，排除交叉格','Garrett 只剩 R5C2、R6C5。无论选哪格，其他人都不能使用 R5C5 或 R6C2。Curtis 在 R5C5 的椅子因此被排除。',['G','C'],[(5,2),(6,5),(5,5),(6,2)],'对角候选产生两个交叉排除',['若 Garrett 在 R5C2，R5C5 同行，R6C2 同列。','若 Garrett 在 R6C5，R5C5 同列，R6C2 同行。','两个分支都排除相同交叉格，所以无需猜 Garrett 的最终位置。'])
assert d['C']=={(2,1)};place('C',(2,1));emit('确定 Curtis：R2C1','现有行列限制已把 Curtis 缩到 R2C1、R5C5 两把椅子。上一阶段排除了后者，因此他只能坐在牧师家。',['C'],[(2,1)],'最后候选落位',['Hazel 占用的椅子不能再用；第 4 行、第 7 行、第 8 行、第 9 行、第 10 行以及第 8、9、10 列已被确定人物或两行锁定排除。','Curtis 落位后，第 2 行和第 1 列也被占据。'])
assert d['B']=={(1,5),(6,3)};emit('Bessie 只剩两个角落','逐一检查区域角落，并扣除已占用行列，Bessie 只剩教堂的 R1C5 和杂货店的 R6C3。',['B'],sorted(d['B']),'角落由区域墙线决定',['角落不是只看整张地图四角，而是所在区域两面垂直墙的交点。','她原本有多个角落候选；Curtis 占第 1 列和第 2 行后，最后缩到这两个位置。'])
for k in ids:
 if k not in placed and k!='B':d[k]-={(6,5),(1,3)}
assert d['G']=={(5,2)};place('G',(5,2));emit('再次用交叉格，确定 Garrett','Bessie 的两个候选共同排除 R6C5。Garrett 因此失去其中一个候选，只能在 R5C2，站在仙人掌旁。',['B','G'],[(1,5),(6,3),(6,5),(5,2)],'同一种方法，可以重复使用',['Bessie 若在 R1C5，R6C5 与她同列。','Bessie 若在 R6C3，R6C5 与她同行。','Garrett 原本在 R5C2、R6C5 二选一，因此确定 R5C2。'])
assert d['D']=={(3,7)};place('D',(3,7));emit('确定 Duke：R3C7','Garrett 占第 5 行后，Duke 在椅子旁的候选只剩 R3C7。注意：他不是亡命徒，但仍可能是凶手。',['D'],[(3,7)],'不同身份不能混为一谈',['此时 Duke 原有候选为 R3C7、R5C3、R5C6、R5C7。','后面三格全部被 Garrett 所在的第 5 行排除。'])
assert d['I']=={(8,5)};place('I',(8,5));emit('确定 Ivy：R8C5','Ivy 在第 8 行原本有三格：R8C2、R8C5、R8C7。Garrett 占第 2 列，Duke 占第 7 列，剩下门廊的 R8C5。',['I'],[(8,2),(8,5),(8,7)],'行已确定，再用列收尾',['R8C5 比 Hazel 的 R7C10 更南。','Ivy 在门廊，Hazel 在银行，满足不同区域条件。','这格有马，但 Ivy 没有不能坐马的线索；Frank 在马背不意味着只有他能在马背。'])
assert d['B']=={(6,3)};place('B',(6,3));emit('确定 Bessie：R6C3','Ivy 占第 5 列，Bessie 的 R1C5 被排除。她只剩杂货店角落 R6C3。',['B'],[(1,5),(6,3)],'把新落位带回保留的二选一',['这也是为什么之前不应猜 Bessie：保留两个候选，后续信息会自然区分。'])
assert d['V']=={(1,6)};place('V',(1,6));emit('确定死者 Virgil：R1C6','九个人已经落位，只剩第 1 行与第 6 列没有人物。死者只能位于它们的交点 R1C6，在教堂内。',['V'],[(1,6)],'最后一行与最后一列相交',['死者也遵守每行、每列的人数限制。','R1C6 是可站立的空格，符合地图条件。'])
assert {k for k,p in placed.items() if room[p]==room[placed['V']]}=={'D','V'}
emit('Duke 是凶手，Etta 是亡命徒','教堂里只有 Duke 和死者 Virgil，符合“死者与凶手独处”。所以凶手是 Duke。亡命徒 Etta 则在银行，与 Hazel 同区。',['D','V','E','H'],[placed[k] for k in ['D','V','E','H']],'用死者线索判定凶手，而非特殊身份',['复核教堂：Duke 在 R3C7，Virgil 在 R1C6；其余八人均在别区。','Duke 不是亡命徒，这不妨碍他成为凶手。','Etta 是唯一亡命徒，在桌子旁且与 Hazel 同区；这条身份线索已独立满足。'])
# Only now consult the source's stored solution.
official={k:(int(g[f'solution_y_{i}'])+1,int(g[f'solution_x_{i}'])+1) for i,k in enumerate(ids)}
assert placed==official;assert ids[int(raw['PROPERTIES']['murderer'])]=='D'
(root/'src/tutorial/data/frontier-town.json').write_text(json.dumps(steps,ensure_ascii=False,indent=2))
(root/'analysis/frontier-proof.json').write_text(json.dumps({'initial':{k:list(map(cell,sorted(v))) for k,v in initial.items()},'hazelSupport':{cell(h):[(k,cell(p)) for k,p in v] for h,v in support.items()},'snapshots':proofs,'final':{k:cell(v) for k,v in placed.items()},'officialMatch':True},ensure_ascii=False,indent=2))
# Normalized map: v2 uses row-column keys, unlike the first case.
kinds={2:'chair',4:'table',6:'bed',13:'shelf',15:'horse',16:'cactus',83:'safe',89:'sack',94:'register'}
labels={0:'教堂',1:'户外',2:'杂货店',4:'牧师家',5:'银行',6:'门廊'}
zh=['她在收银机旁边。','她在所在区域的一个角落。','他坐在椅子上。','他不是亡命徒。他在椅子旁边。','她在银行里。','他骑在一匹马上。','他在仙人掌旁边。','她坐在椅子上，与亡命徒同区。','她在 Hazel 南方，且位于不同区域。','死者。他不是亡命徒，与凶手独处。']
objects=[{'id':f'object-{r}-{c}','kind':kinds[obj[(r,c)]],'cells':[cell((r,c))],'asset':f'/assets/frontier/objects/{kinds[obj[(r,c)]]}.svg','x':c-1,'y':r-1,'width':1,'height':1} for r,c in cells if obj[(r,c)]]
puzzle={'id':'frontier-town','width':10,'height':10,'cells':[{'id':cell(p),'row':p[0],'col':p[1],'roomId':room[p],'occupiable':p in free,'carpet':False,'objectIds':[obj[p]] if obj[p] else []} for p in cells],'objects':objects,'rooms':[{'id':i,'label':labels[i],'fill':g[f'room_color_{i}'],'cells':[cell(p) for p in cells if room[p]==i]} for i in labels],'characters':[{'id':k,'name':g[f'char_name_{i}'],'portrait':f'/assets/frontier/portraits/{k}.svg','clueId':k+'-clue','clueEn':g[f'char_quote_en_{i}'],'clueZh':zh[i]} for i,k in enumerate(ids)],'generalClues':[{'id':'general-outlaw','text':'恰好一名亡命徒，位于桌子旁；他不一定是凶手。'}]}
(root/'src/case/data/frontier-town.json').write_text(json.dumps(puzzle,ensure_ascii=False,indent=2))
md=['# Frontier Town：17 步推理教学','来源：https://murdoku.com/play_puzzles/en/puzzle-frontier-town-hard.json','主线 17 步，细讲按需展开。推理从线索与候选开始，最后才核对 JSON 答案字段。','']
for i,s in enumerate(steps,1):md+=['## '+str(i)+'. '+s['title'],s['explanation'],'','细讲：']+['- '+t for t in s['details']]+['']
(root/'analysis/frontier-walkthrough.md').write_text('\n'.join(md))
print('Prepared',len(steps),'main steps;',sum(len(s['details']) for s in steps),'optional explanations; all placements match source.')
