import type {Character} from '../case/types';
import {escape} from './helpers';
export const portraitColors:Record<string,string>={A:'#ae6453',B:'#50894e',C:'#78aeb3',D:'#7c89c2',E:'#715880',F:'#ad7954',G:'#4b9254',H:'#b988bc',I:'#679eb5',J:'#bbae68',K:'#858598',L:'#8da47f',M:'#bd996a',N:'#939894',O:'#777b78',V:'#d0a3a3'};
/** Shared artwork, crop and background for suspect cards and evidence chips. */
export function portraitMarkup(character:Character,letter=false):string {
 return `<span class="portrait-wrap" style="--card-color:${portraitColors[character.id]}"><img src="${escape(character.portrait)}" alt="${letter?escape(character.name):''}"/>${letter?`<span class="character-letter">${character.id}</span>`:''}</span>`;
}
