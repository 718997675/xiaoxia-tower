#!/usr/bin/env python3
"""卡牌效果闸门（第 21 轮）：跑 Node 断言并固化 docs/card-effects-report.json。

用法：python3 tools/verify_card_effects.py
退出码 0 = 全部断言 PASS；1 = 有 FAIL 或缺依赖。

边界：只验「只读冻结卡库 → 编译效果集 → 战斗内核按它变化」，
      不验画面、不验手感、不验平衡性、不碰 Godot、不改冻结数值。
      未映射的键一律如实列出理由，不得当成已实现效果。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "card-effects-report.json"
CHECKER = ROOT / "tools" / "verify_card_effects.js"


def find_node() -> str:
    found = shutil.which("node")
    if found:
        return found
    versions = Path.home() / ".workbuddy/binaries/node/versions"
    if versions.is_dir():
        for p in sorted(versions.glob("*/bin/node"), reverse=True):
            if p.is_file():
                return str(p)
    return ""


def fail(msg: str) -> int:
    print(f"CARD_FX|FAIL|{msg}")
    return 1


def main() -> int:
    for rel in ("tools/verify_card_effects.js", "tools/card_effects.js",
                "tools/battle_sim.js", "data/buff-card-library.json"):
        if not (ROOT / rel).is_file():
            return fail(f"缺 {rel}")
    node = find_node()
    if not node:
        return fail("找不到 node 可执行文件")

    proc = subprocess.run([node, str(CHECKER)], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        return fail(f"Node 断言异常 rc={proc.returncode} stderr={proc.stderr[:400]}")
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return fail(f"Node 输出不是合法 JSON：{exc} / {proc.stdout[:300]}")

    report = dict(result)
    report["generatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report["generator"] = "tools/verify_card_effects.py"
    report["nodeBinary"] = Path(node).name
    report["scope"] = (
        "网页验证层：tools/card_effects.js 只读 data/buff-card-library.json，"
        "编译成 tools/battle_sim.js 可消费的 EffectSet。不是冻结规格、不是平衡结论、"
        "不迁移到 Godot 实机；Godot 侧仍无战斗逻辑。"
    )
    report["proposalNote"] = (
        "效果映射按卡面 text 与 params 逐张核对；语义需设计确认、归抽卡层、"
        "或网页验证层没有对应系统的参数一律列入 unbound 并给出理由，不猜数值、不伪造效果。"
        "R54：破云式卡面「总伤不变」与 params split:2 × per_hit:0.6 = 1.2 不自洽，"
        "本验证层以冻结卡面 text 为准，待设计确认。"
    )
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    s = report["summary"]
    verdict = report["verdict"]
    print(f"CARD_FX|{verdict}|checks={s['total']}|passed={s['passed']}|failed={s['failed']}")
    print(f"CARD_FX|report={REPORT.relative_to(ROOT)}")
    if verdict != "PASS":
        for c in report["checks"]:
            if not c["ok"]:
                print(f"CARD_FX|FAIL|{c['label']}|{c['detail'][:200]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
