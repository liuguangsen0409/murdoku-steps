import {steps} from './lessons/easy-lesson';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {normalizeCase,readSolution} from '../src/case/normalize';
const raw=JSON.parse(readFileSync('sources/24h-delivery.json','utf8'));const puzzle=normalizeCase(raw);
for(const a of [...puzzle.objects.map(o=>o.asset),...puzzle.characters.map(c=>c.portrait)])if(!existsSync('public'+a))throw Error(`缺少素材 ${a}`);
writeFileSync('src/case/data/24h-delivery.json',JSON.stringify(puzzle,null,2));writeFileSync('sources/24h-delivery-solution.json',JSON.stringify(readSolution(raw),null,2));console.log('Prepared 36 cells, 6 characters and local assets.');

writeFileSync('src/tutorial/data/24h-delivery.json',JSON.stringify(steps,null,2));
