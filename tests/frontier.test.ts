import {expect,test} from 'vitest';
import data from '../src/case/data/frontier-town.json';
import raw from '../sources/frontier-town.json';
import lesson from '../src/tutorial/data/frontier-town.json';
import {buildSnapshots} from '../src/tutorial/replay';
import type {Puzzle,CellId} from '../src/case/types';
import type {Step} from '../src/tutorial/types';
const p=data as Puzzle,steps=lesson as Step[],snapshots=buildSnapshots(p,steps);
const at=(id:string)=>p.cells.find(c=>c.id===id)!;
const compatible=(a:string,b:string)=>at(a).row!==at(b).row&&at(a).col!==at(b).col;
const beside=(id:string,kind:number)=>p.cells.some(c=>c.roomId===at(id).roomId&&c.objectIds.includes(kind)&&Math.abs(c.row-at(id).row)+Math.abs(c.col-at(id).col)===1);
const corner=(id:string)=>{const c=at(id),wall=(r:number,col:number)=>!p.cells.some(q=>q.row===r&&q.col===col&&q.roomId===c.roomId);return (wall(c.row-1,c.col)||wall(c.row+1,c.col))&&(wall(c.row,c.col-1)||wall(c.row,c.col+1));};
test('v2 map orientation is grounded by chairs and register clues',()=>{expect(at('R7C10').objectIds).toContain(2);expect(at('R2C1').objectIds).toContain(2);expect(beside('R9C4',94)).toBe(true);expect(p.cells).toHaveLength(100);});
test('independent constrained search finds exactly one arrangement without reading answer fields',()=>{
 const free=p.cells.filter(c=>c.occupiable).map(c=>c.id);const domains:Record<string,CellId[]>={A:free.filter(c=>beside(c,94)),B:free.filter(corner),C:free.filter(c=>at(c).objectIds.includes(2)),D:free.filter(c=>beside(c,2)),E:free.filter(c=>at(c).roomId===5),F:free.filter(c=>at(c).objectIds.includes(15)),G:free.filter(c=>beside(c,16)),H:free.filter(c=>at(c).objectIds.includes(2)),I:free,V:free};
 const outlaws=Object.keys(domains).filter(k=>!['D','V','H','I'].includes(k));
 const support=domains.H.flatMap(h=>outlaws.flatMap(k=>domains[k].filter(c=>beside(c,4)&&at(c).roomId===at(h).roomId&&compatible(c,h)).map(c=>({h,k,c}))));
 expect([...new Set(support.map(s=>s.k))]).toEqual(['E']);domains.H=domains.H.filter(h=>support.some(s=>s.h===h));domains.E=domains.E.filter(c=>support.some(s=>s.c===c));
 const solutions:Record<string,string>[]=[];
 const search=(assigned:Record<string,string>)=>{if(solutions.length>1)return;const remaining=Object.keys(domains).filter(k=>!assigned[k]);if(!remaining.length){const companions=Object.keys(assigned).filter(k=>k!=='V'&&at(assigned[k]).roomId===at(assigned.V).roomId);if(companions.length===1)solutions.push({...assigned});return;}
 const choices=remaining.map(k=>({k,cells:domains[k].filter(c=>Object.values(assigned).every(other=>compatible(c,other))&&(k!=='I'||!assigned.H||at(c).row>at(assigned.H).row&&at(c).roomId!==at(assigned.H).roomId)&&(k!=='H'||!assigned.I||at(assigned.I).row>at(c).row&&at(assigned.I).roomId!==at(c).roomId))})).sort((a,b)=>a.cells.length-b.cells.length);const next=choices[0];for(const c of next.cells)search({...assigned,[next.k]:c});};
 search({});expect(solutions).toHaveLength(1);expect(snapshots.at(-1)!.placements).toEqual(solutions[0]);
});
test('17 reversible main stages retain candidate evidence and match source only at the end',()=>{
 expect(steps).toHaveLength(17);expect(snapshots[2].candidates.H).toEqual(['R7C10']);expect(snapshots[4].candidates.E).toEqual(['R8C9','R9C9','R10C8']);expect(snapshots[11].candidates.B).toEqual(['R1C5','R6C3']);expect(snapshots[0].placements).toEqual({});
 const g=raw.CHARACTERS as Record<string,string>;for(const [i,k] of [...'ABCDEFGHIV'].entries())expect(snapshots.at(-1)!.placements[k as keyof typeof snapshots[0]['placements']]).toBe(`R${Number(g[`solution_y_${i}`])+1}C${Number(g[`solution_x_${i}`])+1}`);
});
