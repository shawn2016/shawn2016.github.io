#!/usr/bin/env python3
"""Regression tests for validate_baseline.py using only Python stdlib."""

import json
import tempfile
import unittest
from pathlib import Path

from validate_baseline import REQUIRED_PRD_SECTIONS, validate_baseline


class BaselineValidatorTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.write_valid_fixture()

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_valid_fixture(self):
        baseline = {
            "schema_version": "1.0",
            "project_name": "示例项目",
            "baseline_version": "v1.0",
            "status": "approved",
            "confirmed_by": "示例用户",
            "confirmed_at": "2026-11-10T18:00:00+08:00",
            "blocking_open_issues": 0,
            "core_flows_confirmed": True,
            "gates": {
                "direction_confirmed": True,
                "wireframe_reviewed": True,
                "prototype_approved": True,
                "final_approved": True,
            },
            "artifacts": {
                "prd": "PRD.md",
                "prototype": "prototype.html",
                "acceptance_record": "08-acceptance-record.md",
            },
        }
        (self.root / "baseline.json").write_text(json.dumps(baseline, ensure_ascii=False), encoding="utf-8")

        prd_parts = ["# 产品需求文档：示例项目", "基线版本：v1.0", "文档状态：已确认"]
        prd_parts.extend(REQUIRED_PRD_SECTIONS)
        prd_parts.append(
            """### REQ-PROJECT-001 创建项目

| 字段 | 内容 |
|---|---|
| 优先级 | P0 |
| 对应原型 | PG-001 / ST-001 |

AC-PROJECT-001-01

Given：用户已登录
When：用户提交合法项目名称
Then：系统显示创建成功并进入项目详情
"""
        )
        (self.root / "PRD.md").write_text("\n\n".join(prd_parts), encoding="utf-8")
        (self.root / "prototype.html").write_text(
            "<!DOCTYPE html><html><body><button type=\"button\">创建项目</button></body></html>",
            encoding="utf-8",
        )
        (self.root / "08-acceptance-record.md").write_text(
            "基线版本：v1.0\n确认人：示例用户\n确认时间：2026-11-10T18:00:00+08:00\n确认结论：通过，已确认",
            encoding="utf-8",
        )

    def test_valid_baseline_passes(self):
        result = validate_baseline(self.root)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["stats"]["requirements"], 1)
        self.assertEqual(result["stats"]["acceptance_criteria"], 1)

    def test_missing_gate_acceptance_and_offline_support_fail(self):
        baseline_path = self.root / "baseline.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        baseline["gates"]["final_approved"] = False
        baseline_path.write_text(json.dumps(baseline, ensure_ascii=False), encoding="utf-8")

        prd_path = self.root / "PRD.md"
        prd = prd_path.read_text(encoding="utf-8")
        prd = prd.replace("AC-PROJECT-001-01", "验收说明")
        prd = prd.replace("Given：", "").replace("When：", "").replace("Then：", "")
        prd_path.write_text(prd, encoding="utf-8")

        (self.root / "prototype.html").write_text(
            "<html><head><script src=\"https://example.com/app.js\"></script></head><body>静态页面</body></html>",
            encoding="utf-8",
        )
        result = validate_baseline(self.root)
        self.assertFalse(result["valid"])
        joined = "\n".join(result["errors"])
        self.assertIn("final_approved", joined)
        self.assertIn("验收", joined)
        self.assertIn("外部资源依赖", joined)

    def test_draft_cannot_be_approved(self):
        baseline_path = self.root / "baseline.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        baseline["status"] = "draft"
        baseline_path.write_text(json.dumps(baseline, ensure_ascii=False), encoding="utf-8")
        result = validate_baseline(self.root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("status" in message for message in result["errors"]))

    def test_preflight_allows_unconfirmed_draft(self):
        baseline_path = self.root / "baseline.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        baseline["status"] = "draft"
        baseline["confirmed_by"] = ""
        baseline["confirmed_at"] = ""
        baseline["gates"]["final_approved"] = False
        baseline_path.write_text(json.dumps(baseline, ensure_ascii=False), encoding="utf-8")

        prd_path = self.root / "PRD.md"
        prd_path.write_text(prd_path.read_text(encoding="utf-8").replace("文档状态：已确认", "文档状态：草案"), encoding="utf-8")
        (self.root / "08-acceptance-record.md").write_text("基线版本：v1.0\n确认结论：待用户确认", encoding="utf-8")

        result = validate_baseline(self.root, preflight=True)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["stats"]["mode"], "preflight")

    def test_external_anchor_is_not_treated_as_resource_dependency(self):
        (self.root / "prototype.html").write_text(
            "<html><body><a href=\"https://example.com/help\">帮助</a><button>继续</button></body></html>",
            encoding="utf-8",
        )
        result = validate_baseline(self.root)
        self.assertTrue(result["valid"], result["errors"])


if __name__ == "__main__":
    unittest.main()
