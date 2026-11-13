#!/usr/bin/env python3
"""Validate the final PRD and HTML prototype baseline with Python stdlib only."""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_PRD_SECTIONS = [
    "## 1. 文档信息",
    "## 2. 项目背景与问题定义",
    "## 3. 产品目标、成功指标与非目标",
    "## 4. 用户、场景与权限",
    "## 5. 版本范围与优先级",
    "## 6. 产品结构与核心流程",
    "## 7. 功能需求详述",
    "## 8. 数据与权限要求",
    "## 9. 非功能要求",
    "## 10. 依赖、风险与待验证假设",
    "## 11. PRD 与原型追溯关系",
    "## 12. 决策记录与最终确认",
]

REQUIRED_GATES = [
    "direction_confirmed",
    "wireframe_reviewed",
    "prototype_approved",
    "final_approved",
]


def validate_baseline(directory, preflight=False):
    root = Path(directory).expanduser().resolve()
    errors = []
    warnings = []
    stats = {"requirements": 0, "acceptance_criteria": 0, "mode": "preflight" if preflight else "final"}

    def error(message):
        errors.append(message)

    def warn(message):
        warnings.append(message)

    if not root.is_dir():
        return {"valid": False, "errors": [f"目录不存在：{root}"], "warnings": [], "stats": stats}

    baseline_path = root / "baseline.json"
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        error("缺少 baseline.json")
        baseline = {}
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        error(f"baseline.json 无法解析：{exc}")
        baseline = {}

    if baseline.get("schema_version") != "1.0":
        error("baseline.json 的 schema_version 必须为 1.0")
    if not baseline.get("project_name"):
        error("baseline.json 缺少 project_name")
    status = baseline.get("status")
    if preflight:
        if status not in {"draft", "approved"}:
            error("预检时 baseline.json 的 status 必须为 draft 或 approved")
    elif status != "approved":
        error("最终校验时 baseline.json 的 status 必须为 approved；草案不能作为最终基线")
    if not baseline.get("baseline_version"):
        error("baseline.json 缺少 baseline_version")
    if not preflight:
        if not baseline.get("confirmed_by"):
            error("baseline.json 缺少 confirmed_by，不能代替用户确认")
        if not baseline.get("confirmed_at"):
            error("baseline.json 缺少 confirmed_at")
    if baseline.get("blocking_open_issues") != 0:
        error("基线预检和最终校验都要求 blocking_open_issues 为 0")
    if baseline.get("core_flows_confirmed") is not True:
        error("core_flows_confirmed 必须为 true")

    gates = baseline.get("gates")
    if not isinstance(gates, dict):
        error("baseline.json 缺少 gates 对象")
        gates = {}
    required_gates = REQUIRED_GATES[:-1] if preflight else REQUIRED_GATES
    for gate in required_gates:
        if gates.get(gate) is not True:
            error(f"用户门禁未通过：{gate}")

    artifacts = baseline.get("artifacts") if isinstance(baseline.get("artifacts"), dict) else {}
    prd_name = artifacts.get("prd", "PRD.md")
    prototype_name = artifacts.get("prototype", "prototype.html")
    acceptance_name = artifacts.get("acceptance_record", "08-acceptance-record.md")

    for label, name in [("PRD", prd_name), ("HTML 原型", prototype_name), ("确认记录", acceptance_name)]:
        if Path(name).is_absolute() or ".." in Path(name).parts:
            error(f"{label} 路径必须位于基线目录内：{name}")

    def read_artifact(name, label):
        path = root / name
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            error(f"缺少{label}：{name}")
        except UnicodeDecodeError:
            error(f"{label} 不是有效 UTF-8 文件：{name}")
        return ""

    prd = read_artifact(prd_name, "PRD") if prd_name else ""
    html = read_artifact(prototype_name, "HTML 原型") if prototype_name else ""
    acceptance = read_artifact(acceptance_name, "确认记录") if acceptance_name else ""

    for section in REQUIRED_PRD_SECTIONS:
        if section not in prd:
            error(f"PRD 缺少规范章节：{section}")

    if prd:
        if not preflight and "已确认" not in prd:
            error("最终 PRD 文档状态必须包含「已确认」")
        version = baseline.get("baseline_version", "")
        if version and version not in prd:
            error("PRD 未标注与 baseline.json 一致的基线版本")
        if "<填写>" in prd or "<产品名称>" in prd:
            error("PRD 仍包含未替换的模板占位符")
        if "待确认" in prd:
            warn("PRD 仍含「待确认」；须确认这些事项均已评估为非阻塞并记录处理方式")

    req_matches = list(re.finditer(r"^###\s+(REQ-[A-Z0-9-]+-\d{3})\b.*$", prd, re.MULTILINE))
    stats["requirements"] = len(req_matches)
    if not req_matches:
        error("PRD 未包含格式为 ### REQ-<MODULE>-001 的功能需求详述")

    for index, match in enumerate(req_matches):
        start = match.start()
        end = req_matches[index + 1].start() if index + 1 < len(req_matches) else len(prd)
        next_section = re.search(r"^##\s+(?:8|9|10|11|12)\.", prd[start:end], re.MULTILINE)
        if next_section:
            end = start + next_section.start()
        block = prd[start:end]
        req_id = match.group(1)
        if not re.search(r"\bAC-[A-Z0-9-]+-\d{3}-\d{2}\b", block):
            error(f"需求缺少规范验收编号：{req_id}")
        if not all(token in block for token in ["Given：", "When：", "Then："]):
            error(f"需求缺少 Given/When/Then 验收标准：{req_id}")
        if "对应原型" not in block:
            error(f"需求缺少对应原型追溯：{req_id}")

    stats["acceptance_criteria"] = len(set(re.findall(r"\bAC-[A-Z0-9-]+-\d{3}-\d{2}\b", prd)))

    if html:
        if not re.search(r"<html\b", html, re.IGNORECASE) or not re.search(r"</html>", html, re.IGNORECASE):
            error("最终原型必须是完整 HTML 文件")
        external_patterns = [
            r"<(?:script|img|iframe|source|audio|video)\b[^>]*(?:src|poster)=[\"']https?://[^\"']+[\"']",
            r"<link\b[^>]*href=[\"']https?://[^\"']+[\"']",
        ]
        external = []
        for pattern in external_patterns:
            external.extend(re.findall(pattern, html, re.IGNORECASE))
        if external:
            error("最终原型包含外部资源依赖，无法保证离线打开：" + "、".join(external[:3]))
        if not re.search(r"<(?:button|a|input|select|textarea)\b|onclick=", html, re.IGNORECASE):
            error("最终原型未检测到可操作控件")
        if "待确认" in html:
            warn("最终原型仍含「待确认」；须确认未掩盖阻塞性流程或页面缺口")

    if acceptance:
        if not preflight:
            for field in ["确认人", "确认时间", "确认结论"]:
                if field not in acceptance:
                    error(f"确认记录缺少字段：{field}")
            if "通过" not in acceptance and "已确认" not in acceptance:
                error("确认记录未包含通过或已确认结论")
        version = baseline.get("baseline_version", "")
        if version and version not in acceptance:
            error("确认记录未标注与 baseline.json 一致的基线版本")

    return {"valid": not errors, "errors": errors, "warnings": warnings, "stats": stats}


def main():
    parser = argparse.ArgumentParser(description="校验 PRD 与 HTML 原型最终双基线")
    parser.add_argument("directory", help="包含 PRD.md、prototype.html、确认记录和 baseline.json 的目录")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    parser.add_argument("--preflight", action="store_true", help="最终用户确认前预检，允许 draft 和 final_approved=false")
    args = parser.parse_args()

    result = validate_baseline(args.directory, preflight=args.preflight)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for message in result["errors"]:
            print(f"[FAIL] {message}")
        for message in result["warnings"]:
            print(f"[WARN] {message}")
        if result["valid"]:
            print("[PASS] 双基线预检通过" if args.preflight else "[PASS] 双基线最终结构校验通过")
        print(
            "统计：{requirements} 项需求，{acceptance_criteria} 条验收标准，{warnings} 条警告".format(
                requirements=result["stats"]["requirements"],
                acceptance_criteria=result["stats"]["acceptance_criteria"],
                warnings=len(result["warnings"]),
            )
        )
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
