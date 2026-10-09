# Murdoku Steps

已收录 39 道公开题目，共用地图、人物卡、可逆步骤回放和“主线 + 展开细讲”阅读器。首页另保留 Hoarders 待解锁卡片，没有下载其受限题目数据。

| 路径 | 题目 | 人数 | 主线 / 可选细讲 |
|---|---|---|---|
| `/` | 40 张卡片的题目目录（39 可玩 + 1 待解锁） | — | — |
| `/24h-delivery` | 24-Hour Delivery · 入门 | 6 | 9 / 24 |
| `/frontier-town` | Frontier Town · 困难 | 10 | 17 / 48 |
| `/the-zoo` | The Zoo · 专家 | 16 | 21 / 68 |

旧 `/?case=frontier-town` 链接自动跳到独立路径。未知路径显示返回题目入口；部署时需要将这些前端路径回退到 `index.html`，Vite 本地开发已支持。

## 运行与验证

建议 Node.js 22（`nvm use`）。本目录执行 `npm ci`、`npm run dev -- --host 127.0.0.1`，访问 http://127.0.0.1:5173/。

- `npm test`：地图语义、约束、步骤回放、路线兼容与旧题回归。
- `npm run build`：类型检查与生产构建。
- `npm run prepare:case`：重新生成入门题数据。
- `python3 scripts/prepare-frontier.py` / `python3 scripts/prepare-zoo.py`：从保存的原始 JSON 生成地图、推理步骤与证据；每次落位都断言候选唯一，最后核对源答案。

素材已保存在 `public/assets`，启动不访问原站。`prepare-*-assets.py` 是素材提取记录，依赖研究时观察到的 `/tmp/murdoku-app.js` 与 `/tmp/murdoku-game.js`；只解析静态 SVG 引用，不执行下载的脚本。重新提取需要对应的源文件与网络。

## 使用

点击“开始推理”，可随时后退或通过目录跳转。点击人物及关联头像，单独查看他的候选；已落位人物以头像右上角对钩标识。地图格子可点击或用键盘检查。

“为什么”按条展示细讲，地图保留当前主线终点的状态，尚未为每条细讲独立回放。刷新回到本题介绍，未实现持久进度。

桌面采用三栏一屏布局。人物卡统一头像在上、线索在下：6 人 3×2，7 人 4×2，8–9 人 3×3，10 人以上固定 4 行并按需增加列；专家题的 16 人为 4×4；窄屏采用地图、教学、人物的纵向排列。

## 数据与复用

- `src/case/catalog.ts`：题目配置和路径解析。
- `src/case/data/<slug>.json`：标准化地图、人物、线索；专家题保留水域样式，同时将其归入所在栖息地。
- `src/tutorial/data/<slug>.json`：39 题统一的教学数据；同目录下的 TS 文件负责类型与回放。
- `src/ui/*`：全部题目共享的视图。
- `sources/`：原始数据与素材出处；`analysis/`：中文推理稿和计算证据。
- `analysis/reusable-components.md`：通用组件与案件专用逻辑的边界。

已有 3 题及 Golf、CEO’s Office 采用人工编排的可验证教学；另 34 题由显式线索模型生成证明，再编译为主线与简短细讲。这不是自动理解任意 Murdoku 自然语言的通用解题器。推导阶段不读取答案字段，完成后才核对官网答案。

本次新增 36 题共 645 步主线，单题 11–29 步。页面细讲每步最多 7 条、单条最长 124 字符；完整候选列表、排除证据与反证传播链保存在 `analysis/generated/`。依靠完整枚举才能排除的分支明确说明枚举，不伪装成局部直推。

地图与教学均按题目动态加载，首页地图缩略图进入可见范围才加载对应数据并绘制。目录支持难度筛选和中英文名称即时搜索，不展示解答耗时。

## 来源

原题及美术素材属于 Murdoku / Manuel Garand；本项目为非官方中文教学，独立的非官方攻略项目。中文讲解基于地图和线索细化推导。家具配色和人物使用原 SVG；部分桌子按单格显示，地板纹理和排版为教学版处理，非逐像素复刻。

- https://murdoku.com/play/puzzle-24h-delivery-easy
- https://murdoku.com/play/puzzle-frontier-town-hard
- https://murdoku.com/play/puzzle-the-zoo-expert

## 批量内容流程

以 `sources/catalog/available.json` 为公开题目清单；保留了原始英文及官方简体中文 JSON。日期清单为此次访问官网所得快照，不在浏览器运行时自动更新。

1. `python3 scripts/normalize-catalog.py`：标准化 36 个新增地图（重新执行依赖研究时保存的官方 core 脚本）。
2. `python3 scripts/catalog-solver.py`：对 34 题建立单人、人物关系、行列、人数与匿名同伴约束，记录候选缩减；可在命令后附单个 slug。
3. `python3 scripts/prepare-expert-lessons.py`：生成另外两篇专家教学和完整线索检查。
4. `python3 scripts/compile-catalog-lessons.py`：将 34 份证明压缩为教学，完整证据留在 analysis。
5. `python3 scripts/verify-catalog-lessons.py`：独立逐动作回放 36 题，检查每次落位前候选唯一、引用合法、行列不冲突、死者同区恰好两人。
6. `npm test && npm run build`：58 项自动测试、TypeScript 检查与打包。

素材生成工具为 `prepare-catalog-assets.py`、`prepare-catalog-textures.py`。所有教学所需资源已本地保存。

### 已核实的数据差异

- River Crossing 实际地图为 9 列 × 10 行，按原始网格渲染和求解，不沿用目录中的 9×9 标签。
- Minigolf 的 Path 与 Water 共用纹理编号，路径按区域语义判定，不能以纹理推断水域。
- Golf 最后一条官方提示误把与死者同区的 B 写成 D；教学根据地图、全部线索及答案核验，凶手为 B。
- Pigsty 的物体 142 在官网当前注册表无定义，官方画面对应格也未显示物体。本地用透明占位保留源记录；它没有参与泥坑约束，仍可推得唯一且一致的答案。
- 部分旧纹理注册项没有对应 SVG，保留官方区域底色；地毯按格绘制，教学版未复刻所有原站的门窗装饰。

## 目录约定与维护

- `src/case/data/` 和 `src/tutorial/data/` 各 39 个 JSON，以相同 slug 一一对应，不再区分首批与批量生成题目。
- `src/case/entries.ts` 是唯一目录清单（标题、难度、地图尺寸等轻量元信息）；`catalog.ts` 使用 Vite glob 自动关联地图、教学的异步加载器。
- `scripts/lessons/` 保留入门题原始编排和分组代码；`npm run prepare:case` 同时产出地图与教学 JSON，前端不再运行编排脚本。
- 所有生产脚本统一写入 `data/`；批量求解器保留原来的 34 题范围，独立 Python 验证保留 36 题范围，原 3 题由对应测试覆盖。
- 数据一致性测试检查目录文件一一对应、元信息匹配和 39 道终局回放，避免新增题目时漏配地图或教学。

本次统一目录后，入口 JS 从约 1.53 MB 降至 42.48 KB（gzip 13.33 KB）；地图和教学数据分块按需获取，不计入该入口大小。

## GitHub 与 Vercel 部署

- 仓库：`liuguangsen0409/murdoku-steps`，主分支 `main`。
- Vercel 导入 GitHub 仓库时，Root Directory 选择根目录，Framework Preset 为 Vite；`vercel.json` 已指定 `npm ci`、`npm run build` 和 `dist`。
- Node.js 使用 22.x。此静态站无需环境变量、数据库或密钥。
- SPA rewrite 将题目地址回退到 `index.html`，支持直接访问与刷新 `/the-zoo` 等路由。
- 目标域名：`murdoku-steps.unclejiwa.com`。在 Vercel 项目 Settings → Domains 添加该域名，再在 DNS 服务商填写 Vercel 为此项目给出的 CNAME 目标；不要修改根域名或现有其他子域名记录。
- 后续向 `main` 推送可由 Vercel Git 集成自动部署，Pull Request 可生成预览。GitHub Actions 自动运行测试与构建。

参考：[Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite)、[自定义域名](https://vercel.com/docs/domains/working-with-domains/add-a-domain)。
