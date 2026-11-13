# 状态与设计基线 Schema

所有 JSON 使用 UTF-8、2 空格缩进。字段值不得为占位符字符串（如 `TODO`、`待填`）；尚未产生的值用 `null` 或空数组，并同步写入 `open_questions`。

`source_baseline` 是对**项目根 `baseline.json`** 的如实抄录，不是自述。校验脚本会直接读取真实基线核对：四个门禁全为 `true`、`confirmed_at` 非空、具备已批准证据（顶层 `status="approved"` 或 `gate_c.status="passed"`，两者兼容），且 `source_baseline.confirmed_at` 必须与真实文件完全一致。`evidence` 写明实际命中的是哪种写法。

## 一、`design-state.json`

```json
{
  "schema_version": "1.0",
  "project": "string",
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD",
  "source_baseline": {
    "prd_version": "string",
    "prototype_version": "string",
    "approved": true,
    "confirmed_at": "2026-11-11T23:10:00+0800",
    "confirmed_by": "string",
    "evidence": "gate_c.status=passed + gates.final_approved=true"
  },
  "phase": "ENTRY_CHECK",
  "gates": {
    "style_selected": false,
    "base_spec_confirmed": false,
    "tab_designs_accepted": false,
    "design_baseline_approved": false
  },
  "versions": {
    "candidates": "r1",
    "design_spec": null,
    "design_tokens": null,
    "tab_designs": null
  },
  "selected_style": null,
  "rejection_rounds": 0,
  "pages": [
    { "id": "home", "name": "首页", "file": "06-tab-designs/home.html", "status": "pending" }
  ],
  "unresolved_conflicts": 0,
  "blocking_issues": [],
  "open_questions": [],
  "last_decision": null
}
```

### phase 枚举

`ENTRY_CHECK` / `REFERENCE_STUDY` / `STYLE_CANDIDATES` / `STYLE_GATE` / `BASE_SPEC` / `UX_REVIEW` / `TAB_DESIGNS` / `SPEC_REGRESSION` / `DESIGN_BASELINE` / `APPROVED`

### 门禁与阶段的对应关系

| 门禁 | 通过后的最小 phase | 前置条件 |
|---|---|---|
| `style_selected` | `BASE_SPEC` | 候选稿 4–5 组、`04-style-decision.md` 有选定项与未选项否决理由 |
| `base_spec_confirmed` | `TAB_DESIGNS` | `design-spec.md` 与 `design-tokens.json` 存在且版本非 null，`05-ux-review.md` 完成 |
| `tab_designs_accepted` | `DESIGN_BASELINE` | 每个 `pages[].file` 存在，`unresolved_conflicts` 为 0，`07-spec-regression.md` 有结论 |
| `design_baseline_approved` | `APPROVED` | 前三项均为 true、`blocking_issues` 为空、`design-baseline.json` 为 `approved` |

门禁只能按表顺序推进；返工时把目标门禁及其后所有门禁重置为 `false`，`phase` 写为实际返回阶段，`last_decision` 记录返工原因。

## 二、`design-baseline.json`

```json
{
  "schema_version": "1.0",
  "project": "string",
  "status": "draft",
  "design_baseline_approved": false,
  "confirmed_by": null,
  "confirmed_at": null,
  "source_baseline": {
    "prd_version": "string",
    "prototype_version": "string"
  },
  "gates": {
    "style_selected": true,
    "base_spec_confirmed": true,
    "tab_designs_accepted": true,
    "design_baseline_approved": false
  },
  "selected_style": "string",
  "versions": {
    "design_spec": "v0.2",
    "design_tokens": "v0.2",
    "tab_designs": "v1.0"
  },
  "artifacts": {
    "design_spec": "design-spec.md",
    "design_tokens": "design-tokens.json",
    "tab_designs": "06-tab-designs/",
    "acceptance": "08-design-acceptance.md"
  },
  "reference_sources": [
    { "url": "string", "sampled_at": "YYYY-MM-DD", "note": "仅风格特征学习，未复制素材" }
  ],
  "rejection_rounds": 0,
  "accepted_risks": [],
  "deferred": [],
  "blocking_issues": []
}
```

`status` 仅允许 `draft` 或 `approved`。`approved` 时必须有 `confirmed_by`、`confirmed_at`、四个门禁全为 `true`、`blocking_issues` 为空。

## 三、`design-tokens.json`

字段结构见 `assets/design-tokens.schema.json`。要点：

- 顶层必须含 `schema_version`、`version`、`source`、`colors`、`neutrals`、`typography`、`spacing`、`radius`、`elevation`、`iconography`
- 所有色值为 `#RRGGBB` 或 `#RRGGBBAA` 格式；间距与字号为数字（单位在 `units` 字段统一声明）
- 每个命名空间带 `source` 标注（`observed` / `derived` / `user_specified`），`derived` 值必须在 `design-spec.md` 中标注「推导」
- 不得出现规范文档未记录的孤立变量

## 四、校验对照

`scripts/validate_design_baseline.py` 按本文件执行：

| 校验项 | `--preflight` | 最终验收 |
|---|---|---|
| 必需文件齐备 | 是 | 是 |
| 真实 `baseline.json` 已批准且与 `source_baseline` 一致 | 是 | 是 |
| 候选稿数量 4–5 | 是 | 是 |
| 页面清单覆盖 | 否（允许进行中） | 是 |
| 前三个门禁为 true | 是 | 是 |
| `unresolved_conflicts` 为 0 | 否 | 是 |
| `blocking_issues` 为空 | 否 | 是 |
| 四个门禁全 true 且 `status=approved` | 否（允许 draft） | 是 |
| tokens 通过 schema 校验 | 是 | 是 |

预检失败时按错误码修复产物，不得修改校验脚本以绕过。
