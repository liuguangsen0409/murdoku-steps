import lessonData from '../src/tutorial/data/24h-delivery.json';
import {expect,test} from 'vitest';
import data from '../src/case/data/24h-delivery.json';
import type {Puzzle} from '../src/case/types';
import {steps as atomic} from '../scripts/lessons/steps';
import {steps,easyGroups} from '../scripts/lessons/easy-lesson';
import {buildSnapshots} from '../src/tutorial/replay';

test('grouped lessons preserve every verified stage outcome and candidate set',()=>{
 const original=buildSnapshots(data as Puzzle,atomic),grouped=buildSnapshots(data as Puzzle,steps);
 expect(steps).toHaveLength(9);
 easyGroups.forEach((group,index)=>{
  expect(grouped[index+1].placements).toEqual(original[group.to].placements);
  expect(grouped[index+1].candidates).toEqual(original[group.to].candidates);
  expect(steps[index].details).toHaveLength(group.to-group.from+1);
 });
 expect(grouped[1].placements).toEqual({});
 expect(grouped[1].candidates.A).toEqual(['R5C2','R6C1']);
 expect(grouped.at(-1)!.placements).toEqual({A:'R6C1',B:'R1C2',C:'R3C5',D:'R2C4',E:'R5C3',V:'R4C6'});
});

test('published easy JSON matches the authored lesson',()=>expect(lessonData).toEqual(steps));
