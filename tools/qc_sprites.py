#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全项目像素素材逐帧质检（可复现，换账号照跑；只需 Python + Pillow）

用法：
  /opt/homebrew/bin/python3 tools/qc_sprites.py
  /opt/homebrew/bin/python3 tools/qc_sprites.py --only enemy
  /opt/homebrew/bin/python3 tools/qc_sprites.py --json-out docs/qc-report.json

检查项（M7 / M8 / R19 / R20）：
  命名正则（ID 段允许下划线）、单帧尺寸、RGBA、半透明像素、
  24 色锁定调色板越界色、alpha coverage、孤立噪点连通域、
  引擎 JSON 帧数一致性、帧表动作计数、锚点整数行、报告无绝对路径。

输出：docs/qc-report.json（全部写项目内相对路径）+ 控制台摘要。
verdict: >=80 SHIP / 60-79 FIX / <60 或硬失败 REDRAW。

规格来源：docs/04-像素国风规格修订.md、docs/06-素材生产清单.md §11
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

PALETTE_HEX = [
    "#12161F", "#2A3140", "#4A5568",          # 墨
    "#8A8268", "#C9BFA3", "#E8DFC8",          # 宣纸
    "#2F6E6A", "#5FA8A0", "#9BD4CC",          # 青玉
    "#7A2420", "#C8453B", "#E8806F",          # 朱砂
    "#8A6520", "#D9A441", "#F2D089",          # 金
    "#4A3A6B", "#8A6FC4", "#C0A8E0",          # 紫
    "#000000", "#FFFFFF",                      # 功能色
]
PALETTE = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in PALETTE_HEX}

# R19：ID 段必须允许下划线（mob_zhi_kui / vfx_thunder_talisman ...），
# 旧的 [a-z0-9]+ 会把 43 帧里的 20 帧误判为非法。
PATTERNS = {
    "char": re.compile(r"^char_[a-z0-9_]+_(idle|run|cast|hit|death)_r_[0-9]{2}$"),
    "mob": re.compile(r"^mob_[a-z0-9_]+_(idle|run|atk|hit|death)_r_[0-9]{2}$"),
    "boss": re.compile(r"^boss_[a-z0-9_]+_(idle|run|atk|skill|hit|death)_r_[0-9]{2}$"),
    "vfx": re.compile(r"^vfx_[a-z0-9_]+_[0-9]{2}$"),
    "ovl": re.compile(r"^ovl_[a-z0-9_]+_[0-9]{2}$"),
    "icon": re.compile(r"^icon_[a-z0-9_]+$"),
    "acc": re.compile(r"^acc_[a-z0-9_]+$"),
}

EXPECTED = {
    "char": {"idle": 3, "run": 4, "cast": 4, "hit": 1, "death": 3},
    "mob": {"idle": 3, "run": 4, "atk": 4, "hit": 1, "death": 3},
    "boss": {"idle": 3, "run": 3, "atk": 4, "skill": 4, "hit": 1, "death": 3},
}

# 第 29 轮：docs/06 §6 给塔主的是 24 帧扩展帧表
# （18 帧表 + skill 追加 4 + 大招起手 2，都归到 skill 动作），
# 通用 boss 期望（合计 18）会把这一组判成 frameTableComplete=n/a。
# 按 ID 覆盖，不改默认契约；判据仍是「帧数总和 + 各动作计数」全匹配。
EXPECTED_OVERRIDES = {
    "boss_tower_lord": {"idle": 3, "run": 3, "atk": 4, "skill": 10,
                        "hit": 1, "death": 3},
}

SCAN_DIRS = [
    ("assets/char", "char"),
    ("assets/enemy", "mob"),
    ("assets/boss", "boss"),
    ("assets/vfx/frames", "vfx"),
    ("assets/vfx/overlay", "ovl"),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def isolated_specks(im: Image.Image) -> int:
    """统计面积 <=2px 的孤立连通域数量（AI 源图常见杂点）。"""
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    count = 0
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if seen[i] or px[x, y][3] == 0:
                continue
            q = deque([(x, y)])
            seen[i] = 1
            area = 0
            while q:
                cx, cy = q.popleft()
                area += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        j = ny * w + nx
                        if not seen[j] and px[nx, ny][3] > 0:
                            seen[j] = 1
                            q.append((nx, ny))
            if area <= 2:
                count += 1
    return count


def qc_frame(path: Path, kind: str, size: int) -> dict:
    stem = path.stem
    issues, score, hard = [], 100, False
    pat = PATTERNS.get(kind)
    if pat and not pat.match(stem):
        issues.append(f"命名不合规（{kind} 正则）")
        hard = True

    src_mode = Image.open(path).mode
    im = Image.open(path).convert("RGBA")
    if src_mode != "RGBA":
        issues.append(f"源模式 {src_mode} 非 RGBA")
        hard = True
    w, h = im.size
    if (w, h) != (size, size):
        issues.append(f"尺寸 {w}x{h} != {size}x{size}")
        hard = True

    px = im.load()
    alphas, out_colors, opaque = set(), set(), 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            alphas.add(a)
            if a > 0:
                opaque += 1
                if (r, g, b) not in PALETTE:
                    out_colors.add((r, g, b))

    semi = sum(1 for a in alphas if 0 < a < 255)
    if semi:
        issues.append(f"半透明 alpha 档位 {semi} 种")
        score -= 20
    if out_colors:
        issues.append(f"24 色板越界色 {len(out_colors)} 种")
        score -= 20

    coverage = opaque / (w * h)
    if opaque == 0:
        issues.append("空白帧（无可见像素）")
        hard = True
    # R21：阈值放宽到 [0.015, 0.92]。第 8 轮把 coverage≈0.30 当边界扣分，
    # 属误判——生长/消散型特效与小碎片死亡帧天然低覆盖，不应按素材缺陷处理。
    elif coverage < 0.015 or coverage > 0.92:
        issues.append(f"coverage={coverage:.3f} 偏离合理区间")
        score -= 15

    # 程序化图标 / 挂件里的 1px 装饰点（火花、星屑、角标）是设计意图，
    # 不是 AI 源图杂点；对 icon/acc 跳过孤立域检查，避免误判（R21 同源）。
    specks = 0 if kind in ("icon", "acc") else isolated_specks(im)
    if specks:
        issues.append(f"孤立噪点连通域 {specks} 个")
        score -= min(20, 5 * specks)

    verdict = ("REDRAW" if hard else
               "SHIP" if score >= 80 else
               "FIX" if score >= 60 else "REDRAW")
    return {
        "file": rel(path),
        "score": max(0, score),
        "verdict": verdict,
        "issues": issues,
        "size": [w, h],
        "sizeOk": (w, h) == (size, size),
        "coverage": round(coverage, 4),
        "semiAlphaLevels": semi,
        "outOfPaletteColors": len(out_colors),
        "isolatedSpecks": specks,
    }


def has_abs_path(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return "/Users/" in text or "C:\\" in text or "/home/" in text


# 单帧图标 / 挂件没有引擎 JSON，单独按目录扫描（M9）
# R24：07 §2.1 规定词缀 16x16、其余图标 32x32 两档并存；写死 32 会在
# 16x16 词缀入库时把该帧误判为尺寸不符（v0.3 工单尺寸标注也由此校正）。
LOOSE_SCAN = [
    ("assets/ui/icons", "icon", (16, 32)),
    ("assets/char/acc", "acc", 16),
]


def qc_loose_group(dirname: str, kind: str, sizes) -> dict | None:
    allowed = (sizes,) if isinstance(sizes, int) else tuple(sizes)
    folder = ROOT / dirname
    if not folder.exists():
        return None
    paths = sorted(folder.glob("*.png"))
    if not paths:
        return None
    fr = []
    for p in paths:
        w, h = Image.open(p).size
        # 用实际尺寸跑逐帧检查，再单独核对它是否落在允许的档位里
        r = qc_frame(p, kind, w)
        if w != h or w not in allowed:
            r["issues"].append(f"尺寸 {w}x{h} 不在允许档位 {allowed}")
            r["sizeOk"] = False
            r["verdict"] = "REDRAW"
        fr.append(r)
    bad = [r for r in fr if r["verdict"] != "SHIP"]
    return {
        "engineJson": None,
        "id": dirname,
        "kind": kind,
        "frameCount": len(fr),
        "frameSize": sorted(allowed) if len(allowed) > 1 else allowed[0],
        "anchor": {"note": "单帧图标 / 挂件，无脚底锚点"},
        "actionCounts": {},
        "frameTableComplete": None,
        "groupIssues": [],
        "ship": len(fr) - len(bad),
        "notShip": len(bad),
        "verdict": "SHIP" if not bad else "FIX",
        "frames": fr,
        "loose": True,
    }


def qc_group(json_path: Path, kind: str) -> dict:
    engine = json.loads(json_path.read_text(encoding="utf-8"))
    frames = engine.get("frames", [])
    size = engine.get("frameSize", [64, 64])[0]
    frame_results = [qc_frame(json_path.parent / n, kind, size) for n in frames]

    group_issues = []
    if engine.get("frameCount") != len(frames):
        group_issues.append("frameCount 与 frames 长度不一致")
    anchor = engine.get("anchor", {})
    if not isinstance(anchor.get("y"), int) or not isinstance(anchor.get("x"), int):
        group_issues.append("锚点不是整数像素")

    counts = Counter()
    for n in frames:
        m = re.search(r"_(idle|run|atk|cast|skill|hit|death)_r_", n)
        if m:
            counts[m.group(1)] += 1
    expected = EXPECTED_OVERRIDES.get(engine.get("id"), EXPECTED.get(kind))
    table_ok = None
    if expected and engine.get("frameCount") == sum(expected.values()):
        missing = [f"{a}:{counts[a]}/{v}" for a, v in expected.items() if counts[a] != v]
        table_ok = not missing
        if missing:
            group_issues.append("帧表动作计数不符 → " + ", ".join(missing))

    report_path = json_path.parent / f"{engine.get('id', json_path.stem)}_report.json"
    if report_path.exists() and has_abs_path(report_path):
        group_issues.append("规整报告含机器绝对路径（换账号会失效）")

    bad = [r for r in frame_results if r["verdict"] != "SHIP"]
    return {
        "engineJson": rel(json_path),
        "id": engine.get("id"),
        "kind": kind,
        "frameCount": len(frames),
        "frameSize": size,
        "anchor": anchor,
        "actionCounts": dict(counts),
        "frameTableComplete": table_ok,
        "groupIssues": group_issues,
        "ship": len(frame_results) - len(bad),
        "notShip": len(bad),
        "verdict": "SHIP" if not bad and not group_issues else "FIX",
        "frames": frame_results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None,
                    help="只查某个目录名，如 enemy / char / frames")
    ap.add_argument("--json-out", default="docs/qc-report.json")
    args = ap.parse_args()

    groups = []
    for dirname, kind in SCAN_DIRS:
        if args.only and args.only not in dirname:
            continue
        folder = ROOT / dirname
        if not folder.exists():
            continue
        for jp in sorted(folder.glob("*.json")):
            if jp.name.endswith("_report.json"):
                continue
            groups.append(qc_group(jp, kind))

    for dirname, kind, size in LOOSE_SCAN:
        if args.only and args.only not in dirname:
            continue
        loose = qc_loose_group(dirname, kind, size)
        if loose:
            groups.append(loose)

    all_frames = [f for g in groups for f in g["frames"]]
    verdicts = Counter(f["verdict"] for f in all_frames)
    summary = {
        "groups": len(groups),
        "frames": len(all_frames),
        "verdicts": dict(verdicts),
        "outOfPaletteTotal": sum(f["outOfPaletteColors"] for f in all_frames),
        "semiAlphaFrames": sum(1 for f in all_frames if f["semiAlphaLevels"]),
        "sizeMismatchFrames": sum(
            1 for g in groups for f in g["frames"] if not f["sizeOk"]),
        "groupVerdicts": dict(Counter(g["verdict"] for g in groups)),
        "scope": "全项目" if not args.only else args.only,
    }
    out = {"summary": summary, "groups": groups}
    out_path = ROOT / args.json_out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for g in groups:
        flag = "OK " if g["verdict"] == "SHIP" else "!! "
        print(f"{flag}{g['id']:<26} {g['frameCount']:>2} 帧  "
              f"SHIP {g['ship']:>2}  NOT-SHIP {g['notShip']:>2}  "
              f"帧表={'完整' if g['frameTableComplete'] else '样板/待补' if g['frameTableComplete'] is False else 'n/a'}"
              + (f"  {g['groupIssues']}" if g["groupIssues"] else ""))
        for f in g["frames"]:
            if f["verdict"] != "SHIP":
                print(f"     - {f['file']}  {f['verdict']} {f['score']}分  {f['issues']}")
    print(f"\n报告 → {rel(out_path)}")


if __name__ == "__main__":
    main()
