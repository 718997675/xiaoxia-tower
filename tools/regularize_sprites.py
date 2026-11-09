#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
像素素材规整器（项目自带，可复现，换机器只需 Python + Pillow）

用途：把 AI 生成的「2x2 多格动作条」源图，规整成引擎可直接导入的
      64x64 透明硬边 PNG 序列帧 + 精灵图 + 动画 GIF 预览 + 引擎 JSON。

设计要点：
  1. 四格用【统一裁剪框】——这是像素动画帧间一致性的关键，逐格各自裁剪会漂移。
  2. 白底用【从四角 BFS floodfill】删除，只删连到边缘的背景，保护内部米白高光。
  3. 缩放一律 NEAREST，不做任何平滑，保证硬边。
  4. 所有非透明像素【吸附到 24 色锁定调色板】，越界色数必须为 0。
  5. 人物脚底对齐到同一整数像素行，底部留 >=1px 透明边。

用法：
  python3 tools/regularize_sprites.py \
      --source assets/_source/xxx.png --kind char \
      --prefix char_player_idle --names idle_r_00 idle_r_01 idle_r_02 \
      --out assets/char

  python3 tools/regularize_sprites.py \
      --source assets/_source/yyy.png --kind vfx \
      --prefix vfx_sword_qi --names 00 01 02 03 \
      --out assets/vfx/frames

规格来源：docs/asset-manifest-pixel.json、docs/04-像素国风规格修订.md
"""
from __future__ import annotations

import argparse
import json
import os
from collections import deque
from pathlib import Path

from PIL import Image

# 24 色锁定调色板（与 asset-manifest-pixel.json 一致）
PALETTE_HEX = [
    "#12161F", "#2A3140", "#4A5568",          # 墨
    "#8A8268", "#C9BFA3", "#E8DFC8",          # 宣纸
    "#2F6E6A", "#5FA8A0", "#9BD4CC",          # 青玉
    "#7A2420", "#C8453B", "#E8806F",          # 朱砂
    "#8A6520", "#D9A441", "#F2D089",          # 金
    "#4A3A6B", "#8A6FC4", "#C0A8E0",          # 紫
    "#000000", "#FFFFFF",                      # 功能色：描边 / 闪白
]
PALETTE = [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in PALETTE_HEX]
RESERVED_SLOTS = 4
FRAME_SIZE = 64
BOTTOM_PADDING = 2          # 人物脚底留 2px 透明边
SIDE_PADDING = 2            # 左右各留 2px，防止攻击/前扑帧贴边切爪
VFX_MARGIN = 4              # 特效四周留边
GIF_SCALE = 4
PREVIEW_SCALE = 6


def is_near_white(rgb, tol=30):
    r, g, b = rgb[:3]
    return min(r, g, b) >= 255 - tol


def remove_white_bg(cell: Image.Image, tol=30) -> Image.Image:
    """从四角 BFS，只删除与边缘连通的白色背景。"""
    im = cell.convert("RGBA")
    w, h = im.size
    px = im.load()
    seen = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not seen[y][x] and is_near_white(px[x, y], tol):
                seen[y][x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not seen[y][x] and is_near_white(px[x, y], tol):
                seen[y][x] = True
                q.append((x, y))
    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and is_near_white(px[nx, ny], tol):
                seen[ny][nx] = True
                q.append((nx, ny))
    # 二次清理：只删【紧贴已透明区域】的近白抗锯齿像素。
    # 不能全图遍历删近白 —— 特效内部的纯白亮核会被误删成黑洞（B0 丹火实测）。
    edge_candidates = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 0 and min(r, g, b) >= 235:
                if any(0 <= nx < w and 0 <= ny < h and px[nx, ny][3] == 0
                       for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))):
                    edge_candidates.append((x, y))
    for x, y in edge_candidates:
        px[x, y] = (0, 0, 0, 0)

    # 清掉 AI 源图常见的 1-2px 孤立杂点，不碰主体连通域
    visited = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if visited[y][x] or px[x, y][3] == 0:
                continue
            comp, stack = [], [(x, y)]
            visited[y][x] = True
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and px[nx, ny][3] > 0:
                        visited[ny][nx] = True
                        stack.append((nx, ny))
            if len(comp) <= 2:
                for cx, cy in comp:
                    px[cx, cy] = (0, 0, 0, 0)
    return im


def clear_enclosed_white(im: Image.Image, threshold=245, min_area=16) -> Image.Image:
    """删除【不与格子边缘连通】的纯白连通域。

    仅用于 --hollow：空心环 / 六边罩这类特效，内部白底被轮廓完全包围，
    边缘 floodfill 到不了，规整后会留下一块实心白饼。
    阈值 245 只吃近乎纯白的背景；米白亮核 #E8DFC8 (min=200) 与浅色内缘
    不受影响，避免重演 B0「亮核被抠成黑洞」。
    """
    w, h = im.size
    px = im.load()
    seen = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if seen[y][x] or px[x, y][3] == 0 or min(px[x, y][:3]) < threshold:
                continue
            comp, stack, touches_edge = [], [(x, y)], False
            seen[y][x] = True
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                if cx in (0, w - 1) or cy in (0, h - 1):
                    touches_edge = True
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if (0 <= nx < w and 0 <= ny < h and not seen[ny][nx]
                            and px[nx, ny][3] > 0 and min(px[nx, ny][:3]) >= threshold):
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if not touches_edge and len(comp) >= min_area:
                for cx, cy in comp:
                    px[cx, cy] = (0, 0, 0, 0)
    return im


ACTION_ORDER = ["idle", "run", "cast", "atk", "skill", "hit", "death"]


def frame_sort_key(name: str):
    """按动作语义排序，保证合并后的引擎 JSON / 预览顺序符合动画逻辑。"""
    for i, action in enumerate(ACTION_ORDER):
        if f"_{action}_" in name or f"_{action}." in name or name.endswith(f"_{action}"):
            return (i, name)
    return (len(ACTION_ORDER), name)


def snap_to_palette(im: Image.Image):
    """吸附到 24 色板，返回 (图, 越界色数, 吸附前不同色数)。"""
    px = im.load()
    before = set()
    changed = 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            before.add((r, g, b))
            if (r, g, b) in PALETTE:
                continue
            best = min(PALETTE, key=lambda c: (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2)
            px[x, y] = (best[0], best[1], best[2], a)
            changed += 1
    return im, len(before), changed


def unified_crop(cells, kind):
    """四格取统一裁剪框，保证帧间脚底/中心不漂移。"""
    boxes = [c.getbbox() for c in cells]
    boxes = [b for b in boxes if b]
    if not boxes:
        raise ValueError("所有格子都是空的，源图可能没有内容")
    left = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    right = max(b[2] for b in boxes)
    bottom = max(b[3] for b in boxes)
    if kind == "char":
        # 人物：统一底部基线，宽度取并集
        return (left, top, right, bottom)
    # 特效：以并集中心为准，取正方形区域，保证四帧同心
    cx, cy = (left + right) / 2, (top + bottom) / 2
    side = max(right - left, bottom - top) / 2
    return (int(cx - side), int(cy - side), int(cx + side), int(cy + side))


def fit_frame(cell, crop, kind, char_scale=None, anchor_mode="bottom"):
    """NEAREST 缩放 → 贴到 64x64 透明画布。

    人物：逐格按自身 bbox 裁剪，但所有帧共用【同一个缩放系数】，再强制
          水平居中 + 脚底对齐。源图各格布局不齐时，统一裁剪框会把漂移带进
          成品，所以人物必须用「逐格裁剪 + 统一 scale + 强制对齐」。
    特效：用统一裁剪框（同心正方形），保持帧间从小到大的尺寸递进。
    """
    if kind == "char":
        piece = cell.crop(cell.getbbox())
        cw, ch = piece.size
        scale = char_scale
        nw, nh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
        # 安全兜底：等比收缩，绝不只压宽度（那会把动作帧压扁）
        if nw > FRAME_SIZE - 2 * SIDE_PADDING or nh > FRAME_SIZE - BOTTOM_PADDING:
            k = min((FRAME_SIZE - 2 * SIDE_PADDING) / nw,
                    (FRAME_SIZE - BOTTOM_PADDING) / nh)
            nw, nh = max(1, int(nw * k)), max(1, int(nh * k))
        resized = piece.resize((nw, nh), Image.NEAREST)
        canvas = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))
        x = (FRAME_SIZE - nw) // 2
        # 漂浮物（剑魂 / 灵体）没有脚底基线，改用中心锚点，
        # 否则会被压到画布底部，挂到角色手上时整体偏低。
        y = ((FRAME_SIZE - nh) // 2 if anchor_mode == "center"
             else FRAME_SIZE - BOTTOM_PADDING - nh)
        canvas.paste(resized, (x, y), resized)
    else:
        piece = cell.crop(crop)
        cw, ch = piece.size
        avail = FRAME_SIZE - 2 * VFX_MARGIN
        scale = min(avail / cw, avail / ch)
        nw, nh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
        resized = piece.resize((nw, nh), Image.NEAREST)
        canvas = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))
        canvas.paste(resized, ((FRAME_SIZE - nw) // 2, (FRAME_SIZE - nh) // 2), resized)
    return canvas, round(scale, 4)


def build_sheet(frames):
    sheet = Image.new("RGBA", (FRAME_SIZE * len(frames), FRAME_SIZE), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * FRAME_SIZE, 0), f)
    return sheet


def build_gif(frames, path, kind):
    bg = (232, 223, 200, 255) if kind == "char" else (18, 22, 31, 255)
    seq = []
    for f in frames:
        big = f.resize((FRAME_SIZE * GIF_SCALE, FRAME_SIZE * GIF_SCALE), Image.NEAREST)
        flat = Image.new("RGBA", big.size, bg)
        flat.alpha_composite(big)
        seq.append(flat.convert("RGB"))
    seq[0].save(path, save_all=True, append_images=seq[1:],
                duration=[140] * (len(seq) - 1) + [180], loop=0, optimize=False)


def build_preview(frames, path, kind):
    bg = (232, 223, 200, 255) if kind == "char" else (18, 22, 31, 255)
    s = FRAME_SIZE * PREVIEW_SCALE
    out = Image.new("RGBA", (s * len(frames), s), bg)
    for i, f in enumerate(frames):
        big = f.resize((s, s), Image.NEAREST)
        out.alpha_composite(big, (i * s, 0))
    out.convert("RGB").save(path)


def main():
    global FRAME_SIZE
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--kind", choices=["char", "mob", "boss", "vfx"], required=True)
    ap.add_argument("--size", type=int, default=FRAME_SIZE,
                    help="单帧边长，2 的幂或 32 的整数倍；Boss 用 96")
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--names", nargs="+", required=True, help="帧名后缀，不含前缀与扩展名")
    ap.add_argument("--cells", nargs="+", type=int, default=None,
                    help="源图 2x2 格索引（0-3，左上/右上/左下/右下）；用于跳过不达标的格子")
    ap.add_argument("--hollow", action="store_true",
                    help="清除空心环内部不与边缘连通的纯白底；仅空心特效启用")
    ap.add_argument("--anchor", choices=["bottom", "center"], default=None,
                    help="锚点：bottom=脚底（角色/怪物默认），center=居中（漂浮物/特效）")
    ap.add_argument("--append", action="store_true",
                    help="把本批帧合并进已有 <prefix>.json，而不是覆盖；用于同一角色分批生产")
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview-out", default=None)
    ap.add_argument("--fps", type=float, default=8.0)
    args = ap.parse_args()
    FRAME_SIZE = args.size
    # 人物 / 怪物 / Boss 都走「脚底对齐」；仅特效走「同心正方形」。
    # --anchor center 用于无腿漂浮物（剑魂），保留逐格裁剪 + 统一 scale，
    # 只把落点从脚底改成画布中心。
    char_like = args.kind in ("char", "mob", "boss")
    anchor_mode = args.anchor or ("center" if args.kind == "vfx" else "bottom")

    src = Image.open(args.source).convert("RGBA")
    W, H = src.size
    cw, ch = W // 2, H // 2
    cells_raw = [src.crop((x * cw, y * ch, (x + 1) * cw, (y + 1) * ch))
                 for y in range(2) for x in range(2)]
    # 默认取前 N 格；--cells 可显式挑选，用于跳过源图里不达标的格子
    indices = args.cells if args.cells is not None else list(range(len(args.names)))
    if len(indices) != len(args.names):
        raise ValueError("--cells 数量必须与 --names 一致")
    if any(i < 0 or i > 3 for i in indices):
        raise ValueError("--cells 索引只允许 0-3（2x2 源图）")
    cells = [remove_white_bg(cells_raw[i]) for i in indices]
    if args.hollow:
        cells = [clear_enclosed_white(c) for c in cells]
    crop = unified_crop(cells, "char" if char_like else "vfx")
    # 脚底对齐类：所有帧共用同一缩放系数。
    # 必须同时按「最高帧」与「最宽帧」取 min —— 只按高度算，前扑/挥爪这类
    # 宽帧会被压扁并贴到画布边缘（B0 怪物批次实测 bbox=(0,10,64,62)）。
    char_scale = None
    if char_like:
        used = cells[:len(args.names)]
        boxes = [c.getbbox() for c in used if c.getbbox()]
        max_w = max(b[2] - b[0] for b in boxes)
        max_h = max(b[3] - b[1] for b in boxes)
        char_scale = min((FRAME_SIZE - 2 * SIDE_PADDING) / max_w,
                         (FRAME_SIZE - BOTTOM_PADDING) / max_h)

    out = Path(args.out)
    prev = Path(args.preview_out or out)
    out.mkdir(parents=True, exist_ok=True)
    prev.mkdir(parents=True, exist_ok=True)

    # 只记源图文件名，不把机器绝对路径写进项目文件（换账号续做的关键）
    frames, report = [], {"source": Path(args.source).name, "kind": args.kind,
                          "cells": indices, "hollow": args.hollow, "append": args.append,
                          "crop": list(crop), "frames": []}
    for name in args.names:
        idx = len(frames)
        frame, scale = fit_frame(cells[idx], crop, "char" if char_like else "vfx",
                                 char_scale, anchor_mode)
        frame, before_colors, snapped_px = snap_to_palette(frame)
        fname = f"{args.prefix}_{name}.png" if not name.endswith(".png") else f"{args.prefix}_{name}"
        fpath = out / fname
        frame.save(fpath)
        # Pillow 12.3 起 get_flattened_data() 取代 getdata()；老版本回退兼容。
        try:
            pix_iter = frame.get_flattened_data()
        except AttributeError:
            pix_iter = frame.getdata()
        used = {px[:3] for px in pix_iter if px[3] > 0}
        out_of_palette = sum(1 for c in used if c not in PALETTE)
        frames.append(frame)
        report["frames"].append({
            "file": fname,
            "scale": scale,
            "colorsBeforeSnap": before_colors,
            "pixelsSnapped": snapped_px,
            "usedColors": len(used),
            "outOfPalette": out_of_palette,
        })

    # --append：同一组分批生产时，合并已有帧列表并重建【整组】预览
    json_path = out / f"{args.prefix}.json"
    previous = []
    if args.append and json_path.exists():
        previous = json.loads(json_path.read_text(encoding="utf-8")).get("frames", [])
    merged = sorted(set(previous + [f["file"] for f in report["frames"]]),
                    key=frame_sort_key)
    merged_imgs = [Image.open(out / n).convert("RGBA") for n in merged]

    sheet = build_sheet(merged_imgs)
    sheet_path = prev / f"{args.prefix}_sheet.png"
    sheet.save(sheet_path)
    gif_path = prev / f"{args.prefix}.gif"
    build_gif(merged_imgs, gif_path, "char" if char_like else "vfx")
    png_preview = prev / f"{args.prefix}_preview.png"
    build_preview(merged_imgs, png_preview, "char" if char_like else "vfx")

    if char_like and anchor_mode == "bottom":
        anchor_meta = {"x": FRAME_SIZE // 2, "y": FRAME_SIZE - BOTTOM_PADDING,
                       "note": "脚底锚点，全组统一且落在同一整数像素行"}
    elif char_like:
        anchor_meta = {"x": FRAME_SIZE // 2, "y": FRAME_SIZE // 2,
                       "note": "中心锚点（漂浮物），全组统一整数像素行"}
    else:
        anchor_meta = {"x": FRAME_SIZE // 2, "y": FRAME_SIZE // 2,
                       "note": "特效中心，与判定框对齐"}

    engine = {
        "version": 1,
        "id": args.prefix,
        "kind": args.kind,
        "frameSize": [FRAME_SIZE, FRAME_SIZE],
        "logicalResolution": [480, 270],
        "integerScale": 4,
        "palette": PALETTE_HEX,
        "paletteReservedSlots": RESERVED_SLOTS,
        "fps": args.fps,
        "frameCount": len(merged),
        "frames": merged,
        "appendedFromPreviousBatches": bool(args.append and previous),
        "anchor": anchor_meta,
        "hitbox": [24, 32],
        "hitboxOffsetX": 16,
        "loop": True,
        "status": "待目检与合规确认；不得直接入库",
    }
    json_path.write_text(json.dumps(engine, ensure_ascii=False, indent=2), encoding="utf-8")

    report["outputs"] = {
        "frames": merged,
        "framesAddedThisBatch": [f["file"] for f in report["frames"]],
        "sheet": sheet_path.name, "gif": gif_path.name,
        "preview": png_preview.name, "engineJson": json_path.name,
    }
    report["paletteOutOfRangeTotal"] = sum(f["outOfPalette"] for f in report["frames"])
    (out / f"{args.prefix}_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "prefix": args.prefix, "kind": args.kind,
        "crop": list(crop), "framesThisBatch": len(frames), "framesInGroup": len(merged),
        "usedColorsPerFrame": [f["usedColors"] for f in report["frames"]],
        "paletteOutOfRangeTotal": report["paletteOutOfRangeTotal"],
        "outputs": report["outputs"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
