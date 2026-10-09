import {portraitColors} from './portrait';
import type {Puzzle,Cell,CharacterId,CellId} from '../case/types';
import type {TutorialState,Step} from '../tutorial/types';
import {escape} from './helpers';
export function describeCell(puzzle:Puzzle,state:TutorialState,c:Cell):string {const who=Object.entries(state.placements).find(([,pos])=>pos===c.id)?.[0];const candidates=Object.entries(state.candidates).filter(([,cells])=>cells.includes(c.id)).map(([id])=>id);return `${c.id} · ${puzzle.rooms.find(r=>r.id===c.roomId)?.label}${c.objectIds.map(id=>' · '+(puzzle.objectNames??{1:'盆栽',2:'椅子',4:'桌子',6:'床',37:'灌木',42:'箱子',13:'货架',15:'马',16:'仙人掌',83:'保险箱',89:'麻袋',94:'收银机'} as Record<number,string>)[id]).join('')}${c.carpet?' · 地毯':''}${c.water?' · 水域':''}${!c.occupiable?' · 物体占用，不可站立':''}${who?` · ${puzzle.characters.find(p=>p.id===who)?.name} 已确定`:candidates.length?` · 待筛选候选 ${candidates.join('、')}`:' · 尚无人物落位'}`;}
export function visibleCandidate(state:TutorialState,step:Step|undefined,cell:CellId):CharacterId|undefined {return (step?.candidateCharacters??step?.focusCharacters)?.find(id=>state.candidates[id].includes(cell));}
export function renderBoard(puzzle:Puzzle,state:TutorialState,step?:Step):SVGSVGElement {
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');const boardWidth=puzzle.width*100,boardHeight=puzzle.height*100;svg.setAttribute('viewBox',`-48 -38 ${boardWidth+86} ${boardHeight+76}`);svg.setAttribute('role','group');svg.setAttribute('aria-label',`${puzzle.width}×${puzzle.height} 案发现场，可点击格子查看详情`);svg.classList.add('crime-map');
 const textureOf=(c:Cell)=>c.texture??(c.roomId===1?'grass':c.roomId===5?'squaretile':'woodentile');
 const textures=new Map(puzzle.cells.map(c=>[textureOf(c),c.textureAsset===undefined?`/assets/textures/${textureOf(c)}.svg`:c.textureAsset]));
 const parts:string[]=['<defs>'+[...textures].filter(([,asset])=>asset).map(([kind,asset])=>`<pattern id="floor-${kind}" width="100" height="100" patternUnits="userSpaceOnUse"><image href="${asset}" width="100" height="100" opacity=".28"/></pattern>`).join('')+'</defs>'];
 parts.push(`<rect x="12" y="15" width="${boardWidth}" height="${boardHeight}" fill="#bcb9c4" aria-hidden="true"/>`);
 for(let n=0;n<puzzle.width;n++)parts.push(`<text x="${n*100+50}" y="-17" class="axis">C${n+1}</text>`);
 for(let n=0;n<puzzle.height;n++)parts.push(`<text x="-26" y="${n*100+55}" class="axis">R${n+1}</text>`);
 for(const c of puzzle.cells){const x=(c.col-1)*100,y=(c.row-1)*100;parts.push(`<rect x="${x}" y="${y}" width="100" height="100" fill="${c.fill??puzzle.rooms.find(r=>r.id===c.roomId)!.fill}"/>`);if(textures.get(textureOf(c)))parts.push(`<rect x="${x}" y="${y}" width="100" height="100" fill="url(#floor-${textureOf(c)})"/>`);}
 for(const o of [...puzzle.objects].sort((a,b)=>Number(!!b.carpet)-Number(!!a.carpet))){const pad=o.carpet?9:11;parts.push(`<image href="${o.asset}" x="${o.x*100+pad}" y="${o.y*100+pad}" width="${o.width*100-pad*2}" height="${o.height*100-pad*2}" preserveAspectRatio="none"/>`);}
 for(let n=1;n<puzzle.width;n++)parts.push(`<path d="M${n*100} 0V${boardHeight}" stroke="#302b24" stroke-width="2" opacity=".7"/>`);
 for(let n=1;n<puzzle.height;n++)parts.push(`<path d="M0 ${n*100}H${boardWidth}" stroke="#302b24" stroke-width="2" opacity=".7"/>`);
 for(const c of puzzle.cells){const x=(c.col-1)*100,y=(c.row-1)*100;for(const [dx,dy,d] of [[1,0,`M${x+100} ${y}v100`],[0,1,`M${x} ${y+100}h100`]] as const){const other=puzzle.cells.find(q=>q.col===c.col+dx&&q.row===c.row+dy);if(other&&other.roomId!==c.roomId)parts.push(`<path d="${d}" stroke="#171717" stroke-width="7"/>`);}}
 parts.push(`<rect width="${boardWidth}" height="${boardHeight}" fill="none" stroke="#171717" stroke-width="7" rx="2"/>`);
 // Room labels sit at the edges of their regions, below the central furniture.
 for(const [label,x,y] of (puzzle.roomLabels?.map(r=>[r.label,r.x,r.y])??(puzzle.width===10?[['教堂',650,488],['户外',580,685],['杂货店',230,988],['牧师家',148,288],['银行',840,988],['门廊',550,988]]:[['餐厅',148,388],['卧室',448,188],['厨房',448,388],['门廊',98,588],['前院',399,588]])) as [string,number,number][])parts.push(`<text x="${x}" y="${y}" class="room-label">${label}</text>`);
 const positions=Object.entries(state.placements);
 for(const c of puzzle.cells){
  const x=(c.col-1)*100,y=(c.row-1)*100,who=positions.find(([,id])=>id===c.id)?.[0] as CharacterId|undefined;
  const inLine=state.blockedCells?.includes(c.id)||positions.some(([,id])=>{const other=puzzle.cells.find(q=>q.id===id)!;return other.row===c.row||other.col===c.col;})||state.eliminations.some(e=>e.cell===c.id&&e.reason.ruleId==='行列占用'||e.cell===c.id&&e.reason.ruleId==='每行每列一人');
  if(inLine&&!who&&c.occupiable)parts.push(`<image class="excluded-cell" href="/assets/objects/x.svg" x="${x+15}" y="${y+15}" width="70" height="70"/>`);
  if(step?.highlightCells.includes(c.id))parts.push(`<rect x="${x+5}" y="${y+5}" width="90" height="90" rx="7" fill="#cc6235" fill-opacity=".08" stroke="#bc5a30" stroke-width="3"/>`);
  const candidate=visibleCandidate(state,step,c.id);const primary=candidate??(step?.candidateCharacters??step?.focusCharacters)?.[0];const active=!!candidate;
  const removed=primary&&state.eliminations.some(e=>e.character===primary&&e.cell===c.id)&&step?.actions.some(a=>a.type==='removeCandidate'&&a.character===primary&&a.cell===c.id);
  if(active&&!who)parts.push(`<circle cx="${x+50}" cy="${y+50}" r="24" fill="#fff9ed" stroke="#bc5a30" stroke-width="2" stroke-dasharray="4 3"/><text x="${x+50}" y="${y+59}" class="candidate">${primary}</text>`);
  if(removed&&!who&&!inLine)parts.push(`<circle cx="${x+50}" cy="${y+50}" r="23" fill="#fff9f3" fill-opacity=".95"/><text x="${x+50}" y="${y+59}" class="candidate removed">${primary}</text><path d="M${x+31} ${y+69}l38-38" stroke="#a65548" stroke-width="3"/>`);
  if(who){const color=portraitColors[who];parts.push(`<image class="placed-portrait" href="${puzzle.characters.find(c=>c.id===who)!.portrait}" x="${x+12.5}" y="${y+12.5}" width="75" height="75"/><text x="${x+6}" y="${y+29}" class="placed-letter" style="fill:${color}">${who}</text>`);}

  const desc=escape(describeCell(puzzle,state,c));parts.push(`<rect class="cell-hit" data-cell="${c.id}" x="${x+2}" y="${y+2}" width="96" height="96" fill="transparent" tabindex="0" role="button" aria-label="${desc}"><title>${desc}</title></rect>`);
 }
 svg.innerHTML=parts.join('');return svg;
}
