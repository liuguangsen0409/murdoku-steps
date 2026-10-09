import {portraitMarkup} from './portrait';
import type {Puzzle} from '../case/types';import type {TutorialState,Step} from '../tutorial/types';import {element,escape} from './helpers';
export function rosterLayout(count:number):{rows:number;columns:number} {
 const rows=count>=10||count===7?4:Math.min(3,count);
 return {rows,columns:Math.ceil(count/rows)};
}
export function renderCharacters(p:Puzzle,s:TutorialState,step?:Step):HTMLElement {
 const {rows,columns}=rosterLayout(p.characters.length);
 return element(`<div class="characters-list" style="--roster-rows:${rows};--roster-columns:${columns}" data-rows="${rows}" data-columns="${columns}">${p.characters.map(c=>`<article class="character ${s.placements[c.id]?'is-placed':''} ${step?.focusCharacters.includes(c.id)?'is-focused':''}" data-character="${c.id}"><button class="character-head" data-focus="${c.id}" aria-label="查看 ${c.name} 的线索">${portraitMarkup(c,true)}${s.placements[c.id]?'<span class="placement-check" role="img" aria-label="位置已确定"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m3.5 8 3 3 6-6"/></svg></span>':''}<span class="identity"><strong>${c.name}</strong>${c.role?`<small>${c.role}</small>`:''}</span></button><div class="clue-card"><p>${escape(c.clueZh).replace(/箱子|椅子|唯一|地毯|卧室|灌木|盆栽|死者|独处/g, word=>`<strong>${word}</strong>`)}</p></div></article>`).join('')}</div>`);
}
