import type {CaseDefinition} from '../case/catalog';
import type {TutorialState} from '../tutorial/types';
import {renderBoard} from './board';
import {escape} from './helpers';
import './case-index.css';

const difficultyOrder = ['入门', '简单', '中等', '困难', '专家'] as const;
let indexInstance = 0;

/** The directory deliberately shows unsolved maps, with no teaching overlays. */
export function renderCaseIndex(cases: readonly CaseDefinition[]): HTMLElement {
  const instance = ++indexInstance;
  const root = document.createElement('main');
  root.className = 'case-library';
  root.innerHTML = `
    <header class="case-library-heading">
      <p class="case-library-eyebrow">MURDOKU · 逐步推理攻略</p>
      <h1>每一步推理，都讲清楚</h1>
      <p>从线索出发，跟着地图逐步排除、确定人物位置，理解每个结论的来由。卡住时，展开细讲再看一步。</p>
    </header>
    <div class="case-library-toolbar">
      <div class="case-library-filters" role="group" aria-label="按难度筛选">
        ${['全部', ...difficultyOrder].map((label, i) => `<button type="button" data-difficulty="${label}" aria-pressed="${i === 0}">${label}</button>`).join('')}
      </div>
      <label class="case-library-search"><span>查找攻略</span>
        <input type="search" aria-label="搜索题目" placeholder="输入中文或英文题目名称" autocomplete="off" />
      </label>
    </div>
    <p class="case-library-count" role="status" aria-live="polite"></p>
    <div class="case-library-grid"></div>
    <p class="case-library-empty" hidden>没有找到匹配的攻略，试试其他关键词或难度。</p>`;
  const grid = root.querySelector<HTMLElement>('.case-library-grid')!;
  const count = root.querySelector<HTMLElement>('.case-library-count')!;
  const empty = root.querySelector<HTMLElement>('.case-library-empty')!;
  let activeDifficulty = '全部';
  let query = '';
  const normalize = (value:string) => value.normalize('NFKC').toLowerCase().trim();
  const pending = new Map<Element, () => Promise<void>>();
  const observer = typeof IntersectionObserver === 'undefined' ? undefined : new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      pending.get(entry.target)?.();
      pending.delete(entry.target);
      observer?.unobserve(entry.target);
    }
    if (!pending.size) observer?.disconnect();
  }, {rootMargin: '400px'});

  const cards = cases.map((definition, index) => {
    const card = document.createElement('a');
    card.className = 'case-library-card';
    card.href = `/${definition.slug}`;
    card.dataset.difficulty = definition.difficulty;
    card.setAttribute('aria-label', `${definition.title}，${definition.subtitle}，${definition.difficulty}，${definition.width} × ${definition.height}`);
    card.innerHTML = `<div class="case-library-preview" aria-hidden="true"></div>
      <div class="case-library-card-body">
        <h2>${escape(definition.title)}</h2>
        <p class="case-library-subtitle">${escape(definition.subtitle)}</p>
        <div class="case-library-card-meta"><span class="case-library-badge">${escape(definition.difficulty)}</span><span class="case-library-size">${definition.width} × ${definition.height}</span><span class="case-library-arrow" aria-hidden="true">↗</span></div>
      </div>`;
    const preview = card.querySelector<HTMLElement>('.case-library-preview')!;
    const draw = async () => {
      try {
        const puzzle=await definition.loadPuzzle();
        const blank = {placements: {}, candidates: {}, eliminations: []} as unknown as TutorialState;
        const svg = renderBoard(puzzle, blank);
        svg.querySelectorAll('.cell-hit, .axis, .room-label').forEach(node => node.remove());
        svg.setAttribute('viewBox', `-9 -9 ${definition.width * 100 + 30} ${definition.height * 100 + 33}`);
        svg.setAttribute('aria-hidden', 'true');
        svg.removeAttribute('aria-label');
        svg.removeAttribute('role');
        svg.setAttribute('focusable', 'false');
        // Each SVG owns its patterns: duplicate document IDs break some browsers.
        svg.querySelectorAll('[id]').forEach(pattern => {
          const oldId = pattern.id;
          const newId = `preview-${instance}-${index}-${oldId}`;
          pattern.id = newId;
          svg.querySelectorAll(`[fill="url(#${oldId})"]`).forEach(node => node.setAttribute('fill', `url(#${newId})`));
        });
        preview.append(svg);
        preview.classList.add('is-ready');
      }catch{preview.textContent='地图预览暂不可用';}
    };
    if (observer) {
      pending.set(card, draw);
      observer.observe(card);
    } else draw();
    return {definition, card, searchText:normalize(`${definition.title} ${definition.subtitle} ${definition.slug}`)};
  });
  const locked = document.createElement('article');
  locked.className = 'case-library-card case-library-locked';
  locked.setAttribute('aria-label', 'Hoarders，待解锁');
  locked.innerHTML = `<div class="case-library-preview case-library-locked-preview" aria-hidden="true"><svg viewBox="0 0 72 86" fill="none"><rect x="10" y="35" width="52" height="43" rx="6" fill="#e7d7b3" stroke="currentColor" stroke-width="4"/><path d="M22 35V23a14 14 0 0 1 28 0v12" stroke="currentColor" stroke-width="4"/><circle cx="36" cy="54" r="5" fill="currentColor"/><path d="M36 58v8" stroke="currentColor" stroke-width="4"/></svg></div><div class="case-library-card-body"><h2>Hoarders</h2><p class="case-library-subtitle">待解锁</p><div class="case-library-card-meta"><span class="case-library-badge">待解锁</span></div></div>`;

  function update() {
    let visible = 0;
    for (const {card, definition, searchText} of cards) {
      card.hidden = (activeDifficulty !== '全部' && definition.difficulty !== activeDifficulty) || !query.split(/\s+/).every(word=>searchText.includes(word));
      if (!card.hidden) visible++;
    }
    locked.hidden = activeDifficulty !== '全部' || !query.split(/\s+/).every(word=>normalize('Hoarders 待解锁').includes(word));
    grid.replaceChildren(...cards.map(item => item.card), locked);
    count.textContent = `${visible} 篇推理攻略${!locked.hidden ? ' · 1 道待解锁' : ''}`;
    empty.hidden = visible > 0 || !locked.hidden;
  }
  root.querySelectorAll<HTMLButtonElement>('[data-difficulty]').forEach(button => button.addEventListener('click', () => {
    activeDifficulty = button.dataset.difficulty!;
    root.querySelectorAll<HTMLButtonElement>('[data-difficulty]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    update();
  }));
  root.querySelector('input')!.addEventListener('input', event => {
    query = normalize((event.target as HTMLInputElement).value);
    update();
  });
  update();
  return root;
}
