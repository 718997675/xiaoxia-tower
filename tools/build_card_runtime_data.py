#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把唯一设计源 docs/buff-card-library.json 生成一份引擎运行时副本 data/buff-card-library.json。

为什么要副本（R45）：
  docs/ 下有空 .gdignore（第 15 轮 R39，为避免 Godot 把设计 CSV 当翻译表导入）。
  .gdignore 会让编辑器跳过整目录扫描，**导出后该目录不进包**，因此运行时
  `res://docs/buff-card-library.json` 不能作为游戏数据来源。
  设计源仍只保留在 docs/（策划唯一源、不二改），运行时只读 data/ 副本；
  本脚本是二者之间唯一的、可复跑的一致性闸门。

用法：
  python3 tools/build_card_runtime_data.py            # 生成副本 + 写一致性报告
  python3 tools/build_card_runtime_data.py --check    # 只校验不写盘（供自检/CI 用）
退出码：0=PASS，1=FAIL
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "buff-card-library.json"
TARGET = ROOT / "data" / "buff-card-library.json"
REPORT = ROOT / "docs" / "card-runtime-data-report.json"


def canonical(obj) -> str:
    """与键顺序无关的规范化串，用于指纹比对。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate(lib: dict) -> None:
    cards = lib.get("cards")
    assert isinstance(cards, list) and len(cards) == 72, "卡库不是 72 张"
    assert len({c.get("cat") for c in cards}) == 6, "类别不是 6 类"
    assert len({c.get("rarity") for c in cards}) == 4, "稀有度不是 4 档"
    ids = [c.get("id") for c in cards]
    assert len(set(ids)) == 72, "卡 ID 有重复"
    assert isinstance(lib.get("offenseCeiling"), dict), "缺 offenseCeiling 五上界声明"
    assert isinstance(lib.get("drawRule"), dict), "缺 drawRule 抽取规则声明"
    assert isinstance(lib.get("hookWhitelist"), list), "缺 hookWhitelist"
    for c in cards:
        for key in ("id", "cat", "rarity", "stack", "excl", "req", "hook", "weight", "unlock", "params"):
            assert key in c, f"{c.get('id')} 缺字段 {key}"


def main() -> int:
    check_only = "--check" in sys.argv[1:]
    if not SOURCE.is_file():
        print(f"FAIL | 缺设计源 {SOURCE.relative_to(ROOT).as_posix()}")
        return 1
    lib = json.loads(SOURCE.read_text(encoding="utf-8"))
    validate(lib)
    fingerprint = sha256(canonical(lib))

    if check_only:
        if not TARGET.is_file():
            print("FAIL | 缺运行时副本 data/buff-card-library.json")
            return 1
        runtime = json.loads(TARGET.read_text(encoding="utf-8"))
        if canonical(runtime) != canonical(lib):
            print("FAIL | 运行时副本与设计源语义不一致，请重跑本脚本")
            return 1
        print(f"PASS | 运行时副本与设计源一致 | cards=72 | sha256={fingerprint[:16]}")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(lib, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    back = json.loads(TARGET.read_text(encoding="utf-8"))
    assert canonical(back) == canonical(lib), "回读校验失败"

    report = {
        "version": 1,
        "generatedAt": date.today().isoformat(),
        "generator": "tools/build_card_runtime_data.py",
        "reason": "docs/ 的 .gdignore 使该目录导出后不可用；运行时只读 data/ 副本（R45）",
        "source": "docs/buff-card-library.json",
        "target": "data/buff-card-library.json",
        "canonicalSha256": fingerprint,
        "cards": len(lib["cards"]),
        "categories": len({c["cat"] for c in lib["cards"]}),
        "rarities": len({c["rarity"] for c in lib["cards"]}),
        "verdict": "PASS",
        "note": "数值、权重、概率一律为 PROPOSAL / 待实测；本脚本只搬运数据，不改任何卡面或规则。",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS | 已生成 data/buff-card-library.json | 72 张 | sha256={fingerprint[:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
