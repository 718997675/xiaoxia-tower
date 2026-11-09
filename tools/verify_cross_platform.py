#!/usr/bin/env python3
"""跨端口径闸门（第 19 轮）：Godot 黄金样本 ←→ Node/网页规则实现。

流程：
  1) 检查 docs/card-golden-samples.json（由 export_card_golden.gd 经 Godot headless 导出）；
  2) 调 node tools/cross_platform_check.js 逐层复算；
  3) 把结果固化为 docs/cross-platform-report.json，供 final_selfcheck.py 与网页看板读取。

用法：python3 tools/verify_cross_platform.py
退出码 0 = 三端口径一致；1 = 有差异或缺文件。

边界：只证明规则/数值可跨端复算，不证明画面，不证明平衡性；权重与概率仍为 PROPOSAL / 待实测。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "docs" / "card-golden-samples.json"
REPORT = ROOT / "docs" / "cross-platform-report.json"
CHECKER = ROOT / "tools" / "cross_platform_check.js"


def find_node() -> str:
    found = shutil.which("node")
    if found:
        return found
    for candidate in (
        Path.home() / ".workbuddy/binaries/node/versions",
    ):
        if candidate.is_dir():
            for p in sorted(candidate.glob("*/bin/node"), reverse=True):
                if p.is_file():
                    return str(p)
    return ""


def fail(msg: str) -> int:
    print(f"CROSS|FAIL|{msg}")
    return 1


def main() -> int:
    if not GOLDEN.is_file():
        return fail("缺 docs/card-golden-samples.json，请先跑 Godot --headless --script res://tools/export_card_golden.gd")
    if not CHECKER.is_file():
        return fail("缺 tools/cross_platform_check.js")
    node = find_node()
    if not node:
        return fail("找不到 node 可执行文件")

    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    proc = subprocess.run([node, str(CHECKER)], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        return fail(f"Node 复算异常 rc={proc.returncode} stderr={proc.stderr[:400]}")
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return fail(f"Node 输出不是合法 JSON：{exc} / {proc.stdout[:300]}")

    report = dict(result)
    report["generatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report["generator"] = "tools/verify_cross_platform.py"
    report["goldenGenerator"] = golden.get("generator", "")
    report["goldenGeneratedAt"] = golden.get("generatedAt", "")
    report["algorithm"] = golden.get("algorithm", "")
    report["nodeBinary"] = Path(node).name
    report["scope"] = "网页 / Node 复算 Godot 黄金样本（规则与数值），非画面验证"
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    s = report["summary"]
    verdict = report["verdict"]
    print(f"CROSS|{verdict}|checks={s['total']}|passed={s['passed']}|failed={s['failed']}")
    print(f"CROSS|report={REPORT.relative_to(ROOT)}")
    if verdict != "PASS":
        for c in report["checks"]:
            if not c["ok"]:
                print(f"CROSS|FAIL|{c['label']}|{c['detail'][:200]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
