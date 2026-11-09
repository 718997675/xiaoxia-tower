#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B3 / B4 程序化像素素材生成器（第 29 轮，零出图积分、可复现）

用途：补齐 docs/06 §4/§5/§6 里 B3（两个 Boss 正式帧表）与 B4
      （剩余 4 技能特效 / 通用命中 / 5 组状态 overlay）的入库候选资源。

口径（不得省略）：
  - Q21=128 → Boss 单帧 128x128；Q24=procedural_plus_pixelfx → 本脚本产出的
    PNG 是【形状样板 / 形状板级实现】，运行时实现形态仍按回执走程序化 shader，
    不得把本批序列帧写成「特效系统已完成」（C01 / R55 / docs/21 §8）。
  - 三个 Boss 阶段不重画轮廓：本批只出第一阶段（青玉 / 墨 / 朱砂），
    紫 / 金阶段由运行时换色 + 纹样道数实现，报告里注明。
  - 全部输出 24 色锁定板、1px 纯黑描边、硬边透明、半透明像素 0、无抗锯齿。
  - 每组的 status 沿用既有引擎 JSON 的「待目检与合规确认；不得直接入库」。
    本脚本只产静态可导入资源，不代表 GUI F5 目检通过、不代表接入 Godot。

用法：
  python3 tools/build_b3b4_assets.py
  python3 tools/build_b3b4_assets.py --check     # 只复算已产出文件的指标，不写 PNG

产出：
  assets/boss/boss_judge_*.png          18 帧（idle3/run3/atk4/skill4/hit1/death3）
  assets/boss/boss_tower_lord_*.png    24 帧（skill 10 = 18 帧表里 4 + 追加 4 + 大招起手 2）
  assets/vfx/frames/vfx_<4 个 id>_0*.png / vfx_hit_00..03.png
  assets/vfx/overlay/ovl_<5 个 id>_00..01.png
  各组同名 .json（引擎元数据）+ _report.json（生成/体检报告）
  assets/_preview/b3b4_contact_sheet.png        全批联系表（NEAREST 2x）
  docs/b3b4-build-report.json                   汇总（相对路径，无机器绝对路径）

规格来源：docs/06-素材生产清单.md §3/§4/§5/§6、docs/asset-manifest-pixel.json、
          docs/asset-content-manifest.json（Q21 / Q24 回执）、docs/20-场景与Boss外发提示词.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BOSS_DIR = ROOT / "assets/boss"
VFX_DIR = ROOT / "assets/vfx/frames"
OVL_DIR = ROOT / "assets/vfx/overlay"
PREVIEW_DIR = ROOT / "assets/_preview"
REPORT_PATH = ROOT / "docs/b3b4-build-report.json"

PALETTE_HEX = [
    "#12161F", "#2A3140", "#4A5568",          # 墨
    "#8A8268", "#C9BFA3", "#E8DFC8",          # 宣纸
    "#2F6E6A", "#5FA8A0", "#9BD4CC",          # 青玉
    "#7A2420", "#C8453B", "#E8806F",          # 朱砂
    "#8A6520", "#D9A441", "#F2D089",          # 金
    "#4A3A6B", "#8A6FC4", "#C0A8E0",          # 紫
    "#000000", "#FFFFFF",                      # 功能色：描边 / 闪白
]
PALETTE = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in PALETTE_HEX}
TRANSPARENT = (0, 0, 0, 0)


def C(hexstr: str) -> tuple[int, int, int, int]:
    h = hexstr.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


INK = C("#000000")
WHITE = C("#FFFFFF")
MO1, MO2, MO3 = C("#12161F"), C("#2A3140"), C("#4A5568")
PAPER_DD, PAPER_D, PAPER = C("#8A8268"), C("#C9BFA3"), C("#E8DFC8")
JADE_D, JADE, JADE_L = C("#2F6E6A"), C("#5FA8A0"), C("#9BD4CC")
RED_D, RED, RED_L = C("#7A2420"), C("#C8453B"), C("#E8806F")
GOLD_D, GOLD, GOLD_L = C("#8A6520"), C("#D9A441"), C("#F2D089")
VIO_D, VIO, VIO_L = C("#4A3A6B"), C("#8A6FC4"), C("#C0A8E0")


def canvas(size: int) -> Image.Image:
    return Image.new("RGBA", (size, size), TRANSPARENT)


def rect(d: ImageDraw.ImageDraw, box, fill, outline=INK):
    d.rectangle(box, fill=fill)
    if outline:
        d.rectangle(box, outline=outline, width=1)


def poly(d: ImageDraw.ImageDraw, pts, fill, outline=INK):
    d.polygon(pts, fill=fill)
    if outline:
        d.line(list(pts) + [pts[0]], fill=outline, width=1)


def line(d: ImageDraw.ImageDraw, pts, fill, width=3):
    d.line(pts, fill=fill, width=width)


def hollow_polygon(d: ImageDraw.ImageDraw, outer, inner, fill, outline=INK):
    """硬边空心环：外多边形填色，内多边形用全透明覆盖（不是半透明）。"""
    poly(d, outer, fill, outline)
    d.polygon(inner, fill=TRANSPARENT)
    if outline:
        d.line(list(inner) + [inner[0]], fill=outline, width=1)


# ---------------------------------------------------------------------------
# B3 · 两个 Boss（128x128，脚底锚点 y=126）
# ---------------------------------------------------------------------------

def draw_judge(action: str, idx: int) -> Image.Image:
    """锁血判官：横向梯形 + 乌纱帽 + 朱砂印文，与塔主的纵向剪影一眼可分。"""
    im = canvas(128)
    d = ImageDraw.Draw(im)
    flash = action == "hit"
    F = (lambda c: WHITE) if flash else (lambda c: c)
    O = WHITE if flash else INK

    dy = {"idle": (0, -2, 0), "run": (0, -3, 1), "atk": (0, -1, 1, 0),
          "skill": (0, -2, -4, -3)}.get(action, (0,) * 10)[idx]
    lean = (0, 3, 7, 3)[idx] if action == "atk" else 0
    arm = (0, 6, 14, 9)[idx] if action == "atk" else 0
    aura = (0, 3, 6, 9)[idx] if action == "skill" else 0
    x = lean

    # 判官笔（右侧纵向硬边条），长 >= 3px，避免孤立噪点
    rect(d, (106 + x, 52 + dy, 111 + x, 96 + dy - arm // 2), F(GOLD_D), O)
    # 下摆
    poly(d, [(28 + x, 106 + dy), (100 + x, 106 + dy),
             (104 + x, 126 + dy), (24 + x, 126 + dy)], F(MO1), O)
    # 肩 + 宽袍（横向梯形）
    poly(d, [(36 + x, 54 + dy), (92 + x, 54 + dy),
             (100 + x, 108 + dy), (28 + x, 108 + dy)], F(MO2), O)
    rect(d, (26 + x, 56 + dy, 102 + x, 68 + dy), F(RED_D), O)
    # 双臂：atk 时右臂抬起
    rect(d, (14 + x, 66 + dy, 30 + x, 100 + dy), F(MO2), O)
    rect(d, (98 + x, 66 + dy, 114 + x, 100 + dy - arm), F(MO2), O)
    # 乌纱帽 + 帽翅
    rect(d, (42 + x, 14 + dy, 86 + x, 34 + dy), F(MO1), O)
    rect(d, (24 + x, 22 + dy, 42 + x, 31 + dy), F(MO1), O)
    rect(d, (86 + x, 22 + dy, 104 + x, 31 + dy), F(MO1), O)
    # 头 / 目
    rect(d, (48 + x, 34 + dy, 80 + x, 56 + dy), F(PAPER_D), O)
    line(d, [(54 + x, 44 + dy), (60 + x, 44 + dy)], F(INK) if flash else INK, 3)
    line(d, [(68 + x, 44 + dy), (74 + x, 44 + dy)], F(INK) if flash else INK, 3)
    # 朱砂印文：锁血触发的视觉锚，skill 时换亮阶（不新增轮廓）
    seal = RED_L if aura >= 6 else (RED if aura >= 3 else RED_D)
    rect(d, (54 + x, 78 + dy, 74 + x, 98 + dy), F(seal), O)
    line(d, [(59 + x, 88 + dy), (69 + x, 88 + dy)], F(RED_L) if flash else GOLD_L, 3)
    line(d, [(64 + x, 82 + dy), (64 + x, 94 + dy)], F(RED_L) if flash else GOLD_L, 3)
    # 袍上横向金线 3 道（3px 宽，长度 >= 6）
    for k in range(3):
        line(d, [(40 + x, 100 + dy - k * 6), (88 + x, 100 + dy - k * 6)],
             F(GOLD_D) if not flash else WHITE, 3)
    return im


def draw_tower_lord(action: str, idx: int) -> Image.Image:
    """天梯之主：高耸纵向 + 外扩肩甲 + 层叠高冠 + 硬边半环背光。"""
    im = canvas(128)
    d = ImageDraw.Draw(im)
    flash = action == "hit"
    F = (lambda c: WHITE) if flash else (lambda c: c)
    O = WHITE if flash else INK

    dy = {"idle": (0, -2, 0), "run": (0, -3, 1), "atk": (0, -1, 1, 0),
          "skill": (0, -2, -3, -4, -5, -6, -6, -5, -4, -3)}.get(action, (0,) * 10)[idx]
    lean = (0, 2, 5, 2)[idx] if action == "atk" else 0
    arm = (0, 5, 12, 8)[idx] if action == "atk" else 0
    aura = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)[idx] if action == "skill" else 0
    x = lean

    # 硬边几何半环背光（同心色块阶梯，不是渐变也不是辉光）
    for ring, col in enumerate((JADE_D, JADE, JADE_L)):
        r = 42 + ring * 6 + aura
        d.rectangle((64 - r, 44 + dy - r // 2, 64 + r, 44 + dy + 4),
                    outline=F(col) if not flash else WHITE, width=3)
    # 高冠三层
    rect(d, (54 + x, 6 + dy, 74 + x, 20 + dy), F(JADE_D), O)
    rect(d, (50 + x, 18 + dy, 78 + x, 27 + dy), F(JADE), O)
    rect(d, (46 + x, 26 + dy, 82 + x, 33 + dy), F(GOLD_D), O)
    # 外扩肩甲
    poly(d, [(22 + x, 50 + dy), (44 + x, 48 + dy), (44 + x, 70 + dy),
             (18 + x, 70 + dy)], F(JADE_D), O)
    poly(d, [(84 + x, 48 + dy), (106 + x, 50 + dy), (110 + x, 70 + dy),
             (84 + x, 70 + dy)], F(JADE_D), O)
    # 宽袍（纵向）+ 下摆
    poly(d, [(40 + x, 48 + dy), (88 + x, 48 + dy),
             (98 + x, 118 + dy), (30 + x, 118 + dy)], F(JADE_D), O)
    poly(d, [(30 + x, 118 + dy), (98 + x, 118 + dy),
             (102 + x, 126 + dy), (26 + x, 126 + dy)], F(MO1), O)
    # 头
    rect(d, (54 + x, 32 + dy, 74 + x, 50 + dy), F(PAPER_D), O)
    line(d, [(58 + x, 41 + dy), (63 + x, 41 + dy)], INK, 3)
    line(d, [(65 + x, 41 + dy), (70 + x, 41 + dy)], INK, 3)
    # 双手交叠，skill 时上举
    rect(d, (50 + x, 80 + dy - aura * 2, 78 + x, 90 + dy - aura * 2), F(PAPER), O)
    # 袍上 5 道金纹（第一阶段 5 道；紫 / 金阶段运行时改 7 / 9 道，不重画轮廓）
    for k in range(5):
        yy = 96 + dy - k * 7
        line(d, [(44 + x, yy), (84 + x, yy)], F(GOLD) if not flash else WHITE, 3)
    # atk 时右臂前伸
    if action == "atk" and arm:
        rect(d, (100 + x, 62 + dy, 118 + x, 78 + dy - arm // 3), F(JADE), O)
    return im


def draw_death(which: str, idx: int) -> Image.Image:
    """崩解 3 帧：整块剪影拆成 >=3px 的色块并下移，逐帧减少。"""
    im = canvas(128)
    d = ImageDraw.Draw(im)
    base = MO2 if which == "judge" else JADE_D
    accent = RED_D if which == "judge" else GOLD_D
    blocks = [
        (34, 40, 94, 62), (30, 64, 98, 88), (36, 90, 92, 112),
        (22, 52, 32, 76), (96, 52, 106, 76), (46, 24, 82, 38),
    ]
    keep = 6 - idx * 2
    for i, (x0, y0, x1, y1) in enumerate(blocks[:keep]):
        drop = idx * (8 + i * 2)
        shrink = idx * 3
        col = accent if i % 3 == 0 else base
        rect(d, (x0 + shrink, y0 + drop, x1 - shrink, y1 + drop), col, INK)
    return im


BOSS_TABLE = {
    "boss_judge": {"draw": draw_judge, "size": 128, "fps": 6.0,
                   "table": {"idle": 3, "run": 3, "atk": 4, "skill": 4,
                             "hit": 1, "death": 3}},
    "boss_tower_lord": {"draw": draw_tower_lord, "size": 128, "fps": 6.0,
                        "table": {"idle": 3, "run": 3, "atk": 4, "skill": 10,
                                  "hit": 1, "death": 3}},
}


# ---------------------------------------------------------------------------
# B4 · 剩余 4 技能 + 通用命中（64x64，中心锚点）
# ---------------------------------------------------------------------------

def vfx_flying_sword(i: int) -> Image.Image:
    """斜向三道细长飞剑；靠方向（斜）与剑数区别于横弧剑气。"""
    im = canvas(64)
    d = ImageDraw.Draw(im)
    for k in range(3):
        off = (i * 5 + k * 9) - 12
        y = 18 + k * 12 + off // 3
        x = 12 + off
        poly(d, [(x, y + 8), (x + 30, y - 8), (x + 36, y - 11),
                 (x + 8, y + 5)], JADE if k != 1 else JADE_L, INK)
        rect(d, (x + 2, y + 6, x + 8, y + 9), GOLD, INK)
    return im


def vfx_paper_puppet(i: int) -> Image.Image:
    """方形符纸旋转展成傀儡剪影，第 3/4 帧定形。"""
    im = canvas(64)
    d = ImageDraw.Draw(im)
    if i <= 1:
        s = 14 + i * 8
        poly(d, [(32, 32 - s), (32 + s, 32), (32, 32 + s), (32 - s, 32)],
             PAPER, INK)
        rect(d, (28, 28, 36, 36), RED_D, INK)
        line(d, [(26, 26), (38, 38)], RED, 3)
    else:
        rect(d, (20, 14, 44, 38), PAPER, INK)          # 方符头
        rect(d, (24, 38, 40, 56), PAPER_D, INK)         # 身
        rect(d, (14, 38, 22, 52), RED_D, INK)           # 左臂
        rect(d, (42, 38, 50, 52), RED_D, INK)           # 右臂
        rect(d, (27, 22, 32, 27), RED, INK)
        rect(d, (34, 22, 39, 27), RED, INK)
        if i == 3:
            line(d, [(26, 44), (38, 44)], GOLD_D, 3)    # 收势印文
    return im


def vfx_fist_force(i: int) -> Image.Image:
    """短距扇形冲击波，贴地由窄到宽推进。"""
    im = canvas(64)
    d = ImageDraw.Draw(im)
    w = 10 + i * 12
    y = 48 - i * 3
    poly(d, [(32, y), (32 - w, 56), (32 + w, 56), (32, y - 6)], MO3, INK)
    poly(d, [(32, y - 4), (32 - w + 6, 54), (32 + w - 6, 54)], GOLD_D, INK)
    line(d, [(32 - w // 2, 54), (32 + w // 2, 54)], GOLD_L, 3)
    return im


def hexagon(cx, cy, r):
    return [(cx + r, cy), (cx + r // 2, cy - r), (cx - r // 2, cy - r),
            (cx - r, cy), (cx - r // 2, cy + r), (cx + r // 2, cy + r)]


def vfx_vajra_body(i: int) -> Image.Image:
    """六边形金罩空环，脉动 4 帧（半径递进 + 亮阶换色）。"""
    im = canvas(64)
    d = ImageDraw.Draw(im)
    r = 20 + (i % 2) * 2
    col = GOLD if i % 2 == 0 else GOLD_L
    hollow_polygon(d, hexagon(32, 32, r), hexagon(32, 32, r - 6), col, INK)
    for k in range(6):
        a = hexagon(32, 32, r)[k]
        rect(d, (a[0] - 2, a[1] - 2, a[0] + 2, a[1] + 2), GOLD_L, INK)
    return im


def vfx_hit(i: int) -> Image.Image:
    """通用命中：四向星芒，起手 / 成长 / 峰值 / 消散。"""
    im = canvas(64)
    d = ImageDraw.Draw(im)
    r = (6, 12, 20, 10)[i]
    col = (RED_L, RED, GOLD_L, GOLD_D)[i]
    poly(d, [(32, 32 - r), (36, 28), (32 + r, 32), (36, 36),
             (32, 32 + r), (28, 36), (32 - r, 32), (28, 28)], col, INK)
    rect(d, (29, 29, 35, 35), WHITE if i == 2 else GOLD_L, INK)
    return im


VFX_TABLE = {
    "vfx_flying_sword": vfx_flying_sword,
    "vfx_paper_puppet": vfx_paper_puppet,
    "vfx_fist_force": vfx_fist_force,
    "vfx_vajra_body": vfx_vajra_body,
    "vfx_hit": vfx_hit,
}


# ---------------------------------------------------------------------------
# B4 · 5 组状态 overlay（64x64，每组 2 帧）
# 两帧【同形状、只换亮阶】：像素数差 0%，满足 docs/21 sheetPulse <=25% 口径。
# ---------------------------------------------------------------------------

def ovl_shield(bright):
    im = canvas(64)
    d = ImageDraw.Draw(im)
    col = JADE_L if bright else JADE
    hollow_polygon(d, hexagon(32, 32, 25), hexagon(32, 32, 20), col, INK)
    line(d, [(32, 8), (32, 14)], GOLD_L, 3)
    return im


def ovl_elite(bright):
    im = canvas(64)
    d = ImageDraw.Draw(im)
    col = GOLD_L if bright else GOLD
    d.rectangle((7, 7, 56, 56), outline=col, width=3)
    for x, y in ((7, 7), (52, 7), (7, 52), (52, 52)):
        rect(d, (x, y, x + 6, y + 6), col, INK)
    return im


def ovl_burn(bright):
    im = canvas(64)
    d = ImageDraw.Draw(im)
    col = RED_L if bright else RED
    for cx in (16, 32, 48):
        poly(d, [(cx, 16), (cx + 7, 34), (cx + 4, 52),
                 (cx - 4, 52), (cx - 7, 34)], col, INK)
        rect(d, (cx - 2, 38, cx + 2, 48), GOLD_L, INK)
    return im


def ovl_chill(bright):
    im = canvas(64)
    d = ImageDraw.Draw(im)
    col = JADE_L if bright else JADE
    for cx in (16, 32, 48):
        poly(d, [(cx, 12), (cx + 9, 32), (cx, 52), (cx - 9, 32)], col, INK)
        line(d, [(cx, 20), (cx, 44)], PAPER, 3)
        line(d, [(cx - 6, 32), (cx + 6, 32)], PAPER, 3)
    return im


def ovl_affix(bright):
    im = canvas(64)
    d = ImageDraw.Draw(im)
    col = RED_L if bright else RED
    d.rectangle((10, 10, 54, 54), outline=col, width=3)
    rect(d, (18, 18, 46, 46), RED_D, INK)
    line(d, [(22, 22), (42, 42)], col, 3)
    line(d, [(42, 22), (22, 42)], col, 3)
    return im


OVL_TABLE = {
    "ovl_shield": ovl_shield,
    "ovl_elite": ovl_elite,
    "ovl_burn": ovl_burn,
    "ovl_chill": ovl_chill,
    "ovl_affix": ovl_affix,
}


# ---------------------------------------------------------------------------
# 通用输出 / 指标
# ---------------------------------------------------------------------------

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
        "outOfPalette": len([c for c in colors if c not in PALETTE]),
        "semiAlphaLevels": sum(1 for a in alphas if 0 < a < 255),
        "opaquePixels": opaque,
    }


def engine_json(path: Path, ident: str, kind: str, size: int, fps: float,
                frames: list[str], anchor_note: str) -> None:
    data = {
        "version": 1,
        "id": ident,
        "kind": kind,
        "frameSize": [size, size],
        "logicalResolution": [480, 270],
        "integerScale": 4,
        "palette": PALETTE_HEX,
        "paletteReservedSlots": 4,
        "fps": fps,
        "frameCount": len(frames),
        "frames": frames,
        "appendedFromPreviousBatches": False,
        "anchor": {"x": size // 2,
                   "y": size - 2 if kind == "boss" else size // 2,
                   "note": anchor_note},
        "hitbox": [24, 32],
        "hitboxOffsetX": 16,
        "loop": True,
        "status": "待目检与合规确认；不得直接入库",
        "pipeline": "程序化像素（Pillow 几何绘制，0 出图积分）",
        "implementationForm": ("形状样板 / 运行时按 Q24 走程序化 shader，不作运行时绑定"
                               if kind in ("vfx", "ovl") else "第一阶段配色；阶段二/三靠换色 + 纹样道数，不重画轮廓"),
    }
    (path / f"{ident}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_group(out_dir: Path, ident: str, kind: str, size: int, fps: float,
                images: list[tuple[str, Image.Image]], anchor_note: str,
                extra: dict | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    names = []
    for name, im in images:
        if not im.mode == "RGBA":
            im = im.convert("RGBA")
        im.save(out_dir / name)
        names.append(name)
    engine_json(out_dir, ident, kind, size, fps, names, anchor_note)
    per = {name: frame_metrics(im) for name, im in images}
    report = {
        "id": ident,
        "kind": kind,
        "pipeline": "tools/build_b3b4_assets.py（程序化，0 积分）",
        "frameCount": len(images),
        "frames": per,
        "outOfPaletteTotal": sum(v["outOfPalette"] for v in per.values()),
        "semiAlphaTotal": sum(v["semiAlphaLevels"] for v in per.values()),
        "status": "静态资源已产出；GUI F5 目检 / 实机对比度 / 帧率一律待实测",
        "note": "报告内不含机器绝对路径",
    }
    if extra:
        report.update(extra)
    (out_dir / f"{ident}_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"id": ident, "frameCount": len(images),
            "outOfPaletteTotal": report["outOfPaletteTotal"],
            "semiAlphaTotal": report["semiAlphaTotal"],
            "minCoverage": min(v["coverage"] for v in per.values()),
            "maxCoverage": max(v["coverage"] for v in per.values())}


def build_contact_sheet(groups: list[tuple[str, list[tuple[str, Image.Image]]]]) -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    scale = 2
    cell = 64 * scale
    per_row = 12
    rows = []
    for _, imgs in groups:
        for i in range(0, len(imgs), per_row):
            rows.append(imgs[i:i + per_row])
    height = len(rows) * cell
    sheet = Image.new("RGBA", (per_row * cell, height), PAPER_D)
    for r, row in enumerate(rows):
        for c, (_, im) in enumerate(row):
            big = im.resize((cell, cell), Image.NEAREST)
            sheet.alpha_composite(big, (c * cell, r * cell))
    sheet.convert("RGB").save(PREVIEW_DIR / "b3b4_contact_sheet.png")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="只复算已有 PNG 的尺寸 / 色板 / 半透明指标，不写文件")
    args = ap.parse_args()

    if args.check:
        results = []
        for d in (BOSS_DIR, VFX_DIR, OVL_DIR):
            for p in sorted(d.glob("*.png")):
                m = frame_metrics(Image.open(p).convert("RGBA"))
                results.append({"file": str(p.relative_to(ROOT)), **m})
        bad = [r for r in results if r["outOfPalette"] or r["semiAlphaLevels"]]
        print(json.dumps({"count": len(results), "bad": bad[:10]},
                         ensure_ascii=False, indent=2))
        return

    groups: list[tuple[str, list[tuple[str, Image.Image]]]] = []
    summary = []

    # B3
    for ident, spec in BOSS_TABLE.items():
        imgs = []
        for action, count in spec["table"].items():
            for idx in range(count):
                if action == "death":
                    im = draw_death(ident, idx)
                else:
                    im = spec["draw"](action, idx)
                imgs.append((f"{ident}_{action}_r_{idx:02d}.png", im))
        groups.append((ident, imgs))
        summary.append(write_group(
            BOSS_DIR, ident, "boss", spec["size"], spec["fps"], imgs,
            "脚底锚点，全组统一且落在同一整数像素行",
            {"frameTable": spec["table"],
             "q21SizeReceipt": "128x128（docs/decision-receipt.json Q21）",
             "phasePolicy": "只出第一阶段青玉/墨/朱砂；紫/金阶段运行时换色 + 纹样 5/7/9 道，不重画"}))

    # B4 · 技能 + 命中
    for ident, fn in VFX_TABLE.items():
        imgs = [(f"{ident}_{i:02d}.png", fn(i)) for i in range(4)]
        groups.append((ident, imgs))
        summary.append(write_group(
            VFX_DIR, ident, "vfx", 64, 12.0, imgs,
            "特效中心，与判定框对齐",
            {"shapeLanguage": {
                "vfx_flying_sword": "斜向三道飞剑",
                "vfx_paper_puppet": "方形符纸展成傀儡",
                "vfx_fist_force": "贴地短距扇形波",
                "vfx_vajra_body": "六边形金罩空环",
                "vfx_hit": "通用四向星芒命中",
            }[ident],
             "q24Note": "PNG 为形状样板；运行时按 Q24=procedural_plus_pixelfx 走程序化 shader"}))

    # B4 · overlay
    for ident, fn in OVL_TABLE.items():
        imgs = [(f"{ident}_{i:02d}.png", fn(bool(i))) for i in range(2)]
        groups.append((ident, imgs))
        a = frame_metrics(imgs[0][1])["opaquePixels"]
        b = frame_metrics(imgs[1][1])["opaquePixels"]
        pulse = round(abs(a - b) / max(a, b), 4)
        summary.append(write_group(
            OVL_DIR, ident, "ovl", 64, 4.0, imgs,
            "状态层中心，与角色 Sprite2D 对齐",
            {"pulsePixelDeltaRatio": pulse,
             "pulsePolicy": "两帧同形状、只换亮阶（像素数差 0%，满足 docs/21 sheetPulse <=25%）",
             "q24Note": "运行时可由 shader 替代；PNG 为形状样板"}))

    build_contact_sheet(groups)
    report = {
        "round": 29,
        "tool": "tools/build_b3b4_assets.py",
        "scope": "B3 两个 Boss 正式帧表 + B4 剩余 4 技能 / 命中 / 5 组 overlay",
        "pipeline": "程序化像素几何绘制，0 出图积分、0 张 AI 源图",
        "paletteSource": "docs/asset-manifest-pixel.json（24 色锁定板）",
        "groups": summary,
        "totals": {
            "groups": len(summary),
            "frames": sum(s["frameCount"] for s in summary),
            "bossFrames": sum(s["frameCount"] for s in summary if s["id"].startswith("boss_")),
            "vfxFrames": sum(s["frameCount"] for s in summary if s["id"].startswith("vfx_")),
            "overlayFrames": sum(s["frameCount"] for s in summary if s["id"].startswith("ovl_")),
            "outOfPaletteTotal": sum(s["outOfPaletteTotal"] for s in summary),
            "semiAlphaTotal": sum(s["semiAlphaTotal"] for s in summary),
        },
        "boundaries": [
            "全部只算静态可导入资源，status 沿用「待目检与合规确认；不得直接入库」",
            "Q17 未拍板、GUI F5 未跑、正式战斗工程未建；本轮不接任何 Godot 场景",
            "Q24=procedural_plus_pixelfx：特效 / overlay 的运行时实现形态仍是程序化 shader，PNG 仅作形状样板",
            "贴图内存、帧率、实机对比度（R22）、hitboxOffsetX=16px、4x 排版一律待实测",
            "Boss 三阶段的紫 / 金不重画轮廓，靠换色 + 纹样 5/7/9 道，本批只出第一阶段",
            "本轮不修改冻结数值、抽卡规则、docs/06 正文、docs/asset-manifest-pixel.json",
        ],
        "status": "HEADLESS 静态指标自检；画面未验证",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(json.dumps(report["totals"], ensure_ascii=False, indent=2))
    for s in summary:
        print(f"  {s['id']:<24} {s['frameCount']:>2} 帧  "
              f"越界色 {s['outOfPaletteTotal']}  半透明 {s['semiAlphaTotal']}  "
              f"coverage {s['minCoverage']:.3f}~{s['maxCoverage']:.3f}")


if __name__ == "__main__":
    main()
