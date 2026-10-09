import {ids,type Puzzle,type CellId,type CharacterId,type PlacedObject} from './types';
type Raw = Record<string,Record<string,string>>;
function source(raw:unknown):Raw {if(!raw||typeof raw!=='object')throw Error('缺少关卡数据');const r=raw as Raw;for(const k of ['PROPERTIES','GRID','CHARACTERS'])if(!r[k])throw Error(`缺少 ${k}`);return r;}
function num(value:unknown):number {if(value===undefined||value===null||value===''||!Number.isFinite(Number(value)))throw Error('缺少有效数值');return Number(value);}
const cell=(row:number,col:number):CellId=>`R${row}C${col}`;
const zh=['他在箱子旁边。','她坐在椅子上。','她是唯一站在地毯上的人。','她在卧室里。','她在灌木或盆栽旁边。','他是死者。案发时，他与凶手在同一区域独处。'];
const kinds:Record<number,string>={1:'plant',2:'chair',4:'table',6:'bed',37:'shrub',42:'box'};
export function normalizeCase(raw:unknown):Puzzle {
 const r=source(raw),p=r.PROPERTIES,g=r.GRID,c=r.CHARACTERS;
 const width=num(p.grid_w),height=num(p.grid_h);if(width!==6||height!==6||num(p.total_chars)!==6)throw Error('此教学仅支持 24-Hour Delivery 的 6×6 关卡');
 const cells: Puzzle['cells']=[];const objects:PlacedObject[]=[];
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const obj=num(g[`room_objects_${x}_${y}`]);if(obj&&!kinds[obj])throw Error(`未知物体 ${obj}`);
  cells.push({id:cell(y+1,x+1),row:y+1,col:x+1,roomId:num(g[`room_code_${x}_${y}`]),occupiable:![1,4,37,42].includes(obj),carpet:num(g[`carpet_objects_${x}_${y}`])===5,objectIds:obj?[obj]:[]});
  if(obj&&obj!==4)objects.push({id:`object-${x}-${y}`,kind:kinds[obj],cells:obj===6?[cell(y+1,x+1),cell(y+1,x+2)]:[cell(y+1,x+1)],asset:`/assets/objects/${kinds[obj]}.svg`,x,y,width:obj===6?2:1,height:1});
 }
 // This case's connected two-cell furniture is rendered as a single original SVG.
 for(const [kind,x,y,w,h] of [['table',1,1,1,2],['table',3,3,2,1],['carpet',0,4,2,1],['carpet',3,2,2,1],['carpet',5,0,1,2]] as const){
  const occupied:CellId[]=[];for(let yy=y;yy<y+h;yy++)for(let xx=x;xx<x+w;xx++)occupied.push(cell(yy+1,xx+1));
  objects.push({id:`${kind}-${x}-${y}`,kind,cells:occupied,asset:`/assets/objects/${kind}.svg`,x,y,width:w,height:h,carpet:kind==='carpet'});
 }
 for(const o of objects.filter(o=>o.kind==='bed'))for(const id of o.cells){const s=cells.find(c=>c.id===id);if(!s)throw Error('床越界');if(!s.objectIds.includes(6))s.objectIds.push(6);}
 const names:Record<number,string>={0:'门廊',1:'前院',3:'餐厅',4:'卧室',5:'厨房'};
 const colors:Record<number,string>={0:'#dbb98f',1:'#b3fbdd',3:'#e4d2b9',4:'#feeda6',5:'#fde5b2'};
 const rooms=[...new Set(cells.map(c=>c.roomId))].map(id=>{if(!names[id])throw Error('未知区域');return {id,label:names[id],fill:colors[id],cells:cells.filter(c=>c.roomId===id).map(c=>c.id)};});
 return {id:'24h-delivery',width,height,cells,objects,rooms,characters:ids.map((id,i)=>{if(!c[`char_name_${i}`]||!c[`char_quote_en_${i}`])throw Error('缺少人物线索');return {id,name:c[`char_name_${i}`],portrait:`/assets/portraits/${id}.svg`,clueId:`${id}-clue`,clueZh:zh[i],clueEn:[c[`char_quote_en_${i}`],c[`char_subquote_en_${i}`]].filter(Boolean).join(' ')};})};
}
export function readSolution(raw:unknown):Record<CharacterId,CellId>{const r=source(raw),p=r.PROPERTIES;const size=num(p.cellsize);if(size<=0)throw Error('格子尺寸无效');return Object.fromEntries(ids.map((id,i)=>{const col=Math.floor((num(r.CHARACTERS[`letter_xpos_${i}`])-num(p.grid_rx))/size),row=Math.floor((num(r.CHARACTERS[`letter_ypos_${i}`])-num(p.grid_ry))/size);if(col<0||row<0||col>=num(p.grid_w)||row>=num(p.grid_h))throw Error('答案坐标越界');return [id,cell(row+1,col+1)];})) as Record<CharacterId,CellId>;}
