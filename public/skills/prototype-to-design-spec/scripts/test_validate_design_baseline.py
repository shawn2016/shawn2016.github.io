#!/usr/bin/env python3
"""Regression tests for validate_design_baseline.py."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("validate_design_baseline.py")

STATE = {
    "schema_version": "1.0",
    "project": "demo",
    "created_at": "2026-11-12",
    "updated_at": "2026-11-12",
    "source_baseline": {
        "prd_version": "v1.0",
        "prototype_version": "v1.5",
        "approved": True,
        "confirmed_at": "2026-11-11T23:10:00+0800",
        "confirmed_by": "用户",
        "evidence": "gate_c.status=passed + gates.final_approved=true",
    },
    "phase": "DESIGN_BASELINE",
    "gates": {
        "style_selected": True,
        "base_spec_confirmed": True,
        "tab_designs_accepted": True,
        "design_baseline_approved": False,
    },
    "versions": {
        "candidates": "r1", "design_spec": "v0.2",
        "design_tokens": "v0.2", "tab_designs": "v1.0",
    },
    "selected_style": "A 克制极简",
    "rejection_rounds": 0,
    "pages": [
        {"id": "home", "name": "首页", "file": "06-tab-designs/home.html", "status": "done"},
    ],
    "unresolved_conflicts": 0,
    "blocking_issues": [],
    "open_questions": [],
    "last_decision": None,
}

# 真实需求基线：与 idea-to-prd-prototype 实际产物结构一致（无顶层 status，用 gate_c）
SOURCE_BASELINE = {
    "schema_version": "1.0",
    "project_name": "demo",
    "baseline_type": "PRD + 可操作原型 双基线",
    "confirmed_at": "2026-11-11T23:10:00+0800",
    "confirmed_by": "用户",
    "gate_c": {"status": "passed", "conclusion": "通过"},
    "artifacts": {
        "prd": "PRD.md", "prd_version": "v1.0",
        "prototype": "prototype.html", "prototype_version": "v1.5",
    },
    "gates": {
        "direction_confirmed": True, "wireframe_reviewed": True,
        "prototype_approved": True, "final_approved": True,
    },
    "open_items": ["OPEN-006", "OPEN-009", "OPEN-010"],
}

BASELINE = {
    "schema_version": "1.0",
    "project": "demo",
    "status": "draft",
    "design_baseline_approved": False,
    "confirmed_by": None,
    "confirmed_at": None,
    "source_baseline": {"prd_version": "v1.0", "prototype_version": "v1.5"},
    "gates": copy.deepcopy(STATE["gates"]),
    "selected_style": "A 克制极简",
    "versions": {"design_spec": "v0.2", "design_tokens": "v0.2", "tab_designs": "v1.0"},
    "artifacts": {},
    "reference_sources": [],
    "rejection_rounds": 0,
    "accepted_risks": [],
    "deferred": [],
    "blocking_issues": [],
}

TOKENS = {
    "schema_version": "1.0",
    "version": "v0.2",
    "units": {"length": "px", "size": "px"},
    "source": "style-A / derived",
    "source_kind": "derived",
    "colors": {
        "source": "参考取样观察",
        "values": {"primary": "#3A6FF7", "success": "#2E9E6B", "danger": "#D5453B"},
    },
    "neutrals": {
        "source": "设计推导",
        "values": {"background": "#F7F8FA", "surface": "#FFFFFF", "text": "#1D2330"},
    },
    "typography": {
        "source": "设计推导",
        "scale": [
            {"name": "title", "size": 20, "lineHeight": 28, "weight": 600},
            {"name": "body", "size": 14, "lineHeight": 22, "weight": 400},
        ],
    },
    "spacing": {"source": "设计推导", "step": 4, "scale": [4, 8, 12, 16, 24]},
    "radius": {"source": "设计推导", "values": {"card": 12, "button": 8, "input": 8, "modal": 16}},
    "elevation": {"source": "设计推导", "strategy": "border", "levels": ["flat", "raised"]},
    "iconography": {"source": "设计推导", "style": "line", "stroke": 1.5, "sizes": [16, 20, 24]},
}

TEXT_FILES = {
    "01-entry-check.md": "# 前置检查\n页面清单已锁定。\n",
    "02-style-references.md": "# 参考取样\n- 来源链接：https://uinotes.com/app/example\n- 取样时间：2026-11-12\n- 风格特征：文字描述，不含图片。\n",
    "04-style-decision.md": "# 风格决策\n选定 A；未选项否决理由已记录。\n",
    "05-ux-review.md": "# AI 角色化 UI/UX 评审\n未启用 UI/UX 专家，非真人专家意见。\n",
    "07-spec-regression.md": "# 一致性回归\n未解决冲突数：0\n",
    "08-design-acceptance.md": "# 设计验收记录\n",
    "design-spec.md": "# 设计规范\n| 编号 | 规则 | 可判定条件 | 反例 | 适用范围 |\n| SP-01 | 主色仅用于主操作 | 面积占比可测 | 大面积背景 | 全部页面 |\n",
    "03-style-candidates/comparison.html": "<html><body>comparison</body></html>",
    "06-tab-designs/index.html": "<html><body>index</body></html>",
    "06-tab-designs/home.html": "<html><body>home</body></html>",
}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(root, state=None, baseline=None, tokens=None, candidate_count=4,
          source_baseline=None, include_source_baseline=True):
    root = Path(root)
    for stale in (root / "03-style-candidates").glob("style-*.html"):
        stale.unlink()
    # 真实布局：<project>/design/ 与 <project>/baseline.json
    if include_source_baseline:
        write_json(root.parent / "baseline.json", source_baseline if source_baseline is not None else copy.deepcopy(SOURCE_BASELINE))
    elif (root.parent / "baseline.json").exists():
        (root.parent / "baseline.json").unlink()
    write_json(root / "design-state.json", state if state is not None else copy.deepcopy(STATE))
    write_json(root / "design-baseline.json", baseline if baseline is not None else copy.deepcopy(BASELINE))
    write_json(root / "design-tokens.json", tokens if tokens is not None else copy.deepcopy(TOKENS))
    for rel, text in TEXT_FILES.items():
        write_text(root / rel, text)
    for i in range(candidate_count):
        write_text(root / "03-style-candidates" / "style-{}.html".format(chr(65 + i)), "<html></html>")


def approve(root):
    state = json.loads((root / "design-state.json").read_text(encoding="utf-8"))
    baseline = json.loads((root / "design-baseline.json").read_text(encoding="utf-8"))
    state["phase"] = "APPROVED"
    state["gates"]["design_baseline_approved"] = True
    baseline["status"] = "approved"
    baseline["design_baseline_approved"] = True
    baseline["confirmed_by"] = "用户"
    baseline["confirmed_at"] = "2026-11-12"
    baseline["gates"] = copy.deepcopy(state["gates"])
    write_json(root / "design-state.json", state)
    write_json(root / "design-baseline.json", baseline)


def run_validate(root, preflight=False):
    cmd = [sys.executable, str(SCRIPT), str(root)]
    if preflight:
        cmd.append("--preflight")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout)


class ValidateDesignBaselineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project_root = Path(self.tmp.name)
        self.root = self.project_root / "design"
        build(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_preflight_passes_on_complete_draft(self):
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 0, report["errors"])
        self.assertTrue(report["ok"])

    def test_final_passes_on_approved_baseline(self):
        approve(self.root)
        code, report = run_validate(self.root, preflight=False)
        self.assertEqual(code, 0, report["errors"])
        self.assertTrue(report["ok"])

    def test_final_rejects_draft_status(self):
        code, report = run_validate(self.root, preflight=False)
        self.assertEqual(code, 1)
        self.assertTrue(any("四个门禁" in e for e in report["errors"]))

    def test_rejects_unapproved_source_baseline(self):
        real = copy.deepcopy(SOURCE_BASELINE)
        real["gate_c"]["status"] = "pending"
        real["gates"]["final_approved"] = False
        build(self.root, source_baseline=real)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("已批准证据" in e or "四个门禁" in e for e in report["errors"]))

    def test_rejects_missing_real_baseline(self):
        build(self.root, include_source_baseline=False)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("无法读取需求基线" in e for e in report["errors"]))

    def test_rejects_missing_source_evidence(self):
        state = copy.deepcopy(STATE)
        del state["source_baseline"]["evidence"]
        build(self.root, state=state)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("已批准证据" in e for e in report["errors"]))

    def test_rejects_confirmed_at_mismatch(self):
        state = copy.deepcopy(STATE)
        state["source_baseline"]["confirmed_at"] = "2026-01-01T00:00:00+0800"
        build(self.root, state=state)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("不一致" in e for e in report["errors"]))

    def test_accepts_documented_status_schema(self):
        real = {
            "schema_version": "1.0",
            "status": "approved",
            "confirmed_at": "2026-11-11T23:10:00+0800",
            "gates": copy.deepcopy(SOURCE_BASELINE["gates"]),
            "artifacts": {"prd": "PRD.md", "prototype": "prototype.html"},
        }
        build(self.root, source_baseline=real)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 0, report["errors"])

    def test_rejects_wrong_candidate_count(self):
        build(self.root, candidate_count=3)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("候选稿数量" in e for e in report["errors"]))

    def test_rejects_gate_order_violation(self):
        state = copy.deepcopy(STATE)
        state["gates"]["base_spec_confirmed"] = False
        build(self.root, state=state)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("门禁顺序错误" in e for e in report["errors"]))

    def test_rejects_invalid_color_value(self):
        tokens = copy.deepcopy(TOKENS)
        tokens["colors"]["values"]["primary"] = "blue"
        build(self.root, tokens=tokens)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("色值非法" in e for e in report["errors"]))

    def test_rejects_missing_token_section(self):
        tokens = copy.deepcopy(TOKENS)
        del tokens["iconography"]
        build(self.root, tokens=tokens)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("缺少顶层字段 iconography" in e for e in report["errors"]))

    def test_final_rejects_missing_page_design(self):
        approve(self.root)
        (self.root / "06-tab-designs" / "home.html").unlink()
        code, report = run_validate(self.root, preflight=False)
        self.assertEqual(code, 1)
        self.assertTrue(any("设计稿缺失" in e for e in report["errors"]))

    def test_final_rejects_unresolved_conflict(self):
        approve(self.root)
        state = json.loads((self.root / "design-state.json").read_text(encoding="utf-8"))
        state["unresolved_conflicts"] = 2
        write_json(self.root / "design-state.json", state)
        code, report = run_validate(self.root, preflight=False)
        self.assertEqual(code, 1)
        self.assertTrue(any("未解决冲突" in e for e in report["errors"]))

    def test_rejects_excessive_rejection_rounds(self):
        state = copy.deepcopy(STATE)
        state["rejection_rounds"] = 4
        build(self.root, state=state)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("收敛上限" in e for e in report["errors"]))

    def test_rejects_embedded_reference_image(self):
        path = self.root / "02-style-references.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n![第三方截图](ref.png)\n", encoding="utf-8")
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("内嵌了图片引用" in e for e in report["errors"]))

    def test_rejects_baseline_gate_mismatch(self):
        baseline = copy.deepcopy(BASELINE)
        baseline["gates"]["style_selected"] = False
        build(self.root, baseline=baseline)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("gates 不一致" in e for e in report["errors"]))

    def test_preflight_requires_first_three_gates(self):
        state = copy.deepcopy(STATE)
        state["gates"]["tab_designs_accepted"] = False
        baseline = copy.deepcopy(BASELINE)
        baseline["gates"] = copy.deepcopy(state["gates"])
        build(self.root, state=state, baseline=baseline)
        code, report = run_validate(self.root, preflight=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("前三个门禁" in e for e in report["errors"]))

    def test_final_rejects_non_testable_spec(self):
        approve(self.root)
        write_text(self.root / "design-spec.md", "# 设计规范\n整体要协调、美观、有质感。\n")
        code, report = run_validate(self.root, preflight=False)
        self.assertEqual(code, 1)
        self.assertTrue(any("SP-xx" in e or "可判定条件" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
