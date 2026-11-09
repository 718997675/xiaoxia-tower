#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 docs/19 抽出纯提示词，生成一份「整段复制用」的提示词包。

用法：
    python3 tools/build_ui_prompt_pack.py            # 生成 previews/ui-prompts-pack.md
    python3 tools/build_ui_prompt_pack.py --check    # 只校验产物是否与源文档一致

源文档里用 HTML 注释标记提示词区块：
    <!--PROMPT:<id>:<lang>-->  ```text ... ```  <!--/PROMPT-->
本脚本只做搬运，不改写提示词内容，保证「文档 = 包」。
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "19-UI界面设计规格与外发提示词.md"
OUT = ROOT / "previews" / "ui-prompts-pack.md"

TITLES = {
    ("anchor", "zh"): "⓪ 风格锚点板（先出这张）· 中文",
    ("anchor", "en"): "⓪ Style sheet (do this one first) · English",
    ("menu", "zh"): "① MainMenu 主菜单 · 中文",
    ("menu", "en"): "① MainMenu · English",
    ("hud", "zh"): "② TowerHUD 横版战斗 HUD · 中文",
    ("hud", "en"): "② TowerHUD · English",
    ("draft", "zh"): "③ RewardPicker 层间三选一 · 中文",
    ("draft", "en"): "③ RewardPicker · English",
    ("result", "zh"): "④ RunResult 单局结算 · 中文",
    ("result", "en"): "④ RunResult · English",
    ("pause", "zh"): "⑤ Pause 暂停界面 · 中文",
    ("pause", "en"): "⑤ Pause · English",
    ("affix", "zh"): "⑥ AffixPicker 天劫词缀自选 · 中文",
    ("affix", "en"): "⑥ AffixPicker · English",
    ("codex", "zh"): "⑦ Codex 卡牌图鉴（可选）· 中文",
    ("codex", "en"): "⑦ Codex (optional) · English",
    ("icons", "zh"): "⑧ 图标系统样式表（可选）· 中文",
    ("icons", "en"): "⑧ Icon style sheet (optional) · English",
}

BLOCK = re.compile(
    r"<!--PROMPT:(?P<id>[a-z]+):(?P<lang>zh|en)-->\s*```text\s*\n(?P<body>.*?)\n```\s*<!--/PROMPT-->",
    re.S,
)

HEADER = """# UI 提示词包（第 22 轮 · 可整段复制）

> 本文件由 `tools/build_ui_prompt_pack.py` 从 `docs/19-UI界面设计规格与外发提示词.md` 自动抽取，**不要手改**。
> 用法：先出「⓪ 风格锚点板」，确认风格后再一次出 1 个界面；出图后把 PNG 丢进 `previews/ui/`，运行
> `python3 tools/check_ui_art.py previews/ui/` 做调色板 / 尺寸 / 半透明体检。

"""


def build() -> str:
    src = SRC.read_text(encoding="utf-8")
    blocks = list(BLOCK.finditer(src))
    if not blocks:
        raise SystemExit("[FAIL] docs/19 里没有找到任何 PROMPT 区块")
    out = [HEADER]
    for i, m in enumerate(blocks, 1):
        pid, lang = m.group("id"), m.group("lang")
        title = TITLES.get((pid, lang), f"{pid} · {lang}")
        out.append(f"\n## {i}. {title}\n")
        out.append(f"<!-- {pid}:{lang} -->\n")
        out.append("```text\n" + m.group("body").strip() + "\n```\n")
    out.append("\n---\n")
    out.append(f"\n> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}　"
               f"共 {len(blocks)} 段提示词。\n")
    return "".join(out)


def canonical(text: str) -> str:
    """忽略生成时间戳后再比对，避免自我判过期。"""
    lines = [ln for ln in text.splitlines() if not ln.startswith("> 生成时间：")]
    return "\n".join(lines).strip()


def main(argv: list[str]) -> int:
    content = build()
    if "--check" in argv:
        if not OUT.exists():
            print("[FAIL] previews/ui-prompts-pack.md 不存在")
            return 1
        cur = canonical(OUT.read_text(encoding="utf-8"))
        if canonical(content) == cur:
            print(f"UIPACK|PASS|与源文档一致 | blocks={content.count('<!-- ')} | bytes={len(content)}")
            return 0
        print("[FAIL] 提示词包与 docs/19 不一致，请重新生成")
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    n = content.count("\n## ")
    print(f"UIPACK|PASS|已生成 previews/ui-prompts-pack.md | 提示词 {n} 段 | bytes={len(content)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
