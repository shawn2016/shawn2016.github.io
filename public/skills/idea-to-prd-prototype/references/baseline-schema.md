# 双基线状态与确认文件格式

## baseline.json

最终确认前将 `status` 保持为 `draft`，并将 `final_approved` 保持为 `false`。获得用户明确最终确认后再改为 `approved` 和 `true`。确认时间使用实际系统时间生成，不手工估算 Unix 时间戳。

```json
{
  "schema_version": "1.0",
  "project_name": "示例项目",
  "baseline_version": "v1.0",
  "status": "approved",
  "confirmed_by": "用户提供的姓名或称呼",
  "confirmed_at": "2026-11-10T18:00:00+08:00",
  "blocking_open_issues": 0,
  "core_flows_confirmed": true,
  "gates": {
    "direction_confirmed": true,
    "wireframe_reviewed": true,
    "prototype_approved": true,
    "final_approved": true
  },
  "artifacts": {
    "prd": "PRD.md",
    "prototype": "prototype.html",
    "acceptance_record": "08-acceptance-record.md"
  }
}
```

所有产物路径必须位于基线目录内。`blocking_open_issues` 只有在全部阻塞问题关闭后才能设为 0。非阻塞的待确认事项可以保留，但必须在 PRD 和确认记录中说明处理方式。

## state.json

`state.json` 用于中断恢复，不代替最终确认记录。建议结构：

```json
{
  "schema_version": "1.0",
  "project_name": "示例项目",
  "phase": "DISCOVERY",
  "gates": {
    "direction_confirmed": false,
    "wireframe_reviewed": false,
    "prototype_approved": false,
    "final_approved": false
  },
  "versions": {
    "prd": "draft",
    "wireframe": null,
    "prototype": null
  },
  "blocking_open_issues": [],
  "last_decision": null
}
```

每次阶段变化、用户反馈或返工后更新。恢复会话时先读取现有产物和该文件，不重复已经完成并确认的阶段。发生返工时将 `phase` 写为实际返回阶段，并重置受影响的当前及后续门禁；不得保留旧批准状态。

## 08-acceptance-record.md

至少包含：

```text
项目：
基线版本：v1.0
确认阶段：最终基线
确认人：
确认时间：
确认范围：
核心流程及体验结果：
用户明确接受的事项：
用户明确拒绝或延期的事项：
已接受风险：
非阻塞遗留事项：
未解决阻塞项：无
关联 PRD 及版本：
关联 HTML 原型及版本：
确认结论：通过 / 退回修改
```

只有用户明确表达最终确认后才能写「通过」。AI 不得代签、推断确认或将「继续」自动等同于最终批准。
