#!/usr/bin/env python3
"""Validate a design baseline directory produced by prototype-to-design-spec.

Usage:
    python3 validate_design_baseline.py <design-directory> [--preflight]

Exit code 0 when validation passes, 1 otherwise. Prints a JSON report.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PHASES = {
    "ENTRY_CHECK", "REFERENCE_STUDY", "STYLE_CANDIDATES", "STYLE_GATE",
    "BASE_SPEC", "UX_REVIEW", "TAB_DESIGNS", "SPEC_REGRESSION",
    "DESIGN_BASELINE", "APPROVED",
}
GATE_ORDER = (
    "style_selected",
    "base_spec_confirmed",
    "tab_designs_accepted",
    "design_baseline_approved",
)
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")
VERSION_RE = re.compile(r"^v[0-9]+\.[0-9]+$")
SOURCE_KINDS = ("observed", "derived", "user_specified")

REQUIRED_FILES = (
    "design-state.json",
    "01-entry-check.md",
    "02-style-references.md",
    "04-style-decision.md",
    "05-ux-review.md",
    "07-spec-regression.md",
    "design-spec.md",
    "design-tokens.json",
    "03-style-candidates/comparison.html",
    "06-tab-designs/index.html",
)
TOKEN_SECTIONS = (
    "schema_version", "version", "units", "source", "colors", "neutrals",
    "typography", "spacing", "radius", "elevation", "iconography",
)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def read_json(path):
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh), None
    except (OSError, ValueError) as exc:
        return None, "无法读取 {}: {}".format(path.name, exc)


SOURCE_GATES = (
    "direction_confirmed", "wireframe_reviewed", "prototype_approved", "final_approved",
)


def check_source_baseline(project_dir):
    """Read the real requirement baseline instead of trusting a copied claim.

    Accepts both the documented schema (top-level status=approved) and the
    shape actually produced by idea-to-prd-prototype (gate_c.status=passed
    plus gates.final_approved=true plus confirmed_at).
    """
    path = Path(project_dir) / "baseline.json"
    data, err = read_json(path)
    if err:
        return None, ["无法读取需求基线 {}: {}".format(path, err)]
    errors = []
    gates = data.get("gates", {}) if isinstance(data, dict) else {}
    if not isinstance(gates, dict) or any(gates.get(k) is not True for k in SOURCE_GATES):
        errors.append("需求基线四个门禁未全部通过")
    gate_c = data.get("gate_c") if isinstance(data, dict) else None
    status_ok = isinstance(data, dict) and data.get("status") == "approved"
    gate_c_ok = isinstance(gate_c, dict) and gate_c.get("status") == "passed"
    if not (status_ok or gate_c_ok):
        errors.append("需求基线缺少已批准证据（status=approved 或 gate_c.status=passed）")
    if not isinstance(data, dict) or not data.get("confirmed_at"):
        errors.append("需求基线缺少 confirmed_at")
    return data, errors


def check_tokens(data):
    errors = []
    if not isinstance(data, dict):
        return ["design-tokens.json 顶层必须是对象"]
    for key in TOKEN_SECTIONS:
        if key not in data:
            errors.append("token 缺少顶层字段 {}".format(key))
    if errors:
        return errors

    if data.get("schema_version") != "1.0":
        errors.append("token schema_version 必须为 1.0")
    if not VERSION_RE.match(str(data.get("version", ""))):
        errors.append("token version 格式应为 vX.Y")
    units = data.get("units")
    if not isinstance(units, dict) or not units.get("length") or not units.get("size"):
        errors.append("token units 需要 length 与 size")

    source_kind = data.get("source_kind")
    if source_kind is not None and source_kind not in SOURCE_KINDS:
        errors.append("token source_kind 取值非法")

    for section in ("colors", "neutrals"):
        block = data.get(section)
        if not isinstance(block, dict):
            errors.append("token {} 必须是对象".format(section))
            continue
        if not block.get("source"):
            errors.append("token {} 缺少 source 说明".format(section))
        values = block.get("values")
        if not isinstance(values, dict) or not values:
            errors.append("token {} 缺少 values".format(section))
            continue
        for name, value in values.items():
            if not isinstance(value, str) or not COLOR_RE.match(value):
                errors.append("token {}.{} 色值非法: {!r}".format(section, name, value))

    typo = data.get("typography")
    if not isinstance(typo, dict) or not typo.get("source"):
        errors.append("token typography 缺少 source")
    scale = typo.get("scale") if isinstance(typo, dict) else None
    if not isinstance(scale, list) or not scale:
        errors.append("token typography.scale 必须是非空数组")
    else:
        for i, item in enumerate(scale):
            if not isinstance(item, dict) or not all(
                k in item for k in ("name", "size", "lineHeight", "weight")
            ):
                errors.append("token typography.scale[{}] 字段不全".format(i))
                continue
            for key in ("size", "lineHeight", "weight"):
                if not _is_number(item[key]):
                    errors.append("token typography.scale[{}].{} 必须为数字".format(i, key))

    spacing = data.get("spacing")
    if not isinstance(spacing, dict) or not spacing.get("source"):
        errors.append("token spacing 缺少 source")
    if isinstance(spacing, dict):
        if not _is_number(spacing.get("step")):
            errors.append("token spacing.step 必须为数字")
        steps = spacing.get("scale")
        if not isinstance(steps, list) or not steps or not all(_is_number(v) for v in steps):
            errors.append("token spacing.scale 必须是非空数字数组")

    radius = data.get("radius")
    if not isinstance(radius, dict) or not radius.get("source"):
        errors.append("token radius 缺少 source")
    if isinstance(radius, dict):
        values = radius.get("values")
        if not isinstance(values, dict) or not values or not all(
            _is_number(v) for v in values.values()
        ):
            errors.append("token radius.values 必须是非空数字字典")

    elevation = data.get("elevation")
    if not isinstance(elevation, dict) or not elevation.get("source") or not elevation.get("strategy"):
        errors.append("token elevation 缺少 source 或 strategy")

    icons = data.get("iconography")
    if not isinstance(icons, dict) or not icons.get("source") or not icons.get("style"):
        errors.append("token iconography 缺少 source 或 style")
    if isinstance(icons, dict):
        sizes = icons.get("sizes")
        if not isinstance(sizes, list) or not sizes or not all(_is_number(v) for v in sizes):
            errors.append("token iconography.sizes 必须是非空数字数组")

    return errors


def validate(design_dir, preflight=False):
    errors = []
    warnings = []
    root = Path(design_dir)

    if not root.is_dir():
        return {
            "ok": False, "mode": "preflight" if preflight else "final",
            "errors": ["设计目录不存在: {}".format(root)], "warnings": [],
        }

    for rel in REQUIRED_FILES:
        if not (root / rel).is_file():
            errors.append("缺少必需文件 {}".format(rel))

    state, err = read_json(root / "design-state.json")
    if err:
        errors.append(err)
        state = None
    tokens, err = read_json(root / "design-tokens.json")
    if err:
        errors.append(err)
        tokens = None
    baseline, err = read_json(root / "design-baseline.json")
    if err:
        if preflight:
            warnings.append("{}（preflight 允许尚未生成）".format(err))
        else:
            errors.append(err)
        baseline = None

    # 前置：直接读取真实需求基线，不信任 design-state.json 的自述
    source_baseline_data, source_errors = check_source_baseline(root.parent)
    errors.extend(source_errors)

    if isinstance(state, dict):
        source = state.get("source_baseline", {})
        if (
            not isinstance(source, dict)
            or source.get("approved") is not True
            or not source.get("confirmed_at")
            or not source.get("evidence")
        ):
            errors.append("design-state.json 的 source_baseline 未记录已批准证据（approved / confirmed_at / evidence）")
        elif source_baseline_data and source.get("confirmed_at") != source_baseline_data.get("confirmed_at"):
            errors.append("source_baseline.confirmed_at 与真实 baseline.json 不一致")
        if state.get("phase") not in PHASES:
            errors.append("phase 取值非法: {!r}".format(state.get("phase")))
        gates = state.get("gates", {})
        if not isinstance(gates, dict) or set(gates) != set(GATE_ORDER):
            errors.append("gates 必须且只能包含四个标准门禁")
        else:
            for key in GATE_ORDER:
                if not isinstance(gates[key], bool):
                    errors.append("门禁 {} 必须为布尔值".format(key))
            for i in range(1, len(GATE_ORDER)):
                if gates.get(GATE_ORDER[i]) is True and gates.get(GATE_ORDER[i - 1]) is not True:
                    errors.append("门禁顺序错误：{} 已通过但 {} 未通过".format(GATE_ORDER[i], GATE_ORDER[i - 1]))
            if preflight:
                for key in GATE_ORDER[:3]:
                    if gates.get(key) is not True:
                        errors.append("preflight 要求前三个门禁均通过，{} 未通过".format(key))
            else:
                for key in GATE_ORDER:
                    if gates.get(key) is not True:
                        errors.append("最终验收要求四个门禁全通过，{} 未通过".format(key))

        rounds = state.get("rejection_rounds", 0)
        if not isinstance(rounds, int) or rounds < 0 or rounds > 3:
            errors.append("rejection_rounds 超出 0-3 的收敛上限")

        pages = state.get("pages")
        if not isinstance(pages, list) or not pages:
            errors.append("pages 必须是非空数组")
        elif not preflight:
            for page in pages:
                rel = page.get("file") if isinstance(page, dict) else None
                if not rel or not (root / rel).is_file():
                    errors.append("页面清单中的设计稿缺失: {!r}".format(rel))

        if not preflight:
            if state.get("unresolved_conflicts") != 0:
                errors.append("仍有未解决冲突 {}".format(state.get("unresolved_conflicts")))
            if state.get("blocking_issues"):
                errors.append("仍有未解决阻塞项 {}".format(state.get("blocking_issues")))
            if state.get("phase") != "APPROVED":
                errors.append("最终验收要求 phase=APPROVED")
            if not state.get("selected_style"):
                errors.append("缺少选定风格 selected_style")

        if baseline is not None and isinstance(baseline, dict) and isinstance(gates, dict):
            if baseline.get("gates") != gates:
                errors.append("design-baseline.json 与 design-state.json 的 gates 不一致")

    # 候选稿数量 4-5
    candidate_dir = root / "03-style-candidates"
    candidates = sorted(candidate_dir.glob("style-*.html")) if candidate_dir.is_dir() else []
    if not 4 <= len(candidates) <= 5:
        errors.append("风格候选稿数量必须为 4-5，当前 {}".format(len(candidates)))

    # token 结构
    if tokens is not None:
        errors.extend(check_tokens(tokens))

    # 合规：参考记录不得内嵌第三方图片
    ref_path = root / "02-style-references.md"
    if ref_path.is_file():
        text = ref_path.read_text(encoding="utf-8", errors="replace")
        if "![" in text:
            errors.append("02-style-references.md 内嵌了图片引用，禁止复制第三方截图")
        if "来源链接" not in text:
            warnings.append("02-style-references.md 未见「来源链接」字段")

    # 规范可判定性
    spec_path = root / "design-spec.md"
    if spec_path.is_file():
        spec = spec_path.read_text(encoding="utf-8", errors="replace")
        if "SP-" not in spec:
            msg = "design-spec.md 未见 SP-xx 编号条款"
            errors.append(msg) if not preflight else warnings.append(msg)
        if "可判定条件" not in spec:
            msg = "design-spec.md 未见「可判定条件」列"
            errors.append(msg) if not preflight else warnings.append(msg)

    # 评审口径声明
    review_path = root / "05-ux-review.md"
    if review_path.is_file():
        review = review_path.read_text(encoding="utf-8", errors="replace")
        if "AI 角色化" not in review and "专家" not in review:
            warnings.append("05-ux-review.md 未见专家口径声明")

    # 最终基线状态
    if not preflight and baseline is not None and isinstance(baseline, dict):
        if baseline.get("status") != "approved":
            errors.append("design-baseline.json status 必须为 approved")
        if baseline.get("design_baseline_approved") is not True:
            errors.append("design_baseline_approved 必须为 true")
        if not baseline.get("confirmed_by") or not baseline.get("confirmed_at"):
            errors.append("缺少 confirmed_by / confirmed_at")
        if baseline.get("blocking_issues"):
            errors.append("design-baseline.json 仍有阻塞项")

    return {
        "ok": len(errors) == 0,
        "mode": "preflight" if preflight else "final",
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate a design baseline directory")
    parser.add_argument("design_directory", help="Path to the design/ directory")
    parser.add_argument("--preflight", action="store_true", help="Allow draft status")
    args = parser.parse_args()
    report = validate(args.design_directory, preflight=args.preflight)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
