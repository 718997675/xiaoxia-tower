#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
塔层背景四深度层程序化重绘器（第 29 轮，零出图积分、可复现）

用途：把 docs/20 A 组的 4 类塔层背景，落成 Godot 可直接叠层的
      L1 远景 / L2 中景 / L3 地面 / L4 前景 四张独立透明 PNG（480x270 逻辑像素）。

口径（R55 / docs/03 §4 / docs/21 §8）：
  - 外部模型出的 A1–A4 只算【构图与配色参考稿】，绝不把 AI 原图裁切当入库资源；
    本脚本用 24 色锁定板 + 1px 纯黑描边 + 硬边几何色块【逐像素重绘】。
  - 每层独立可切：只在自己的 y 带 / 边缘条带内绘制，其余全透明，叠起来还原整幅。
  - 四层之间不许半透明 / 雾气 / 渐变，只许色阶 + 1px 黑描边分界。
  - 深墨占比守 docs/20 §4.1 的 R22 约束：L1 暗像素 <20%、中央战斗区暗像素 <30%、
    L3 最实最亮、L4 前景剪影 <10%。
  - 视差系数是 PROPOSAL，未实测；贴图内存 / 实机对比度一律待实测。

用法：
  python3 tools/build_bg_layers.py
  python3 tools/build_bg_layers.py --check    # 只复算已产出 PNG 的指标

产出：
  assets/bg/<scene>/bg_<scene>_L1..L4.png    4 类 x 4 层 = 16 张
  assets/bg/<scene>/bg_<scene>_composite.png 4 张合成目检图
  assets/bg/<scene>/bg_<scene>.json          层清单 / 契约 / 状态
  assets/_preview/bg_layers_contact_sheet.png
  docs/bg-layers-report.json

规格来源：docs/20-场景与Boss外发提示词.md §2.3 / §4.1、docs/04-像素国风规格修订.md、
          docs/asset-manifest-pixel.json、docs/reference-art-report.json（指标定义）
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BG_DIR = ROOT / "assets/bg"
PREVIEW_DIR = ROOT / "assets/_preview"
REPORT_PATH = ROOT / "docs/bg-layers-report.json"

W, H = 480, 270
L1_END, L2_END = 68, 202                  # 上 1/4 / 中 1/2 / 下 1/4
EDGE = 24                                # 左右 5%（480 * 0.05 = 24）
BOTTOM_L4 = 243                          # 最下 10%（270 * 0.9 = 243）
COMBAT = (int(W * 0.20), int(H * 0.35), int(W * 0.80), int(H * 0.75))
# 独立可切的硬判据：L1/L2/L3 只能在本层 y 带内出现不透明像素。
# L4 是覆盖在最上层的前景剪影，按设计可跨 L2/L3 带，不参与本判据。
BANDS = {"L1": (0, L1_END), "L2": (L1_END, L2_END), "L3": (L2_END, H)}

PALETTE_HEX = [
    "#12161F", "#2A3140", "#4A5568",
    "#8A8268", "#C9BFA3", "#E8DFC8",
    "#2F6E6A", "#5FA8A0", "#9BD4CC",
    "#7A2420", "#C8453B", "#E8806F",
    "#8A6520", "#D9A441", "#F2D089",
    "#4A3A6B", "#8A6FC4", "#C0A8E0",
    "#000000", "#FFFFFF",
]
PALETTE = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in PALETTE_HEX}
# docs/reference-art-report.json：darkSet = 0.299R+0.587G+0.114B < 60 的三个板色
DARK_SET = {(0, 0, 0), (18, 22, 31), (42, 49, 64)}
INK_SET = {(0, 0, 0), (18, 22, 31), (42, 49, 64), (74, 85, 104)}
PAPER_SET = {(138, 130, 104), (201, 191, 163), (232, 223, 200)}
TRANSPARENT = (0, 0, 0, 0)


def C(h: str) -> tuple[int, int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


INK = C("#000000")
MO1, MO2, MO3 = C("#12161F"), C("#2A3140"), C("#4A5568")
PAPER_DD, PAPER_D, PAPER = C("#8A8268"), C("#C9BFA3"), C("#E8DFC8")
JADE_D, JADE, JADE_L = C("#2F6E6A"), C("#5FA8A0"), C("#9BD4CC")
RED_D, RED, RED_L = C("#7A2420"), C("#C8453B"), C("#E8806F")
GOLD_D, GOLD, GOLD_L = C("#8A6520"), C("#D9A441"), C("#F2D089")
VIO_D, VIO, VIO_L = C("#4A3A6B"), C("#8A6FC4"), C("#C0A8E0")

SCENES = {
    "bg_normal": {"ref": "A1-bgnormal-gpt-image2_palette24.png",
                  "floors": "1-3", "tone": "常规塔层"},
    "bg_rest": {"ref": "A2R-bgrest-gpt-image2_palette24.png",
                "floors": "3/6/8", "tone": "喘息层（全塔最亮）"},
    "bg_high": {"ref": "A3-bghigh-gpt-image2_palette24.png",
                "floors": "7", "tone": "高层复合敌群"},
    "bg_boss": {"ref": "A4-bgboss-gpt-image2_palette24.png",
                "floors": "5/9", "tone": "Boss 层"},
}


def blank() -> Image.Image:
    return Image.new("RGBA", (W, H), TRANSPARENT)


def rect(d, box, fill, outline=INK):
    d.rectangle(box, fill=fill)
    if outline:
        d.rectangle(box, outline=outline, width=1)


def poly(d, pts, fill, outline=INK):
    d.polygon(pts, fill=fill)
    if outline:
        d.line(list(pts) + [pts[0]], fill=outline, width=1)


def line(d, pts, fill, width=3):
    d.line(pts, fill=fill, width=width)


def tower(d, x, top, w, h, body, roof):
    """远塔剪影：塔身 + 上下两道檐 + 尖顶，全部硬边几何块，不跨 L1 下边界。"""
    rect(d, (x, top + 10, x + w, top + h), body, INK)
    rect(d, (x - 5, top + 10, x + w + 5, top + 16), roof, INK)
    rect(d, (x - 3, top + h - 12, x + w + 3, top + h - 7), roof, INK)
    rect(d, (x + w // 2 - 3, top, x + w // 2 + 3, top + 10), roof, INK)


def draw_l1(scene: str) -> Image.Image:
    im = blank()
    d = ImageDraw.Draw(im)
    rest = scene == "bg_rest"
    boss = scene == "bg_boss"
    high = scene == "bg_high"
    # 下边界取 L1_END-1：Pillow rectangle 右/下边界是【含】的，
    # 写到 L1_END 会让 L1 多占 L2 的首行，四层就不能严格独立切图。
    rect(d, (0, 0, W, L1_END - 1), PAPER if rest else PAPER_D, None)
    if rest:
        # 云带：分段色块 + 1px 黑描边，禁止柔边
        for i, (x, y, cw) in enumerate(((24, 22, 96), (152, 12, 120),
                                        (300, 26, 88), (392, 16, 64))):
            rect(d, (x, y, x + cw, y + 12), PAPER if i % 2 else PAPER_D, INK)
        line(d, [(0, 50), (W, 50)], PAPER_DD, 3)
    else:
        positions = (36, 150, 300, 396) if high else ((44, 196, 344) if not boss else (72, 320))
        for i, x in enumerate(positions):
            tower(d, x, 12 + (i % 2) * 6, 36 if not boss else 48,
                  46, PAPER_DD if not boss else MO3,
                  MO3 if not boss else MO2)
        if high:
            poly(d, [(0, 54), (96, 26), (180, 54), (278, 30), (380, 54),
                     (W, 34), (W, L1_END - 1), (0, L1_END - 1)], PAPER_DD, INK)
        if boss:
            # 硬边几何半环背光（阶梯色块，不是辉光 / 渐变）
            for k, col in enumerate((GOLD_D, GOLD, GOLD_L)):
                y = 20 + k * 8
                rect(d, (172 - k * 10, y, 308 + k * 10, y + 7), col, INK)
    # L1 / L2 水平分界（色阶 + 1px 黑描边，不许渐变）
    line(d, [(0, L1_END - 2), (W, L1_END - 2)], MO3, 2)
    return im


def draw_l2(scene: str) -> Image.Image:
    im = blank()
    d = ImageDraw.Draw(im)
    rest = scene == "bg_rest"
    boss = scene == "bg_boss"
    high = scene == "bg_high"
    rect(d, (0, L1_END, W, L2_END - 1), PAPER if rest else PAPER_D, None)
    # 立柱：窄矩形，彼此留浅色缝隙；战斗区以浅宣纸为主
    if boss:
        xs = (54, 400)
        width = 26
    elif rest:
        xs = (72, 384)
        width = 12
    elif high:
        xs = (28, 108, 188, 268, 348, 428)
        width = 15
    else:
        xs = (56, 172, 288, 404)
        width = 18
    pillar_col = PAPER_DD if not boss else MO3
    for i, x in enumerate(xs):
        top = L1_END + (6 if i % 2 == 0 else 10)
        rect(d, (x, top, x + width, L2_END - 6), pillar_col, INK)
        rect(d, (x - 4, top - 4, x + width + 4, top + 4),
             MO3 if boss else PAPER_DD, INK)
        if high and i % 3 == 1:                 # 破损柱：缺口靠硬边色块
            rect(d, (x + 4, L1_END + 60, x + width - 2, L1_END + 78),
                 PAPER_D, None)
    # 横向栏杆 / 经幡
    rail_y = L1_END + 74
    line(d, [(0, rail_y), (W, rail_y)], PAPER_DD if rest else MO3, 3)
    for i, x in enumerate((96, 216, 336)):
        col = (JADE if i % 2 == 0 else RED_D)
        rect(d, (x, rail_y - 2, x + 14, rail_y + 20), col, INK)
        line(d, [(x + 7, rail_y + 20), (x + 7, rail_y + 28)], GOLD_D, 3)
    if boss:
        # 朱砂印文（Boss 层识别符），不用文字
        rect(d, (220, L1_END + 40, 260, L1_END + 80), RED_D, INK)
        line(d, [(226, L1_END + 60), (254, L1_END + 60)], RED_L, 3)
        line(d, [(240, L1_END + 46), (240, L1_END + 74)], RED_L, 3)
    if high:
        for i, x in enumerate((60, 150, 240, 330, 420)):
            rect(d, (x, L2_END - 34, x + 12, L2_END - 16), MO3, INK)
    # L2 / L3 分界
    line(d, [(0, L2_END - 2), (W, L2_END - 2)], MO3, 2)
    return im


def draw_l3(scene: str) -> Image.Image:
    im = blank()
    d = ImageDraw.Draw(im)
    rest = scene == "bg_rest"
    boss = scene == "bg_boss"
    rect(d, (0, L2_END, W, H - 1), PAPER if rest else PAPER_D, None)
    # 石阶平台：下部 1/4 是全场最实最亮的一带
    steps = 3 if (rest or boss) else 5
    for k in range(steps):
        y = L2_END + 6 + k * 11
        rect(d, (0 + k * 6, y, W - k * 6, y + 9),
             PAPER if k % 2 == 0 else PAPER_D, INK)
    # 平台中央纹样（硬边，不跨层）
    line(d, [(W // 2 - 40, H - 12), (W // 2 + 40, H - 12)],
         PAPER_DD if rest else MO3, 3)
    if boss:
        rect(d, (188, L2_END + 2, 292, H - 6), GOLD_D, INK)
        rect(d, (196, L2_END + 10, 284, H - 12), PAPER_D, INK)
    if scene == "bg_high":
        for x in (72, 216, 360):
            line(d, [(x, L2_END + 8), (x + 18, H - 8)], MO3, 2)
    return im


def draw_l4(scene: str) -> Image.Image:
    im = blank()
    d = ImageDraw.Draw(im)
    rest = scene == "bg_rest"
    boss = scene == "bg_boss"
    col = MO3 if rest else (MO1 if boss else MO2)
    # 左右边缘 5% 窄条（只在 L2/L3 区间，避免盖住 L1 远景）
    if not rest:
        for x0, x1 in ((0, 8), (W - 8, W)):
            rect(d, (x0, L1_END, x1, BOTTOM_L4), col, INK)
    # 最下缘窄条 + 前景剪影块，总面积 <10%
    rect(d, (0, BOTTOM_L4, W, BOTTOM_L4 + 6), col, INK)
    if boss:
        rect(d, (0, BOTTOM_L4 - 16, 54, BOTTOM_L4), col, INK)
        rect(d, (W - 54, BOTTOM_L4 - 16, W, BOTTOM_L4), col, INK)
    elif not rest:
        for x in (36, 228, 420):
            rect(d, (x, BOTTOM_L4 - 10, x + 24, BOTTOM_L4), col, INK)
    else:
        rect(d, (W // 2 - 24, BOTTOM_L4 - 6, W // 2 + 24, BOTTOM_L4), PAPER_DD, INK)
    return im


DRAWERS = {"L1": draw_l1, "L2": draw_l2, "L3": draw_l3, "L4": draw_l4}
LEVEL_NOTE = {
    "L1": "远景：y 0-68，浅宣纸底 + 远塔 / 云带 / 半环背光",
    "L2": "中景：y 68-202，立柱 / 栏杆 / 经幡，浅色留缝",
    "L3": "地面：y 202-270，石阶平台，全场最实最亮",
    "L4": "前景：最下 10% 条带 + 左右 5% 边缘剪影，面积 <10%",
}


def metrics(im: Image.Image, band: tuple[int, int] | None = None) -> dict:
    px = im.load()
    w, h = im.size
    colors, alphas, opaque = set(), set(), 0
    dark = ink = paper = stray = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            alphas.add(a)
            if a > 0:
                opaque += 1
                c = (r, g, b)
                colors.add(c)
                dark += c in DARK_SET
                ink += c in INK_SET
                paper += c in PAPER_SET
                if band and not (band[0] <= y < band[1]):
                    stray += 1
    return {
        "size": [w, h],
        "band": list(band) if band else None,
        "bandStrayPixels": stray,
        "coverage": round(opaque / (w * h), 4),
        "opaquePixels": opaque,
        "usedColors": len(colors),
        "outOfPalette": len([c for c in colors if c not in PALETTE]),
        "semiAlphaLevels": sum(1 for a in alphas if 0 < a < 255),
        "darkRatio": round(dark / max(opaque, 1), 4),
        "inkGroupRatio": round(ink / max(opaque, 1), 4),
        "paperGroupRatio": round(paper / max(opaque, 1), 4),
    }


def combat_metrics(im: Image.Image) -> dict:
    x0, y0, x1, y1 = COMBAT
    px = im.load()
    total = dark = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            total += 1
            r, g, b, a = px[x, y]
            if a > 0 and (r, g, b) in DARK_SET:
                dark += 1
    return {"zone": [x0, y0, x1, y1],
            "darkPixelRatio": round(dark / total, 4),
            "r22Proxy": "HIGH" if dark / total >= 0.60 else
                        "MEDIUM" if dark / total >= 0.30 else "LOW"}


def composite(layers: dict[str, Image.Image]) -> Image.Image:
    out = Image.new("RGBA", (W, H), PAPER)
    for key in ("L1", "L2", "L3", "L4"):
        out.alpha_composite(layers[key])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只复算已有 PNG，不写文件")
    args = ap.parse_args()
    scenes_report = []
    thumbs = []

    for scene, meta in SCENES.items():
        folder = BG_DIR / scene
        folder.mkdir(parents=True, exist_ok=True)
        layers = {k: fn(scene) for k, fn in DRAWERS.items()} if not args.check else {
            k: Image.open(folder / f"{scene}_{k}.png").convert("RGBA")
            for k in DRAWERS}
        per = {}
        for key, im in layers.items():
            if not args.check:
                im.save(folder / f"{scene}_{key}.png")
            m = metrics(im, BANDS.get(key))
            per[key] = {"file": f"{scene}_{key}.png", "note": LEVEL_NOTE[key], **m}

        comp = composite(layers)
        if not args.check:
            comp.convert("RGB").save(folder / f"{scene}_composite.png")
        thumbs.append(comp.convert("RGB"))
        cm = combat_metrics(comp)

        l4_area = per["L4"]["opaquePixels"] / (W * H)
        entry = {
            "scene": scene,
            "reference": meta["ref"],
            "referenceRole": "构图 / 配色依据，不裁切 AI 原图入库（R55）",
            "floors": meta["floors"],
            "tone": meta["tone"],
            "layers": per,
            "l4AreaRatio": round(l4_area, 4),
            "l4Under10Percent": l4_area < 0.10,
            "combatZone": cm,
            "l1DarkUnder20Percent": per["L1"]["darkRatio"] < 0.20,
            "combatDarkUnder30Percent": cm["darkPixelRatio"] < 0.30,
            "outOfPaletteTotal": sum(v["outOfPalette"] for v in per.values()),
            "semiAlphaTotal": sum(v["semiAlphaLevels"] for v in per.values()),
        }
        scenes_report.append(entry)

        if not args.check:
            engine = {
                "version": 1,
                "id": scene,
                "kind": "background",
                "logicalResolution": [480, 270],
                "integerScale": 4,
                "layerSize": [W, H],
                "palette": PALETTE_HEX,
                "layers": [
                    {"id": key, "file": f"{scene}_{key}.png", "note": LEVEL_NOTE[key],
                     "parallaxFactor": {"L1": 0.15, "L2": 0.45, "L3": 1.0,
                                        "L4": 1.30}[key]}
                    for key in ("L1", "L2", "L3", "L4")
                ],
                "composite": f"{scene}_composite.png",
                "parallaxFactorsStatus": "PROPOSAL 占位，未实测；不得当已验证的平衡结论",
                "pipeline": "tools/build_bg_layers.py（24 色板程序化重绘，0 出图积分）",
                "status": "待目检与合规确认；不得直接入库",
            }
            (folder / f"{scene}.json").write_text(
                json.dumps(engine, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.check:
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        sheet = Image.new("RGB", (W, H * len(thumbs)), PAPER[:3])
        for i, t in enumerate(thumbs):
            sheet.paste(t, (0, i * H))
        sheet.save(PREVIEW_DIR / "bg_layers_contact_sheet.png")

        report = {
            "round": 29,
            "tool": "tools/build_bg_layers.py",
            "scope": "A1 / A2R / A3 / A4 四类塔层背景 x 四深度层",
            "pipeline": "程序化像素重绘（R55：AI 参考稿只作构图依据，不裁切入库）",
            "namingContract": "^bg_[a-z0-9_]+_L[1-4]$",
            "layerSize": [W, H],
            "paletteSource": "docs/asset-manifest-pixel.json（24 色锁定板）",
            "darkSetDefinition": "docs/reference-art-report.json：luma < 60 的三个板色",
            "scenes": scenes_report,
            "totals": {
                "scenes": len(scenes_report),
                "layers": len(scenes_report) * 4,
                "composites": len(thumbs),
            "bandStrayTotal": sum(s["layers"][k]["bandStrayPixels"]
                                  for s in scenes_report for k in BANDS),
            "outOfPaletteTotal": sum(s["outOfPaletteTotal"] for s in scenes_report),
            "semiAlphaTotal": sum(s["semiAlphaTotal"] for s in scenes_report),
                "l4Under10PercentAll": all(s["l4Under10Percent"] for s in scenes_report),
                "combatDarkUnder30PercentAll": all(
                    s["combatDarkUnder30Percent"] for s in scenes_report),
            },
            "boundaries": [
                "四层仅做静态可导入资源，未接 Godot 场景、未做 Parallax2D 节点",
                "视差系数 0.15/0.45/1.0/1.30 是 PROPOSAL 占位，待实测",
                "R22 实机对比度、贴图内存、4x 排版、层间是否可独立切图需人工目检（机器不判）",
                "Q17 未拍板、GUI F5 未跑、正式战斗工程未建",
                "不修改 docs/20 冻结规格正文、docs/06、docs/asset-manifest-pixel.json",
            ],
            "status": "HEADLESS 静态指标自检；画面未验证",
        }
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(json.dumps(report["totals"], ensure_ascii=False, indent=2))
        for s in scenes_report:
            print(f"  {s['scene']:<12} L1暗 {s['layers']['L1']['darkRatio']:.3f}  "
                  f"战斗区暗 {s['combatZone']['darkPixelRatio']:.3f} "
                  f"({s['combatZone']['r22Proxy']})  L4占比 {s['l4AreaRatio']:.3f}  "
                  f"越界色 {s['outOfPaletteTotal']}  半透明 {s['semiAlphaTotal']}")
    else:
        print(json.dumps([{"scene": s["scene"],
                           "outOfPaletteTotal": s["outOfPaletteTotal"],
                           "semiAlphaTotal": s["semiAlphaTotal"]}
                          for s in scenes_report], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
