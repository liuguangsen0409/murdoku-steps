"""Independent action replayer: validate every singleton placement and final board."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
report=[]
for path in sorted((ROOT/'src/case/data').glob('*.json')):
 if path.stem in ['24h-delivery','frontier-town','the-zoo']:continue
 slug=path.stem;puzzle=json.loads(path.read_text());lesson_path=ROOT/f'src/tutorial/data/{slug}.json'
 if not lesson_path.exists():raise AssertionError(f'missing lesson {slug}')
 lesson=json.loads(lesson_path.read_text());proof=json.loads((ROOT/f'analysis/generated/{slug}-proof.json').read_text());expected=proof.get('final') or proof['snapshots'][-1]['placements']
 ids=[c['id'] for c in puzzle['characters']];cells={c['id']:c for c in puzzle['cells']};clues={c['clueId'] for c in puzzle['characters']}|{c['id'] for c in puzzle.get('generalClues',[])};domains={k:set() for k in ids};placed={};seen=set();placements=[]
 audits_path=ROOT/f'analysis/generated/{slug}-lesson-audit.json';audits=json.loads(audits_path.read_text())['steps'] if audits_path.exists() else None
 for i,step in enumerate(lesson):
  assert len(step['focusCharacters'])<=4,(slug,step['id'],'focus')
  assert step.get('details'),(slug,step['id'],'missing details')
  assert set(step['clueRefs'])<=clues
  for action in step['actions']:
   reason=action.get('reason')
   if reason:
    assert set(reason['clueRefs'])<=clues,(slug,step['id'],'clueRefs')
    assert set(reason['dependsOn'])<=seen,(slug,step['id'],'future dependency')
   kind=action['type'];k=action.get('character')
   if kind=='setCandidates':
    assert all(q in cells and cells[q]['occupiable'] for q in action['cells']);domains[k]=set(action['cells'])
   elif kind=='removeCandidate':
    assert action['cell'] in domains[k],(slug,step['id'],'removing absent candidate',k,action['cell']);domains[k].remove(action['cell'])
   elif kind=='placeCharacter':
    q=action['cell'];assert k not in placed and domains[k]=={q},(slug,step['id'],'non-singleton placement',k,domains[k]);assert cells[q]['occupiable']
    assert all(cells[r]['row']!=cells[q]['row'] and cells[r]['col']!=cells[q]['col'] for r in placed.values()),(slug,step['id'],'collision')
    placed[k]=q;domains[k]=set();placements.append({'step':step['id'],'character':k,'cell':q,'singletonVerified':True})
   elif kind=='blockCells':assert all(q in cells for q in action['cells'])
   else:raise AssertionError((slug,'unexpected action',kind))
  if audits:
   audit=audits[i];assert placed==audit['placements']
   assert all(domains[k]==(set() if k in placed else set(audit['domains'][k])) for k in ids),(slug,step['id'],'audit mismatch')
  seen.add(step['id'])
 assert placed==expected,(slug,'final mismatch');assert all(not d for d in domains.values())
 companions=[k for k,q in placed.items() if cells[q]['roomId']==cells[placed['V']]['roomId']];assert len(companions)==2
 killer=next(k for k in companions if k!='V');report.append({'slug':slug,'steps':len(lesson),'allSingletonPlacementsVerified':True,'finalMatchesSourceProof':True,'killer':killer,'placements':placements})
 print(slug,len(lesson),'steps',len(placements),'verified placements')
(ROOT/'analysis/generated/lesson-replay-verification.json').write_text(json.dumps({'cases':len(report),'results':report},ensure_ascii=False,indent=2))
print('ALL',len(report),'CASES VERIFIED')
