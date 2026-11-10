#!/usr/bin/env python3
"""第 39 轮 · 6 组拼版回稿导入 / 留档 / 标准化（集成链路第 1 步）。

用户一次交回 6 张 gpt-image2 拼版（A–F），要求集成进游戏。本脚本负责：

  assets/_source/card_art_sheets/<sheet-0N>-<组>-source.jpg   （聊天原稿留档）
    → 按 docs/card-art-plan.json 的 sheetSpec 标准化成 1536×1024 PNG
    → previews/card_art_sheets/sheet-01..06.png
    → docs/card-art-integration-report.json

后续：tools/split_card_art_sheets.py --adaptive 裁 72 张 384×256 原稿，
      tools/transcribe_card_art.py 做 84×56 转录 + 24 色吸附 + 卡面预览。

组 → sheet 映射由「12 格母题逐格核对」确定，不是按文件名顺序猜：
  A=01 技能伤害 / B=02 属性提升 / C=03 机制改变
  D=04 资源灵力 / E=05 生存回复 / F=06 构筑风险

已知例外：B 组回稿是 1024×1024（平台出了 1:1），其余 5 张是 1536×1024。
对 B 组按 3×4 切出 341/342×256 的格，每格**原像素居中嵌入** 512×256 标准格、
左右补该格自身底色 —— 不拉伸、不裁内容，只是把窄格放进宽格。

纪律：本步不改像素内容（只换容器 + 重排位置）；聊天 JPEG 的压缩噪声留给
transcribe_card_art.py 的 24 色吸附消除。所有产物 status 为
「待目检与合规确认；不得直接入库」，Q17 未拍板、GUI F5 未跑。

用法：
    python3 tools/import_card_art_sheets.py --import-from <剪贴板目录>
    python3 tools/import_card_art_sheets.py            # 用留档重跑（幂等）
    python3 tools/import_card_art_sheets.py --check    # 只校验，不写文件
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs"
PLAN_PATH = DOC / "card-art-plan.json"
REPORT_PATH = DOC / "card-art-integration-report.json"
SRC_DIR = ROOT / "assets" / "_source" / "card_art_sheets"
SHEET_DIR = ROOT / "previews" / "card_art_sheets"

# (组名, sheet 序号, 聊天附件文件名, 该组 12 格目检结论)
GROUPS = [
    ("A", 1, "clipboard-2026-11-10T13-35-30-170Z-ea056752.jpg",
     "12/12：磨石淬剑、对称双剑、双雷柱符篆、丹炉回卷火舌、符纸方阵、三段同心弧、半叶半刃、破钟罩扇形、水平剑贯穿三人、五行环裂盾、三符环、斜剑坠星"),
    ("B", 2, "clipboard-2026-11-10T13-35-30-172Z-ba733a84.jpg",
     "12/12：晶体收束、掌上丹丸、灵脉分三、步摇垂弧、四片叠甲、靶心命中、劈开方框、寿桃刻痕、逆风羽毛、气息静环、砧上方坯、三魂剥落"),
    ("C", 3, "clipboard-2026-11-10T13-35-30-171Z-c9160a10.jpg",
     "12/12：符号倒转、双槽换位、双流派主印、三段残影、序号轨道、印章封旧卡、两张撑成三张、令旗铁砧、敌人卷轴、舍利断流、两灵韵汇一、两道途同挂"),
    ("D", 4, "clipboard-2026-11-10T13-35-30-172Z-8df0f929.jpg",
     "12/12：魂火入阵眼、收窄漏斗、刻度瓶回灌、丹香、满潮浪头、截四点灵光、空盏一滴、反涌护盾、三珠连珠、无根木、六枚灵石、三印引爆"),
    ("E", 5, "clipboard-2026-11-10T13-35-30-172Z-c4e93a99.jpg",
     "12/12：新芽光晕、三层护盾格、拉长无敌窗、断续阶梯、纸傀儡挡击、铁壳骨节、阈值门、淡入墨底人形、灰烬 CD 环、叶尖露、罩内气旋、命盘削角"),
    ("F", 6, "clipboard-2026-11-10T13-35-30-172Z-8c35772f.jpg",
     "12/12：刻度四降三、CD 环概率点、灼伤三层、放大拳、第四候选、天劫四格、一刀两刃、第五槽空位、朱印倍率、退让减伤梯、异色离群卡、卡流断开放大"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corner_bg(img: Image.Image) -> tuple[int, int, int]:
    w, h = img.size
    samples = []
    for x0, y0 in ((0, 0), (w - 3, 0), (0, h - 3), (w - 3, h - 3)):
        for dx in range(3):
            for dy in range(3):
                samples.append(img.getpixel((x0 + dx, y0 + dy)))
    return tuple(sum(c[i] for c in samples) // len(samples) for i in range(3))


def standardize(img: Image.Image, spec: dict) -> tuple[Image.Image, str, dict | None]:
    """把回稿摆到标准 1536×1024 画布上；返回 (图, 处理方式, 例外详情)。"""
    sw, sh = spec["sheetSize"]
    cols, rows = spec["grid"]
    cw, ch = spec["cellSize"]
    src = img.convert("RGB")
    if src.size == (sw, sh):
        return src.copy(), "原尺寸直转 PNG（像素内容未改）", None
    if src.size != (1024, 1024):
        raise AssertionError(
            f"回稿尺寸 {src.size} 既不是 {sw}×{sh} 也不是已知的 1024×1024；"
            "不要拉伸，先确认平台比例或改规格")
    if ch * rows != 1024:
        raise AssertionError("1024×1024 不能按 3×4 均分行高")

    bg = corner_bg(src)
    out = Image.new("RGB", (sw, sh), bg)
    cell_widths = []
    for r in range(rows):
        for c in range(cols):
            x0, x1 = c * 1024 // cols, (c + 1) * 1024 // cols
            y0, y1 = r * ch, (r + 1) * ch
            cell = src.crop((x0, y0, x1, y1))
            cell_widths.append(cell.width)
            # 该格自身底色（四角均值）用于补两边，避免出现比原稿更亮的接缝
            pad_bg = corner_bg(cell)
            tile = Image.new("RGB", (cw, ch), pad_bg)
            tile.paste(cell, ((cw - cell.width) // 2, 0))
            out.paste(tile, (c * cw, r * ch))
    detail = {
        "reason": "平台导出 1:1 方图，而非提示词要求的 3:2 / 1536×1024",
        "sourceSize": [1024, 1024],
        "sourceCellWidths": sorted(set(cell_widths)),
        "action": "按 3×4 切出 341/342×256 的格，原像素居中嵌入 512×256 标准格，左右补该格自身底色；不拉伸、不裁内容",
        "effect": "主体在标准格内横向占比变小、留白更多；裁切框 384×256 仍能完整容纳主体",
        "palette": "底色差异在后续 24 色吸附时统一到 #12161F",
    }
    return out, "1024×1024 无损重排到 1536×1024（不拉伸）", detail


def build(import_from: Path | None, write: bool) -> dict:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    spec = plan["sheetSpec"]
    if spec["sheetCount"] != 6 or spec["cellsPerSheet"] != 12:
        raise AssertionError("sheetSpec 不是 6×12")
    if [s["index"] for s in plan["sheets"]] != list(range(1, 7)):
        raise AssertionError("card-art-plan.json 的 6 组序号不连续")

    sources, outputs, exceptions = [], [], []
    for group, idx, clip_name, eyeball in GROUPS:
        fname = f"sheet-{idx:02d}.png"
        src_name = f"sheet-{idx:02d}-{group}-source.jpg"
        src_path = SRC_DIR / src_name
        out_path = SHEET_DIR / fname

        if import_from is not None:
            clip = import_from / clip_name
            if not clip.is_file():
                raise AssertionError(f"缺聊天附件：{clip}")
            if write:
                SRC_DIR.mkdir(parents=True, exist_ok=True)
                if not src_path.is_file():
                    shutil.copy2(clip, src_path)
        if not src_path.is_file():
            raise AssertionError(f"缺留档原稿 {src_path}；首次运行请带 --import-from")

        with Image.open(src_path) as raw:
            src_size = list(raw.size)
            bg = corner_bg(raw.convert("RGB"))
            img, method, detail = standardize(raw, spec)
        if img.size != tuple(spec["sheetSize"]):
            raise AssertionError(f"{group} 组标准化后尺寸不对：{img.size}")

        if write:
            SHEET_DIR.mkdir(parents=True, exist_ok=True)
            img.save(out_path, format="PNG")
        sources.append({
            "group": group, "sheetIndex": idx, "sourceFile": str(src_path.relative_to(ROOT)),
            "clipboardName": clip_name, "sourceSha256": sha256(src_path),
            "sourceSize": src_size, "sourceBackground": list(bg),
            "sourceFormat": "JPEG（聊天附件压缩版，非无损 PNG 原件）",
            "standardizeMethod": method,
            "motifEyeball": eyeball,
        })
        outputs.append({
            "sheet": idx, "group": group, "file": str(out_path.relative_to(ROOT)),
            "outputSha256": sha256(out_path) if out_path.is_file() else None,
            "size": list(spec["sheetSize"]), "format": "PNG",
        })
        if detail:
            exceptions.append({"sheet": idx, "group": group, **detail})
        img.close()

    return {
        "version": 1,
        "generatedBy": "tools/import_card_art_sheets.py",
        "status": "待目检与合规确认；不得直接入库",
        "sheetSpec": spec,
        "groupToSheet": {g: i for g, i, _, _ in GROUPS},
        "mappingBasis": "按 12 格母题逐格核对确定，非文件名顺序；见每条 motifEyeball",
        "sources": sources,
        "outputs": outputs,
        "sheetsReceived": sum(1 for o in outputs if o["outputSha256"]),
        "knownExceptions": exceptions,
        "pixelPolicy": "导入阶段只换容器与重排位置，不做缩放/拉伸/量化；JPEG 压缩噪声由 24 色吸附消除",
        "boundary": "Q17 未拍板、GUI F5 未跑；冻结卡面 assets/ui/cards/ 的 10 张 PNG 未改动；不接数值与规则",
    }


def check() -> str:
    report = build(None, write=False)
    for o in report["outputs"]:
        p = ROOT / o["file"]
        if not p.is_file():
            raise AssertionError(f"缺 {o['file']}")
        with Image.open(p) as im:
            if list(im.size) != o["size"] or im.format != "PNG":
                raise AssertionError(f"{o['file']} 尺寸或格式不符")
        if sha256(p) != o["outputSha256"]:
            raise AssertionError(f"{o['file']} 与报告 sha256 不一致")
    return (f"6/6 拼版标准化产物齐备 / 组→sheet 映射 "
            f"{report['groupToSheet']} / 已知例外 {len(report['knownExceptions'])} 条")


def main() -> int:
    ap = argparse.ArgumentParser(description="6 组拼版回稿导入 / 标准化")
    ap.add_argument("--import-from", type=Path, help="聊天附件所在目录（首次导入时给）")
    ap.add_argument("--check", action="store_true", help="只校验，不写文件")
    args = ap.parse_args()
    try:
        if args.check:
            print("PASS | " + check())
            return 0
        report = build(args.import_from, write=True)
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE | {REPORT_PATH.relative_to(ROOT)}")
        print(f"INFO  | 拼版 {report['sheetsReceived']}/6；"
              f"已知例外 {len(report['knownExceptions'])} 条")
        for e in report["knownExceptions"]:
            print(f"INFO  | sheet-{e['sheet']:02d}（{e['group']} 组）：{e['reason']} → {e['action']}")
        print("PASS | " + check())
    except Exception as exc:
        print(f"FAIL | {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
