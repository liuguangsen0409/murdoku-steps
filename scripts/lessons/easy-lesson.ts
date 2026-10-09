import {steps as atomicSteps} from './steps';
import type {Step} from '../../src/tutorial/types';

// Preserve the verified atomic action order while presenting larger reading stages.
export const easyGroups = [
 {from:1,to:2,title:'先圈出 Alexander 的两个候选',explanation:'箱子在门廊的 R6C2。符合“同一区域、上下左右相邻”的位置只有 R5C2 和 R6C1，先保留两个候选。',rule:'先找候选，不急着落位'},
 {from:3,to:6,title:'用地毯线索，确定 Alexander',explanation:'Carol 是唯一能站在地毯上的人，因此 Alexander 不能在 R5C2。他只能在 R6C1，同时占据第 6 行和第 1 列。',rule:'一条人物线索，也会约束其他人'},
 {from:7,to:9,title:'确定 Bella：R1C2',explanation:'三把椅子中，R2C1 和 R3C1 都与 Alexander 同列。Bella 只剩 R1C2，第 1 行和第 2 列也随之被占据。',rule:'家具条件与行列限制同时满足'},
 {from:10,to:13,title:'确定 Dalia：R2C4',explanation:'卧室第一行被 Bella 排除；第二行的盆栽不能站人，地毯只属于 Carol。Dalia 因此只能在 R2C4。',rule:'分别检查区域、物体和其他线索'},
 {from:14,to:16,title:'确定 Carol：R3C5',explanation:'三张地毯共覆盖六格。其中五格与已确定的人物同行或同列，只有厨房的 R3C5 留给 Carol。',rule:'用已知位置筛选全部候选'},
 {from:17,to:17,title:'Evangeline 的两类候选都要检查',explanation:'Evangeline 在盆栽或灌木旁边。先圈出室内盆栽和前院灌木周围的候选；“或”表示两类位置都要考虑。',rule:'分支都要检查，不能只选一种可能'},
 {from:18,to:20,title:'确定 Evangeline：R5C3',explanation:'室内候选全部与已知位置冲突；前院的四个候选也排除了三个。Evangeline 只剩 R5C3。',rule:'先分区域，再逐项排除'},
 {from:21,to:22,title:'确定死者 Viraj：R4C6',explanation:'五人落位后，只剩第 4 行和第 6 列没有人。死者位于交点 R4C6，在厨房里。',rule:'死者也计入每行、每列的人数'},
 {from:23,to:24,title:'谁与死者独处？',explanation:'厨房里只有 Carol 和死者 Viraj，没有第三人。因此 Carol 就是凶手；“独处”看的是同一区域，不要求两人相邻。',rule:'用区域人数验证最终结论'}
] as const;
const owner=new Map(atomicSteps.map((s,i)=>[s.id,easyGroups.findIndex(g=>i+1>=g.from&&i+1<=g.to)]));
export const steps:Step[]=easyGroups.map((group,index)=>{
 const source=atomicSteps.slice(group.from-1,group.to),last=source[source.length-1];
 return {
  id:`easy-${index+1}`,title:group.title,explanation:group.explanation,rule:group.rule,
  clueRefs:[...new Set(source.flatMap(s=>s.clueRefs))],
  focusCharacters:last.focusCharacters,highlightCells:last.highlightCells,
  details:source.map(s=>s.explanation),
  actions:source.flatMap(s=>s.actions).map(action=>{
   const copy=structuredClone(action);
   if('reason' in copy)copy.reason.dependsOn=[...new Set(copy.reason.dependsOn.map(id=>{
    const dependency=owner.get(id);if(dependency===undefined||dependency>index)throw Error(`无效教学依赖：${id}`);
    return dependency===index?null:`easy-${dependency+1}`;
   }).filter((id):id is string=>id!==null))];
   return copy;
  })
 };
});
