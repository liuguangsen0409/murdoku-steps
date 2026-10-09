import {expect,test} from 'vitest';
import raw from '../sources/24h-delivery.json';
import {normalizeCase,readSolution} from '../src/case/normalize';
test('loads only six active characters',()=>{const p=normalizeCase(raw);expect([p.width,p.height,p.cells.length]).toEqual([6,6,36]);expect(p.characters.map(c=>c.id)).toEqual(['A','B','C','D','E','V']);});
test('preserves bed occupancy, carpets and room boundaries',()=>{const p=normalizeCase(raw);const get=(id:string)=>p.cells.find(c=>c.id===id)!;expect(get('R6C2').occupiable).toBe(false);expect(get('R1C4').occupiable).toBe(true);expect(get('R1C5').occupiable).toBe(true);expect(get('R5C2').carpet).toBe(true);expect(get('R6C2').roomId).not.toBe(get('R6C3').roomId);});
test('matches reference coordinates',()=>expect(readSolution(raw)).toEqual({A:'R6C1',B:'R1C2',C:'R3C5',D:'R2C4',E:'R5C3',V:'R4C6'}));
test('rejects outside coordinates',()=>{const r=structuredClone(raw);r.CHARACTERS.letter_xpos_0='0';expect(()=>readSolution(r)).toThrow(/越界/);});
