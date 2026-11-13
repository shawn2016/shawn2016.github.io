---
name: idea-to-prd-prototype
description: 将模糊产品 Idea 通过追问澄清、行业专家指导、PRD 草案与评审、低保真线框 HTML、完整可操作 HTML 和用户体验确认，转化为已验证的 PRD v1.0、HTML 原型 v1.0 和确认记录。This skill should be used when 用户提出新产品、网站、小程序或工具想法，要求从 idea 梳理需求、生成或评审 PRD、制作需求验证原型，或在正式设计和开发前确认产品范围与交互。双基线确认后立即停止，不用于视觉设计深化、技术方案、项目编码或直接上线。
agent_created: true
---

# Idea to PRD and validated prototype

## 目标

将用户对产品的模糊理解转化为可检查、可体验、可追溯的产品基线。通过文字澄清、专业指导和实际操作逐步暴露认知偏差，避免将未经验证的 PRD 直接交给 AI 开发。

将 PRD 作为业务规则、范围和验收依据，将 HTML 原型作为页面结构、流程和交互意图的验证依据。不要把 HTML 原型当作最终视觉设计稿或生产代码。

## 不可违反的边界

- 在用户完成对应阶段确认前，不得自动进入下一阶段。
- 不得替用户作出产品方向、MVP 范围、预算、优先级或风险取舍决定。
- 不得将假设写成事实；将未明确内容标为「待确认」。
- 不得声称已完成真实用户测试或真实专家评审。使用当前已启用的专家能力；未启用时，明确标记为「AI 角色化评审」。
- 不得把行业惯例包装成强制标准。区分硬约束、行业建议和个人偏好；涉及现行法规、平台规则或行业事实时先检索可靠来源并记录依据。
- 不得擅自增加页面、功能或需求，也不得重新引入用户已经否决的建议。
- 修改原型时必须同步修改受影响的 PRD、验收标准和追溯关系。
- 双基线确认后立即停止。将视觉设计深化、设计系统、技术方案、任务拆解、正式编码、测试实施和上线交给后续 Skill。
- 用户要求跳过原型或直接开发时，说明当前流程的完成条件并停留在当前门禁；可以提供建议，但不得伪装已完成确认。

## 按需加载资源

| 资源 | 加载时机 |
|---|---|
| `references/prd-template.md` | 创建 PRD 草案及生成最终 PRD 时 |
| `references/review-checklists.md` | 行业指导、PRD 评审、阶段确认和返工时 |
| `references/prototype-spec.md` | 创建或修改任何 HTML 原型、组织用户体验时 |
| `references/baseline-schema.md` | 初始化状态、保存确认记录及生成最终 baseline.json 时 |
| `scripts/validate_baseline.py` | 最终确认前预检及确认后验收时 |
| `scripts/test_validate_baseline.py` | 修改 Skill 后执行回归测试时 |

## 产物与状态

默认在当前项目根目录创建 `product-baseline/<project-name>/`。项目位置不明确时再询问，不要反复询问已有信息。发现已有产物时先读取并恢复状态，不要覆盖历史或从头重跑。

```text
product-baseline/<project-name>/
├── state.json
├── 01-discovery-brief.md
├── 02-expert-guidance.md
├── 03-prd-draft.md
├── 04-prd-review.md
├── 05-wireframe.html
├── 06-wireframe-feedback.md
├── 07-prototype.html
├── 08-acceptance-record.md
├── PRD.md
└── baseline.json
```

使用以下阶段状态，每次完成阶段或收到反馈后更新 `state.json`：

```text
DISCOVERY
EXPERT_GUIDANCE
DIRECTION_GATE
PRD_DRAFT
PRD_REVIEW
WIREFRAME
WIREFRAME_GATE
INTERACTIVE_PROTOTYPE
EXPERIENCE_VALIDATION
BASELINE_CHECK
APPROVED
```

在 `state.json` 中至少记录当前阶段、四个门禁状态、各产物版本、待解决阻塞项和最近决策。四个门禁为 `direction_confirmed`、`wireframe_reviewed`、`prototype_approved`、`final_approved`。只有获得明确用户确认后才能将对应门禁设为通过。

发生返工时，将受影响的当前及后续门禁重置为 `false`，将 `state.json` 的 `phase` 写为实际返回阶段。不得以旧 `state.json` 为准继续推进，也不得在返工期间保留旧的最终批准。

## 阶段一：澄清 Idea

采用高价值追问，不要机械执行固定问卷。优先覆盖：

1. 目标用户、核心问题、使用场景和产品价值。
2. 用户提出的方案与真正要解决的问题之间的关系。
3. MVP 初步范围、非目标、平台、资源及约束。
4. 核心任务、异常情况、成功指标和验收预期。

每轮只询问最影响后续方向的问题，通常不超过五项。提供选项或推荐默认值，允许回答「暂不确定」。信息足够时立即停止追问。初次交互，或用户要求一次做完、跳过步骤、直接开发时，先用不超过五行说明「需求澄清 → 行业指导 → PRD → 线框原型 → 可操作原型 → 双基线」及当前所在步骤；后续不要重复展示完整流程。

生成 `01-discovery-brief.md`，区分：

- 用户明确表达的事实和需求
- AI 推断但仍待验证的假设
- 初步 MVP 与非目标
- 已知约束
- 未决问题

此阶段只形成需求事实简报，不写 PRD。先用简短摘要请用户检查目标用户、核心问题、AI 推断和待验证假设是否准确；用户指出偏差时先修订简报。未完成这一核实前，不得将简报标为已核实或进入行业指导。该核实不代替门禁 A 的方向与取舍确认。

## 阶段二：进行行业与产品指导

加载 `references/review-checklists.md`。开始前明确说明本次由哪个已启用专家/专家团队完成；未启用专家时，明确说明将使用「AI 角色化行业/产品指导」。将需求简报交给当前已启用的适合专家；未启用专家时，以同一检查清单执行角色化指导，不得冒充真人或外部专家。

重点纠正问题定义、用户场景、业务规则、行业惯例、MVP 范围及前置风险。提供推荐方案、替代方案、代价和适用条件，不直接接管产品。

生成 `02-expert-guidance.md`，至少包括：

- 对问题定义的复述与诊断
- 可能存在的理解偏差及依据
- 硬约束、行业建议和可选偏好
- 推荐路径、替代路径及取舍
- MVP 调整建议
- 仍需验证的假设
- 需要用户决策的事项

### 门禁 A：方向与决策确认

向用户展示简短摘要，而不是要求阅读全部材料。使用提问工具集中确认：

- 问题定义是否准确
- 接受哪些专家建议
- 拒绝哪些建议及原因
- 第一版做什么、不做什么
- 哪些风险和假设被接受

将用户选择写回 `02-expert-guidance.md` 和 `state.json`。只有明确确认后才能进入 PRD 草案。若方向变化，返回 DISCOVERY 或 EXPERT_GUIDANCE，不继续沿用旧结论。

## 阶段三：生成并评审 PRD 草案

加载 `references/prd-template.md`，基于已确认简报和指导纪要生成 `03-prd-draft.md`。

遵守以下要求：

- 使用统一需求编号、验收编号、页面编号和决策编号。
- 为每项 P0 需求编写可测试的 Given/When/Then 验收标准。
- 明确主流程、分支、异常、权限和恢复路径。
- 将未明确内容标为「待确认」，不要自行补全。
- 将文档状态标为「草案」，不得提前标为 v1.0 已确认。

随后加载 `references/review-checklists.md`，组织产品、用户体验、技术及按需的数据/安全评审。先独立检查，再合并成一份 `04-prd-review.md`，去重并处理冲突。每条意见标明严重程度、依据、建议和是否需要用户决策。

只将业务目标、范围、预算、优先级和风险取舍交给用户。专业评审能够解决的问题不得反复追问用户。修订后仅复查受影响部分及关联一致性，不无限重开全文评审。

## 阶段四：生成低保真线框 HTML

加载 `references/prototype-spec.md`，根据评审后的 PRD 草案生成 `05-wireframe.html`。

采用单文件、黑白灰、幻灯片式流程导览，并支持主要按钮点击跳转和页面目录跳转。覆盖 PRD 中的核心页面、分支和关键状态。不要用长页面简单平铺所有屏幕，不要制作正式 UI。

使用 `present_files` 打开原型，引导用户实际检查页面和跳转关系。

### 门禁 B：线框流程检查

引导用户回答四类问题：页面是否缺失、流程顺序是否正确、点击目标是否符合预期、页面内容和操作是否符合理解。

将反馈写入 `06-wireframe-feedback.md`。对每项反馈标记接受、替代处理、延期或拒绝及原因，并同步修改 PRD 和线框原型。用户明确确认主流程可进入下一阶段后才能继续。

## 阶段五：生成完整可操作 HTML 原型

加载 `references/prototype-spec.md`，生成 `07-prototype.html`。使用接近真实场景的文案和模拟数据，实现核心导航、表单、状态切换、成功与失败反馈及异常恢复。

保持需求验证定位，不接真实后端，不引入生产项目架构，不开展品牌视觉或设计系统深化。

使用 `present_files` 打开原型，并给出三至五个核心任务，让用户通过实际操作验收，而不是询问「PRD 是否没问题」。

将每轮反馈同步写入 PRD、原型和 `08-acceptance-record.md`。仅重新体验受影响的任务；若改变产品方向或 P0 范围，返回对应早期阶段。核心任务通过且用户明确认可原型已符合需求时，将 `prototype_approved` 设为 `true`；这不等于最终双基线批准，`final_approved` 仍须保持 `false`。

## 阶段六：形成双基线

加载 `references/prd-template.md` 和 `references/baseline-schema.md`，生成最终 `PRD.md` 并完成：

- PRD 与原型需求追溯表
- 用户决策记录
- 反馈处理记录
- 非目标及延期事项
- 未决问题及阻塞级别
- 最终验收摘要

将 `baseline.json` 初始化为 `draft`，然后运行：

```bash
python3 <skill-directory>/scripts/validate_baseline.py <baseline-directory> --preflight
```

修复所有结构性错误。预检允许 `draft` 和 `final_approved=false`，但前三个门禁必须通过。警告必须逐项判断，不得为通过校验而删除真实待确认事项。

### 门禁 C：最终基线确认

向用户展示本期范围、非目标、核心流程、已接受风险、遗留事项及原型入口。获得明确最终确认后，才能：

1. 将 PRD 状态改为「已确认」并标记对应基线版本。
2. 将 `08-acceptance-record.md` 标记为已确认。
3. 将 `baseline.json` 改为 `approved`，填写确认人、确认时间、门禁及零阻塞状态。
4. 将 `state.json` 改为 `APPROVED`。
5. 再次运行校验脚本，确保最终文件有效。

最终交付 `PRD.md`、`prototype.html`（由 `07-prototype.html` 复制或重命名）、`08-acceptance-record.md` 和 `baseline.json`。交付后停止，不自动启动设计或开发 Skill。

## 局部返工规则

| 变化类型 | 返回位置 | 必须同步更新 |
|---|---|---|
| 问题定义或目标用户变化 | DISCOVERY | 简报、指导纪要、PRD、两类原型 |
| 行业、核心服务或合规风险等级变化 | DISCOVERY，澄清后进入 EXPERT_GUIDANCE | 简报、指导纪要、PRD、验收标准、追溯关系、风险记录及两类原型 |
| 专家建议或 MVP 取舍变化 | EXPERT_GUIDANCE | 决策记录、PRD、受影响原型 |
| 业务规则、权限或验收缺失 | PRD_DRAFT | PRD 评审及受影响原型 |
| 页面缺失或跳转错误 | WIREFRAME | PRD 页面流程、线框及追溯表 |
| 交互体验或文案不符合预期 | INTERACTIVE_PROTOTYPE | 原型、相关 PRD 和体验记录 |
| 仅涉及颜色、字体、组件视觉风格 | 不返工 | 记录给后续设计 Skill，不扩大当前范围 |

按实际影响判断是否构成方向变化，不以用户声称「核心目标不变」为准。重大方向变化时保留历史版本，将方向及所有受影响的下游门禁重置为 `false`，禁止沿用旧批准。

## Skill 自身验证

修改本 Skill 后依次执行：

1. 结构校验：使用 skill-creator 的 `quick_validate.py` 检查本目录。
2. 单元测试：`python3 scripts/test_validate_baseline.py`。
3. 产物预检：对尚未最终确认的基线目录运行 `python3 scripts/validate_baseline.py <baseline-directory> --preflight`。
4. 最终验收：对已确认基线目录运行 `python3 scripts/validate_baseline.py <baseline-directory>`。
5. 行为干跑：至少覆盖以下场景：
   - 用户要求「直接一次生成最终 PRD 和原型」时，Skill 从少量澄清问题开始。
   - 用户要求「全权代决策、跳过评审和原型、直接开发」时，Skill 不伪造确认、不跳门禁、不编码。
   - 线框阶段发生行业或核心服务重大变化时，Skill 返回 DISCOVERY/EXPERT_GUIDANCE，而不是只修改页面。
6. 真实项目端到端验证：用一个真实但低风险的小 Idea 完整走一遍，重点记录用户反馈是否确实改变了 PRD 和原型，以及三个用户门禁是否留有明确确认。

## 最终完成定义

只有同时满足以下条件才可声称完成：

- 三个用户确认门禁（方向、线框、最终基线）均有明确记录，四个状态标记均通过。
- 所有 P0 需求均有验收标准和原型追溯。
- 核心页面、分支及关键状态完整。
- 用户反馈均已处理、延期或明确拒绝并记录原因。
- 没有未解决的阻塞项。
- PRD、最终原型和确认记录版本一致。
- 最终校验脚本通过。
- 未开始视觉设计深化、技术设计或正式项目编码。
