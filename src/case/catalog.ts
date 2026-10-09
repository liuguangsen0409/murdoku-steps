import {entries} from './entries';
import type {Puzzle} from './types';
import type {Step} from '../tutorial/types';

export interface CaseDefinition {
 slug:string; title:string; subtitle:string; difficulty:string; source:string;
 width:number; height:number; characterCount:number; intro:string;
 loadPuzzle:()=>Promise<Puzzle>;
 loadSteps:()=>Promise<Step[]>;
}
const puzzles=import.meta.glob<Puzzle>('./data/*.json',{import:'default'});
const lessons=import.meta.glob<Step[]>('../tutorial/data/*.json',{import:'default'});
export const cases:readonly CaseDefinition[]=entries.map(entry=>{
 const loadPuzzle=puzzles[`./data/${entry.slug}.json`];
 const loadSteps=lessons[`../tutorial/data/${entry.slug}.json`];
 if(!loadPuzzle||!loadSteps)throw new Error(`题目数据不完整：${entry.slug}`);
 return {...entry,loadPuzzle,loadSteps};
});
export function resolveRoute(pathname:string,search=''):{case?:CaseDefinition;redirect?:string;notFound?:boolean} {
 const path=pathname.replace(/\/+$/,'')||'/';
 const legacy=new URLSearchParams(search).get('case');
 if(path==='/'&&legacy){const found=cases.find(c=>c.slug===legacy);return found?{redirect:`/${found.slug}`}:{notFound:true};}
 if(path==='/')return {};
 const found=cases.find(c=>path===`/${c.slug}`);
 return found?{case:found,...(pathname!==path?{redirect:path}:{})}:{notFound:true};
}
