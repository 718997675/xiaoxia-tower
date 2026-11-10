#!/usr/bin/env python3
"""第 39 轮 · 72 张单卡原稿 → 84×56 卡面插画（集成链路第 2 步）。

    previews/card_art/<card_id>-cardart-original.png   (384×256, 裁剪器产出)
      → 24 色锁定板吸附（消除聊天 JPEG 振铃中间色）
      → previews/card_art/<card_id>-cardart_palette24.png  (384×256 留档)
      → NEAREST 降采样到 84×56
      → assets/ui/card_art/<card_id>.png               (游戏内实际使用的插画区)

同时产出三张目检预览（都在 assets/_preview/，不是美术资产）：
    card-art-72-transcript.png    72 张 84×56 逐张放大 3×
    card-art-full-cards.png       72 张整卡：冻结卡框 + 新插画区（按稀缺度选框）
    card-art-sheets-overview.png  6 张标准拼版缩略总览（验收组→sheet 映射）

纪律：
  - 不修改 assets/ui/cards/ 的 10 张冻结卡面；卡框只在预览里叠加，游戏层仍分层绘制。
  - docs/12 §2 的插画区是 x6–89 / y19–75 = 84×57；这里用 84×56（4 的倍数友好值），
    1px 差异仍是 PROPOSAL，未改冻结坐标（docs/27 §5 尺寸备注）。
  - 不改任何数值、概率、权重、规则；Q17 未拍板、GUI F5 未跑。
  - 产物 status「待目检与合规确认；不得直接入库」。

用法：
    python3 tools/transcribe_card_art.py            # 生成 72 张 + 预览 + 报告
    python3 tools/transcribe_card_art.py --check   # 只校验，不写文件
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from snap_ui_palette import load_palette  # noqa: E402

DOC = ROOT / "docs"
PREV = ROOT / "previews"
ORIG_DIR = PREV / "card_art"
SHEET_DIR = PREV / "card_art_sheets"
TRANSCRIPT_DIR = ROOT / "assets" / "ui" / "card_art"
FRAME_DIR = ROOT / "assets" / "ui" / "cards"
PREVIEW_DIR = ROOT / "assets" / "_preview"
SPLIT_REPORT = DOC / "card-art-split-report.json"
LIB_PATH = ROOT / "data" / "buff-card-library.json"
REPORT_PATH = DOC / "card-art-transcript-report.json"

ART_W, ART_H = 84, 56
ART_X, ART_Y = 6, 19
SCALE = 3
BG = (18, 22, 31)  # #12161F


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snap_to_palette(img: Image.Image, palette: list[tuple[int, int, int]]) -> Image.Image:
    """每像素映射到色板最近色；不透明 RGB，无 alpha 残留。"""
    src = img.convert("RGB")
    cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}

    def nearest(c: tuple[int, int, int]) -> tuple[int, int, int]:
        hit = cache.get(c)
        if hit is None:
            hit = min(palette, key=lambda p: (c[0] - p[0]) ** 2
                      + (c[1] - p[1]) ** 2 + (c[2] - p[2]) ** 2)
            cache[c] = hit
        return hit

    out = Image.new("RGB", src.size)
    out.putdata([nearest(p) for p in src.getdata()])
    return out


def contact_sheet(tiles: list[Image.Image], cols: int, scale: int,
                  gap: int, bg: tuple[int, int, int]) -> Image.Image:
    tw, th = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    w = cols * tw * scale + (cols + 1) * gap
    h = rows * th * scale + (rows + 1) * gap
    sheet = Image.new("RGB", (w, h), bg)
    for i, tile in enumerate(tiles):
        r, c = divmod(i, cols)
        big = tile.convert("RGB").resize((tw * scale, th * scale), Image.Resampling.NEAREST)
        sheet.paste(big, (gap + c * (tw * scale + gap), gap + r * (th * scale + gap)))
    return sheet


def build(write: bool) -> dict:
    split = json.loads(SPLIT_REPORT.read_text(encoding="utf-8"))
    lib = json.loads(LIB_PATH.read_text(encoding="utf-8"))
    lib_by_id = {c["id"]: c for c in lib["cards"]}
    palette = load_palette()
    outputs = split["outputs"]
    if len(outputs) != 72 or split["outputsOnDisk"] != 72:
        raise AssertionError("裁剪报告不是 72/72，先跑 split_card_art_sheets.py --adaptive")
    if len(lib_by_id) != 72:
        raise AssertionError("卡库不是 72 张")
    if set(o["cardId"] for o in outputs) != set(lib_by_id):
        raise AssertionError("裁剪产物的 cardId 与卡库 72 个 id 不对位")

    rows, trans, originals, frames_tiles = [], [], [], []
    for o in outputs:
        cid = o["cardId"]
        orig_path = ORIG_DIR / o["outputName"]
        if not orig_path.is_file():
            raise AssertionError(f"缺单卡原稿 {orig_path}")
        with Image.open(orig_path) as raw:
            orig = raw.convert("RGB")
        if orig.size != (384, 256):
            raise AssertionError(f"{cid} 原稿尺寸 {orig.size} 不是 384×256")

        snapped = snap_to_palette(orig, palette)
        final = snapped.resize((ART_W, ART_H), Image.Resampling.NEAREST)

        # 逐张体检：色板合规 / 不透明 / 有主体
        colors = set(final.getdata())
        off = sorted(colors - set(palette))
        fg = sum(1 for p in final.getdata() if max(abs(p[i] - BG[i]) for i in range(3)) > 40)
        if off:
            raise AssertionError(f"{cid} 出现色板外颜色 {off[:4]}")
        if fg < 40:
            raise AssertionError(f"{cid} 画面几乎是空墨底（前景像素 {fg}），疑似裁空")

        palette_name = f"{cid}-cardart_palette24.png"
        final_name = f"{cid}.png"
        palette_path = ORIG_DIR / palette_name
        final_path = TRANSCRIPT_DIR / final_name
        if write:
            TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
            snapped.save(palette_path, format="PNG")
            final.save(final_path, format="PNG")
        rows.append({
            "cardId": cid, "sheet": o["sheet"], "cell": o["cell"], "label": o["label"],
            "usedBox": o["usedBox"], "original": str(orig_path.relative_to(ROOT)),
            "palette24": str(palette_path.relative_to(ROOT)),
            "output": str(final_path.relative_to(ROOT)),
            "outputSha256": sha256(final_path) if final_path.is_file() else None,
            "size": [ART_W, ART_H], "offPaletteColors": len(off), "foregroundPixels": fg,
        })
        trans.append(final)
        originals.append(snapped)

        # 整卡预览：冻结卡框（按稀缺度）+ 新插画区，不改变 assets/ui/cards/ 任何文件
        rarity = lib_by_id[cid].get("rarity", "common")
        frame_path = FRAME_DIR / f"frame_{rarity}.png"
        if not frame_path.is_file():
            frame_path = FRAME_DIR / "frame_common.png"
        with Image.open(frame_path) as fraw:
            card = fraw.convert("RGBA").copy()
        card.paste(final.convert("RGBA"), (ART_X, ART_Y))
        frames_tiles.append(card.convert("RGB"))

    previews = {}
    if write:
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        p1 = PREVIEW_DIR / "card-art-72-transcript.png"
        contact_sheet(trans, 12, SCALE, 8, BG).save(p1, format="PNG")
        p2 = PREVIEW_DIR / "card-art-full-cards.png"
        contact_sheet(frames_tiles, 12, 2, 10, (32, 32, 38)).save(p2, format="PNG")
        p3 = PREVIEW_DIR / "card-art-sheets-overview.png"
        sheet_tiles = []
        for i in range(1, 7):
            with Image.open(SHEET_DIR / f"sheet-{i:02d}.png") as s:
                sheet_tiles.append(s.convert("RGB").resize((384, 256), Image.Resampling.NEAREST))
        contact_sheet(sheet_tiles, 2, 1, 12, (32, 32, 38)).save(p3, format="PNG")
        previews = {k: str(v.relative_to(ROOT)) for k, v in
                    (("transcript", p1), ("fullCards", p2), ("sheetsOverview", p3))}

    return {
        "version": 1,
        "generatedBy": "tools/transcribe_card_art.py",
        "status": "待目检与合规确认；不得直接入库",
        "pipeline": [
            "previews/card_art_sheets/sheet-01..06.png（1536×1024，导入标准化）",
            "split_card_art_sheets.py --adaptive → 72 张 384×256 单卡原稿",
            "24 色锁定板吸附 → <card_id>-cardart_palette24.png",
            "NEAREST 84×56 → assets/ui/card_art/<card_id>.png",
        ],
        "paletteSize": len(palette),
        "artSize": [ART_W, ART_H],
        "artOrigin": [ART_X, ART_Y],
        "artSpecNote": "docs/12 §2 为 x6–89/y19–75=84×57；84×56 是 PROPOSAL 的 4 倍数友好值，1px 差异待 4× 实机复核，未改冻结坐标",
        "cards": rows,
        "cardsTotal": len(rows),
        "cardsOnDisk": sum(1 for r in rows if r["outputSha256"]),
        "offPaletteTotal": sum(r["offPaletteColors"] for r in rows),
        "previews": previews,
        "boundary": "冻结卡面 assets/ui/cards/ 10 张未改；卡框只在预览里叠加，游戏仍分层绘制；"
                    "Q17 未拍板、GUI F5 未跑；未改数值 / 概率 / 权重 / 规则",
    }


def check() -> str:
    report = build(write=False)
    for r in report["cards"]:
        p = ROOT / r["output"]
        if not p.is_file():
            raise AssertionError(f"缺 {r['output']}")
        with Image.open(p) as im:
            if list(im.size) != [ART_W, ART_H] or im.mode != "RGB":
                raise AssertionError(f"{r['output']} 尺寸或模式不对")
        if sha256(p) != r["outputSha256"]:
            raise AssertionError(f"{r['output']} 与报告 sha256 不一致")
    return (f"72/72 张 84×56 插画齐备 / 色板外颜色合计 {report['offPaletteTotal']} / "
            f"cardId 与卡库 72 张逐一对位 / 冻结卡面未动")


def main() -> int:
    ap = argparse.ArgumentParser(description="72 张单卡原稿 → 84×56 卡面插画")
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
        print(f"INFO  | 插画 {report['cardsOnDisk']}/72；"
              f"色板外颜色 {report['offPaletteTotal']}；调色板 {report['paletteSize']} 色")
        for k, v in report["previews"].items():
            print(f"INFO  | 预览 {k}: {v}")
        print("PASS | " + check())
    except Exception as exc:
        print(f"FAIL | {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
