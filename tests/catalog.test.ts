import {expect,test} from 'vitest';
import {readFileSync,existsSync,readdirSync} from 'node:fs';
import {cases} from '../src/case/catalog';
import {buildSnapshots} from '../src/tutorial/replay';
import type {CharacterId,CellId} from '../src/case/types';
import {rosterLayout} from '../src/ui/characters';

test('all 39 public cases are complete and uniquely routed; premium stays out of playable data',()=>{
 expect(cases).toHaveLength(39);expect(new Set(cases.map(c=>c.slug)).size).toBe(39);expect(cases.some(c=>/hoarders/.test(c.slug))).toBe(false);
 for(const [count,rows,columns] of [[6,3,2],[7,4,2],[8,3,3],[9,3,3],[10,4,3],[12,4,3],[16,4,4]])expect(rosterLayout(count)).toEqual({rows,columns});
});
for(const definition of cases.filter(c=>!['24h-delivery','frontier-town','the-zoo'].includes(c.slug)))test(`${definition.slug}: evidence replay preserves the solution and all assets exist`,async()=>{
 const p=await definition.loadPuzzle(),steps=await definition.loadSteps(),states=buildSnapshots(p,steps);
 const proof=JSON.parse(readFileSync(new URL(`../analysis/generated/${definition.slug}-proof.json`,import.meta.url),'utf8'));
 const end=states.at(-1)!.placements;
 expect(end).toEqual(proof.final??proof.snapshots.at(-1).placements);
 expect(Object.keys(end)).toHaveLength(p.characters.length);
 expect(steps.every(s=>s.details?.length)).toBe(true);
 for(const step of steps){expect(step.details!.length).toBeLessThanOrEqual(12);for(const detail of step.details!)expect(detail.length).toBeLessThanOrEqual(180);}
 const at=(id:string)=>p.cells.find(c=>c.id===id)!;
 const initialized=new Set<CharacterId>();
 for(const [i,step] of steps.entries()){
  const domain=structuredClone(states[i].candidates);
  for(const action of step.actions){
   if(action.type==='setCandidates'){initialized.add(action.character);domain[action.character]=[...action.cells];}
   if(action.type==='removeCandidate')domain[action.character]=domain[action.character].filter(c=>c!==action.cell);
   if(action.type==='placeCharacter')expect(domain[action.character],`${step.id}: unique before placement`).toEqual([action.cell]);
   if(action.type==='applyRowColumnConstraint'){
    const pos=step.actions.find(a=>a.type==='placeCharacter'&&a.character===action.character);
    const id=pos&&pos.type==='placeCharacter'?pos.cell:states[i].placements[action.character];
    if(id)for(const k of Object.keys(domain) as CharacterId[])if(k!==action.character)domain[k]=domain[k].filter(c=>at(c).row!==at(id).row&&at(c).col!==at(id).col);
   }
  }
  for(const k of initialized){const state=states[i+1];if(state.placements[k])expect(state.placements[k]).toBe(end[k]);else expect(state.candidates[k]).toContain(end[k]);}
 }
 expect(new Set(Object.values(end).map(id=>at(id!).row)).size).toBe(p.characters.length);
 expect(new Set(Object.values(end).map(id=>at(id!).col)).size).toBe(p.characters.length);
 expect(p.characters.filter(c=>c.id!=='V'&&at(end[c.id]!).roomId===at(end.V!).roomId)).toHaveLength(1);
 for(const asset of [...p.objects.map(o=>o.asset),...p.characters.map(c=>c.portrait),...p.cells.flatMap(c=>c.textureAsset?[c.textureAsset]:[])])expect(existsSync(new URL(`../public${asset}`,import.meta.url)),asset).toBe(true);
 expect(buildSnapshots(p,steps.slice(0,3)).at(-1)).toEqual(states[3]);
});

test('every registered case has exactly one map and lesson with matching metadata',async()=>{
 const slugs=cases.map(c=>c.slug).sort();
 for(const directory of ['case','tutorial']){
  const files=readdirSync(new URL(`../src/${directory}/data/`,import.meta.url)).filter(f=>f.endsWith('.json')).map(f=>f.slice(0,-5)).sort();
  expect(files).toEqual(slugs);
  expect(readdirSync(new URL(`../src/${directory}/`,import.meta.url)).filter(f=>f.endsWith('.json')||f==='generated')).toEqual([]);
 }
 for(const entry of cases){
  const [puzzle,steps]=await Promise.all([entry.loadPuzzle(),entry.loadSteps()]);
  expect([puzzle.width,puzzle.height,puzzle.characters.length]).toEqual([entry.width,entry.height,entry.characterCount]);
  expect(Object.keys(buildSnapshots(puzzle,steps).at(-1)!.placements)).toHaveLength(entry.characterCount);
 }
});
