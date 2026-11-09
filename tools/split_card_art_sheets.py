#!/usr/bin/env python3
"""第 35–36 轮 · 6 张拼版 sheet → 72 张单卡原稿的裁剪器。

用户决策：「一张图里包含多个卡片图，72 / 12 = 6 次生成即可，节省 gpt-image2 额度，
效果不变，裁剪由 AI 负责」。本脚本就是「裁剪」那一半：

  previews/card_art_sheets/sheet-01..06.png  (各 1536×1024，3 列 × 4 行 = 12 格)
    → 每格 512×256 → 中心裁 384×256（左右各弃 64px 安全边，3:2）
    → previews/card_art/<card_id>-cardart-original.png  (72 张)
    → docs/card-art-split-report.json  (sha256 / 格位 / 裁切框 / 如实回稿数)

默认（fixed）模式的格位与裁切框**全部来自 docs/card-art-plan.json**，不猜坐标、
不做视觉检测、不改原稿像素、不做 24 色吸附（那是后续转录链路的事）。

第 36 轮实测：AI 回稿的行边界会漂移。第 1 张 sheet 实测 y=289 / 534 / 779，
固定 256 / 512 / 768 偏移 +33 / +22 / +11 px，固定裁切 12/12 格都出现上下切边。
因此新增 --adaptive：扫描亮像素密度低谷自动定位真实行 / 列空隙，按实测边界分段
取中心 384×256。理论边界本身已落在空隙里时保持不动（不引入无谓偏移）；
不拉伸变形，越界处补墨底。报告里的 cropBox 是标称框、usedBox 是实际使用框。

用法：
    python3 tools/split_card_art_sheets.py                       # 固定坐标硬裁
    python3 tools/split_card_art_sheets.py --check               # 只校验，不写文件
    python3 tools/split_card_art_sheets.py --adaptive            # 推荐：自动对齐真实格位
    python3 tools/split_card_art_sheets.py --adaptive --check    # 只复算，不写文件

纪律：原稿不改写；所有产物 status 为「待目检与合规确认；不得直接入库」；
Q17 未拍板、GUI F5 未跑；R58 拼版风险（画成整图 / 格位漂移 / 元素跨格 / 擅画格线）
必须在试裁后由人眼目检确认。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs"
PREV = ROOT / "previews"
PLAN_PATH = DOC / "card-art-plan.json"
REPORT_PATH = DOC / "card-art-split-report.json"
SHEET_DIR = PREV / "card_art_sheets"
OUT_DIR = PREV / "card_art"

FIXED_POLICY = "固定像素坐标硬裁：cellBox 512×256 → 中心 384×256；不做视觉检测、不改像素、不做 24 色吸附"
ADAPTIVE_POLICY = (
    "自适应格位：扫描亮像素密度低谷定位真实行/列空隙，按实测边界分段取中心 384×256，"
    "不拉伸、越界补墨底；报告 usedBox 为实际使用框，cropBox 为标称框"
)


def load_plan() -> dict:
    if not PLAN_PATH.is_file():
        raise AssertionError("缺 docs/card-art-plan.json，请先跑 tools/build_card_art_plan.py")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    spec = plan.get("sheetSpec")
    sheets = plan.get("sheets")
    if not isinstance(spec, dict) or not isinstance(sheets, list):
        raise AssertionError("映射表缺 sheetSpec / sheets（是第 34 轮旧版？请重跑生成器）")
    if spec.get("sheetCount") != 6 or spec.get("cellsPerSheet") != 12:
        raise AssertionError("拼版规格不是 6 张 × 12 格")
    if len(sheets) != 6:
        raise AssertionError("sheets 不是 6 组")
    sw, sh = spec["sheetSize"]
    cols, rows = spec["grid"]
    cw, ch = spec["cellSize"]
    crop_w, crop_h = spec["cropSize"]
    pad = spec["cropPadX"]
    if cols * cw != sw or rows * ch != sh:
        raise AssertionError("网格不能整除画布")
    if crop_w + 2 * pad != cw or crop_h != ch:
        raise AssertionError("中心裁切数学不自洽")
    if crop_w / crop_h != 1.5:
        raise AssertionError("裁切框不是 3:2")
    cells = [c for s in sheets for c in s["cells"]]
    if len(cells) != 72 or len({c["outputName"] for c in cells}) != 72:
        raise AssertionError("72 格位或输出命名不唯一")
    labels = [(s["index"], c["label"]) for s in sheets for c in s["cells"]]
    if len(set(labels)) != 72:
        raise AssertionError("(sheet, 格位) 不是 72 个唯一键")
    expect = [f"r{r}c{col}" for r in range(1, rows + 1) for col in range(1, cols + 1)]
    for s in sheets:
        if [c["label"] for c in s["cells"]] != expect:
            raise AssertionError(f"{s['file']} 格位不是行优先 3×4")
        for c in s["cells"]:
            x0 = (c["col"] - 1) * cw
            y0 = (c["row"] - 1) * ch
            if c["cellBox"] != [x0, y0, x0 + cw, y0 + ch]:
                raise AssertionError(f"{c['cardId']} cellBox 不复算")
            if c["cropBox"] != [x0 + pad, y0, x0 + pad + crop_w, y0 + ch]:
                raise AssertionError(f"{c['cardId']} cropBox 不复算")
            bx = c["cropBox"]
            if bx[0] < 0 or bx[1] < 0 or bx[2] > sw or bx[3] > sh:
                raise AssertionError(f"{c['cardId']} 裁切框越出画布")
    return plan


def sheet_state(path: Path) -> tuple[bool, str | None, list[int] | None]:
    if not path.is_file():
        return False, None, None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as img:
        size = list(img.size)
    return True, digest, size


def detect_boundaries(img: Image.Image, spec: dict) -> dict:
    """扫描亮像素密度低谷，定位 AI 实际画出的行 / 列空隙。

    理论边界本身已落在空隙里（密度 <= tolerance）就保持不动，避免引入无谓偏移。
    """
    rgb = img.convert("RGB")
    W, H = rgb.size
    px = rgb.load()
    corners = []
    for x0, y0 in ((0, 0), (W - 3, 0), (0, H - 3), (W - 3, H - 3)):
        for dx in range(3):
            for dy in range(3):
                corners.append(rgb.getpixel((x0 + dx, y0 + dy)))
    bg = tuple(sum(c[i] for c in corners) // len(corners) for i in range(3))

    def fg(p: tuple[int, int, int]) -> bool:
        return max(abs(p[i] - bg[i]) for i in range(3)) > 45

    row_d = [sum(fg(px[x, y]) for x in range(0, W, 4)) for y in range(H)]
    col_d = [sum(fg(px[x, y]) for y in range(0, H, 4)) for x in range(W)]
    sw, sh = spec["sheetSize"]
    cols, rows = spec["grid"]
    cw, ch = spec["cellSize"]
    tolerance, window = 2, 64

    def pick(theory: int, density: list[int], limit: int) -> tuple[int, int]:
        if density[theory] <= tolerance:
            return theory, 0
        lo, hi = max(1, theory - window), min(limit - 1, theory + window)
        v = min(range(lo, hi + 1), key=lambda k: density[k])
        return v, v - theory

    ys = [r * ch for r in range(1, rows)]
    xs = [c * cw for c in range(1, cols)]
    dy = [pick(v, row_d, H) for v in ys]
    dx = [pick(v, col_d, W) for v in xs]
    return {
        "background": list(bg),
        "theoreticalY": ys, "detectedY": [a for a, _ in dy], "offsetY": [b for _, b in dy],
        "theoreticalX": xs, "detectedX": [a for a, _ in dx], "offsetX": [b for _, b in dx],
        "tolerance": tolerance, "searchWindow": window,
        "method": "亮像素密度低谷；理论边界已在空隙内则保持不变",
    }


def adaptive_boxes(det: dict, spec: dict) -> dict[str, list[int]]:
    """按实测边界分段，每格取中心 384×256；不拉伸，越界部分由裁切函数补墨底。"""
    sw, sh = spec["sheetSize"]
    crop_w, crop_h = spec["cropSize"]
    yb = [0] + det["detectedY"] + [sh]
    xb = [0] + det["detectedX"] + [sw]
    out = {}
    for r in range(len(yb) - 1):
        for c in range(len(xb) - 1):
            cx = (xb[c] + xb[c + 1]) // 2
            cy = (yb[r] + yb[r + 1]) // 2
            out[f"r{r + 1}c{c + 1}"] = [
                cx - crop_w // 2, cy - crop_h // 2,
                cx + crop_w // 2, cy + crop_h // 2]
    return out


def crop_with_pad(img: Image.Image, box: list[int], bg: tuple[int, int, int]) -> Image.Image:
    """按 box 裁切；box 越出画布时补墨底，绝不拉伸变形。"""
    x0, y0, x1, y1 = box
    out = Image.new("RGB", (x1 - x0, y1 - y0), bg)
    src = img.crop((max(0, x0), max(0, y0), min(img.width, x1), min(img.height, y1)))
    out.paste(src, (max(0, -x0), max(0, -y0)))
    return out


def build_report(plan: dict, write_outputs: bool, adaptive: bool = False) -> dict:
    spec = plan["sheetSpec"]
    sw, sh = spec["sheetSize"]
    sheet_rows = []
    outputs: list[dict] = []
    for s in plan["sheets"]:
        path = SHEET_DIR / s["file"]
        present, digest, size = sheet_state(path)
        if present and size != [sw, sh]:
            raise AssertionError(
                f"{s['file']} 尺寸为 {size[0]}×{size[1]}，必须是 {sw}×{sh}；"
                "拼版尺寸不对会让固定坐标裁歪，重出这张或改规格后再裁")
        det = None
        boxes: dict[str, list[int]] = {}
        img = None
        if present:
            with Image.open(path) as raw:
                if raw.mode not in ("RGB", "RGBA", "P"):
                    raise AssertionError(f"{s['file']} 色彩模式异常：{raw.mode}")
                img = raw.convert("RGB")
                if adaptive:
                    det = detect_boundaries(img, spec)
                    boxes = adaptive_boxes(det, spec)
        cell_rows = []
        for c in s["cells"]:
            out_name = c["outputName"]
            out_path = OUT_DIR / out_name
            used_box = boxes.get(c["label"], c["cropBox"]) if adaptive else c["cropBox"]
            if present and write_outputs and img is not None:
                if adaptive:
                    crop_with_pad(img, used_box, tuple(det["background"])).save(
                        out_path, format="PNG")
                else:
                    img.crop(tuple(used_box)).save(out_path, format="PNG")
            cell_rows.append({
                "cell": c["cell"], "label": c["label"],
                "cardId": c["cardId"], "cardName": c["cardName"],
                "cellBox": c["cellBox"], "cropBox": c["cropBox"],
                "usedBox": used_box,
                "outputName": out_name,
                "outputPresent": out_path.is_file(),
            })
            outputs.append({
                "sheet": s["file"], "cell": c["cell"], "label": c["label"],
                "cardId": c["cardId"], "outputName": out_name,
                "cropBox": c["cropBox"], "usedBox": used_box,
            })
        sr = {
            "file": s["file"], "category": s["category"], "title": s["title"],
            "present": present, "sha256": digest, "size": size,
            "cellCount": len(cell_rows), "cells": cell_rows,
        }
        if adaptive:
            sr["detectedBoundaries"] = det
        sheet_rows.append(sr)
        if img is not None:
            img.close()
    present_count = sum(1 for s in sheet_rows if s["present"])
    out_count = sum(1 for p in OUT_DIR.glob("*-cardart-original.png")) if OUT_DIR.is_dir() else 0
    return {
        "version": 2,
        "generatedBy": "tools/split_card_art_sheets.py",
        "status": "待目检与合规确认；不得直接入库",
        "sheetSpec": spec,
        "adaptive": adaptive,
        "sheets": sheet_rows,
        "sheetsReceived": present_count,
        "sheetsPending": 6 - present_count,
        "outputsTotal": 72,
        "outputsOnDisk": out_count,
        "outputs": outputs,
        "cropPolicy": ADAPTIVE_POLICY if adaptive else FIXED_POLICY,
        "knownExceptions": [
            "R58 拼版风险：AI 可能画成一张整图、格位漂移、元素跨格、格间风格漂移或擅画格线；先出 1 张试裁目检",
            "第 36 轮实测：sheet-01 真实行边界 y=289/534/779，与固定 256/512/768 偏移 +33/+22/+11px，固定裁切 12/12 格有上下切边；建议用 --adaptive",
            "每格有效分辨率 384×256，低于单张 1024×1024 方案；目标插画区仅 84×56（4× 约 336×224），够用但不等价",
            "回稿未到齐；sheetsReceived / outputsOnDisk 如实统计，不伪造 6/6 或 72/72",
        ],
        "boundary": "本表只是裁剪记录，不是美术资产、不是已入库资源；Q17 未拍板、GUI F5 未跑、未接 Godot 场景。",
    }


def check(adaptive: bool = False) -> str:
    plan = load_plan()
    # 无回稿时也要能 PASS：只校验规格、命名与磁盘既有文件，不要求 6 张 sheet 存在。
    report = build_report(plan, write_outputs=False, adaptive=adaptive)
    if OUT_DIR.is_dir():
        registered = {o["outputName"] for o in report["outputs"]}
        extra = sorted(p.name for p in OUT_DIR.glob("*-cardart-original.png")
                       if p.name not in registered)
        if extra:
            raise AssertionError(f"单卡原稿目录出现未登记命名：{extra}")
    if REPORT_PATH.is_file():
        saved = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        if saved.get("outputsTotal") != 72 or len(saved.get("outputs", [])) != 72:
            raise AssertionError("已存在的裁剪报告不是 72 条输出")
        if len(saved.get("sheets", [])) != 6:
            raise AssertionError("已存在的裁剪报告不是 6 张 sheet")
        if saved.get("sheetSpec") != plan["sheetSpec"]:
            raise AssertionError("裁剪报告与当前 sheetSpec 不一致，请重跑裁剪脚本")
    mode = "自适应格位" if adaptive else "固定坐标"
    return (f"{mode} / 6 张拼版 × 12 格 / 72 格位与裁切框复算一致 / "
            f"回稿 {report['sheetsReceived']}/6、单卡原稿 {report['outputsOnDisk']}/72（如实披露）")


def main() -> int:
    ap = argparse.ArgumentParser(description="6 张拼版 sheet → 72 张单卡原稿")
    ap.add_argument("--check", action="store_true", help="只校验，不写文件")
    ap.add_argument("--adaptive", action="store_true",
                    help="扫描亮像素密度低谷自动对齐真实行/列格位（推荐，解决 R58 格位漂移）")
    args = ap.parse_args()
    try:
        if args.check:
            print("PASS | " + check(args.adaptive))
            return 0
        plan = load_plan()
        SHEET_DIR.mkdir(parents=True, exist_ok=True)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        report = build_report(plan, write_outputs=True, adaptive=args.adaptive)
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE | {REPORT_PATH.relative_to(ROOT)}")
        print(f"INFO  | 模式={'adaptive' if args.adaptive else 'fixed'}；"
              f"拼版回稿 {report['sheetsReceived']}/6，"
              f"单卡原稿 {report['outputsOnDisk']}/72（如实统计）")
        for s in report["sheets"]:
            if args.adaptive and s.get("detectedBoundaries"):
                d = s["detectedBoundaries"]
                print(f"INFO  | {s['file']} 实测行边界 {d['detectedY']} 偏移 {d['offsetY']}；"
                      f"实测列边界 {d['detectedX']} 偏移 {d['offsetX']}")
        print("PASS | " + check(args.adaptive))
    except Exception as exc:
        print(f"FAIL | {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
