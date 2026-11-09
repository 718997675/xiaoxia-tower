#!/usr/bin/env python3
"""战斗内核闸门（第 20 轮）：跑 Node 断言并固化 docs/battle-sim-report.json。

用法：python3 tools/verify_battle_sim.py
退出码 0 = 全部断言 PASS；1 = 有 FAIL 或缺依赖。

边界：只验规则内核（伤害公式 / 五上界 / 状态机 / 确定性 / 卡牌联动 / 层波形），
      不验画面、不验手感、不验平衡性；技能 CD / cost / HP 等均为 PROPOSAL 占位，
      待设计确认与实机实测，不构成对冻结数值的修改。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "battle-sim-report.json"
CHECKER = ROOT / "tools" / "verify_battle_sim.js"


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
    print(f"BATTLE|FAIL|{msg}")
    return 1


def main() -> int:
    if not CHECKER.is_file():
        return fail("缺 tools/verify_battle_sim.js")
    if not (ROOT / "tools" / "battle_sim.js").is_file():
        return fail("缺 tools/battle_sim.js")
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
    report["generator"] = "tools/verify_battle_sim.py"
    report["nodeBinary"] = Path(node).name
    report["scope"] = "横版战斗规则内核（浏览器 / Node 共用 tools/battle_sim.js），非画面、非 Godot、非平衡结论"
    report["proposalNote"] = ("技能 CD / 灵力消耗 / 玩家 HP / 敌人伤害 / 暴击率 / 回复速率等策划案未给值，"
                              "全部为 PROPOSAL 占位，待设计确认，不改 docs/design-freeze.json 任何冻结数值。")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    s = report["summary"]
    verdict = report["verdict"]
    print(f"BATTLE|{verdict}|checks={s['total']}|passed={s['passed']}|failed={s['failed']}")
    print(f"BATTLE|report={REPORT.relative_to(ROOT)}")
    if verdict != "PASS":
        for c in report["checks"]:
            if not c["ok"]:
                print(f"BATTLE|FAIL|{c['label']}|{c['detail'][:200]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
