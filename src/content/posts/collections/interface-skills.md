---
title: 让 Agent 做界面：把「好不好看」换成「凭什么算问题」
published: 2026-11-25
draft: false
description: 一个 Markdown 仓库拿下 1.2 万星，装的不是设计知识，是两条边界：什么算问题、什么动作不许自己跑。拆开 16 个 SKILL.md 的分流规则，附安装到日常的完整步骤、按场景对号入座的清单、同类方案判据对比
tags: [开源, 工具, AI, agent, 设计, 方法论]
category: 收藏
sourceLink: https://github.com/jakubkrehel/skills
---

先说一个场景。

你把一张页面截图丢给 coding agent，说「这里看着不太对，改一下」。它很配合，回你一段自信的分析：间距略紧、层次不够、建议加个阴影。你让它动手，它把圆角、颜色、动效一起改了。等你回头看 diff，说不清哪一条是必须改的，哪一条只是它的口味。想反驳也无从下手，因为「略紧」没有数值，「层次不够」没有出处。

多数人把这个结果归因于模型不懂设计，于是去补更多设计知识、写更长的提示词。但卡住验收的不是知识量。「好不好看」是形容词，形容词不能当判据；一份能进 code review 的意见，得能指出具体文件、具体行、具体违反了哪条规则，以及改完怎么验证。

这篇想把判断往前挪一步：**给 agent 补界面能力，稀缺的不是设计知识，是两条边界——什么算问题，以及什么动作不许它自己跑**。前一条把口味挡在报告之外，后一条把副作用留在人手里。

[jakubkrehel/skills](https://github.com/jakubkrehel/skills) 是一个把这两条边界写得很清楚的样本。2026 年 7 月 10 日建库，11 月 24 日实测 12,651 star、494 fork、1 个 open issue，MIT 协议，语言统计只有 Markdown，322,408 字节，仓库体积 882 KB。没有构建、没有 lint、没有测试，全部内容就是 16 个目录里的 `SKILL.md` 和它们旁边 40 多个专题文档。

## 一、它到底装了什么

一句话：`npx skills add jakubkrehel/skills`。skill 是 agent 能按需加载的说明文件夹，入口是 `SKILL.md`，frontmatter 里的 `name` 和 `description` 决定什么时候被想起来，正文在命中时才读进上下文。

这个仓库的 16 个 `SKILL.md` 一共 1905 行，分成两类。仓库的 `AGENTS.md` 自己给了命名：**domain skill 装知识**（什么是对的，比如排版、颜色、布局），**verb skill 装过程**（做什么动作，比如审查这个改动、把这个组件的所有状态铺开）。

七个 `better-*` 是知识：accessibility、layout、writing、typography、colors、ui、motion。`better-interface` 不装知识，只做编排——把界面路由给这七个，收齐证据，合并成一份排序后的报告。剩下八个是动作：`interface-review` 审一次改动，`explain-interface` 解释别人怎么做的，`break`、`state-machine`、`variant` 各自在临时页面上摆组件，`build-design` 按 Figma 建 UI，`afk` 趁你离开时做事，`upskill` 回头翻你的历史会话找该补的工具。

每个 `SKILL.md` 的结构是固定的，这套结构比内容更值得抄。frontmatter 之后是一个纯名字的 H1、两句说明「这是什么、它做什么」，然后是一到两行**校准句**，专门交代按多重的力气压：哪些数值是精确的、什么算 finding 而什么只是偏好、什么时候正确做法是「什么都不写」。再后面是标题本身就带观点的小标题（用 `Native elements first`，不用 `Semantics`）、指向兄弟 skill 的交接行、一张 `Before you finish` 表（左列是错误模式，不是原则复述），以及 domain skill 必备的 `Reporting` 段落。

深度内容不塞进入口文件。`better-motion` 的 `SKILL.md` 只写原则，把 enters/exits、drag、shared layout、性能这些配方放进同目录的 `enter-exit.md`、`drag.md`、`layout-animation.md`、`performance.md`，从需要它的那条原则处链接过去。规范和 `AGENTS.md` 都要求：原则陈述规则并链到配方，不在入口里缩写一遍，参考文件也不把原则扩写一遍。

## 二、第一条边界：什么算问题

`better-interface` 开篇的标题就叫 `Evidence, not taste`。它给的界线很硬：升级触发器是失败，无论风格指南怎么写；你只是不认同的密度、圆角、语气，不是 finding。上报的门槛是证据，`Approve` 的门槛是你确实检查了你声称检查过的东西。

具体落到三条可执行规则。

**每条 finding 必须带 `path/to/file:line` 和当前实现。** 源码推不出视觉结论时，得去看渲染结果并写下确切命令和观察结果；跑不了的检查标 `Not verified`，不写成 finding。`better-colors` 更直接：没量过的对比度不许报，能算出来的颜色不许估。

**判定用可证伪的数值，不用形容词。** `better-motion` 写明按压缩比例 `0.96` 不是 `0.95`；`better-ui` 写明嵌套圆角等于内层圆角加 padding 加边框宽度，并说这些值是精确值不是范围；`better-typography` 把「18px 以下用 400 或更重」「60–75 字符行宽」「iOS 输入框 16px」列为 finding，而字距、搭配、比例只是启发式。`better-accessibility` 要求每条 finding 引用 WCAG 2.2 A 或 AA 的准则编号，AAA、APG 惯例、44px 这类启发式永远不能标 `HIGH`。

**刻意的项目约定不算缺陷。** 七份 domain skill 几乎都写了一句同样的意思：项目已有且一致的约定是偏好，不是 finding；同一个细节在项目里做了两种，才是 finding。`better-layout` 说那些数值只在项目没有 spacing scale 或密度系统时才适用，有就用项目的 token。

报告格式也收口。`review-format.md` 规定一张按严重度排序的表，字段是 Severity / Domain / Location / Before / After / Why，最多 15 条，一个根因一行并列出全部位置；结论只有 `Block` 和 `Approve` 两种。13 条升级触发器（无可读名称的控件、无可见焦点、320px 或 200% 缩放下不可达、忽略 `prefers-reduced-motion` 等）一经确认直接 `HIGH`，且**不受 15 条上限约束**——报告可以缩短，但不能因为缩短而漏掉阻断项。

修法也排了序：删 → 用平台原生 → 复用项目已有的 token → 改数值 → 新增。一个本可以删掉的分隔线被写成了新代码，本身就是一条 finding，`After` 写的是删除。

这套东西的成立条件很明确：项目里已经有设计系统、token 或组件库，你要的是能进 review 的改动。反过来，从零起一个新界面、要的是灵感发散、或者项目自己就没有一套约定，它给的数值只是起点，不构成判据。

## 三、第二条边界：什么动作不许自己跑

16 个 skill 里，7 个的 frontmatter 带着 `disable-model-invocation: true`：`interface-review`、`variant`、`break`、`state-machine`、`explain-interface`、`afk`、`upskill`。README 里标成 `User-invoked`。它们只能由人打斜杠命令触发，模型不能自作主张启动。

这不是随手分的。`AGENTS.md` 用一整节逐条写了理由，每条都指向副作用：

- `variant`、`break`、`state-machine` 会在项目里写一次性页面。agent 要是每碰一个组件就起一个，仓库会被没人删掉的测试页铺满。
- `afk` 无人值守跑几小时并且会 commit。只有要离开的人知道什么时候该起。
- `upskill` 要读你在这个项目上的全部历史会话，里面有贴进去的密钥和没发布的东西。什么时候打开，只能本人决定。
- `explain-interface` 研究别人的站点，粘个链接不等于请求分析它。
- `interface-review` 审的是一次改动，范围必须来自人给的 PR 号或分支，猜出来的 diff 没人能核对。

配套的还有一条纪律：user-invoked skill 可以调用 model-invoked skill，但**永远不能调用另一个 user-invoked skill**。`better-interface` 想审改动时不能自己拉起 `interface-review`，只能请你去跑。把 `better-interface` 也设成手动会切断这条向上的交接，逼着 `interface-review` 把严重度、上限、格式和结论重抄一遍。

还有个容易漏的实现细节：`disable-model-invocation: true` 是 Claude Code 那半边的开关，每个这类 skill 的 `agents/openai.yaml` 里还写着 `policy.allow_implicit_invocation: false`，是 Codex 那半边。`AGENTS.md` 要求两者必须成对设置，否则同一个 skill 在不同 harness 里行为不一样。我核对了 `skills/break/agents/openai.yaml`，确实如此。

这套分流的价值在于：**可自动的是判断，不可自动的是副作用**。读代码、量数值、合并报告可以交给模型；写临时文件、改代码、跑几个小时、翻全部历史，得有人按一下。

## 四、从零跑通：安装到日常

按使用顺序走一遍，每步都能照做。

**第一步，装。** 需要 Node.js 22.20 以上，npx 不用预装。`skills` CLI 是 Vercel Labs 出的开源安装器，会检测机器上装了哪些 agent 并问你装到哪几个：

```bash
npx skills add jakubkrehel/skills
```

项目级安装会把一份文件写进 `.agents/skills/`，再软链到 `.claude/skills/`，并生成 `skills-lock.json` 记录来源和文件哈希。想全局可用加 `-g`，只给某个 agent 加 `-a claude-code`（也有 `codex`、`cursor`、`opencode`），不想被问就加 `-y`，Windows 或不支持软链的仓库用 `--copy`。先看不装用 `npx skills add jakubkrehel/skills --list`。装完用 `npx skills list` 核对，更新用 `npx skills update`，移除用 `npx skills remove`。CLI 默认收集匿名用量数据，`DISABLE_TELEMETRY=1` 可关。

**第二步，认另一条安装路径。** 同一仓库还带一个 Claude Code 插件市场，`.claude-plugin/plugin.json` 里插件名 `interfaces`，当前版本 `1.23.0`。插件用户调用时要带命名空间 `/interfaces:better-interface`，CLI 用户直接 `/better-interface`。`AGENTS.md` 特别提醒：改 `skills/` 下任何内容都必须在同一个 commit 里 bump `plugin.json` 的 version，`claude plugin update` 只比这个数字，漏了会报「已是最新」而永远送不到插件用户手上。两条路径别混用同一个 agent，插件自己会更新，CLI 装的是你要手动更新的可编辑副本。

**第三步，重启 agent 会话。** 多数 harness 在会话启动时读 skills，装完不重启会在斜杠菜单里找不到。

**第四步，跑一次不改代码的审查。** 最稳的起点是 `better-interface`，它默认只读：

```
/better-interface review the checkout flow
```

它会先声明解析出的范围，侦察项目的框架、样式系统、组件库和 token，读 `CONTRIBUTING.md`、`AGENTS.md`、设计系统文档，再按固定顺序加载七个 domain skill：accessibility → layout → writing → typography → colors → ui → motion。顺序不是随意的，基础失败不能被打磨层的意见盖住。某个 skill 不可用时它标 `Not reviewed` 并说明，不凭记忆补规则、不拿邻居顶替、不宣称全覆盖。

**第五步，审一次改动用另一个命令。** 分支、PR 或工作区未提交的改动属于 `interface-review`，它是手动的：

```
/interface-review pr 482
```

不带参数时它按固定顺序解析范围：`HEAD` 领先于 merge base 就审这段区间加上未提交改动；工作区脏就审未提交改动；都没有就列出事实并请你选，不会自作主张退回 `HEAD~1..HEAD`。它排除 lockfile、快照、生成物和二进制，把改动文件展开到受影响的界面，读 diff 的 `-` 侧找回归，然后给每条 finding 标 `Introduced`、`Regression` 或 `Pre-existing`，再把报告交给 `better-interface` 定严重度和结论。整个过程不改工作区：`gh pr checkout`、`git switch`、`git stash` 都明令禁止，只允许 `git fetch`。

## 五、按场景对号入座

用户问「什么场景下用」，最省事的答法是按你要的动作分类，而不是背 16 个名字。

| 你手上的事 | 用哪个 | 命令长什么样 | 它交回什么 |
|---|---|---|---|
| 想整体体检一个页面或流程 | `better-interface` | `/better-interface review the checkout flow` | 一份跨七领域、最多 15 条、带 `Block`/`Approve` 的报告 |
| 提了 PR，想知道有没有把界面改坏 | `interface-review` | `/interface-review pr 482` | 带 `Status` 列和 pre-existing 段的改动范围报告 |
| 只关心某一类问题 | 对应 `better-*` | `/better-colors`、`/better-accessibility` | 该领域独立的 severity ladder 与报告 |
| 想知道别人那个效果怎么做的 | `explain-interface` | `/explain-interface how is the copy page animation on interfaces.dev built?` | 逐层拆解，不评判好坏 |
| 从 Figma 或设计图还原 UI | `build-design` | `/build-design` 后给 Figma 链接 | 用项目现有 token 建好，附逐项比对表 |
| 想在一个组件上试几种方向 | `variant` | `/variant` 后指明组件 | 三个变体挂在真实页面上、带 picker，只给取舍不排名 |
| 想把一个组件的所有状态铺开慢慢改 | `state-machine` | `/state-machine` 后指明组件 | 临时页面 + mock 数据 + 切换器，改完一句话删掉 |
| 想看极端内容会不会把它撑破 | `break` | `/break` 后指明组件 | 一页列出所有场景，标出哪儿断了，不改代码 |
| 离开几小时，想让它自己找改进 | `afk` | `/afk look into assets for the skills page` | 新分支 `afk/<date>` 上的本地提交 + 两分钟能读完的报告 |
| 想知道该给项目补什么工具 | `upskill` | `/upskill` | 按「省下多少时间」排序的 skill / hook / 自动化提案 |
| 写提示词时顺手带上判据 | 模型自动 | 直接描述任务 | 匹配的 domain skill 被自动加载 |

作者自己的网站给了几个具体例子，比功能列表更能说明边界：`/explain-interface` 那个案例把「Copy Page」按钮的图标交换拆到了 `AnimatePresence` 的 `popLayout` 模式、`bounce: 0` 且 `300ms` 的 spring、`initial={false}` 防止首帧动画；`/break` 的案例把同一张问题卡片喂进 60 字符不换行标题、超长编号、空描述、`12,840` 这种大数字，看哪里溢出；`/interface-review` 的示例输出是「点击区域过小 / `text-wrap: pretty` / 对比度不达 WCAG AA / 圆角不共心」四条带序号的意见。

要挑一个最不容易踩坑的起步组合：`better-interface` 看现状，`interface-review` 卡 PR，`break` 验极端内容。三个都不主动改你的代码。

## 六、进阶：让它反过来改进你的工作流

`upskill` 值得单独说，因为它把「该补什么」也变成了有证据的判断。它读两样东西：你在某项目上写给 agent 的每一条 prompt，以及项目自己留下的记录（commits、PR、CI 运行、文件现状）。前者会被 harness 删掉，后者不过期；历史不够时报告要说明哪些计数来自记录。

它的提案顺序是一架梯子，从最轻的机制开始：能让机器判定的先写会失败的检查 → 某个时刻反复犯的错用 hook → 固定输入的杂活用脚本或 dev-only 页 → 没有机械判定的约定写进 agent 文档 → 需要人分步骤口述的过程才做成 skill → 该无人触发的才用 subagent 或定时任务。一条已经写下来却仍被反复违反的规则，要往梯子上挪一级，再抄一遍没用。

每条提案都得带计数：来自历史的是 prompt 次数和天数，来自记录的是 commit / PR / CI 次数和日期，还要带上「当初恢复它花了什么」。只出现两次的需求会明确写出来，免得为它造一个工具。隐私处理也写死了：工作文件放 `.upskill/` 并加进 `.git/info/exclude`，写文件时先把密钥和邮箱替换成标记，不引用客户原话，历史不发给外部服务。

`afk` 是另一个方向的极端。它要求一次跑几小时，广撒网再深入，改动逐条 commit 到 `afk/<date>` 分支，笔记写在 `.afk/<date>.md` 且不进提交；连接的服务一律只读；不 push、不合并、不部署、不发消息，除非这次明确要求。它甚至要求「出发前把每个要用的工具先跑一遍」，因为凌晨三点没人能回一个权限确认。

## 七、同类方案对比

按判据维度看，不按功能打分。

| 方案 | 判据从哪来 | 谁决定触发 | 冲突时谁让步 | 换 agent 的代价 | 什么场景不成立 |
|---|---|---|---|---|---|
| 在提示词里写「注意设计细节」 | 模型自己的口味 | 每次由人重说 | 无裁定规则 | 低，但每次都要重写 | 几乎都需要可验收结论时 |
| 项目里的 `AGENTS.md` / 设计规范文档 | 团队已写下的约定 | agent 始终读 | 文档与临时判断混在一起 | 中，格式绑在单个仓库 | 没有约定、或约定互相矛盾 |
| 组件库 + 设计 token | 代码里已存在的值 | 编译与调用时 | 编译结果说了算 | 高，与栈绑定 | 要判断「为什么这样不好」时 |
| 自动化检查（lint、axe、Lighthouse） | 可执行规则 | CI 自动 | 规则说了算，但覆盖不到视觉判断 | 中，要接进流水线 | 需要解释取舍、生成候选时 |
| `jakubkrehel/skills` | Markdown 里的原则 + 精确阈值 | 判断可自动，副作用必须手动 | 证据压过口味，项目约定压过默认值 | 低，纯文本、随 agent 目录走 | 项目没有设计系统，或要的是灵感 |

按成立条件给一份选型清单：

- 项目有 token、组件库和一致约定 → 这类 skill 最值钱，因为它把「偏离约定」变成可引用的 finding。
- 你要的是能进 PR review 的结论 → 坚持要求每条带 `file:line`、`Before`/`After` 和 `Block`/`Approve`；只要形容词的方案别进流程。
- 你打算让 agent 常驻无人值守 → 先划清哪些动作必须手动，再看它有没有写临时文件、改代码、读历史。
- 你的团队跨多个 agent → 选纯文本、跟 agent 目录走的载体，别把判据绑在某个 IDE 插件里。
- 你在做全新产品、还没有设计系统 → 先建约定，别指望一份通用 skill 替你决定品牌语气。

## 八、代价，写在前面

第一，口径要看清。skills.sh 页面显示 24 个 skill、437.9K 总安装量，而仓库当前 `skills/` 下只有 16 个目录。安装站按历史发布过的名字统计（里面还有 `teardown`、`away`、`great-interfaces` 这些已不在主分支的条目），别把 24 当成你现在能装到的数量。`better-motion` 是 11 月 19 日才通过 PR #68 合进来的，安装量 1.8K，而 `better-ui` 已有 51.5K；同一个合集里，成熟度差了一个数量级。

第二，强依赖项目已有的设计系统。`AGENTS.md` 和每份 domain skill 都写明：项目有 spacing scale 就用项目的，没有才用那些默认值。一个没有 token、样式各写各的仓库，得到的会是一堆「建议引入某值」，而不是「这里违反了某条」。

第三，插件路径有更新陷阱。改了 skill 却没 bump `plugin.json` 的 version，插件用户会一直停在旧版。`AGENTS.md` 要求改完跑 `claude plugin validate .` 和 `claude plugin validate .claude-plugin/plugin.json`。

第四，`build-design` 要 Figma MCP 才能读到精确值。截图只能按比例估，skill 要求你先声明假设的缩放比例，并主动找 Figma 链接；没连工具时它宁可停下来问，也不凭记忆建。

第五，`upskill` 会读你的全部历史会话。仓库自己把它列进手动触发、并写了脱敏规则，但决定权仍在你：什么时候让 agent 打开这份记录，只有你能判断。

## 收尾

回到开头那张截图。让 agent 做界面，真正卡住验收的是两件事：一份意见凭什么算问题，以及它凭什么自己动手。这个仓库把前者写成可引用的证据规则，把后者收进 7 个必须人按的开关；中间那层「谁可以调用谁」的约束，才是它比一份漂亮设计规范更难抄的部分。

把仓库名换掉，这两问依然成立：**凡是 agent 要给出的判断，先问它能不能被证伪；凡是 agent 要发起的动作，先问副作用有没有留在人手里**。能同时答上来的工具，才配进你的日常流程。

相关链接：

- 仓库：https://github.com/jakubkrehel/skills
- 安装页（含各 skill 安装量）：https://skills.sh/jakubkrehel/skills
- 作者示例页：https://jakub.kr/skills
- 设计工程杂志：https://interfaces.dev/
