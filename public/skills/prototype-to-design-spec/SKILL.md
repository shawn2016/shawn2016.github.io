---
name: prototype-to-design-spec
description: 在 PRD 与可操作 HTML 原型已通过双基线确认后，通过参考风格学习、锁定首页内容契约、首页 4-5 张独立构图的风格设计稿、用户选定、AI 角色化 UX 评审、设计规范抽取、其余 tab 设计稿生成与规范一致性回归，产出可版本化的设计规范（design-spec.md + design-tokens.json）与各 tab 高保真设计稿，形成设计基线。This skill should be used when 用户已确认产品需求与原型、要求定 UI 设计风格、生成多版首页视觉候选、抽取设计规范或设计系统、扩展其他 tab 设计稿，或在正式开发前沉淀可复用的设计规则。不用于需求澄清、PRD 修改、技术方案、生产编码或直接上线。
agent_created: true
---

# Prototype to Design Spec

## 目标

把已经验证过的需求基线，转化为**可复用、可判定、可版本化**的设计规范，以及受该规范约束的各页面设计稿。

明确区分两类产物：风格候选稿是**探索载体**（可被整体否决、可重做），设计规范与各 tab 设计稿是**正式交付资产**（长期约束后续所有页面与开发实现）。设计规范不得只是对选中稿的事后描述，必须能反过来判定「新页面是否合规」。

**核心红线：不改需求 ≠ 不改 DOM。** 原型是信息结构与交互的验证工具，不是视觉设计稿。风格候选稿必须重新设计视觉编排（布局、卡片拆分与合并、图标系统、图形与图表、插画、装饰语言、留白节奏）；「守住需求」靠内容契约，而不是靠复制原型的 HTML 结构。把原型 DOM 换个配色就当设计稿，属于本 Skill 的失败产物，必须重做。

本 Skill 承接 `idea-to-prd-prototype` 的双基线，不重开需求。视觉风格变化不构成需求返工，也不得改动 PRD 业务规则、页面清单、文案与交互结构。

## 输入与前置门禁 S0

开始前读取项目基线目录 `product-baseline/<project-name>/`，确认以下输入齐备：

- `PRD.md`（已确认）、`prototype.html`、`baseline.json`、`state.json`、`08-acceptance-record.md`
- `baseline.json` 已通过门禁 C：四个门禁 `direction_confirmed` / `wireframe_reviewed` / `prototype_approved` / `final_approved` 全为 `true`，`confirmed_at` 非空，且具备已批准证据。已批准证据接受两种真实写法：顶层 `status="approved"`，或 `gate_c.status="passed"`（第一个 Skill 的实际产物常用后者）。
- 从 PRD 页面清单与 `prototype.html` 提取并锁定**页面清单**（tab 名称、页面编号、每页核心元素），写入 `01-entry-check.md`

前置校验由 `validate_design_baseline.py` **直接读取真实的 `baseline.json`**，不接受 `design-state.json` 自述的批准状态；`design-state.json` 的 `source_baseline` 必须如实抄录 `confirmed_at` 与证据字段，时间不一致即判定失败。

前置不满足时停止，说明需要先回到第一个 Skill 完成需求确认；不得在需求未冻结时定风格。项目位置不明确时只问一次，不要反复询问已有信息。发现已有 `design/` 产物时先读取并恢复 `design-state.json`，不覆盖历史、不从头重跑。

生成 `01-entry-check.md`，记录：基线版本与确认时间、锁定的页面清单、本期设计范围、明确不做的范围、参考源清单、已知约束。**把 `baseline.json` 的 `open_items` 与 `deferred_suggestions` 原样抄入「已知约束」**：设计阶段不擅自关闭这些遗留项，尤其涉及合规留痕的条目不得在视觉稿中被违反或抹去。此清单是后续所有 tab 稿覆盖率的验收依据。

## 不可违反的边界

- 在用户完成对应阶段确认前，不得自动进入下一阶段。
- 不得替用户作出风格选择、产品方向、范围或优先级取舍。
- **不得修改 `PRD.md`、`prototype.html`、`baseline.json`、`state.json` 等需求基线文件。** 全部新产物写入 `design/` 子目录。
- **禁止把候选稿做成原型 DOM 的换色复制。** 风格设计稿必须独立重新构图；守住需求边界靠 `content_contract`：信息项、文案、数值、状态、操作语义、页面清单与 tab 不得增删或改写。允许改变呈现方式（分组、层级、图形、图表、图标、装饰），不允许改变信息本身。设计稿中不得出现原型评审道具（演示数据横幅、PRD/原型版本号、评审面板与说明角标）。
- 每个候选与原型首页在**视觉编排**上必须有可感知差异：至少重排 2 组信息结构（如指标呈现方式、待办形态、导航形态），并引入该方向独有的图形/图标语言。仅改色值、圆角、间距而不动构图，判定为不合格。
- 不得声称已完成真实用户测试、真实专家评审或真实市场调研。当前会话已启用 UI/UX 专家时写明专家名称；未启用时，评审文档标题与正文必须标注「AI 角色化 UI/UX 评审（未启用 UI/UX 专家，非真人或外部专家意见）」。
- 不得把行业惯例包装成强制标准。区分硬约束（可访问性、平台规范、已确认需求）、行业建议与个人偏好；每个 token 数值标注来源（参考取样测得 / 设计推导 / 用户指定），推导值标「推导」，不得编造「行业标准值」。
- **合规与原创红线**：第三方 UI 参考站（默认首选 UI Notes，https://uinotes.com/）的截图、图标、文案、品牌与配色方案仅用于风格特征学习。禁止复制截图原图、图标、界面文案、品牌元素到任何交付物；参考记录只写「来源链接 + 页面/条目标识 + 取样时间 + 风格特征文字描述 + 差异说明」。取样截图放入临时目录，不进入交付物。用户提供的内部材料不原文照搬。不使用绝对化用语与广告法违禁词。
- 不得重新引入用户已否决的风格、页面或建议。
- 交付后停止，不自动启动技术方案、任务拆解、正式编码或上线。

## 按需加载资源

| 资源 | 加载时机 |
|---|---|
| `references/reference-study.md` | S1 参考取样、补充样本、否决回路重找参考时 |
| `references/style-dimensions.md` | S2 生成候选稿、定义差异矩阵、S3 写基础层规范时 |
| `references/ux-review-checklist.md` | S3 组织 UI/UX 评审时 |
| `references/design-spec-template.md` | S3 首批规范、S5 规范扩展、S6 定版时 |
| `references/spec-regression.md` | S5 一致性回归、冲突变更评估、S2 否决回路时 |
| `references/state-schema.md` | 初始化状态、保存门禁、生成设计基线时 |
| `assets/candidate-shell.html` | S2 编写内容契约与设计稿骨架时（含「换肤」反面清单） |
| `assets/comparison-shell.html` | S2 生成并排对比页时 |
| `assets/design-tokens.schema.json` | 生成或修改 `design-tokens.json` 时 |
| `scripts/derive_designs.py` | S2 生成独立构图设计稿、并排对比页与内容契约校验；`--verify-only` 只做校验 |
| `references/stitch-workflow.md` | S2 用户要求用 Stitch 等外部 AI 平台生成高保真设计图时 |
| `scripts/validate_design_baseline.py` | 每次门禁前预检、最终确认后验收 |
| `scripts/test_validate_design_baseline.py` | 修改本 Skill 后执行回归测试 |

## 产物与状态

全部写入 `product-baseline/<project-name>/design/`：

```text
design/
├── design-state.json
├── design-baseline.json
├── 01-entry-check.md
├── 02-style-references.md
├── 03-spec-preview.md              （规范形态预览，未冻结；门禁 D 前可给用户看）
├── 03-style-candidates/
│   ├── candidates.json             （含 content_contract 内容契约 + 5 个方向的 meta/token）
│   ├── style-A.html / .png / .tokens.json   （4-5 组，各自独立构图）
│   ├── comparison.html
│   ├── contract-check.json         （内容契约逐稿校验结果）
│   └── _rejected-<round>-<reason>/ （被否决轮次归档，含否决说明）
├── 04-style-decision.md
├── 05-ux-review.md
├── 06-tab-designs/
│   ├── <page-id>.html / <page-id>.png
│   └── index.html
├── 07-spec-regression.md
├── 08-design-acceptance.md
├── design-spec.md
└── design-tokens.json
```

`design-spec.md` 与 `design-tokens.json` 为主交付资产；`06-tab-designs/` 为正式交付的页面设计稿，不是草稿。二者通过 `07-spec-regression.md` 绑定。

`design-state.json` 记录 `phase`、四个门禁状态、各产物版本、否决回路轮次、未解决阻塞项与最近决策。阶段状态：

```text
ENTRY_CHECK
REFERENCE_STUDY
STYLE_CANDIDATES
STYLE_GATE
BASE_SPEC
UX_REVIEW
TAB_DESIGNS
SPEC_REGRESSION
DESIGN_BASELINE
APPROVED
```

四个门禁为 `style_selected`、`base_spec_confirmed`、`tab_designs_accepted`、`design_baseline_approved`。只有获得明确用户确认后才能置为 `true`。返工时把受影响的当前及后续门禁重置为 `false`，`phase` 写为实际返回阶段，不得沿用旧批准。

## 阶段 S1：参考取样与风格学习

加载 `references/reference-study.md`。用浏览器打开参考站（用户需登录时先交还控制权，等用户确认后恢复同一任务空间，不新建空间），按 `01-entry-check.md` 锁定的产品类型挑选**同类真实产品**的界面样本，数量按参考规程下限执行。

输出 `02-style-references.md`，每条样本包含：来源链接、页面/条目标识、取样时间、界面类型、可观察的风格特征（配色关系、信息密度、圆角与描边、字阶与字重、图标语气、留白节奏、卡片与分隔方式）、可借鉴点与明确不借鉴点。只记录特征描述，不落地图。

归纳出 4-5 个**彼此差异可感知**的风格方向，每个方向写明一句话定位与在 `references/style-dimensions.md` 两轴上的取值差异，供 S2 使用。不得把「好看」「高级」这类不可判定词当作风格定义。

## 阶段 S2：首页 4-5 张风格设计稿

### S2.1 先锁内容契约，再动笔

加载 `references/style-dimensions.md` 与 `assets/candidate-shell.html`。从 `prototype.html` 首页与 PRD 提取**内容契约**写入 `candidates.json → content_contract`：页面标题、问候与日期、关键指标（值与标签）、待办项（标签与值）、快捷操作、空状态文案、主操作、底部 tab，以及**明确排除的原型评审道具清单**（演示横幅、版本号、评审面板、说明角标）。

内容契约是设计阶段唯一的需求边界。契约之外的构图全部自由；契约之内的信息一项都不能少、不能改写。

### S2.2 每个方向独立重新构图

生成 4-5 张**真正不同的首页设计图**，不是同一个 DOM 的换色版本。每个方向至少在以下维度重排 2 组以上信息结构：

| 维度 | 可变化的做法 |
|---|---|
| 头部 | 整块品牌色 head / 白底细标题栏 / 问候语作为主标题 / 大数值 hero |
| 指标 | 横排四列 / 2×2 图标卡 / 1 主指标 + 3 个 chip / 大数值 + 折线图 / 贴纸式标签 |
| 待办 | 紧凑列表 / 图标行 / 2×2 网格 / 竖条状态行 / 粗描边卡片 |
| 快捷入口 | 文字链 / 圆形图标宫格 / 胶囊组 / 描边按钮 / 厚底按钮 |
| 空状态 | 细线框 + 日历图形 / 插画卡 / 暗色虚线框 / 角色图形 |
| 底部导航 | 细线指示 / 图标 tab / 浮动胶囊 / 发光指示 / 色块选中 |
| 图形语言 | 自绘线性图标、迷你柱图/折线图、几何角色、光斑与装饰形状 |

所有图标、图形、插画必须自绘，不得复制参考站素材。

### S2.3 生成与校验

用 `scripts/derive_designs.py` 生成 `style-A..E.html`、`comparison.html` 与 `contract-check.json`；`--verify-only` 可对已有稿件单独复验。校验对象是**内容契约齐备**（必需文本、操作是否落在可点击元素、tab 是否在导航内、是否泄漏原型道具文案），不是 DOM 字节一致。

硬性要求：

- 5 张稿的 HTML 结构允许且应当不同；`contract-check.json` 必须零错误。
- 每个候选附一份 token 快照，值可机读，格式遵循 `assets/design-tokens.schema.json`；设计稿 CSS 引用这些 token，保证规范可反向约束。
- 用无头浏览器把每个稿的手机容器渲染为 PNG，用 `assets/comparison-shell.html` 生成并排对比页；用 `present_files` 打开对比页与全尺寸 PNG。
- 给每个候选写「适用场景 / 代价 / 已知风险」三行说明，不替用户排序或暗示唯一正确答案。
- 若用户想提前看规范形态，输出 `03-spec-preview.md`：四要素条款骨架 + 示例值 + 5 方向 token 对照，**醒目标注未冻结**，并写明正式规范须在门禁 D/E 后产生。
- **自检反问**：把 5 张图缩到并排大小，若看起来只是同一张图换了颜色，判定不合格，回到 S2.2 重做，不得进入门禁 D。

### S2.4 外部高保真通道（可选）

用户指定用 Stitch 等外部 AI 平台出图时，加载 `references/stitch-workflow.md`：把选定方向的艺术指导 + 内容契约转成结构化提示词生成整屏设计图，产物归档到 `design/04-stitch/`（brief + PNG + HTML），先按内容契约逐项自检再交用户。外部稿与自制稿同地位——都是候选稿，未经门禁 D 确认不得据此写规范。本机图像生成不足时优先走此通道，而不是用自制稿硬凑。

### S2.5 否决留痕

被整体否决的一轮移入 `_rejected-<round>-<reason>/`，附 `README.md` 写清否决原话、根因与处置；不得覆盖或删除历史。在 `design-state.json` 累计 `rejection_rounds` 并更新 `versions.candidates`。

### 门禁 D：风格选定

请用户明确选定一个方向，或指出全部不满意。记录 `04-style-decision.md`：选定项、选择理由、**每个未选项的否决理由**、保留的局部偏好（如「要 A 的配色但 B 的密度」）。

**否决回路**：全部不满意时，按 `references/spec-regression.md` 执行——把否决理由归到具体维度（配色 / 密度 / 圆角 / 字阶 / 组件语气），补取同类参考样本，回到 S1 与 S2 重出一组候选，并在 `design-state.json` 累计轮次。**收敛上限 3 轮**：第 3 轮仍不满意时停止生成，改为输出风格偏好澄清清单（逐维度给出可选值），请用户逐项指定后再生成最终一版；不得无限重出，也不得把用户 vague 反馈直接当作已选定。

只有明确选定后才能进入 S3。

## 阶段 S3：首批设计规范与 UX 评审

加载 `references/ux-review-checklist.md`，对选定稿组织 UI/UX 评审，输出 `05-ux-review.md`。评审覆盖视觉层级、信息密度、可读性、对比度与可访问性、状态完整性（空/错/载/边界）、操作成本、一致性、与原型需求的吻合度。每条意见标明等级、依据、建议、是否需要用户决策，并保留「AI 角色化」声明。专业问题自行收敛，只把取舍交给用户。

加载 `references/design-spec-template.md`，从选定稿抽取**基础层规范**，形成 `design-spec.md` v0.1 与 `design-tokens.json` v0.1。每条规范必须写成四要素：`规则 / 可判定条件 / 反例 / 适用范围`，例如「主色仅用于主操作与关键数值，禁止用于大面积背景」，并附可判定条件而非主观形容。基础层至少覆盖：色彩与语义色、中性色阶、字阶与字重、间距与栅格、圆角与描边、阴影与层级、图标语气、最小可点击区域与对比度下限。

### 门禁 E：首批规范确认

向用户展示规范摘要（不是全文），确认：token 值是否接受、可判定条件是否过严或过松、是否有需要保留的例外。确认后冻结 v0.1 作为后续 tab 的约束基线。未确认不得开始生成其他 tab。

## 阶段 S4：其余 tab 设计稿

按 `01-entry-check.md` 锁定的页面清单，逐个生成 `06-tab-designs/<page-id>.html` 与 PNG，并生成 `index.html` 总览。每个 tab 稿必须：

- 严格套用已冻结的 `design-tokens.json`，不引入新色值、新字号或新间距档位。
- 保持 PRD 与该页原型的结构、文案、状态与交互，不因视觉调整删减信息。
- 覆盖该页的空状态、加载态、错误态与长文本/超量数据边界。
- 遇到规范未覆盖的组件或状态时**先记录为规范缺口**，用现有 token 临时实现并在 `07-spec-regression.md` 登记，不得静默新增样式。

用 `present_files` 打开总览页，引导用户按页面检查，而不是询问「整体是否满意」。

## 阶段 S5：规范扩展与一致性回归

加载 `references/spec-regression.md`。把 S4 登记的缺口归纳为**组件与状态层规范**（导航、列表、表单、卡片、按钮、反馈、弹层、状态提示、图标用法），写入 `design-spec.md` 后续版本与 `design-tokens.json` 后续版本，每个版本写变更记录与影响范围。

随后对全部 tab 稿执行一致性回归：逐页逐条核对可判定条件，输出通过 / 不通过 / 不适用及依据。发现冲突时走变更评估表，明确二选一并留痕：**改稿**（规范正确、实现偏差）或**改规范**（规范确实不适用并说明适用边界）。禁止为通过回归而放宽判定条件或删除真实冲突。

生成 `07-spec-regression.md`：回归范围、逐条结果、冲突与裁决、规范版本演进、未解决缺口。

### 门禁 F：tab 稿与完整规范确认

向用户展示总览页、规范摘要与回归结果摘要，逐项确认：页面覆盖是否完整、各页视觉是否一致、缺口处理是否接受。用户明确认可后方可进入 S6。

## 阶段 S6：设计基线

加载 `references/state-schema.md`。生成 `08-design-acceptance.md`（用户决策记录、反馈处理、否决回路记录、遗留问题与阻塞级别、最终验收摘要），将 `design-baseline.json` 初始化为 `draft`，运行：

```bash
python3 <skill-directory>/scripts/validate_design_baseline.py <design-directory> --preflight
```

修复所有结构性错误。预检允许 `draft` 与 `design_baseline_approved=false`，但前三个门禁必须通过。警告逐项判断，不得为通过校验删除真实待确认事项。

### 门禁 G：设计基线最终确认

展示本期设计范围、选定风格、规范版本、各 tab 稿入口、已接受风险与遗留事项。获得明确最终确认后才能：

1. 将 `design-spec.md` 与 `design-tokens.json` 标为已确认版本并冻结。
2. 将 `08-design-acceptance.md` 标记为已确认。
3. 将 `design-baseline.json` 改为 `approved`，填写确认人、确认时间、四个门禁与零阻塞状态。
4. 将 `design-state.json` 改为 `APPROVED`。
5. 再次运行校验脚本，确保最终文件有效。

交付 `design-spec.md`、`design-tokens.json`、`06-tab-designs/` 全量设计稿、`08-design-acceptance.md` 与 `design-baseline.json`。交付后停止。

## 局部返工规则

| 变化类型 | 返回位置 | 必须同步更新 |
|---|---|---|
| 仅候选稿配色、密度、圆角不满意 | S1 / S2（计入否决回路） | 参考记录、候选稿、决策记录 |
| 候选稿被判定为「原型换肤 / 与原型同构」 | **S2.2 重做构图**（计入否决回路） | 内容契约、全部候选稿、否决归档、状态与轮次 |
| 选定风格后的局部偏好调整 | S3 | token、design-spec、已生成 tab 稿、回归记录 |
| 规范条款过严或出现不适用 | S5 | design-spec、token、受影响 tab 稿、回归记录 |
| 某 tab 稿信息缺失或状态不全 | S4 | 该页稿、总览、回归记录 |
| 新增/删除页面、改文案、改交互、改业务规则 | 停止本 Skill，回到 `idea-to-prd-prototype` | 需求基线由该 Skill 处理，本 Skill 不越界修改 |

按实际影响判断，不以用户声称「只是换个颜色」为准。风格方向重选时保留历史候选稿与决策记录，重置 `style_selected` 及所有下游门禁。

## Skill 自身验证

修改本 Skill 后依次执行：

1. 结构校验：用 skill-creator 的 `quick_validate.py` 检查本目录。
2. 单元测试：`python3 scripts/test_validate_design_baseline.py`。
3. 产物预检：对 `draft` 状态的设计目录运行 `validate_design_baseline.py --preflight`。
4. 最终验收：对已确认目录运行 `validate_design_baseline.py`。
5. 行为干跑，至少覆盖：
   - 需求基线未 `approved` 时，Skill 停在 S0 且不生成任何设计稿。
   - 用户拒绝全部 4-5 稿时，进入否决回路而非擅自选定；第 3 轮仍拒绝时转为偏好澄清清单。
   - 生成 tab 稿遇到规范未覆盖组件时，登记缺口而非静默新增样式。
   - 回归发现冲突时，明确「改稿 or 改规范」裁决并留痕，不放宽判定条件。
   - **候选稿不是原型 DOM 的换色复制**：把 5 张稿并排缩小后，构图、卡片形态、图形语言应明显不同；`contract-check.json` 零错误；若只有色值差异，判定失败。
   - 用户否决一轮设计稿时，旧稿归档并写明根因，重做后 `rejection_rounds` 递增，不覆盖历史。
6. 真实项目端到端验证：用已完成双基线的真实项目走一遍，重点记录用户风格反馈是否确实改变了 token 与规范、四个门禁是否留有明确确认、设计稿是否真的重新构图。

## 最终完成定义

只有同时满足以下条件才可声称完成：

- 四个用户确认门禁均有明确记录并全部通过。
- `design-spec.md` 每条规范具备规则、可判定条件、反例与适用范围；`design-tokens.json` 通过 schema 校验。
- 页面清单中的每个 tab 均有设计稿，且通过一致性回归，无未解决冲突。
- 否决回路、变更裁决、遗留问题均有记录，未解决阻塞项为零。
- 需求基线文件未被修改，PRD 与原型页面清单保持一致。
- 风格设计稿为独立重新构图，不是原型 DOM 换色；内容契约逐稿校验通过，无信息项丢失或改写。
- 第三方参考仅保留文字特征记录与来源，交付物内无第三方截图、图标、文案或品牌复刻；图标图形均为自绘。
- 最终校验脚本通过，且未开始技术方案或正式编码。

> 本 Skill 为设计流程参考，具体实施请结合公司合规与法务要求确认。
