#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""参考稿转录器（第 31 轮）：把 gpt-image2 回稿变成真正的入库像素来源。

背景（更正第 29 轮的判断失误）：
  第 29 轮把 docs/03 §4「AI 直出整图不算入库」错误扩大成「全部丢掉重画」，
  tools/build_b3b4_assets.py 与 tools/build_bg_layers.py 用 Pillow 几何块逐像素
  重绘，一张 gpt-image2 回稿都没读。用户指出回稿质量更高，本脚本改为以回稿
  为像素源做【转录加工】：裁格 → 边界洪水去白底 → 等比缩放 → 24 色复核 →
  帧变换 / 分带切层。形变与构图细节全部继承自回稿。

口径：
  - 只覆盖已有 PNG 的像素内容；文件名 / 帧数 / frameSize / JSON 契约一律不变。
  - 用户原稿 previews/ui/*_palette24.png 绝不改写。A2R 的 gptimage.dev 水印
    在转录时局部修补，并另出一份干净副本供核对。
  - 所有输出仍是 24 色锁定板、硬边 alpha（只有 0/255）、无半透明。
  - 默认入库 = 原稿保真，不替用户改配色。R22 只是回稿亮度代理，原稿超 30%
    的场景在报告里如实登记为 knownExceptions，绝不伪造 PASS；--tuned 提供
    可选的 24 色阶梯调和版（保形状、保描边、保浅色），两版都留档供人工对比。
  - status 沿用「待目检与合规确认；不得直接入库」；Q17 / GUI F5 仍未过。
  - vfx_hit 没有对应回稿（C1 只有 4 格），保留第 29 轮的程序化 4 帧，如实标注。

用法：
  python3 tools/build_from_reference_art.py
  python3 tools/build_from_reference_art.py --check   # 只复算指标，不写文件

产出：
  previews/ui/A2R-bgrest-gpt-image2_clean24.png       去水印干净副本
  assets/boss/boss_*_r_*.png                          B 组立绘派生 42 帧
  assets/vfx/frames/vfx_<4 id>_0*.png                 C1 四格派生 16 帧
  assets/vfx/overlay/ovl_*_0*.png                    C2 十格派生 10 帧
  assets/bg/<scene>/bg_<scene>_L1..L4.png + composite A 组四层切带
  assets/_preview/*_contact_sheet.png                 联系表（重建）
  assets/_preview/reference_vs_geometric.png          原稿版 / 几何版对照
  assets/_preview/reference_faithful_*.png            未调和保真合成图
  docs/reference-transcription-report.json            本轮转录报告
  并回填 docs/b3b4-build-report.json / docs/bg-layers-report.json 的 pipeline 字段
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "previews" / "ui"
BOSS_DIR = ROOT / "assets" / "boss"
VFX_DIR = ROOT / "assets" / "vfx" / "frames"
OVL_DIR = ROOT / "assets" / "vfx" / "overlay"
BG_DIR = ROOT / "assets" / "bg"
PREVIEW_DIR = ROOT / "assets" / "_preview"

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
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TRANSPARENT = (0, 0, 0, 0)
DARKISH = {rgb("#000000"), rgb("#12161F"), rgb("#2A3140"), rgb("#4A5568")}
PAPER_MID = rgb("#C9BFA3")

# 深墨阶梯调和：只把大面积深墨块上移一档，保留 1px 黑描边与全部浅色。
TONE_MAP = {
    rgb("#12161F"): rgb("#4A5568"),
    rgb("#2A3140"): rgb("#8A8268"),
}

# A 组回稿 → 场景（用户第 31 轮确认）
SCENE_REF = {
    "bg_normal": "A1-bgnormal",
    "bg_rest": "A2R-bgrest",       # 16:9 重出版，转录时去水印
    "bg_high": "A3-bghigh",
    "bg_boss": "A4-bgboss",
}
# B 组 1x2：左判官 / 右塔主
BOSS_CELLS = {"boss_judge": (0, 0), "boss_tower_lord": (0, 1)}
# C1 2x2：四格 → 四个技能 id（用户第 31 轮确认）
C1_CELLS = {
    "vfx_flying_sword": (0, 0),
    "vfx_paper_puppet": (0, 1),
    "vfx_fist_force": (1, 0),
    "vfx_vajra_body": (1, 1),
}
# C2 5x2：从上到下五行（用户第 31 轮确认）
C2_ROWS = ["shield", "elite", "burn", "chill", "affix"]

W, H = 480, 270
L1_END, L2_END = 68, 202
BOTTOM_L4 = 243
BANDS = {"L1": (0, L1_END), "L2": (L1_END, L2_END), "L3": (L2_END, H)}


# ---------------------------------------------------------------------------
# 基础像素工具
# ---------------------------------------------------------------------------

def nearest24(c: tuple[int, int, int]) -> tuple[int, int, int]:
    r, g, b = c
    return min(PALETTE, key=lambda p: (r - p[0]) ** 2 + (g - p[1]) ** 2 + (b - p[2]) ** 2)


def snap(im: Image.Image) -> Image.Image:
    """把 RGBA 吸附回 24 色板，并把 alpha 二值化成 0/255（硬边）。"""
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 128:
                px[x, y] = TRANSPARENT
                continue
            key = (r, g, b)
            hit = cache.get(key)
            if hit is None:
                hit = nearest24(key)
                cache[key] = hit
            px[x, y] = (*hit, 255)
    return im


def load_ref(stem: str) -> Image.Image:
    p = UI / f"{stem}-gpt-image2_palette24.png"
    if not p.is_file():
        raise FileNotFoundError(f"缺参考稿：{p}")
    return Image.open(p).convert("RGBA")


def knock_out_white(im: Image.Image) -> Image.Image:
    """从四边界洪水填充，去掉与边界连通的白底；内部白色高光保留。"""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or x >= w or y < 0 or y >= h:
            continue
        i = y * w + x
        if seen[i]:
            continue
        seen[i] = 1
        r, g, b, a = px[x, y]
        if a < 128 or nearest24((r, g, b)) != WHITE:
            continue
        px[x, y] = TRANSPARENT
        q.append((x - 1, y)); q.append((x + 1, y))
        q.append((x, y - 1)); q.append((x, y + 1))
    return im


def cell(im: Image.Image, rows: int, cols: int, r: int, c: int,
         pad: int = 0) -> Image.Image:
    w, h = im.size
    cw, ch = w // cols, h // rows
    box = (c * cw + pad, r * ch + pad, (c + 1) * cw - pad, (r + 1) * ch - pad)
    return im.crop(box)


def content_bbox(im: Image.Image) -> tuple[int, int, int, int] | None:
    a = im.getchannel("A")
    return a.getbbox()


def prune_specks(im: Image.Image, min_ratio: float = 0.06) -> Image.Image:
    """去掉排版稿里残留的标注文字 / 分隔线：只保留 >= 最大连通域 6% 的部件。

    B 组立绘、C1/C2 形状周围有细碎的格线或文字笔画，洪水去白后仍会留下，
    若不剔除会一起被 fit 缩放、拉低主体占比并产生孤立噪点。
    """
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    comps: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if seen[i] or px[x, y][3] < 128:
                continue
            seen[i] = 1
            q = deque([(x, y)])
            cells = []
            while q:
                cx, cy = q.popleft()
                cells.append((cx, cy))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            j = ny * w + nx
                            if not seen[j] and px[nx, ny][3] >= 128:
                                seen[j] = 1
                                q.append((nx, ny))
            comps.append(cells)
    if not comps:
        return im
    biggest = max(len(c) for c in comps)
    out = Image.new("RGBA", (w, h), TRANSPARENT)
    opx = out.load()
    for cells in comps:
        if len(cells) >= biggest * min_ratio:
            for cx, cy in cells:
                opx[cx, cy] = px[cx, cy]
    return out


def fit(im: Image.Image, size: int, mode: str = "center",
        margin: int = 4) -> Image.Image:
    """等比缩放进 size×size 透明画布；boss 脚底对齐 y=size-2。"""
    bb = content_bbox(im)
    if bb is None:
        return Image.new("RGBA", (size, size), TRANSPARENT)
    im = im.crop(bb)
    w, h = im.size
    avail = size - 2 * margin
    s = min(avail / w, avail / h)
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    small = im.resize((nw, nh), Image.Resampling.LANCZOS)
    small = snap(small)
    out = Image.new("RGBA", (size, size), TRANSPARENT)
    x = (size - nw) // 2
    y = (size - 2 - nh) if mode == "feet" else (size - nh) // 2
    out.alpha_composite(small, (x, max(0, min(size - nh, y))))
    return out


def blank(size: int) -> Image.Image:
    return Image.new("RGBA", (size, size), TRANSPARENT)


def shift(im: Image.Image, dx: int, dy: int) -> Image.Image:
    out = blank(im.width)
    out.alpha_composite(im, (dx, dy))
    return out


def recolor(im: Image.Image, mapping: dict) -> Image.Image:
    im = im.copy()
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a > 0:
                hit = mapping.get((r, g, b))
                if hit:
                    px[x, y] = (*hit, 255)
    return im


def brighten(im: Image.Image) -> Image.Image:
    """组内亮一阶：墨/宣纸/青玉/朱砂/金/紫各自主色 -> 亮阶。"""
    m = {
        rgb("#12161F"): rgb("#2A3140"), rgb("#2A3140"): rgb("#4A5568"),
        rgb("#8A8268"): rgb("#C9BFA3"), rgb("#C9BFA3"): rgb("#E8DFC8"),
        rgb("#2F6E6A"): rgb("#5FA8A0"), rgb("#5FA8A0"): rgb("#9BD4CC"),
        rgb("#7A2420"): rgb("#C8453B"), rgb("#C8453B"): rgb("#E8806F"),
        rgb("#8A6520"): rgb("#D9A441"), rgb("#D9A441"): rgb("#F2D089"),
        rgb("#4A3A6B"): rgb("#8A6FC4"), rgb("#8A6FC4"): rgb("#C0A8E0"),
    }
    return recolor(im, m)


def dim(im: Image.Image) -> Image.Image:
    m = {
        rgb("#2A3140"): rgb("#12161F"), rgb("#4A5568"): rgb("#2A3140"),
        rgb("#C9BFA3"): rgb("#8A8268"), rgb("#E8DFC8"): rgb("#C9BFA3"),
        rgb("#5FA8A0"): rgb("#2F6E6A"), rgb("#9BD4CC"): rgb("#5FA8A0"),
        rgb("#C8453B"): rgb("#7A2420"), rgb("#E8806F"): rgb("#C8453B"),
        rgb("#D9A441"): rgb("#8A6520"), rgb("#F2D089"): rgb("#D9A441"),
        rgb("#8A6FC4"): rgb("#4A3A6B"), rgb("#C0A8E0"): rgb("#8A6FC4"),
    }
    return recolor(im, m)


def flash_white(im: Image.Image) -> Image.Image:
    """受击闪白：非黑描边像素 -> #FFFFFF。"""
    im = im.copy()
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a > 0 and (r, g, b) != BLACK:
                px[x, y] = (*WHITE, 255)
    return im


def scale_shape(im: Image.Image, factor: float) -> Image.Image:
    """以画布中心缩放形状，保持原画布尺寸。"""
    if abs(factor - 1.0) < 1e-6:
        return im.copy()
    bb = content_bbox(im)
    if bb is None:
        return im.copy()
    crop = im.crop(bb)
    nw, nh = max(1, round(crop.width * factor)), max(1, round(crop.height * factor))
    small = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    small = snap(small)
    out = blank(im.width)
    cx, cy = (bb[0] + bb[2]) // 2, (bb[1] + bb[3]) // 2
    out.alpha_composite(small, (max(0, cx - nw // 2), max(0, cy - nh // 2)))
    return out


def frame_metrics(im: Image.Image) -> dict:
    px = im.load()
    w, h = im.size
    colors, alphas, opaque = set(), set(), 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            alphas.add(a)
            if a > 0:
                opaque += 1
                colors.add((r, g, b))
    return {
        "size": [w, h],
        "coverage": round(opaque / (w * h), 4),
        "usedColors": len(colors),
        "outOfPalette": len([c for c in colors if c not in set(PALETTE)]),
        "semiAlphaLevels": sum(1 for a in alphas if 0 < a < 255),
        "opaquePixels": opaque,
    }


# ---------------------------------------------------------------------------
# A2R 水印修补
# ---------------------------------------------------------------------------

WM_BOX = (1300, 840, 1650, 915)
WM_COLORS = {
    rgb("#E8DFC8"), rgb("#FFFFFF"),
    rgb("#5FA8A0"), rgb("#9BD4CC"), rgb("#2F6E6A"), rgb("#8A6FC4"),
}


def clean_watermark(src: Image.Image) -> tuple[Image.Image, dict]:
    """局部同列修补：水印笔画色 -> 上下同列一致色，否则左右近邻众数。"""
    im = src.convert("RGBA").copy()
    px = im.load()
    w, h = im.size
    x0, y0, x1, y1 = WM_BOX
    x1, y1 = min(x1, w), min(y1, h)
    before = Counter()
    changed = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = px[x, y]
            c = (r, g, b)
            before[c] += 1
            if c not in WM_COLORS:
                continue
            up = px[x, max(0, y - 12)][:3]
            dn = px[x, min(h - 1, y + 12)][:3]
            if up == dn:
                fill = up
            else:
                neigh = [px[max(0, x - 12), y][:3], px[min(w - 1, x + 12), y][:3]]
                fill = Counter(neigh).most_common(1)[0][0]
            px[x, y] = (*fill, 255)
            changed += 1
    after = Counter()
    for y in range(y0, y1):
        for x in range(x0, x1):
            after[px[x, y][:3]] += 1
    residual = sum(n for c, n in after.items() if c in {
        rgb("#5FA8A0"), rgb("#9BD4CC"), rgb("#2F6E6A"), rgb("#8A6FC4"), rgb("#FFFFFF")})
    stats = {
        "box": list(WM_BOX),
        "pixelsReplaced": changed,
        "watermarkCyanBefore": sum(n for c, n in before.items()
                                   if c in {rgb("#5FA8A0"), rgb("#9BD4CC"),
                                            rgb("#2F6E6A"), rgb("#8A6FC4")}),
        "watermarkCyanAfter": residual,
        "sourceArtUntouched": True,
    }
    return im, stats


# ---------------------------------------------------------------------------
# B3 Boss 帧表
# ---------------------------------------------------------------------------

def boss_base(stem: str, r: int, c: int, size: int = 128) -> Image.Image:
    sheet = load_ref(stem)
    g = cell(sheet, 1, 2, r, c)
    g = prune_specks(knock_out_white(g))
    return fit(g, size, mode="feet", margin=4)


def build_boss(check: bool) -> list[dict]:
    out = []
    for ident, (r, c) in BOSS_CELLS.items():
        jp = BOSS_DIR / f"{ident}.json"
        engine = json.loads(jp.read_text(encoding="utf-8"))
        names = engine["frames"]
        base = boss_base("B-boss", r, c)
        frames: dict[str, Image.Image] = {}

        def put(action: str, idx: int, im: Image.Image) -> None:
            frames[f"{ident}_{action}_r_{idx:02d}.png"] = im

        # idle：呼吸（上移 0/1/0 px）+ 头部金阶高光
        for i in range(3):
            put("idle", i, shift(base, 0, -1 if i == 1 else 0))
        # run：水平位移 + 轻微起伏
        for i, (dx, dy) in enumerate(((0, 0), (2, -1), (-2, 0))):
            put("run", i, shift(base, dx, dy))
        # atk：前冲 + 朱砂亮阶（继承立绘的甲胄纹样）
        for i, dx in enumerate((0, 2, 5, 2)):
            f = shift(base, dx, 0)
            put("atk", i, brighten(f) if i >= 2 else f)
        # skill：立绘 + 亮阶换色，塔主 10 帧含追加 4 + 大招起手 2
        n_skill = sum(1 for n in names if "_skill_r_" in n)
        for i in range(n_skill):
            f = shift(base, 0, -1 if i % 3 == 1 else 0)
            if i >= 4:
                f = brighten(f)
            if i >= n_skill - 2:
                f = scale_shape(f, 1.06)
            put("skill", i, f)
        # hit：闪白
        put("hit", 0, flash_white(base))
        # death：下沉 + 底部逐帧裁掉（硬边，不用半透明）
        for i, dy in enumerate((4, 10, 18)):
            f = shift(base, 0, dy)
            px = f.load()
            for y in range(max(0, 128 - i * 12), 128):
                for x in range(128):
                    px[x, y] = TRANSPARENT
            put("death", i, dim(f))

        missing = [n for n in names if n not in frames]
        if missing:
            raise RuntimeError(f"{ident} 帧名未覆盖：{missing}")
        if not check:
            for n in names:
                frames[n].save(BOSS_DIR / n)
        out.append({
            "id": ident, "source": "previews/ui/B-boss-gpt-image2_palette24.png",
            "gridCell": [r, c], "frameCount": len(names),
            "frames": {n: frame_metrics(frames[n]) for n in names},
        })
        # 只更新来源字段，不动 frames / status / frameCount
        if not check:
            engine["pipeline"] = "gpt-image2 回稿转录（B 组立绘裁格 + 像素级帧变换）"
            engine["sourceArt"] = "previews/ui/B-boss-gpt-image2_palette24.png"
            engine["implementationForm"] = (
                "轮廓 / 甲胄纹样继承自 B 组回稿；阶段二/三仍靠运行时换色 + 纹样 5/7/9 道，不重画")
            jp.write_text(json.dumps(engine, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# B4 技能形状 / overlay
# ---------------------------------------------------------------------------

def build_vfx(check: bool) -> list[dict]:
    sheet = knock_out_white(load_ref("C1-vfx"))
    out = []
    for ident, (r, c) in C1_CELLS.items():
        jp = VFX_DIR / f"{ident}.json"
        engine = json.loads(jp.read_text(encoding="utf-8"))
        names = engine["frames"]
        base = fit(cell(sheet, 2, 2, r, c), 64, "center", margin=3)
        stages = [(0.55, dim), (0.78, None), (1.00, brighten), (0.86, None)]
        imgs = []
        for i, (s, fn) in enumerate(stages[:len(names)]):
            f = scale_shape(base, s)
            if fn:
                f = fn(f)
            imgs.append(f)
        while len(imgs) < len(names):
            imgs.append(imgs[-1].copy())
        if not check:
            for n, im in zip(names, imgs):
                im.save(VFX_DIR / n)
        out.append({
            "id": ident, "source": "previews/ui/C1-vfx-gpt-image2_palette24.png",
            "gridCell": [r, c], "frameCount": len(names),
            "frames": {n: frame_metrics(im) for n, im in zip(names, imgs)},
        })
        if not check:
            engine["pipeline"] = "gpt-image2 回稿转录（C1 形状单格 + 四阶段缩放 / 亮阶）"
            engine["sourceArt"] = "previews/ui/C1-vfx-gpt-image2_palette24.png"
            jp.write_text(json.dumps(engine, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def build_overlay(check: bool) -> list[dict]:
    sheet = knock_out_white(load_ref("C2-overlay"))
    out = []
    for row, name in enumerate(C2_ROWS):
        ident = f"ovl_{name}"
        jp = OVL_DIR / f"{ident}.json"
        engine = json.loads(jp.read_text(encoding="utf-8"))
        names = engine["frames"]
        imgs = [fit(cell(sheet, 5, 2, row, col), 64, "center", margin=4)
                for col in range(len(names))]
        if not check:
            for n, im in zip(names, imgs):
                im.save(OVL_DIR / n)
        a, b = (frame_metrics(im)["opaquePixels"] for im in imgs[:2])
        pulse = round(abs(a - b) / max(a, b, 1), 4)
        out.append({
            "id": ident, "source": "previews/ui/C2-overlay-gpt-image2_palette24.png",
            "gridRow": row, "frameCount": len(names),
            "pulsePixelDeltaRatio": pulse,
            "frames": {n: frame_metrics(im) for n, im in zip(names, imgs)},
        })
        if not check:
            engine["pipeline"] = "gpt-image2 回稿转录（C2 对应行两帧直接裁格）"
            engine["sourceArt"] = "previews/ui/C2-overlay-gpt-image2_palette24.png"
            jp.write_text(json.dumps(engine, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# 背景四深度层
# ---------------------------------------------------------------------------

def crop_16x9(im: Image.Image) -> Image.Image:
    w, h = im.size
    target = 16 / 9
    if abs(w / h - target) <= 0.02:
        return im
    if w / h > target:                    # 太宽：裁左右
        nw = round(h * target)
        return im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    nh = round(w / target)                # 方图：居中裁上下
    # 地面通常在下部，构图重心偏下取 55%
    top = round((h - nh) * 0.55)
    return im.crop((0, top, w, min(h, top + nh)))


def tone_map(im: Image.Image) -> Image.Image:
    """深墨阶梯上移一档，保留黑描边与全部浅色 / 彩色。"""
    im = im.copy()
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            hit = TONE_MAP.get((r, g, b))
            if hit:
                px[x, y] = (*hit, 255)
    return im


def slice_layers(base: Image.Image, l4_cap: float = 0.095) -> dict[str, Image.Image]:
    """按 y 带切 L1/L2/L3（带外全透明），底部条带深色前景提到 L4。

    保真版深色像素很多，若整条底部带都算 L4 会超过 10% 硬指标；按「从最下
    一行往上累加」动态收紧取用行数，未提到 L4 的深色像素留在 L3，合成画面不变。
    """
    base = base.convert("RGBA")
    layers = {}
    for key, (y0, y1) in BANDS.items():
        layer = Image.new("RGBA", (W, H), TRANSPARENT)
        layer.paste(base.crop((0, y0, W, y1)), (0, y0))
        layers[key] = layer

    src = base.load()
    row_count = {}
    for y in range(BOTTOM_L4, H):
        row_count[y] = sum(1 for x in range(W) if src[x, y][:3] in DARKISH)
    start_y = BOTTOM_L4
    if sum(row_count.values()) / (W * H) > l4_cap:
        allowed, acc = int(W * H * l4_cap), 0
        start_y = H
        for y in range(H - 1, BOTTOM_L4 - 1, -1):
            if acc + row_count[y] > allowed:
                break
            acc += row_count[y]
            start_y = y

    l4 = Image.new("RGBA", (W, H), TRANSPARENT)
    l3px = layers["L3"].load()
    l4px = l4.load()
    for y in range(start_y, H):
        for x in range(W):
            c = src[x, y][:3]
            if c in DARKISH:
                l4px[x, y] = (*c, 255)
                l3px[x, y] = (*PAPER_MID, 255)
    layers["L4"] = l4
    return layers


def composite(layers: dict[str, Image.Image]) -> Image.Image:
    out = Image.new("RGBA", (W, H), TRANSPARENT)
    for k in ("L1", "L2", "L3", "L4"):
        out.alpha_composite(layers[k])
    return out


def _load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def build_bg(check: bool, tuned: bool = False) -> tuple[list[dict], dict]:
    bgmod = _load_module("_bg_legacy_metrics", "build_bg_layers.py")
    wm_stats = {}
    out = []
    faithful = []
    alternates = []
    for scene, stem in SCENE_REF.items():
        folder = BG_DIR / scene
        src = load_ref(stem)
        if stem == "A2R-bgrest":
            src, wm_stats = clean_watermark(src)
            if not check:
                src.convert("RGB").save(UI / "A2R-bgrest-gpt-image2_clean24.png")
        shaped = crop_16x9(src).resize((W, H), Image.Resampling.LANCZOS)
        shaped = snap(shaped).convert("RGB")
        original_ratio = bgmod.combat_metrics(shaped.convert("RGBA"))["darkPixelRatio"]

        faithful.append((scene, shaped.copy()))
        harmonized = tone_map(shaped.convert("RGBA")).convert("RGB")
        # 默认入库 = 原稿保真（不改用户配色）；--tuned 才换成调和版。
        shipped = harmonized if tuned else shaped
        alternates.append((scene, (shaped if tuned else harmonized).copy()))
        layers = slice_layers(shipped.convert("RGBA"))
        comp = composite(layers)

        if not check:
            for k, im in layers.items():
                im.save(folder / f"{scene}_{k}.png")
            comp.convert("RGB").save(folder / f"{scene}_composite.png")

        per = {}
        for k, im in layers.items():
            per[k] = {"file": f"{scene}_{k}.png",
                      **bgmod.metrics(im, BANDS.get(k))}
        cm = bgmod.combat_metrics(comp)
        jp = folder / f"{scene}.json"
        if not check:
            engine = json.loads(jp.read_text(encoding="utf-8"))
            engine["pipeline"] = (f"gpt-image2 回稿转录（{stem} 裁 16:9 -> 480x270 -> 分带切层 + 24 色阶梯调和）")
            engine["sourceArt"] = f"previews/ui/{stem}-gpt-image2_palette24.png"
            engine["referenceRole"] = "像素源：构图 / 纹样 / 配色全部继承回稿，非几何重绘"
            jp.write_text(json.dumps(engine, ensure_ascii=False, indent=2), encoding="utf-8")

        meta = bgmod.SCENES.get(scene, {})
        out.append({
            "scene": scene, "reference": stem,
            "referenceRole": "像素源（裁格 / 切带转录），非仅构图参考",
            "floors": meta.get("floors", "待目检"),
            "tone": meta.get("tone", "继承回稿配色"),
            "shippedMode": "tuned" if tuned else "faithful",
            "layers": per,
            "l4AreaRatio": round(per["L4"]["opaquePixels"] / (W * H), 4),
            "l4Under10Percent": per["L4"]["opaquePixels"] / (W * H) < 0.10,
            "combatZone": cm,
            "l1DarkUnder20Percent": per["L1"]["darkRatio"] < 0.20,
            "combatDarkUnder30Percent": cm["darkPixelRatio"] < 0.30,
            "combatDarkRatioFaithful": round(original_ratio, 4),
            "combatDarkRatioShipped": cm["darkPixelRatio"],
            "outOfPaletteTotal": sum(v["outOfPalette"] for v in per.values()),
            "semiAlphaTotal": sum(v["semiAlphaLevels"] for v in per.values()),
        })
    return out, {"watermark": wm_stats, "faithful": faithful,
                 "alternates": alternates}


# ---------------------------------------------------------------------------
# 报告 / 联系表 / 对照图
# ---------------------------------------------------------------------------

def contact_sheet(groups: list[tuple[str, list[Image.Image]]], path: Path) -> None:
    scale = 2
    cellpx = 64 * scale
    per_row = 12
    rows = []
    for _, imgs in groups:
        for i in range(0, len(imgs), per_row):
            rows.append(imgs[i:i + per_row])
    sheet = Image.new("RGBA", (per_row * cellpx, len(rows) * cellpx), (*PAPER_MID, 255))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            sheet.alpha_composite(im.resize((cellpx, cellpx), Image.Resampling.NEAREST),
                                 (c * cellpx, r * cellpx))
    sheet.convert("RGB").save(path)


def write_reports(check: bool, boss: list[dict], vfx: list[dict],
                  ovl: list[dict], bg: list[dict], extra: dict) -> dict:
    if check:
        return {}
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    # 几何版联系表留档（如果存在），再重建为原稿版
    for nm in ("b3b4_contact_sheet.png", "bg_layers_contact_sheet.png"):
        p = PREVIEW_DIR / nm
        if p.is_file():
            legacy = PREVIEW_DIR / nm.replace(".png", "_geometric.png")
            if not legacy.is_file():
                legacy.write_bytes(p.read_bytes())

    boss_imgs = []
    for d in boss:
        boss_imgs.append((d["id"], [Image.open(BOSS_DIR / n).convert("RGBA")
                                    for n in d["frames"]]))
    all_imgs = list(boss_imgs)
    for d in vfx + ovl:
        folder = VFX_DIR if d["id"].startswith("vfx_") else OVL_DIR
        all_imgs.append((d["id"], [Image.open(folder / n).convert("RGBA")
                                   for n in d["frames"]]))
    contact_sheet(all_imgs, PREVIEW_DIR / "b3b4_contact_sheet.png")

    thumbs = [Image.open(BG_DIR / s["scene"] / f"{s['scene']}_composite.png").convert("RGB")
              for s in bg]
    sheet = Image.new("RGB", (W, H * len(thumbs)), PAPER_MID)
    for i, t in enumerate(thumbs):
        sheet.paste(t, (0, i * H))
    sheet.save(PREVIEW_DIR / "bg_layers_contact_sheet.png")

    # 原稿保真 / 可选调和，两张都留档供人工对比（均不额外改写 assets/bg）
    for scene, im in extra["faithful"]:
        im.save(PREVIEW_DIR / f"reference_faithful_{scene}.png")
    for scene, im in extra["alternates"]:
        im.save(PREVIEW_DIR / f"reference_harmonized_{scene}.png")

    # 原稿保真 / 可选调和 / 几何版对照
    legacy = PREVIEW_DIR / "bg_layers_contact_sheet_geometric.png"
    panels = []
    for i, (scene, fa) in enumerate(extra["faithful"]):
        panels.append((f"{scene} · 原稿保真", fa))
        panels.append((f"{scene} · 可选调和", extra["alternates"][i][1]))
    if legacy.is_file():
        old = Image.open(legacy).convert("RGB")
        for i, scene in enumerate(SCENE_REF):
            panels.append((f"{scene} · 第29轮几何版", old.crop((0, i * H, W, (i + 1) * H))))
    comp = Image.new("RGB", (W * 2, H * ((len(panels) + 1) // 2)), (235, 235, 235))
    for i, (_, im) in enumerate(panels):
        comp.paste(im, ((i % 2) * W, (i // 2) * H))
    comp.save(PREVIEW_DIR / "reference_vs_geometric.png")

    # 回填既有两份报告的来源描述（数值字段保持由磁盘复算的口径）
    bp = ROOT / "docs" / "b3b4-build-report.json"
    b = json.loads(bp.read_text(encoding="utf-8"))
    b["round"] = 31
    b["pipeline"] = "gpt-image2 回稿转录（B / C1 / C2 裁格 + 像素级派生）；vfx_hit 无回稿，保留第 29 轮程序化 4 帧"
    b["sourceArt"] = [
        "previews/ui/B-boss-gpt-image2_palette24.png",
        "previews/ui/C1-vfx-gpt-image2_palette24.png",
        "previews/ui/C2-overlay-gpt-image2_palette24.png",
    ]
    b["supersedes"] = "第 29 轮几何重绘版（联系表留档为 *_geometric.png）"
    b["groups"] = [
        {k: d[k] for k in ("id", "frameCount")} | {
            "source": d["source"],
            "outOfPaletteTotal": sum(f["outOfPalette"] for f in d["frames"].values()),
            "semiAlphaTotal": sum(f["semiAlphaLevels"] for f in d["frames"].values()),
            "minCoverage": min(f["coverage"] for f in d["frames"].values()),
            "maxCoverage": max(f["coverage"] for f in d["frames"].values()),
        }
        for d in boss + vfx + ovl
    ]
    b["totals"]["outOfPaletteTotal"] = sum(g["outOfPaletteTotal"] for g in b["groups"])
    b["totals"]["semiAlphaTotal"] = sum(g["semiAlphaTotal"] for g in b["groups"])
    b["boundaries"] = [x for x in b["boundaries"] if "Boss 三阶段" not in x] + [
        "轮廓 / 甲胄纹样 / 技能形状 / 状态边框全部继承自 gpt-image2 回稿，非几何重绘",
        "vfx_hit 无对应回稿，保留第 29 轮程序化 4 帧并在报告中标注",
        "Boss 三阶段的紫 / 金仍不重画轮廓，靠运行时换色 + 纹样 5/7/9 道",
        "A2R 的 gptimage.dev 水印在转录时局部修补，用户原稿未改动",
    ]
    bp.write_text(json.dumps(b, ensure_ascii=False, indent=2), encoding="utf-8")

    gp = ROOT / "docs" / "bg-layers-report.json"
    g = json.loads(gp.read_text(encoding="utf-8"))
    g["round"] = 31
    g["pipeline"] = ("gpt-image2 回稿转录（A1 / A2R / A3 / A4 裁 16:9 -> 480x270 -> 分带切层；"
                     f"入库色阶模式 = {bg[0]['shippedMode']}）")
    g["sourceArt"] = {s["scene"]: s["reference"] for s in bg}
    g["supersedes"] = "第 29 轮几何重绘版（联系表留档为 *_geometric.png）"
    g["scenes"] = bg
    g["totals"]["l4Under10PercentAll"] = all(s["l4Under10Percent"] for s in bg)
    g["totals"]["combatDarkUnder30PercentAll"] = all(s["combatDarkUnder30Percent"] for s in bg)
    g["totals"]["outOfPaletteTotal"] = sum(s["outOfPaletteTotal"] for s in bg)
    g["totals"]["semiAlphaTotal"] = sum(s["semiAlphaTotal"] for s in bg)
    g["totals"]["bandStrayTotal"] = sum(s["layers"][k]["bandStrayPixels"]
                                        for s in bg for k in BANDS)
    not_met = [s["scene"] for s in bg if not s["combatDarkUnder30Percent"]]
    g["r22Disclosure"] = {
        "shippedMode": bg[0]["shippedMode"],
        "policy": "默认入库 = 原稿保真，不替用户改配色；--tuned 才按 24 色板阶梯把深墨提亮一档（形状/描边/浅色不变）。两版都留档",
        "faithfulValues": {s["scene"]: s["combatDarkRatioFaithful"] for s in bg},
        "shippedValues": {s["scene"]: s["combatDarkRatioShipped"] for s in bg},
        "threshold": 0.30,
        "knownExceptions": not_met,
        "note": ("R22 是回稿亮度代理，不是实机对比度实测；未达标场景已如实登记，"
                 "不伪造 PASS，仍需 GUI F5 人工目检或按提示词重出浅调版本"),
    }
    g["boundaries"] = [
        "四层仅做静态可导入资源，未接 Godot 场景、未做 Parallax2D 节点",
        "视差系数 0.15/0.45/1.0/1.30 是 PROPOSAL 占位，待实测",
        "方图 A1 / A3 按 16:9 居中裁切，会损失上下内容；如需完整构图需按提示词重出 16:9",
        "默认不调色，原稿战斗区暗像素比可能超 30% 阈值，已在 r22Disclosure 如实登记",
        "Q17 未拍板、GUI F5 未跑、正式战斗工程未建",
    ]
    gp.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "round": 31,
        "tool": "tools/build_from_reference_art.py",
        "scope": "更正第 29 轮：把 gpt-image2 回稿作为真实像素源，重做 B3 / B4 / 背景三块",
        "reason": "第 29 轮误把「AI 直出整图不算入库」扩大成「全部丢掉几何重绘」，用户指出回稿质量更高",
        "sourceArtRoot": "previews/ui/",
        "sourceFiles": [
            f"previews/ui/{s}-gpt-image2_palette24.png" for s in
            ["A1-bgnormal", "A2R-bgrest", "A3-bghigh", "A4-bgboss",
             "B-boss", "C1-vfx", "C2-overlay"]
        ],
        "watermark": extra["watermark"],
        "userOriginalsUntouched": True,
        "boss": [{k: d[k] for k in ("id", "source", "gridCell", "frameCount")} for d in boss],
        "vfx": [{k: d[k] for k in ("id", "source", "gridCell", "frameCount")} for d in vfx],
        "overlay": [{"id": d["id"], "gridRow": d["gridRow"],
                     "frameCount": d["frameCount"],
                     "pulsePixelDeltaRatio": d["pulsePixelDeltaRatio"]} for d in ovl],
        "background": [{"scene": d["scene"], "reference": d["reference"],
                        "shippedMode": d["shippedMode"],
                        "combatDarkRatioFaithful": d["combatDarkRatioFaithful"],
                        "combatDarkRatioShipped": d["combatDarkRatioShipped"],
                        "l4AreaRatio": d["l4AreaRatio"]} for d in bg],
        "exceptions": [
            "vfx_hit 没有对应回稿（C1 只有 4 格），保留第 29 轮程序化 4 帧",
            "A1 / A3 / B / C1 / C2 是方图或排版稿，已按目标画幅裁格；方图背景居中裁 16:9 会损失上下内容",
            "默认入库不调色；原稿战斗区暗像素比超 30% 的场景已在 bg-layers-report.json 的 r22Disclosure 如实登记",
            "B 组概念稿的标注文字 / 格线已用最大连通域剔除，立绘主体完整保留",
            "status 一律沿用「待目检与合规确认；不得直接入库」；Q17 / GUI F5 未过",
        ],
        "status": "HEADLESS 静态指标自检；画面未验证",
    }
    (ROOT / "docs" / "reference-transcription-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只复算指标，不写文件")
    ap.add_argument("--tuned", action="store_true",
                    help="入库背景改用 24 色阶梯调和版（默认原稿保真，不替用户改配色）")
    args = ap.parse_args()

    boss = build_boss(args.check)
    vfx = build_vfx(args.check)
    ovl = build_overlay(args.check)
    bg, extra = build_bg(args.check, args.tuned)

    all_frames = [f for d in boss + vfx + ovl for f in d["frames"].values()]
    bad = [f for f in all_frames if f["outOfPalette"] or f["semiAlphaLevels"]]
    result = {
        "groups": len(boss) + len(vfx) + len(ovl),
        "frames": len(all_frames),
        "badFrames": len(bad),
        "bgScenes": len(bg),
        "bgOutOfPalette": sum(s["outOfPaletteTotal"] for s in bg),
        "bgSemiAlpha": sum(s["semiAlphaTotal"] for s in bg),
        "bgBandStray": sum(s["layers"][k]["bandStrayPixels"] for s in bg for k in BANDS),
        "bgR22AllUnder30": all(s["combatDarkUnder30Percent"] for s in bg),
        "bgR22KnownExceptions": [s["scene"] for s in bg
                                 if not s["combatDarkUnder30Percent"]],
        "bgL4All": all(s["l4Under10Percent"] for s in bg),
        "watermark": extra.get("watermark", {}),
    }
    if not args.check:
        report = write_reports(False, boss, vfx, ovl, bg, extra)
        result["report"] = "docs/reference-transcription-report.json"
        print(json.dumps(report["watermark"], ensure_ascii=False))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if bad:
        print("BAD:", [f for f in bad][:5], file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
