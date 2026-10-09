import {expect,test} from 'vitest';import data from '../src/case/data/24h-delivery.json';import type {Puzzle} from '../src/case/types';import {buildSnapshots} from '../src/tutorial/replay';import {steps} from '../scripts/lessons/steps';import {describeCell,visibleCandidate} from '../src/ui/board';
const p=data as Puzzle,s=buildSnapshots(p,steps);
test('names occupiable furniture and blocked objects in cell descriptions',()=>{for(const [id,name] of [['R1C2','椅子'],['R1C5','床'],['R6C2','箱子']])expect(describeCell(p,s[0],p.cells.find(c=>c.id===id)!)).toContain(name);});
test('keeps A candidates when Carol supplies evidence in step 3',()=>{expect(visibleCandidate(s[3],steps[2],'R5C2')).toBe('A');expect(visibleCandidate(s[3],steps[2],'R6C1')).toBe('A');});
