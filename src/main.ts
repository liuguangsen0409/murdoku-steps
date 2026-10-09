import type {Puzzle} from './case/types';
import type {Step,TutorialState} from './tutorial/types';
import {renderCaseIndex} from './ui/case-index';
import './styles.css';import {cases,resolveRoute,type CaseDefinition} from './case/catalog';import type {CharacterId} from './case/types';import {buildSnapshots} from './tutorial/replay';import {renderBoard,describeCell} from './ui/board';import {renderCharacters} from './ui/characters';import {renderLesson} from './ui/lesson';
const app=document.querySelector<HTMLDivElement>('#app')!;
const route=resolveRoute(location.pathname,location.search);
if(route.redirect)location.replace(route.redirect);
else if(route.case)mountCase(route.case);
else {
 document.body.classList.add('home-page');document.title='Murdoku · 推理手记';
 app.innerHTML=`<header class="site-header"><a class="wordmark" href="/"><img src="/assets/logo.svg" alt="Murdoku"/><small>逐步推理教学</small></a></header>`;
 if(route.notFound){const notice=document.createElement('p');notice.className='route-notice';notice.textContent='没有找到这道题，请从下方选择。';app.append(notice);}
 app.append(renderCaseIndex(cases));
 const footer=document.createElement('footer');footer.innerHTML='非官方中文教学 · 原题与美术素材来自 <a href="https://murdoku.com/">Murdoku / Manuel Garand</a>';app.append(footer);
}
async function mountCase(definition:CaseDefinition){
app.innerHTML='<p class="asset-error" role="status">正在加载这道题的推理手记…</p>';
let puzzle:Puzzle,steps:Step[],snapshots:TutorialState[];
try{
 [puzzle,steps]=await Promise.all([definition.loadPuzzle(),definition.loadSteps()]);
 snapshots=buildSnapshots(puzzle,steps);
}catch{
 app.innerHTML='<p class="asset-error" role="alert">题目加载失败，请刷新重试。<a href="/">返回全部题目</a></p>';return;
}
const {title,subtitle}=definition;
document.title=`${title} · Murdoku 推理教学`;
document.body.classList.toggle('hard-case',puzzle.characters.length===10);
document.body.classList.toggle('expert-case',puzzle.characters.length>10);
let currentIndex=0;let focus:CharacterId|undefined;
app.innerHTML=`<header class="site-header"><a class="wordmark" href="/" aria-label="Murdoku 推理手记首页"><img src="/assets/logo.svg" alt="Murdoku"/><small>逐步推理教学</small></a><a class="original-link" href="https://murdoku.com/play/${definition.source}" target="_blank" rel="noopener">去玩原题 <span aria-hidden="true">↗</span></a></header><main><div class="case-heading"><div><h1>${title} <span>${subtitle} · ${puzzle.width}×${puzzle.height}</span></h1></div><div class="case-meta"><a href="/">全部题目</a><span><i></i>${definition.difficulty}</span><span>${steps.length} 步主线</span></div></div><div class="workspace"><aside class="suspects-panel"><div class="panel-heading"><h2>Suspects <small>现场人物</small></h2><span id="placed-count">0 / ${puzzle.characters.length} 已确定</span></div><p class="suspects-note">点击人物，查看线索与候选位置</p>${puzzle.generalClues?.map(c=>`<p class="general-clue">${c.text}</p>`).join('')??''}<div id="characters"></div></aside><section class="map-panel"><div class="map-top"><span>案发现场</span><span>每行、每列最多一人</span></div><div id="board"></div><div class="map-legend"><span><i class="legend-candidate">A</i>候选位置</span><span><i class="legend-eliminated">A</i>本步排除</span><span><i class="legend-placed">A</i>已确定</span></div><p id="cell-description" aria-live="polite">点击地图格子，查看位置与状态</p><div class="map-bottom"><span>点击人物卡，可以单独查看他的线索</span><button id="clear-focus" hidden>返回本步视角</button></div></section><section class="teaching-panel"><div class="panel-heading"><h2>💡 Hint <small>逐步推理</small></h2><label class="directory-label">步骤目录<select id="step-select" aria-label="步骤目录"><option value="0">准备开始</option>${steps.map((s,i)=>`<option value="${i+1}">${String(i+1).padStart(2,'0')} · ${s.title}</option>`).join('')}</select></label></div><div id="lesson"></div></section></div><footer>非官方中文教学 · 原题与美术素材来自 <a href="https://murdoku.com/" target="_blank" rel="noopener">Murdoku / Manuel Garand</a></footer></main>`;
const select=app.querySelector<HTMLSelectElement>('#step-select')!;
function draw(){const state=snapshots[currentIndex];const original=steps[currentIndex-1];const view=focus?{...(original??{id:'intro',title:'',explanation:'',actions:[],clueRefs:[],highlightCells:[]}),focusCharacters:[focus],candidateCharacters:[focus]}:original;
 app.querySelector('#board')!.replaceChildren(renderBoard(puzzle,state,view));app.querySelector('#characters')!.replaceChildren(renderCharacters(puzzle,state,view));app.querySelector('#lesson')!.replaceChildren(renderLesson(original,currentIndex,steps.length,navigate,puzzle,definition.intro));select.value=String(currentIndex);app.querySelector('#placed-count')!.textContent=`${Object.keys(state.placements).length} / ${puzzle.characters.length} 已确定`;app.querySelector<HTMLButtonElement>('#clear-focus')!.hidden=!focus;
 app.querySelector('#cell-description')!.textContent=focus?`正在查看 ${puzzle.characters.find(c=>c.id===focus)!.name} 的线索与候选`:'点击地图格子，查看位置与状态';
 app.querySelectorAll<HTMLButtonElement>('[data-focus]').forEach(b=>b.addEventListener('click',()=>{focus=focus===b.dataset.focus?undefined:b.dataset.focus as CharacterId;const clicked=b.dataset.focus;draw();app.querySelector<HTMLButtonElement>(`[data-focus="${clicked}"]`)?.focus({preventScroll:true});}));
 app.querySelectorAll<SVGElement>('[data-cell]').forEach(el=>{const inspect=()=>{const c=puzzle.cells.find(c=>c.id===el.dataset.cell)!;app.querySelector('#cell-description')!.textContent=describeCell(puzzle,state,c);};el.addEventListener('click',inspect);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();inspect();}});});
}
function navigate(n:number){if(n<0||n>steps.length)return;const wasNext=document.activeElement?.classList.contains('next');const wasPrevious=document.activeElement?.classList.contains('previous');currentIndex=n;focus=undefined;draw();if(wasNext)app.querySelector<HTMLButtonElement>('.next')?.focus({preventScroll:true});if(wasPrevious)app.querySelector<HTMLButtonElement>('.previous')?.focus({preventScroll:true});}
select.addEventListener('change',()=>navigate(Number(select.value)));app.querySelector('#clear-focus')!.addEventListener('click',()=>{focus=undefined;draw();});
async function start(){try{await Promise.all([...new Set([...puzzle.objects.map(o=>o.asset),...puzzle.characters.map(c=>c.portrait)])].map(src=>new Promise<void>((resolve,reject)=>{const img=new Image();img.onload=()=>resolve();img.onerror=()=>reject(Error(`素材加载失败：${src}`));img.src=src;})));draw();}catch(e){const message=document.createElement('div');message.className='asset-error';message.setAttribute('role','alert');message.textContent=`地图未加载完整，教学已暂停。${e instanceof Error?e.message:''} 请刷新页面重试。`;app.querySelector('.workspace')!.replaceChildren(message);}}
start();

}
