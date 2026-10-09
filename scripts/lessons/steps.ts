import type {CharacterId,CellId} from '../../src/case/types';
import type {Step,Action,Reason} from '../../src/tutorial/types';
const reason=(ruleId:string,chars:CharacterId[],prior:number[]=[]):Reason=>({ruleId,clueRefs:chars.map(c=>`${c}-clue`),dependsOn:prior.map(n=>`step-${String(n).padStart(2,'0')}`)});
const set=(character:CharacterId,...cells:CellId[]):Action=>({type:'setCandidates',character,cells});
const remove=(character:CharacterId,cells:CellId[],r:Reason):Action[]=>cells.map(cell=>({type:'removeCandidate',character,cell,reason:r}));
const place=(character:CharacterId,cell:CellId,prior:number[],propagate=true):Action[]=>[{type:'placeCharacter',character,cell,reason:reason('唯一位置',[character],prior)},...(propagate?[{type:'applyRowColumnConstraint',character,reason:reason('每行每列一人',[character],prior)} as Action]:[])];
const rowReason=(prior:number[])=>reason('行列占用',[],prior);
const carpet=reason('地毯独占',['C'],[3]);
const bedroom:CellId[]=['R1C4','R1C5','R1C6','R2C4','R2C5','R2C6'];
const rugs:CellId[]=['R1C6','R2C6','R3C4','R3C5','R5C1','R5C2'];
const indoor:CellId[]=['R3C1','R4C2','R1C5','R2C4','R2C6'];
const outdoor:CellId[]=['R5C3','R5C5','R6C4','R6C6'];
const rows:{title:string;explanation:string;focus:CharacterId[];cells:CellId[];actions:Action[];rule:string}[]=[
 {title:'先找到那只箱子',explanation:'从 Alexander 的线索开始：他在箱子旁边。地图上的箱子位于 R6C2，在左下角的门廊里。先找物体，再判断它周围哪些格子符合条件。',focus:['A'],cells:['R6C2'],actions:[],rule:'旁边 = 上下左右相邻，而且在同一区域'},
 {title:'他只有两个候选位置',explanation:'箱子上方 R5C2 和左边 R6C1 都在门廊内。右边 R6C3 已经是前院，下方则越出地图，因此不符合「旁边」的定义。先给这两格记上小写候选 A。',focus:['A'],cells:['R5C2','R6C1'],actions:[set('A','R5C2','R6C1')],rule:'先圈定候选，不急着落位'},
 {title:'另一条线索里，有一个「唯一」',explanation:'Carol 是唯一站在地毯上的人。它同时告诉我们：Carol 在地毯上，而且其他所有人都不能站在地毯上。回头观察 Alexander 的两个候选。',focus:['C','A'],cells:rugs,actions:[],rule:'一条线索，也能约束其他人物'},
 {title:'地毯上的 A，可以划掉了',explanation:'R5C2 有地毯，而 Alexander 不是 Carol。所以这格不能属于 Alexander。这里只划掉 A，并不表示这个格子永远不能站人。',focus:['A','C'],cells:['R5C2'],actions:remove('A',['R5C2'],carpet),rule:'排除某个人 ≠ 排除整个格子'},
 {title:'确定 Alexander 的位置',explanation:'两个候选排除一个，剩下的 R6C1 就是 Alexander 唯一的位置。将候选 A 换成确定的人物标记。',focus:['A'],cells:['R6C1'],actions:place('A','R6C1',[2,4],false),rule:'只剩一个候选，就可以确定'},
 {title:'一个位置，带来一整行和一整列的排除',explanation:'每行、每列最多一人。Alexander 在 R6C1，因此其他人都不能再占用第 6 行或第 1 列。黑色叉号记录这项公共限制。',focus:['A'],cells:['R6C1'],actions:[{type:'applyRowColumnConstraint',character:'A',reason:rowReason([5])}],rule:'确定位置后，把影响传播出去'},
 {title:'Bella 可以坐在哪把椅子上？',explanation:'Bella 的线索说她坐在椅子上。地图有三把椅子：R1C2、R2C1、R3C1。这里先列出线索给出的原始候选，下一步用已知行列限制筛选。',focus:['B'],cells:['R1C2','R2C1','R3C1'],actions:[set('B','R1C2','R2C1','R3C1')],rule:'原始候选，还要经过已有事实筛选'},
 {title:'两把椅子都在被占用的列',explanation:'R2C1 和 R3C1 都位于第 1 列，与 Alexander 冲突。即使它们是椅子，Bella 也不能坐在那里。只剩 R1C2。',focus:['B','A'],cells:['R2C1','R3C1'],actions:remove('B',['R2C1','R3C1'],rowReason([5,6])),rule:'线索和行列限制必须同时满足'},
 {title:'确定 Bella 的位置',explanation:'把 Bella 放到 R1C2。第 1 行和第 2 列也被占用了，这会帮助我们处理卧室里的 Dalia。',focus:['B'],cells:['R1C2'],actions:place('B','R1C2',[7,8]),rule:'每次落位，都更新公共限制'},
 {title:'把注意力缩小到卧室',explanation:'Dalia 在卧室里，即右上角两行、三列组成的区域。先圈出这六格。这里的植物不能站人，而床可以；我们会逐项筛选。',focus:['D'],cells:bedroom,actions:[set('D',...bedroom)],rule:'区域线索先限制搜索范围'},
 {title:'卧室的第一行不能用了',explanation:'Bella 已经占据第 1 行，因此卧室的 R1C4、R1C5、R1C6 都被排除。注意：床可以站人，排除床上位置的理由是同行冲突。',focus:['D','B'],cells:['R1C4','R1C5','R1C6'],actions:remove('D',['R1C4','R1C5','R1C6'],rowReason([9])),rule:'说清楚真正的排除理由'},
 {title:'植物和地毯，各排除一格',explanation:'R2C5 是盆栽，不允许站人；R2C6 是地毯，而只有 Carol 可以站在地毯上。卧室第二行只剩下 R2C4。',focus:['D','C'],cells:['R2C5','R2C6'],actions:[...remove('D',['R2C5'],reason('物体占用',['D'])),...remove('D',['R2C6'],carpet)],rule:'物体规则 + 地毯独占'},
 {title:'确定 Dalia 的位置',explanation:'Dalia 只能在 R2C4。放好她后，第 2 行和第 4 列也不能再放其他人。现在回到 Carol 的地毯线索。',focus:['D'],cells:['R2C4'],actions:place('D','R2C4',[11,12]),rule:'区域内唯一候选'},
 {title:'把所有地毯格找出来',explanation:'Carol 必须在地毯上。三张地毯一共覆盖六格：卧室 R1C6、R2C6，厨房 R3C4、R3C5，门廊 R5C1、R5C2。先展示这些原始候选。',focus:['C'],cells:rugs,actions:[set('C',...rugs)],rule:'大物体覆盖的每一格都要检查'},
 {title:'六个地毯格，排除五个',explanation:'R1C6 与 Bella 同行；R2C6 与 Dalia 同行；R3C4 与 Dalia 同列；R5C1 与 Alexander 同列；R5C2 与 Bella 同列。于是只剩厨房的 R3C5。',focus:['C'],cells:['R1C6','R2C6','R3C4','R5C1','R5C2'],actions:remove('C',['R1C6','R2C6','R3C4','R5C1','R5C2'],rowReason([5,9,13])),rule:'用已有位置，交叉筛选候选'},
 {title:'确定 Carol 的位置',explanation:'Carol 在 R3C5。她所在的第 3 行和第 5 列也被占用。现在只剩 Evangeline 与死者 Viraj 尚未落位。',focus:['C'],cells:['R3C5'],actions:place('C','R3C5',[14,15]),rule:'唯一候选确定位置'},
 {title:'植物和灌木，两种可能都要看',explanation:'Evangeline 在灌木或盆栽旁边。先找餐厅、卧室里的盆栽，再看前院的两丛灌木。斜角相邻和跨房间相邻都不算。',focus:['E'],cells:['R4C1','R2C5','R5C4','R6C5'],actions:[set('E',...indoor,...outdoor)],rule:'「或」表示两类候选的并集'},
 {title:'室内的候选都不成立',explanation:'餐厅的 R3C1 与 A 同列，R4C2 与 B 同列。卧室的 R1C5 与 B 同行，R2C4 已被 D 占据；R2C6 既与 D 同行，又是仅 C 可站的地毯。室内没有位置留给 E。',focus:['E'],cells:indoor,actions:remove('E',indoor,rowReason([5,9,13,16])),rule:'把每个分支都检查完整'},
 {title:'前院只剩一个位置',explanation:'前院灌木旁的原始候选是 R5C3、R5C5、R6C4、R6C6。R5C5 与 Carol 同列；R6C4 和 R6C6 与 Alexander 同行。只有 R5C3 不冲突。',focus:['E'],cells:outdoor,actions:remove('E',['R5C5','R6C4','R6C6'],rowReason([5,16])),rule:'先分区域，再用行列筛选'},
 {title:'确定 Evangeline 的位置',explanation:'将 Evangeline 放在前院的 R5C3。五位人物的位置已经确定，最后一位是死者 Viraj。',focus:['E'],cells:['R5C3'],actions:place('E','R5C3',[18,19]),rule:'每一次确定，都让剩余问题更小'},
 {title:'最后一行，与最后一列',explanation:'六个人要放入六行、六列，而且不能同行或同列。现在只有第 4 行和第 6 列还没有人，它们的交点 R4C6 必须留给最后一人。',focus:['V'],cells:['R4C6'],actions:[set('V','R4C6')],rule:'人数等于行列数：每行每列恰好一人'},
 {title:'还原死者的位置',explanation:'Viraj 在 R4C6，位于厨房。死者与其他人物遵守相同的行列规则。人物位置已经完整，但还需要用他的线索判断凶手。',focus:['V'],cells:['R4C6'],actions:place('V','R4C6',[20,21]),rule:'死者也计入人数'},
 {title:'检查谁与死者独处',explanation:'死者的线索要求他和凶手处在同一区域，而且没有第三人。厨房里恰好只有 R3C5 和 R4C6 的两个人。这里判断的是整个房间，不要求相邻。',focus:['C','V'],cells:['R3C4','R3C5','R3C6','R4C4','R4C5','R4C6'],actions:[],rule:'同区域 + 恰好两人'},
 {title:'案件还原完成',explanation:'Carol 就是凶手。她与死者 Viraj 在厨房独处，且六个人的位置同时满足全部线索。你已经用到了：候选枚举、独占线索、行列排除、唯一位置，以及房间人数核对。',focus:['C','V'],cells:['R3C5','R4C6'],actions:[],rule:'结论来自完整的位置与人数关系'}
];
export const steps:Step[]=rows.map((r,i)=>({id:`step-${String(i+1).padStart(2,'0')}`,title:r.title,explanation:r.explanation,focusCharacters:r.focus,clueRefs:r.focus.map(c=>`${c}-clue`),highlightCells:r.cells,actions:r.actions,rule:r.rule}));
