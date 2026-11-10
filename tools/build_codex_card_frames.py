#!/usr/bin/env python3
"""第 40 轮 · 按 07-codex 图鉴审美重绘 4 档卡框（PROPOSAL 候选）。

用户第 40 轮反馈：「卡框是不是要按照 07 的美化一下？文字也是排版都乱了」。
核查结论（见 docs/28）：
  - 07-codex 单卡是「整卡深墨底 + 双层细线 + 四角云纹 + 顶部卡名条 +
    内凹插画框 + 底部独立信息条」，稀有度只换边框/线条颜色，结构四档一致。
  - docs/12 §2 冻结卡框是宣纸米色底 + 横线占位；第 39 轮换成 #12161F 墨底
    84×56 插画后，上下半张卡底色割裂，横线被误读成「排版乱」。
  - 网页 wrapText() 按字符硬切，把 "20%" 拆成 "2" / "0%"，且 cname/cdesc/cinfo
    三档字号、底部信息条贴边被裁 —— 这是 R48 的旧债，不是新插画造成的。

本脚本只产**候选**，不覆盖任何冻结资产：
    previews/card_frames_codex/frame_<rarity>.png   4 张 96×144 RGB（不含文字）
    docs/codex-card-frames-report.json               sha256 / 色板 / 结构 / status
    assets/_preview/codex-frames-4tiers.png          4 档放大对照
    assets/_preview/card-art-full-cards-codex.png    72 张整卡（新框 + 84×56 插画）
    assets/_preview/card-frame-frozen-vs-codex.png   旧框 / 新框并排对照

纪律：
  - assets/ui/cards/ 的 10 张冻结卡面一个字节都不动；docs/12 不改。
  - 24 色锁定板内取色，硬边、不透明、无抗锯齿、无半透明。
  - 卡框 PNG 内不含任何文字 / 数字（R9 字体纪律），文字仍由 UI 文字层绘制。
  - 候选 status「待目检与合规确认；不得直接入库」；Q17 未拍板、GUI F5 未跑。

用法：
    python3 tools/build_codex_card_frames.py          # 生成 4 张框 + 预览 + 报告
    python3 tools/build_codex_card_frames.py --check # 只校验，不写文件
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from snap_ui_palette import load_palette  # noqa: E402

OUT_DIR = ROOT / "previews" / "card_frames_codex"
PREVIEW_DIR = ROOT / "assets" / "_preview"
FROZEN_DIR = ROOT / "assets" / "ui" / "cards"
ART_DIR = ROOT / "assets" / "ui" / "card_art"
LIB_PATH = ROOT / "data" / "buff-card-library.json"
REPORT_PATH = ROOT / "docs" / "codex-card-frames-report.json"
OLD_PREVIEW = PREVIEW_DIR / "card-art-full-cards.png"

W, H = 96, 144
ART_X, ART_Y, ART_W, ART_H = 6, 19, 84, 56

PALETTE = load_palette()
PSET = set(PALETTE)


def hexcol(s: str) -> tuple[int, int, int]:
    v = tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))
    if v not in PSET:
        raise AssertionError(f"颜色 {s} 不在 24 色锁定板内")
    return v


INK = hexcol("#12161F")       # 卡面 / 插画底
PANEL = hexcol("#2A3140")     # 卡名条 / 信息条底
BLACK = hexcol("#000000")     # 硬描边 / 分隔
PAPER = hexcol("#E8DFC8")     # 仅对照预览用，框内不画文字

# 稀有度：主色 / 高光 / 深色（均取锁定板）
RARITY = {
    "common": {"line": hexcol("#4A5568"), "hi": hexcol("#8A8268"),
               "dark": hexcol("#2A3140"), "tier": 1, "name": "凡品"},
    "rare":   {"line": hexcol("#5FA8A0"), "hi": hexcol("#9BD4CC"),
               "dark": hexcol("#2F6E6A"), "tier": 2, "name": "灵品"},
    "legend": {"line": hexcol("#D9A441"), "hi": hexcol("#F2D089"),
               "dark": hexcol("#8A6520"), "tier": 3, "name": "仙品"},
    "curse":  {"line": hexcol("#C8453B"), "hi": hexcol("#E8806F"),
               "dark": hexcol("#7A2420"), "tier": 4, "name": "劫品"},
}

# 07-codex 四角的卷云回纹（7×7 位图，# 为落笔），四角镜像复用。
CORNER_BITS = [
    "###....",
    "#..#...",
    "#...#..",
    "#....#.",
    ".#...#.",
    "..#..#.",
    "...###.",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def draw_corner(px, ox: int, oy: int, fx: int, fy: int, line, hi) -> None:
    """在 (ox,oy) 角落画 7×7 回纹；fx/fy = ±1 控制镜像方向。"""
    for r, row in enumerate(CORNER_BITS):
        for c, ch in enumerate(row):
            if ch != "#":
                continue
            x = ox + (c if fx > 0 else 6 - c)
            y = oy + (r if fy > 0 else 6 - r)
            px[x, y] = hi if (r + c) % 3 == 0 else line


def draw_frame(rarity: str) -> Image.Image:
    """96×144 深墨卡框，结构四档一致，只有线条颜色随稀有度变化。"""
    cfg = RARITY[rarity]
    line, hi, dark = cfg["line"], cfg["hi"], cfg["dark"]
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    px = img.load()

    # ① 整卡硬边 + 内圈细线（劫品按 docs/12 §3 语义四边各留一处断点）
    d.rectangle([0, 0, W - 1, H - 1], outline=BLACK)
    d.line([(1, 1), (W - 2, 1)], fill=line)
    d.line([(1, H - 2), (W - 2, H - 2)], fill=line)
    d.line([(1, 1), (1, H - 2)], fill=line)
    d.line([(W - 2, 1), (W - 2, H - 2)], fill=line)
    if rarity == "curse":
        for x, y in ((46, 1), (46, H - 2), (1, 70), (W - 2, 70)):
            d.point((x, y), fill=INK)       # 断线
            d.point((x + 1, y), fill=hi)    # 断点旁高光点

    # ② 顶部卡名条 y2–17：稍亮底 + 上下细线 + 左侧类别纹样位 + 右上阶角标
    d.rectangle([2, 2, W - 3, 17], fill=PANEL)
    d.line([(2, 2), (W - 3, 2)], fill=hi)
    d.line([(2, 17), (W - 3, 17)], fill=line)
    d.rectangle([3, 5, 11, 13], outline=dark)          # 8×8 类别纹样位（UI 层贴图）
    # 右上角稀有度阶角标：菱形 + 1–4 个小点（点数=档位）
    cx, cy = 89, 9
    d.polygon([(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)], outline=hi)
    px[cx, cy] = line
    for k in range(cfg["tier"]):
        d.point((85 + k * 2, 15), fill=hi)

    # ③ 插画区：只画 1px 内凹细边，框内保持 INK 与 84×56 插画同底、无缝衔接
    d.rectangle([ART_X - 1, ART_Y - 1, ART_X + ART_W, ART_Y + ART_H],
                outline=line)
    d.line([(ART_X - 1, ART_Y - 2), (ART_X + ART_W, ART_Y - 2)], fill=BLACK)

    # ④ 效果描述区 y79–116：留纯墨底，不画任何横线（横线是旧框被误读成排版乱的根因）
    d.line([(4, 117), (W - 5, 117)], fill=line)

    # ⑤ 底部信息条 y118–139：独立色带 + 左侧菱形 + 右侧分隔点
    d.rectangle([2, 118, W - 3, 139], fill=PANEL)
    d.line([(2, 118), (W - 3, 118)], fill=hi)
    d.line([(2, 139), (W - 3, 139)], fill=line)
    dx, dy = 10, 128
    d.polygon([(dx, dy - 4), (dx + 4, dy), (dx, dy + 4), (dx - 4, dy)], fill=hi)
    d.point((dx, dy), fill=line)
    d.point((W - 7, 124), fill=line)
    d.point((W - 7, 133), fill=line)

    # ⑥ 四角卷云回纹（07-codex 最显眼的识别特征）
    draw_corner(px, 2, 2, 1, 1, line, hi)
    draw_corner(px, W - 9, 2, -1, 1, line, hi)
    draw_corner(px, 2, H - 9, 1, -1, line, hi)
    draw_corner(px, W - 9, H - 9, -1, -1, line, hi)

    colors = set(img.getdata())
    off = sorted(colors - PSET)
    if off:
        raise AssertionError(f"{rarity} 卡框出现色板外颜色 {off[:4]}")
    return img


def zoom_sheet(tiles: list[Image.Image], cols: int, scale: int, gap: int,
               bg: tuple[int, int, int]) -> Image.Image:
    tw, th = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw * scale + (cols + 1) * gap,
                              rows * th * scale + (rows + 1) * gap), bg)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        big = t.convert("RGB").resize((tw * scale, th * scale), Image.Resampling.NEAREST)
        sheet.paste(big, (gap + c * (tw * scale + gap), gap + r * (th * scale + gap)))
    return sheet


def compose_card(frame: Image.Image, art: Image.Image) -> Image.Image:
    card = frame.copy()
    card.paste(art.convert("RGB"), (ART_X, ART_Y))
    return card


def build(write: bool) -> dict:
    lib = json.loads(LIB_PATH.read_text(encoding="utf-8"))["cards"]
    if len(lib) != 72 or len({c["id"] for c in lib}) != 72:
        raise AssertionError("卡库不是 72 张唯一 id")

    frames = {r: draw_frame(r) for r in RARITY}
    frame_files = {r: OUT_DIR / f"frame_{r}.png" for r in RARITY}
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for r, im in frames.items():
            im.save(frame_files[r], format="PNG")

    # 冻结卡面基线：只记录 sha256，绝不写入
    frozen = {}
    for p in sorted(FROZEN_DIR.glob("*.png")):
        frozen[p.name] = sha256(p)

    # 72 张整卡（新框 + 第 39 轮 84×56 插画）
    cards, card_tiles = [], []
    for c in lib:
        cid, rarity = c["id"], c.get("rarity", "common")
        if rarity not in RARITY:
            rarity = "common"
        art_path = ART_DIR / f"{cid}.png"
        if not art_path.is_file():
            raise AssertionError(f"缺 84×56 插画 {art_path}")
        with Image.open(art_path) as raw:
            art = raw.convert("RGB")
        if art.size != (ART_W, ART_H):
            raise AssertionError(f"{cid} 插画尺寸 {art.size} 不是 84×56")
        card_tiles.append(compose_card(frames[rarity], art))
        cards.append({"cardId": cid, "rarity": rarity,
                      "frame": f"frame_{rarity}.png", "art": f"{cid}.png"})

    previews = {}
    if write:
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        p1 = PREVIEW_DIR / "codex-frames-4tiers.png"
        zoom_sheet([frames[r] for r in RARITY], 4, 4, 12, (32, 32, 38)).save(p1, format="PNG")
        p2 = PREVIEW_DIR / "card-art-full-cards-codex.png"
        zoom_sheet(card_tiles, 12, 2, 10, (32, 32, 38)).save(p2, format="PNG")
        # 旧框 / 新框并排：取 4 档各 1 张
        pairs = []
        picked = {}
        for c, tile in zip(lib, card_tiles):
            r = c.get("rarity", "common")
            if r in RARITY and r not in picked:
                picked[r] = c["id"]
        for r, cid in picked.items():
            with Image.open(FROZEN_DIR / f"frame_{r}.png") as fraw:
                old = fraw.convert("RGBA")
            with Image.open(ART_DIR / f"{cid}.png") as araw:
                art = araw.convert("RGBA")
            old.paste(art, (ART_X, ART_Y))
            pairs.append(old.convert("RGB"))
            pairs.append(compose_card(frames[r], art.convert("RGB")))
        p3 = PREVIEW_DIR / "card-frame-frozen-vs-codex.png"
        zoom_sheet(pairs, 8, 3, 10, (32, 32, 38)).save(p3, format="PNG")
        previews = {k: str(v.relative_to(ROOT)) for k, v in
                    (("tiers", p1), ("fullCardsCodex", p2), ("frozenVsCodex", p3))}

    return {
        "version": 1,
        "round": 40,
        "generatedBy": "tools/build_codex_card_frames.py",
        "status": "待目检与合规确认；不得直接入库",
        "reference": "previews/ui/07-codex-gpt-image2_original.png",
        "size": [W, H],
        "artOrigin": [ART_X, ART_Y],
        "artSize": [ART_W, ART_H],
        "paletteSize": len(PALETTE),
        "structure": [
            "整卡 #12161F 深墨底，与 84×56 插画同色无缝衔接",
            "1px 黑硬边 + 1px 稀有度内圈细线（劫品四边断点）",
            "y2–17 顶部卡名条（#2A3140）：左 8×8 类别纹样位 + 右上菱形阶角标",
            "x5–90 / y18–75 插画区 1px 内凹细边，框内不画任何内容",
            "y79–116 效果描述区留纯墨底，不画占位横线",
            "y118–139 底部信息条：独立色带 + 左侧菱形 + 上下分隔线",
            "四角 7×7 卷云回纹，稀有度只换线条颜色、结构四档一致",
        ],
        "noTextInPng": True,
        "frames": [
            {"rarity": r, "file": str(frame_files[r].relative_to(ROOT)),
             "sha256": sha256(frame_files[r]) if frame_files[r].is_file() else None,
             "lineColor": "#%02X%02X%02X" % RARITY[r]["line"],
             "hiColor": "#%02X%02X%02X" % RARITY[r]["hi"],
             "tier": RARITY[r]["tier"]}
            for r in RARITY
        ],
        "cardsCombo": len(cards),
        "cards": cards,
        "frozenCardAssetsSha256": frozen,
        "previews": previews,
        "oldPreviewRetained": str(OLD_PREVIEW.relative_to(ROOT)) if OLD_PREVIEW.is_file() else None,
        "boundary": "assets/ui/cards/ 10 张冻结卡面与 docs/12 均未改动；候选框仅在 "
                    "previews/card_frames_codex/ 与网页验证层以 ?frame=codex 供对照；"
                    "Q17 未拍板、GUI F5 未跑、数值 / 概率 / 权重 / 规则未改",
    }


def check() -> str:
    report = build(write=False)
    for f in report["frames"]:
        p = ROOT / f["file"]
        if not p.is_file():
            raise AssertionError(f"缺候选卡框 {p}")
        with Image.open(p) as im:
            if list(im.size) != [W, H] or im.mode != "RGB":
                raise AssertionError(f"{p} 尺寸或模式不对")
            off = sorted(set(im.convert("RGB").getdata()) - PSET)
            if off:
                raise AssertionError(f"{p} 色板外颜色 {off[:4]}")
        if sha256(p) != f["sha256"]:
            raise AssertionError(f"{p} 与报告 sha256 不一致")
    now = {p.name: sha256(p) for p in sorted(FROZEN_DIR.glob("*.png"))}
    if now != report["frozenCardAssetsSha256"]:
        raise AssertionError("冻结卡面 assets/ui/cards/ 被改动，违反候选不覆盖基线纪律")
    for p in (PREVIEW_DIR / "codex-frames-4tiers.png",
              PREVIEW_DIR / "card-art-full-cards-codex.png",
              PREVIEW_DIR / "card-frame-frozen-vs-codex.png"):
        if not p.is_file():
            raise AssertionError(f"缺目检预览 {p}")
    return (f"4/4 候选卡框 96×144 / 色板外颜色 0 / 冻结卡面 10 张 sha256 未变 / "
            f"72 张整卡对位 / 3 张目检预览齐备")


def main() -> int:
    ap = argparse.ArgumentParser(description="按 07-codex 重绘 4 档卡框（候选）")
    ap.add_argument("--check", action="store_true", help="只校验，不写文件")
    args = ap.parse_args()
    try:
        if args.check:
            print("PASS | " + check())
            return 0
        report = build(write=True)
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE | {REPORT_PATH.relative_to(ROOT)}")
        print(f"INFO  | 4/4 候选卡框；72 张整卡；色板 {report['paletteSize']} 色；"
              f"冻结卡面 {len(report['frozenCardAssetsSha256'])} 张仅记录 sha256")
        for k, v in report["previews"].items():
            print(f"INFO  | 预览 {k}: {v}")
        print("PASS | " + check())
    except Exception as exc:
        print(f"FAIL | {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
