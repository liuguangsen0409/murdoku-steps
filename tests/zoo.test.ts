import {expect,test} from 'vitest';
import data from '../src/case/data/the-zoo.json';
import lesson from '../src/tutorial/data/the-zoo.json';
import raw from '../sources/the-zoo.json';
import {buildSnapshots} from '../src/tutorial/replay';
import type {Puzzle,CharacterId} from '../src/case/types';
import type {Step} from '../src/tutorial/types';
const p=data as Puzzle,steps=lesson as Step[],states=buildSnapshots(p,steps);
const at=(id:string)=>p.cells.find(c=>c.id===id)!;
const end=states.at(-1)!.placements as Record<CharacterId,string>;
const c=(k:CharacterId)=>at(end[k]);
const beside=(k:CharacterId,predicate:(q:typeof p.cells[number])=>boolean)=>p.cells.some(q=>q.roomId===c(k).roomId&&Math.abs(q.row-c(k).row)+Math.abs(q.col-c(k).col)===1&&predicate(q));
const near=(k:CharacterId,types:number[])=>beside(k,q=>q.objectIds.some(i=>types.includes(i)));
const companions=(k:CharacterId)=>p.characters.filter(q=>q.id!==k&&c(q.id).roomId===c(k).roomId).map(q=>q.id).sort();
test('water subrooms are part of habitats and both elephant footprints are blocked',()=>{
 expect(p.cells).toHaveLength(256);expect(at('R1C9').roomId).toBe(at('R2C8').roomId);expect(at('R1C9').water).toBe(true);expect(at('R2C8').water).toBe(false);
 for(const id of ['R10C10','R10C11','R11C10','R11C11','R13C11','R13C12','R14C11','R14C12']){expect(at(id).objectIds).toContain(54);expect(at(id).occupiable).toBe(false);}
 expect(at('R11C12').occupiable).toBe(true);
});
test('all sixteen original clues and global constraints hold independently at the end',()=>{
 expect(Object.keys(end)).toHaveLength(16);expect(new Set(Object.values(end).map(id=>at(id).row)).size).toBe(16);expect(new Set(Object.values(end).map(id=>at(id).col)).size).toBe(16);
 const habitats=[1,2,3,5,6,8];for(const person of p.characters){expect(c(person.id).occupiable).toBe(true);if(person.role==='游客')expect(habitats).not.toContain(c(person.id).roomId);}
 for(const habitat of habitats)expect(p.characters.some(person=>person.role==='饲养员'&&c(person.id).roomId===habitat)).toBe(true);
 expect(c('A').row+1).toBe(c('I').row);expect(c('B').roomId).toBe(9);expect(companions('B')).toEqual(['E']);expect(c('C').row+1).toBe(c('D').row);expect(c('D').roomId).toBe(0);
 expect(near('E',[4])).toBe(true);expect(c('E').objectIds).not.toContain(2);expect(near('F',[2])).toBe(true);expect(c('G').objectIds).toContain(2);expect(companions('G')).toEqual([]);expect(companions('H')).toEqual([]);
 const animals=[26,47,52,53,54,55];expect(near('I',animals)).toBe(true);expect(c('J').water).toBe(false);expect(beside('J',q=>!!q.water)).toBe(true);expect(companions('K')).toEqual(['M']);expect(c('L').water).toBe(true);expect(near('L',animals)).toBe(false);expect(c('M').col).toBe(2);expect(near('N',[10,11])).toBe(true);expect(near('O',[43])).toBe(true);expect(companions('V')).toEqual(['J']);
});
test('every intermediate state retains the solution and replay is reversible',()=>{
 expect(steps).toHaveLength(21);expect(states[5].candidates.J).toEqual(['R2C8','R9C8']);expect(states[16].candidates.C).toEqual(['R5C6','R5C10']);
 for(const state of states.slice(1))for(const person of p.characters){if(state.placements[person.id])expect(state.placements[person.id]).toBe(end[person.id]);else expect(state.candidates[person.id]).toContain(end[person.id]);expect(state.blockedCells??[]).not.toContain(end[person.id]);}
 expect(states[0].placements).toEqual({});expect(buildSnapshots(p,steps.slice(0,5)).at(-1)).toEqual(states[5]);
 const official=raw.CHARACTERS as Record<string,string>,properties=raw.PROPERTIES;
 for(const [i,person] of p.characters.entries()){const row=Math.floor((Number(official[`letter_ypos_${i}`])-Number(properties.grid_ry))/Number(properties.cellsize))+1;const col=Math.floor((Number(official[`letter_xpos_${i}`])-Number(properties.grid_rx))/Number(properties.cellsize))+1;expect(end[person.id]).toBe(`R${row}C${col}`);}
});
