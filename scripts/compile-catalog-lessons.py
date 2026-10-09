"""Turn independently recorded solver reductions into readable, replayable lessons.
Never derives a position from the stored answer; compiler validates every event against
its recorded pre-state and constraint model, then places only singleton domains.
"""
import json,re,copy,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('catalog_solver',ROOT/'scripts/catalog-solver.py');solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver)
def coords(p):return tuple(map(int,re.findall(r'\d+',p)))
def ranges(ns):
 ns=sorted(set(ns));parts=[]
 if not ns:return '无'
 first=last=ns[0]
 for n in ns[1:]+[None]:
  if n is not None and n==last+1:last=n;continue
  parts.append(str(first) if first==last else f'{first}–{last}')
  first=last=n
 return '、'.join(parts)
def listing(ps):
 ps=sorted(ps,key=coords)
 if not ps:return '无'
 if len(ps)>8:
  rs=[coords(p)[0] for p in ps];cs=[coords(p)[1] for p in ps]
  return f'{len(ps)} 格，分布在 R{min(rs)}–R{max(rs)} / C{min(cs)}–C{max(cs)}（点人物查看候选）'
 rows={}
 for p in ps:
  r,c=coords(p);rows.setdefault(r,[]).append(c)
 return '；'.join(f'R{r}C{ranges(cs)}' for r,cs in rows.items())
def brief(ps,limit=8):return listing(ps)
def compile_one(slug,proof):
 model=solver.Model(slug).build();puzzle=model.p;ids=model.ids;people=model.people;cells=model.cells
 domains={k:set(v) for k,v in proof['initial'].items()};assert domains==model.dom,slug
 steps=[];placed={};audit=[];seen=[];refs=[c['clueId'] for c in puzzle['characters']]+[c['id'] for c in puzzle.get('generalClues',[])]
 name=lambda k:f'{people[k]["name"]}（{k}）'
 def emit(title,text,focus,details,actions=None,rule='逐条约束缩小候选',event_numbers=None):
  sid=f'{slug}-lesson-{len(steps)+1}';reason={'ruleId':rule,'clueRefs':refs,'dependsOn':[steps[-1]['id']] if steps else []}
  actions=actions or []
  for a in actions:
   if a['type'] not in ['setCandidates']:a['reason']=reason
  focus=list(dict.fromkeys(focus))[:4]
  high=set().union(*(domains[k] for k in focus)) if focus else set()
  assert len(details)<=12 and all(len(t)<=180 for t in details),(slug,sid,len(details),max(map(len,details)))
  steps.append({'id':sid,'title':title,'explanation':text,'clueRefs':refs,'focusCharacters':focus,'candidateCharacters':[k for k in focus if k not in placed][:3],'highlightCells':sorted(high,key=coords),'actions':actions,'rule':rule,'details':details})
  audit.append({'step':sid,'sourceEvents':event_numbers or [],'domains':{k:sorted(v,key=coords) for k,v in domains.items()},'placements':placed.copy(),'teachingEvidence':details})
 def new_places():
  actions=[];new=[]
  for k in ids:
   if len(domains[k])==1 and k not in placed:
    q=next(iter(domains[k]));assert all(model.compat(q,r) for r in placed.values());placed[k]=q;new.append(k);actions.append({'type':'placeCharacter','character':k,'cell':q})
  return actions,new
 exclusive=[c for c in puzzle['characters'] if re.search(r'only|唯一|只有',c.get('clueEn','')+' '+c.get('clueZh',''),re.I)]
 setup=['每行、每列最多一人；死者 V 也参与行列限制。','旁边按同一逻辑区域内的上下左右判断；家具是否可站立，以地图格子的属性为准。','本页逐步保存候选排除。只有某人的候选恰好剩一格时，才执行落位。']
 setup += [f'全员都要应用 {name(c["id"])} 的排他线索：{c["clueZh"]}。因此其他人的初始候选也可能受这条线索影响。' for c in exclusive]
 setup += [f'全局条件：{c["text"]}' for c in puzzle.get('generalClues',[])]
 emit('先读地图与全局规则',f'{len(ids)} 人共用 {puzzle["height"]} 行、{puzzle["width"]} 列；先从地形、家具与明确区域建立候选。',[],setup,[{'type':'setCandidates','character':k,'cells':sorted(domains[k],key=coords)} for k in ids],rule='地图与初始单人条件')
 # Small cases can afford one clue per screen; larger ones introduce three at a time.
 group_size=1 if len(ids)<=7 else 3
 for start in range(0,len(ids),group_size):
  group=ids[start:start+group_size];details=[]
  for k in group:
   details += [f'{name(k)} 的原始线索：{people[k]["clueZh"]}',f'{k} 候选：{listing(domains[k])}。已应用地图和全局排他条件；涉及另一人的关系留待交叉验证。']
  actions=[];new=[]
  for k in group:
   if len(domains[k])==1 and k not in placed:
    q=next(iter(domains[k]));placed[k]=q;actions.append({'type':'placeCharacter','character':k,'cell':q});new.append(k)
  title='先确定 '+ '、'.join(f'{people[k]["name"]}：{placed[k]}' for k in new) if new else '先看 '+ '、'.join(people[k]['name'] for k in group)+' 的候选'
  text='；'.join(f'{k}：{people[k]["clueZh"]}（'+(f'只剩 {next(iter(domains[k]))}' if len(domains[k])==1 else f'{len(domains[k])} 个候选')+'）' for k in group)
  emit(title,text,group,details,actions,rule='从原始线索建立候选')
 pending=[];pending_actions=[];pending_details=[];pending_focus=[];pending_changes=[];pending_new=[]
 def flush():
  nonlocal pending,pending_actions,pending_details,pending_focus,pending_changes,pending_new
  if not pending:return
  if pending_new:
   title='确定 '+ '、'.join(people[k]['name'] for k in pending_new[:3])
   text='；'.join(f'{k} 只剩 {placed[k]}' for k in pending_new)+ '。'+pending_changes[-1]
   focus=pending_new+pending_focus
  else:
   primary=pending[-1]['character'];reason=pending[-1]['reason'];title=f'{people[primary]["name"]}：候选缩至 {len(domains[primary])} 格'
   text='；'.join(pending_changes[-2:]);focus=[primary]+pending_focus
  kinds=list(dict.fromkeys(e['reason'] for e in pending));rule=kinds[0] if len(kinds)==1 else '连续应用相关约束'
  visible=[ds[0] for ds in pending_details]+pending_details[-1][1:]
  emit(title,text,focus,visible,pending_actions,rule=rule,event_numbers=[e['_index'] for e in pending]);pending=[];pending_actions=[];pending_details=[];pending_focus=[];pending_changes=[];pending_new=[]
 for index,event in enumerate(proof['events'],1):
  e=copy.deepcopy(event);e['_index']=index;k=e['character'];before=set(e['before']);after=set(e['after']);assert domains[k]==before and after and after<before,(slug,index)
  reason=e['reason'];removed=before-after;focus=e.get('focus',[k])
  related=list(dict.fromkeys(focus+[x for x in ids if re.search(r'(?<![A-Z])'+x+r'(?![A-Z])',reason)]))
  detail=[f'{k}：{reason}。候选从 {len(before)} 格减至 {len(after)} 格；剩余 {listing(after)}。']
  if 'branches' in e:
   assert {q for q,_ in e['branches']}==removed
   traces={b['assumption']:b.get('events',[]) for b in e.get('branchProofs',[])}
   example=next(((q,why,traces[q]) for q,why in e['branches'] if traces.get(q)),None)
   detail=[f'{k}：逐个假设 {len(before)} 个候选，排除 {len(removed)} 个无解分支，剩余 {listing(after)}。这是约束传播与必要时的完整枚举，不是直接看出的唯一位置。']
   if example:
    q,why,chain=example;last=chain[-1]
    detail.append(f'代表分支 {k}={q}：{last["character"]} 因“{last["reason"]}”从 {len(last["before"])} 个候选变为 {len(last["after"])} 个。'+('候选清空，假设矛盾。' if not last['after'] else '继续枚举后无解。')+'完整分支记录保存在证据文件。')
   else:detail.append('这些分支记录为完整枚举无解，没有可展示的短反证链；不将搜索结果改写成某条直接线索。完整记录保存在证据文件。')
  elif '锁定第' in reason:
   group=focus[1:];axis='行' if reason.endswith('行') else '列';fn=model.row if axis=='行' else model.col;axes=set().union(*({fn(q) for q in domains[x]} for x in group));assert len(axes)==len(group)
   assert all(fn(q) in axes for q in removed)
   detail.append(f'{"、".join(group)} 共 {len(group)} 人，只能用第 {ranges(axes)} {axis}，必须恰好占满；{k} 因此不能用这些{axis}。各人范围：'+ '；'.join(f'{x} 在第 {ranges(fn(q) for q in domains[x])} {axis}' for x in group)+'。')
  elif len(focus)==2:
   partner=focus[1] if focus[0]==k else focus[0];assert all(not(model.tables[k,partner][q]&domains[partner]) for q in removed)
   q=min(removed,key=coords)
   if reason=='每行、每列最多一人':
    assert all(model.row(q)==model.row(r) or model.col(q)==model.col(r) for r in domains[partner])
    detail.append(f'例如 {k} 在 {q}，会与 {partner} 的全部剩余位置同行或同列，无法配对。{partner} 现有候选：{listing(domains[partner])}。')
   else:
    detail.append(f'例如 {k} 在 {q}，找不到既满足两人关系、又不同行同列的 {partner}。{partner} 现有候选：{listing(domains[partner])}。')
  else:
   constraints=[f for label,f in model.globals if label==reason];assert constraints,(slug,reason)
   for q in sorted(removed,key=coords):
    trial=model.project(domains,k,q);empty=[x for x,v in trial.items() if not v]
    assert empty or not all(f(trial) for f in constraints),(slug,index,q)
   q=min(removed,key=coords);trial=model.project(domains,k,q);empty=[x for x,v in trial.items() if not v]
   why=('、'.join(empty)+' 已没有可用位置') if empty else ('“'+reason+'”已没有足够的人数或合适同伴')
   detail.append(f'例如假设 {k} 在 {q}，同步排除其他人的行列及关系冲突后，{why}，所以这格不成立。其余被删候选按相同条件逐一核验。')
  domains[k]=after
  assert all(domains[x]==set(e['state'][x]) for x in ids),(slug,index,'state')
  acts=[{'type':'removeCandidate','character':k,'cell':q} for q in sorted(removed,key=coords)];places,new=new_places();acts+=places
  pending.append(e);pending_actions+=acts;pending_details.append(detail);pending_focus+=focus;pending_new+=new
  display_reason=reason
  if '的关系线索' in reason:
   pieces=[]
   for x in related:
    if x not in people:continue
    if any(people[y]['name'].lower() in (people[x].get('clueEn','')+' '+people[x]['clueZh']).lower() for y in related if y in people and y!=x):pieces.append(f'{x}：{people[x]["clueZh"]}')
   display_reason='；'.join(pieces) or reason
  if reason=='每行、每列最多一人' and len(focus)==2:
   other=focus[1] if focus[0]==k else focus[0]
   display_reason=(f'{other} 已锁定 {next(iter(domains[other]))}' if len(domains[other])==1 else f'{other} 的 {len(domains[other])} 个候选共同排除同行同列冲突格')
  change=f'{display_reason}，{k} 从 {len(before)} 格缩到 {len(after)} 格'

  pending_changes.append(change)
  # Up to six reductions per screen; preserve hypothesis and singleton milestones.
  if new or len(pending)>=6 or 'branches' in e:flush()
 flush();assert placed==proof['final'],slug
 victim_room=model.room(placed['V']);companions=[k for k in ids if model.room(placed[k])==victim_room];assert len(companions)==2 and 'V' in companions;culprit=next(k for k in companions if k!='V');label=next(r['label'] for r in puzzle['rooms'] if r['id']==victim_room)
 emit(f'{people[culprit]["name"]} 是凶手',f'死者 V 位于{label}的 {placed["V"]}；同区唯一另一人是 {name(culprit)}，位置为 {placed[culprit]}。',[culprit,'V'],['死者线索要求与凶手独处，必须以最终逻辑区域的同区人数判定。',f'{label}实际人物：'+ '、'.join(f'{k} 在 {placed[k]}' for k in companions)+'；其余所有人都在其他区域。',f'{len(ids)} 人全部有位置，且每行、每列均无冲突。','最终位置由初始候选与记录中的约束排除得到；原始答案只由求解脚本在结束时作一致性核对。'],rule='死者与凶手独处')
 (ROOT/f'src/tutorial/data/{slug}.json').write_text(json.dumps(steps,ensure_ascii=False,indent=2))
 (ROOT/f'analysis/generated/{slug}-lesson-audit.json').write_text(json.dumps({'slug':slug,'sourceEventCount':len(proof['events']),'steps':audit,'final':placed,'killer':culprit},ensure_ascii=False,indent=2))
 return {'slug':slug,'steps':len(steps),'details':sum(len(s['details']) for s in steps),'sourceEvents':len(proof['events']),'killer':culprit}
def main():
 report=[]
 for path in sorted((ROOT/'analysis/generated').glob('*-proof.json')):
  proof=json.loads(path.read_text())
  if 'events' not in proof:continue
  slug=path.name.removesuffix('-proof.json');result=compile_one(slug,proof);report.append(result);print(slug,result['steps'],flush=True)
 (ROOT/'analysis/generated/lesson-compilation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
