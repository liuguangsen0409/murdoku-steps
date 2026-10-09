import {type Puzzle,type CharacterId,type CellId} from '../case/types';
import type {Step,TutorialState,Reason} from './types';
export function buildSnapshots(puzzle:Puzzle,steps:readonly Step[]):TutorialState[]{
 const activeIds=puzzle.characters.map(c=>c.id);
 const initial:TutorialState={placements:{},candidates:Object.fromEntries(activeIds.map(id=>[id,[] as CellId[]])) as Record<CharacterId,CellId[]>,eliminations:[]};
 const snapshots=[initial],seen=new Set<string>(),clues=new Set([...puzzle.characters.map(c=>c.clueId),...(puzzle.generalClues??[]).map(c=>c.id)]);
 const cells=new Map(puzzle.cells.map(c=>[c.id,c]));
 const get=(id:CellId)=>{const c=cells.get(id);if(!c)throw Error(`无效格子 ${id}`);return c;};
 for(const step of steps){
  const state=structuredClone(snapshots[snapshots.length-1]);
  const exclude=(character:CharacterId,cell:CellId,reason:Reason)=>{state.candidates[character]=state.candidates[character].filter(c=>c!==cell);if(!state.eliminations.some(e=>e.character===character&&e.cell===cell&&e.reason.ruleId===reason.ruleId))state.eliminations.push({character,cell,reason});};
  for(const a of step.actions){
   if('reason' in a&&(!a.reason.clueRefs.every(c=>clues.has(c))||!a.reason.dependsOn.every(d=>seen.has(d))))throw Error('无效或未来证据');
   if(a.type==='blockCells'){a.cells.forEach(get);state.blockedCells=[...new Set([...(state.blockedCells??[]),...a.cells])];}
   if(a.type==='setCandidates'){a.cells.forEach(get);state.candidates[a.character]=[...a.cells];}
   if(a.type==='removeCandidate'){get(a.cell);exclude(a.character,a.cell,a.reason);}
   if(a.type==='placeCharacter'){
    const target=get(a.cell);if(!target.occupiable)throw Error('不可站立的格子');
    for(const [who,id] of Object.entries(state.placements)){if(who===a.character)continue;const other=get(id!);if(other.row===target.row||other.col===target.col)throw Error('人物行列冲突');}
    state.placements[a.character]=a.cell;state.candidates[a.character]=[];
   }
   if(a.type==='applyRowColumnConstraint'){
    const pos=state.placements[a.character];if(!pos)throw Error('人物未落位');const occupied=get(pos);
    for(const other of activeIds)if(!state.placements[other])for(const c of puzzle.cells)if(c.row===occupied.row||c.col===occupied.col)exclude(other,c.id,a.reason);
   }
  }
  snapshots.push(state);seen.add(step.id);
 }
 return snapshots;
}
