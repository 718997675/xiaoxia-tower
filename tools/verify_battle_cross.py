#!/usr/bin/env python3
"""战斗「公式层」跨端口径闸门（第 22 轮）：Godot 黄金样本 ←→ Node/网页战斗内核。

流程：
  1) 检查 docs/battle-golden-samples.json（由 export_battle_golden.gd 经 Godot headless 导出）；
  2) 调 node tools/cross_platform_battle_check.js 逐条复算；
  3) 把结果固化为 docs/battle-cross-report.json，供 final_selfcheck.py 与网页看板读取。

用法：python3 tools/verify_battle_cross.py
退出码 0 = 口径一致；1 = 有差异或缺文件。

边界：证明的是**公式与只读数据表**可跨端复算，
     不证明逐 tick 状态机一致、不证明画面、不证明平衡性；
     技能 CD / 灵力 / 玩家 HP 等 PROPOSAL 占位刻意不镜像。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "docs" / "battle-golden-samples.json"
REPORT = ROOT / "docs" / "battle-cross-report.json"
CHECKER = ROOT / "tools" / "cross_platform_battle_check.js"


def find_node() -> str:
    found = shutil.which("node")
    if found:
        return found
    for candidate in (Path.home() / ".workbuddy/binaries/node/versions",):
        if candidate.is_dir():
            for p in sorted(candidate.glob("*/bin/node"), reverse=True):
                if p.is_file():
                    return str(p)
    return ""


def fail(msg: str) -> int:
    print(f"BCROSS|FAIL|{msg}")
    return 1


def main() -> int:
    if not GOLDEN.is_file():
        return fail("缺 docs/battle-golden-samples.json，请先跑 Godot --headless --script res://tools/export_battle_golden.gd")
    if not CHECKER.is_file():
        return fail("缺 tools/cross_platform_battle_check.js")
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
    report["generator"] = "tools/verify_battle_cross.py"
    report["goldenGenerator"] = golden.get("generator", "")
    report["goldenGeneratedAt"] = golden.get("generatedAt", "")
    report["goldenEngine"] = golden.get("engine", "")
    report["nodeBinary"] = Path(node).name
    report["scope"] = "战斗公式层跨端复算（公式 + 五上界 + 9 层波形 + 4 技能冻结字段）；不含逐 tick 状态机"
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    s = report["summary"]
    verdict = report["verdict"]
    print(f"BCROSS|{verdict}|checks={s['total']}|passed={s['passed']}|failed={s['failed']}")
    print(f"BCROSS|report={REPORT.relative_to(ROOT)}")
    if verdict != "PASS":
        for c in report["checks"]:
            if not c["ok"]:
                print(f"BCROSS|FAIL|{c['label']}|{c['detail'][:200]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
