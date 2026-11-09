#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UI 参考稿资产化器（第 31 轮）：把 00-anchor ~ 08-icons 九张 gpt-image2 回稿
做成可复用的 UI 底板 / 组件图库。

背景：用户指出 previews/ui/ 下 *-gpt-image2_* 全部是其本人生成的高质量回稿，
第 29/30 轮只用了 A/B/C 七张，00~08 九张被误判为「本轮用不到」。本脚本把九张
全部纳入，产出整屏底板 + 按相对坐标切出的可复用组件，并给出独立目检页。

口径：
  - 只读用户原稿，绝不改写；08-icons 的 gptimage.dev 水印在转录时局部修补。
  - 全部输出吸附回 24 色锁定板；组件保留硬边，不做抗锯齿。
  - 产出落在 assets/ui/reference/ 新目录，不触碰 assets/ui/icons（47 个 R23 冻结
    ID）与 assets/ui/cards 的既有契约；qc_sprites 的 SCAN_DIRS / LOOSE_SCAN 不覆盖本目录。
  - 裁切框是相对比例估算值，需人工目检微调；报告里如实标注，不冒充精确对位。
  - status 沿用「待目检与合规确认；不得直接入库」；Q17 / GUI F5 未过。

用法：
  python3 tools/build_ui_reference_assets.py
  python3 tools/build_ui_reference_assets.py --check

产出：
  assets/ui/reference/ui_<stem>_full.png              原尺寸去水印 + 24 色复核
  assets/ui/reference/ui_<stem>_panel.png             16:9 归一 960x540 底板
  assets/ui/reference/ui_<stem>_<component>.png       组件切图
  assets/ui/reference/ui_icons_row_01..06.png         08-icons 六行图标带
  assets/ui/reference/ui_icons_<row>_<col>.png        逐格图标（等分 + 内容 bbox 精修）
  assets/ui/reference/ui_reference_manifest.json      每个文件的源稿 / 裁切框 / 用途
  previews/ui-reference-overview.html                 独立零依赖目检页
  docs/ui-reference-assets-report.json                汇总报告
"""
from __future__ import annotations

import argparse
import base64
import io
import json
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "previews" / "ui"
OUT = ROOT / "assets" / "ui" / "reference"
PREVIEW = ROOT / "previews" / "ui-reference-overview.html"
REPORT = ROOT / "docs" / "ui-reference-assets-report.json"
MANIFEST = OUT / "ui_reference_manifest.json"

PALETTE_HEX = [
    "#12161F", "#2A3140", "#4A5568",
    "#8A8268", "#C9BFA3", "#E8DFC8",
    "#2F6E6A", "#5FA8A0", "#9BD4CC",
    "#7A2420", "#C8453B", "#E8806F",
    "#8A6520", "#D9A441", "#F2D089",
    "#4A3A6B", "#8A6FC4", "#C0A8E0",
    "#000000", "#FFFFFF",
]


def rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


PALETTE = [rgb(h) for h in PALETTE_HEX]
DARK_BG = rgb("#12161F")
STATUS = "待目检与合规确认；不得直接入库"

# 九张稿：标签 + 建议用途 + 组件（相对坐标 x0,y0,x1,y1）
SPECS = {
    "00-anchor": {
        "label": "视觉锚定 / 设计系统",
        "use": "色板、纹样、四层边框、界面语汇；可直接做 NinePatch 边框与机制图标母版",
        "components": [
            ("palette_strip", (0.02, 0.02, 0.24, 0.95), "24 色阶梯色板条"),
            ("sigil_01", (0.26, 0.09, 0.48, 0.23), "技能伤害纹样"),
            ("sigil_02", (0.26, 0.24, 0.48, 0.38), "属性提升纹样"),
            ("sigil_03", (0.26, 0.38, 0.48, 0.52), "机制改变纹样"),
            ("sigil_04", (0.26, 0.52, 0.48, 0.65), "资源灵力纹样"),
            ("sigil_05", (0.26, 0.65, 0.48, 0.78), "生存回复纹样"),
            ("sigil_06", (0.26, 0.78, 0.48, 0.93), "构筑风险纹样"),
            ("frame_01", (0.50, 0.10, 0.73, 0.31), "边框层次一（素描细框）"),
            ("frame_02", (0.50, 0.33, 0.73, 0.52), "边框层次二（青玉角饰）"),
            ("frame_03", (0.50, 0.53, 0.73, 0.72), "边框层次三（金角框）"),
            ("frame_04", (0.50, 0.74, 0.73, 0.92), "边框层次四（朱砂切角）"),
            ("vocab_01", (0.76, 0.10, 0.98, 0.32), "界面语汇：壹~玖数字格"),
            ("vocab_02", (0.76, 0.37, 0.98, 0.47), "界面语汇：朱砂警示条"),
            ("vocab_03", (0.76, 0.52, 0.98, 0.70), "界面语汇：圆形徽记框"),
            ("vocab_04", (0.76, 0.73, 0.98, 0.88), "界面语汇：菱形朱印"),
        ],
    },
    "01-mainmenu": {
        "label": "主菜单",
        "use": "整屏背景底板 + 卷轴标题 / 四按钮 / 境界条 / 六边灵韵槽",
        "components": [
            ("title_scroll", (0.03, 0.04, 0.33, 0.60), "卷轴标题框"),
            ("realm_bar", (0.02, 0.62, 0.42, 0.75), "境界 / 金丹进度条"),
            ("button_01", (0.72, 0.12, 0.98, 0.23), "开始入塔按钮"),
            ("button_02", (0.72, 0.25, 0.98, 0.35), "境界总览按钮"),
            ("button_03", (0.72, 0.36, 0.98, 0.46), "传承灵韵按钮"),
            ("button_04", (0.72, 0.47, 0.98, 0.57), "设置按钮"),
            ("legacy_slots", (0.50, 0.78, 0.99, 0.91), "六边灵韵槽 x6"),
        ],
    },
    "02-towerhud": {
        "label": "塔层 HUD",
        "use": "血条 / 灵力条 / 层数标记 / 境界牌 / Boss 血条 / 技能八角框",
        "components": [
            ("bar_hp", (0.01, 0.05, 0.45, 0.10), "生命条"),
            ("bar_qi", (0.01, 0.10, 0.41, 0.15), "灵力条"),
            ("bar_shield", (0.01, 0.15, 0.36, 0.21), "护盾 / 护体条"),
            ("floor_marker", (0.81, 0.04, 0.99, 0.15), "第 N 层 / 9 层数标记"),
            ("realm_plate", (0.73, 0.15, 0.99, 0.24), "金丹境界牌"),
            ("boss_bar", (0.19, 0.33, 0.81, 0.40), "Boss 血条 + 名字"),
            ("skill_01", (0.25, 0.66, 0.37, 0.79), "技能八角框 J"),
            ("skill_02", (0.37, 0.66, 0.50, 0.79), "技能八角框 K"),
            ("skill_03", (0.50, 0.66, 0.63, 0.79), "技能八角框 L"),
            ("skill_04", (0.62, 0.66, 0.75, 0.79), "技能八角框 I"),
        ],
    },
    "03-draft": {
        "label": "择一机缘（选卡）",
        "use": "三色卡框（青 / 金 / 朱）、确认按钮、顶部状态栏 —— 可直接对照 assets/ui/cards/frame_*",
        "components": [
            ("status_bar", (0.04, 0.04, 0.96, 0.14), "顶部层数和道行状态栏"),
            ("card_01", (0.05, 0.22, 0.33, 0.76), "伤害类卡框"),
            ("card_02", (0.35, 0.22, 0.63, 0.76), "属性类卡框（青玉角饰）"),
            ("card_03", (0.64, 0.20, 0.97, 0.78), "机制类卡框（金框选中态）"),
            ("confirm", (0.34, 0.83, 0.66, 0.93), "确认（Enter）按钮"),
        ],
    },
    "04-result": {
        "label": "结算界面",
        "use": "整屏底板 + 结算面板 / 按钮",
        "components": [
            ("result_panel", (0.08, 0.10, 0.92, 0.80), "结算主面板"),
            ("result_button", (0.30, 0.82, 0.70, 0.94), "结算确认按钮"),
        ],
    },
    "05-pause": {
        "label": "暂停界面",
        "use": "整屏底板 + 暂停面板 / 选项按钮",
        "components": [
            ("pause_panel", (0.20, 0.12, 0.80, 0.88), "暂停主面板"),
        ],
    },
    "06-affix": {
        "label": "词缀界面",
        "use": "整屏底板 + 词缀选择面板",
        "components": [
            ("affix_panel", (0.06, 0.08, 0.94, 0.90), "词缀主面板"),
        ],
    },
    "07-codex": {
        "label": "图鉴 / 典籍",
        "use": "16 张卡面（4 稀有度配色）+ 筛选标签 + 详情面板",
        "components": [
            ("filter_bar", (0.01, 0.01, 0.99, 0.10), "顶部筛选 / 稀有度标签"),
            ("card_grid", (0.01, 0.11, 0.72, 0.97), "4x4 卡牌网格"),
            ("detail_panel", (0.73, 0.11, 0.99, 0.97), "右侧效果描述 / 基础信息面板"),
        ],
    },
    "08-icons": {
        "label": "图标系统样式表",
        "use": "六类图标：技能八角 9 / 流派圆 4 / 词缀菱形 12 / 境界卷轴 9 / 装备盾 8 / 灵韵六边 6；对应 docs/icon-catalog.json",
        "components": [],
        "iconRows": [
            ("skill", 0.13, 0.24, 9),
            ("school", 0.26, 0.39, 4),
            ("affix", 0.42, 0.51, 12),
            ("realm", 0.54, 0.65, 9),
            ("equipment", 0.67, 0.79, 8),
            ("legacy", 0.81, 0.93, 6),
        ],
    },
}

# 08-icons 右下角水印区（相对坐标）。文字压在深色底上，用同列上方背景色回填。
ICON_WM_REL = (0.50, 0.925, 0.99, 0.985)
# 该条带在水印之下只剩深色底 + 金色外框；青玉描边属于上一行图标，不在此带内，
# 水印的青色抗锯齿残留也一并清掉，避免留下散点。
WM_KEEP = {
    rgb("#12161F"), rgb("#000000"),
    rgb("#8A6520"), rgb("#D9A441"), rgb("#F2D089"),
}


def nearest24(c):
    r, g, b = c
    return min(PALETTE, key=lambda p: (r - p[0]) ** 2 + (g - p[1]) ** 2 + (b - p[2]) ** 2)


def snap(im: Image.Image) -> Image.Image:
    im = im.convert("RGB")
    px = im.load()
    w, h = im.size
    cache = {}
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            hit = cache.get(c)
            if hit is None:
                hit = nearest24(c)
                cache[c] = hit
            px[x, y] = hit
    return im


def crop_rel(im: Image.Image, box) -> Image.Image:
    w, h = im.size
    return im.crop((round(box[0] * w), round(box[1] * h),
                    round(box[2] * w), round(box[3] * h)))


def clean_icon_watermark(im: Image.Image) -> tuple[Image.Image, dict]:
    im = im.convert("RGB").copy()
    px = im.load()
    w, h = im.size
    x0, y0 = round(ICON_WM_REL[0] * w), round(ICON_WM_REL[1] * h)
    x1, y1 = round(ICON_WM_REL[2] * w), round(ICON_WM_REL[3] * h)
    changed = 0
    for y in range(y0, min(y1, h)):
        for x in range(x0, min(x1, w)):
            if px[x, y] in WM_KEEP:
                continue
            px[x, y] = DARK_BG
            changed += 1
    return im, {"boxRel": list(ICON_WM_REL), "pixelsReplaced": changed,
                "method": "保留深色底 / 金框 / 青玉描边，条带内其余像素一律回填深色底",
                "sourceArtUntouched": True}


def panel_16x9(im: Image.Image) -> Image.Image:
    w, h = im.size
    t = 16 / 9
    if w / h > t:
        nw = round(h * t)
        c = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    elif w / h < t:
        nh = round(w / t)
        top = round((h - nh) * 0.5)
        c = im.crop((0, top, w, min(h, top + nh)))
    else:
        c = im
    return snap(c.resize((960, 540), Image.Resampling.LANCZOS))


def metrics(path: Path) -> dict:
    im = Image.open(path).convert("RGB")
    colors = [c for _, c in (im.getcolors(maxcolors=1 << 24) or [])]
    return {"size": list(im.size),
            "usedColors": len(colors),
            "outOfPalette": len([c for c in colors if c not in set(PALETTE)])}


def b64(im: Image.Image, max_w: int = 320) -> str:
    if im.width > max_w:
        s = max_w / im.width
        im = im.resize((max_w, max(1, round(im.height * s))), Image.Resampling.NEAREST)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def build(check: bool) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    wm = {}
    for stem, spec in SPECS.items():
        src_path = UI / f"{stem}-gpt-image2_palette24.png"
        src = Image.open(src_path).convert("RGB")
        if stem == "08-icons":
            src, wm = clean_icon_watermark(src)
        src = snap(src)
        full_name = f"ui_{stem}_full.png"
        panel_name = f"ui_{stem}_panel.png"
        if not check:
            src.save(OUT / full_name)
            panel_16x9(src).save(OUT / panel_name)
        entries += [
            {"file": full_name, "source": str(src_path.relative_to(ROOT)),
             "kind": "full", "cropRel": [0, 0, 1, 1],
             "use": "原尺寸整屏参考底板", "status": STATUS},
            {"file": panel_name, "source": str(src_path.relative_to(ROOT)),
             "kind": "panel16x9", "cropRel": "居中裁 16:9 -> 960x540",
             "use": "16:9 整屏 UI 底板候选", "status": STATUS},
        ]

        for name, box, use in spec["components"]:
            fn = f"ui_{stem}_{name}.png"
            if not check:
                crop_rel(src, box).save(OUT / fn)
            entries.append({
                "file": fn, "source": str(src_path.relative_to(ROOT)),
                "kind": "component", "cropRel": list(box), "use": use,
                "cropAccuracy": "相对比例估算，需人工目检微调", "status": STATUS})

        if spec.get("iconRows"):
            w, h = src.size
            for ri, (row_id, y0r, y1r, n) in enumerate(spec["iconRows"], start=1):
                band_box = (0.02, y0r, 0.99, y1r)
                band = crop_rel(src, band_box)
                band_name = f"ui_icons_row_{ri:02d}_{row_id}.png"
                if not check:
                    band.save(OUT / band_name)
                entries.append({
                    "file": band_name, "source": str(src_path.relative_to(ROOT)),
                    "kind": "iconRow", "cropRel": list(band_box), "row": row_id,
                    "expectedIcons": n,
                    "use": f"{row_id} 类整行图标带（含左侧分类标签）", "status": STATUS})
                # 逐格：右侧图标区等分 + 内容 bbox 精修
                ix0, ix1 = round(0.19 * w), round(0.985 * w)
                y0, y1 = round(y0r * h), round(y1r * h)
                slot = (ix1 - ix0) / n
                for ci in range(n):
                    a, b = round(ix0 + ci * slot), round(ix0 + (ci + 1) * slot)
                    tile = src.crop((a, y0, b, y1))
                    # 去掉深色底，取非背景内容 bbox
                    tp = tile.load()
                    xs, ys = [], []
                    for yy in range(tile.height):
                        for xx in range(tile.width):
                            if tp[xx, yy] != DARK_BG:
                                xs.append(xx); ys.append(yy)
                    if xs:
                        pad = 2
                        tile = tile.crop((max(0, min(xs) - pad), max(0, min(ys) - pad),
                                          min(tile.width, max(xs) + pad + 1),
                                          min(tile.height, max(ys) + pad + 1)))
                    fn = f"ui_icons_{ri:02d}_{row_id}_{ci + 1:02d}.png"
                    if not check:
                        tile.save(OUT / fn)
                    entries.append({
                        "file": fn, "source": str(src_path.relative_to(ROOT)),
                        "kind": "iconCell", "row": row_id, "col": ci + 1,
                        "cropRel": [round(a / w, 4), y0r, round(b / w, 4), y1r],
                        "use": f"{row_id} 类第 {ci + 1} 个图标（待与 icon-catalog.json 的 ID 人工对位）",
                        "status": STATUS})

    if check:
        files = sorted(OUT.glob("*.png"))
        bad = []
        for p in files:
            m = metrics(p)
            if m["outOfPalette"]:
                bad.append({"file": p.name, **m})
        return {"files": len(files), "bad": bad[:10]}

    # 清单 + 报告
    for e in entries:
        e.update(metrics(OUT / e["file"]))
    manifest = {
        "version": 1,
        "scope": "previews/ui/00-anchor ~ 08-icons 九张 gpt-image2 回稿的 UI 资产化",
        "status": STATUS,
        "note": ("本目录为新增候选资产，不替换 assets/ui/icons 的 47 个 R23 冻结 ID，"
                 "也不替换 assets/ui/cards；组件裁切框为相对比例估算，需人工目检微调"),
        "watermark": wm,
        "files": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 独立目检页（零外部请求，内嵌全部图）
    groups = {}
    for e in entries:
        groups.setdefault(e["source"].split("/")[-1].split("-gpt")[0], []).append(e)
    cards = []
    for stem in SPECS:
        key = stem
        items = groups.get(key, [])
        specs_label = SPECS[stem]["label"]
        cards.append(f'<section><h2>{stem} · {specs_label}</h2>'
                     f'<p class="use">{SPECS[stem]["use"]}</p><div class="grid">')
        for e in items:
            im = Image.open(OUT / e["file"]).convert("RGB")
            cards.append(
                f'<figure><img loading="lazy" src="data:image/png;base64,{b64(im)}">'
                f'<figcaption><b>{e["file"]}</b><br>{e["use"]}<br>'
                f'<small>{e["size"][0]}×{e["size"][1]} · 越界色 {e["outOfPalette"]}</small>'
                f'</figcaption></figure>')
        cards.append("</div></section>")
    html = """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>UI 参考稿资产目检页 · 第 31 轮</title>
<style>
:root{color-scheme:light}body{margin:0;background:#f5f2ea;color:#232731;
font:14px/1.6 -apple-system,"PingFang SC",sans-serif}
header{background:#12161f;color:#e8dfc8;padding:22px 28px}
header h1{margin:0 0 6px;font-size:20px}
header p{margin:2px 0;color:#c9bfa3;font-size:12px}
.warn{background:#7a2420;color:#fff;padding:9px 14px;margin:0;font-size:12px}
main{padding:22px 28px;max-width:1400px;margin:auto}
section{margin-bottom:34px;border-bottom:1px solid #c9bfa3;padding-bottom:22px}
h2{font-size:17px;margin:0 0 4px}
.use{color:#4a5568;margin:0 0 14px;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}
figure{margin:0;background:#fff;border:1px solid #c9bfa3;padding:8px}
figure img{width:100%;image-rendering:pixelated;background:#12161f;display:block}
figcaption{font-size:11px;margin-top:7px;word-break:break-all;color:#232731}
figcaption small{color:#4a5568}
</style>
<header><h1>UI 参考稿资产目检页</h1>
<p>九张 gpt-image2 回稿全部纳入 · 整屏底板 + 组件切图 + 逐格图标</p>
<p>来源：previews/ui/00-anchor ~ 08-icons · 24 色锁定板 · 原稿未改动</p></header>
<p class="warn">⚠ 验证层资产：status 全部为「待目检与合规确认；不得直接入库」。Q17 未拍板、GUI F5 未跑、未接 Godot 场景。裁切框为相对比例估算，需人工微调；本页不替换 assets/ui/icons 的 47 个冻结图标 ID。</p>
<main>""" + "".join(cards) + "</main></html>"
    PREVIEW.write_text(html, encoding="utf-8")

    by_kind = Counter(e["kind"] for e in entries)
    # 全目录源稿覆盖率：防止再次把某张 gpt-image2 回稿误判为「本轮用不到」。
    all_pal = sorted(UI.glob("*_palette24.png"))
    covered = {f"previews/ui/{s}-gpt-image2_palette24.png" for s in SPECS}
    covered |= {f"previews/ui/{s}-gpt-image2_palette24.png" for s in (
        "A1-bgnormal", "A2R-bgrest", "A3-bghigh", "A4-bgboss",
        "B-boss", "C1-vfx", "C2-overlay")}
    unused_rel = [str(p.relative_to(ROOT)) for p in all_pal
                  if str(p.relative_to(ROOT)) not in covered]
    report = {
        "round": 31,
        "tool": "tools/build_ui_reference_assets.py",
        "scope": "previews/ui/00-anchor ~ 08-icons 九张 gpt-image2 回稿资产化",
        "reason": "第 29/30 轮误判 00~08 九张为『本轮用不到』；用户指出全部是其本人生成的可用素材",
        "sourceArtRoot": "previews/ui/",
        "sourceFiles": [f"previews/ui/{s}-gpt-image2_palette24.png" for s in SPECS],
        "watermark": wm,
        "userOriginalsUntouched": True,
        "sourceCoverage": {
            "palette24Total": len(all_pal),
            "usedByRound31": len(covered),
            "unusedSources": unused_rel,
            "unusedReason": ("A2-bgrest 是方图旧版，已被用户重出的 16:9 版 A2R-bgrest 取代；"
                             "原稿保留未删，其余 16 张全部在本轮两个转录脚本中被实际读取"),
        },
        "outputDir": "assets/ui/reference/",
        "overviewPage": "previews/ui-reference-overview.html",
        "counts": {"sources": len(SPECS), "files": len(entries), "byKind": dict(by_kind),
                   "outOfPaletteTotal": sum(e["outOfPalette"] for e in entries)},
        "contractBoundary": [
            "不替换 assets/ui/icons 的 47 个 R23 冻结 ID，也不替换 assets/ui/cards",
            "08-icons 的逐格图标只给候选裁片，与 docs/icon-catalog.json 的 ID 对位需人工确认",
            "组件裁切框为相对比例估算，需人工目检微调；本轮不冒充精确对位",
            "方图 16:9 归一为居中裁切，会损失上下内容",
            "status 沿用「待目检与合规确认；不得直接入库」；Q17 / GUI F5 未过",
        ],
        "status": "HEADLESS 静态指标自检；画面未验证",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report["counts"] | {"watermark": wm}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只复算越界色，不写文件")
    args = ap.parse_args()
    result = build(args.check)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.check and result.get("bad"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
