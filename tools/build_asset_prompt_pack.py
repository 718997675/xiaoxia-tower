#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 docs/20 抽出纯提示词，生成一份「整段复制用」的场景 / Boss / 特效提示词包。

用法：
    python3 tools/build_asset_prompt_pack.py            # 生成 previews/asset-prompts-pack.md
    python3 tools/build_asset_prompt_pack.py --check    # 只校验产物是否与源文档一致

与 tools/build_ui_prompt_pack.py 同构：源文档用 HTML 注释标记提示词区块
    <!--PROMPT:<id>:<lang>-->  ```text ... ```  <!--/PROMPT-->
本脚本只做搬运，不改写提示词内容，保证「文档 = 包」。
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "20-场景与Boss外发提示词.md"
OUT = ROOT / "previews" / "asset-prompts-pack.md"

TITLES = {
    ("bgnormal", "zh"): "A1 常规塔层背景（第 1–3 层）· 中文",
    ("bgnormal", "en"): "A1 Normal tower floor (1-3) · English",
    ("bgrest", "zh"): "A2 喘息层背景（第 3 / 6 / 8 层）· 中文",
    ("bgrest", "en"): "A2 Rest floor (3 / 6 / 8) · English",
    ("bghigh", "zh"): "A3 高层复合敌群背景（第 7 层）· 中文",
    ("bghigh", "en"): "A3 High-floor mixed wave (7) · English",
    ("bgboss", "zh"): "A4 Boss 层背景（第 5 / 9 层）· 中文",
    ("bgboss", "en"): "A4 Boss floor (5 / 9) · English",
    ("boss", "zh"): "B 两个 Boss 概念立绘 · 中文",
    ("boss", "en"): "B Two boss concepts · English",
    ("vfx", "zh"): "C1 剩余 4 技能形状语言板 · 中文",
    ("vfx", "en"): "C1 Remaining 4 VFX shape sheet · English",
    ("overlay", "zh"): "C2 5 组状态 overlay 形状板 · 中文",
    ("overlay", "en"): "C2 Five status overlay shapes · English",
    ("bgpatch", "zh"): "A2/A3/A4 通用补充句（第 27 轮回稿后必加）· 中文",
    ("bgpatch", "en"): "A2/A3/A4 General addendum (round 27, required) · English",
}

BLOCK = re.compile(
    r"<!--PROMPT:(?P<id>[a-z]+):(?P<lang>zh|en)-->\s*```text\s*\n(?P<body>.*?)\n```\s*<!--/PROMPT-->",
    re.S,
)

HEADER = """# 场景 / Boss / 特效提示词包（第 26 轮 · 可整段复制）

> 本文件由 `tools/build_asset_prompt_pack.py` 从 `docs/20-场景与Boss外发提示词.md` 自动抽取，**不要手改**。
> 源文档说明见 `docs/20`：UI 9 张已齐、角色 / 怪物 / 图标均已 SHIP，这批只补**塔层背景 / Boss 概念 / 形状语言**三块空白。
> 出图顺序：A 组（一次 1 个塔层）→ B 组 → C 组；**一次只出 1 组**，别把多组塞进一张图。
> 背景稿在生成平台**手动选 16:9**、导出 PNG；Boss / VFX / overlay 用方图即可。
> **A2 / A3 / A4 出图时，必须把最后两段「通用补充句」整段追加到对应背景提示词末尾**（第 27 轮 A1 回稿暴露了方图与四层不可切的问题）；B / C 组不用加。
> 回稿存 `<名字>_original.png` → `tools/snap_ui_palette.py` 吸附 → `tools/check_ui_art.py` 体检。
> **全部只算参考稿（R55），不入库**；`assets/boss/` 与 `assets/vfx/overlay/` 仍为空。

"""


def build() -> str:
    src = SRC.read_text(encoding="utf-8")
    blocks = list(BLOCK.finditer(src))
    if not blocks:
        raise SystemExit("[FAIL] docs/20 里没有找到任何 PROMPT 区块")
    expected = {(pid, lang) for pid, lang in TITLES}
    found = {(m.group("id"), m.group("lang")) for m in blocks}
    if found != expected:
        raise SystemExit(f"[FAIL] 提示词区块与 TITLES 不一致：缺 {expected - found} / 多 {found - expected}")
    out = [HEADER]
    for i, m in enumerate(blocks, 1):
        pid, lang = m.group("id"), m.group("lang")
        out.append(f"\n## {i}. {TITLES[(pid, lang)]}\n")
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
            print("[FAIL] previews/asset-prompts-pack.md 不存在")
            return 1
        if canonical(content) == canonical(OUT.read_text(encoding="utf-8")):
            print(f"ASSETPACK|PASS|与源文档一致 | blocks={content.count('<!-- ')} | bytes={len(content)}")
            return 0
        print("[FAIL] 提示词包与 docs/20 不一致，请重新生成")
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    n = content.count("\n## ")
    print(f"ASSETPACK|PASS|已生成 previews/asset-prompts-pack.md | 提示词 {n} 段 | bytes={len(content)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
