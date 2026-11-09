#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
塔层三选一卡牌 · 程序化生成器（v0.1，第 12 轮）

只读 docs/buff-card-library.json，产出：
  assets/ui/cards/frame_<rarity>.png       4 张 96x144 卡框（不含文字）
  assets/ui/cards/sigil_<cat>.png         6 张 24x24 类别纹样
  assets/_preview/buff_cards_contact_sheet.png   M10 并排目检图（ASCII 标签）
  assets/_preview/buff-card-preview.html        自包含交互预览（三选一 + 72 张图鉴）
  docs/卡牌库.csv                          72 行策划核对表
  docs/buff-card-report.json               统计与自检报告

硬约束：24 色锁定（docs/04 §4）、半透明像素 0、硬边无抗锯齿、卡面不含文字、
四周留白、类别靠形状 / 稀有度靠边框层次。0 积分、0 张源图、可复现。

用法：
  /opt/homebrew/bin/python3 tools/build_buff_cards.py

注意：本脚本只生成「视觉资源 + 预览 + 核对表」，不实现游戏逻辑、不改任何基线文档。
"""
from __future__ import annotations

import base64
import csv
import io
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
LIB_PATH = ROOT / "docs/buff-card-library.json"
CARD_DIR = ROOT / "assets/ui/cards"
PREVIEW_DIR = ROOT / "assets/_preview"
CSV_OUT = ROOT / "docs/卡牌库.csv"
REPORT_OUT = ROOT / "docs/buff-card-report.json"
HTML_OUT = PREVIEW_DIR / "buff-card-preview.html"
SHEET_OUT = PREVIEW_DIR / "buff_cards_contact_sheet.png"

# 24 色锁定板的 20 核心色（与 build_icons.py / qc_sprites.py 完全一致）
INK = (0, 0, 0, 255)
INK_1 = (18, 22, 31, 255)
INK_2 = (42, 49, 64, 255)
INK_3 = (74, 85, 104, 255)
PAPER = (232, 223, 200, 255)
PAPER_D = (201, 191, 163, 255)
PAPER_DD = (138, 130, 104, 255)
JADE_D = (47, 110, 106, 255)
JADE = (95, 168, 160, 255)
JADE_L = (155, 212, 204, 255)
RED_D = (122, 36, 32, 255)
RED = (200, 69, 59, 255)
RED_L = (232, 128, 111, 255)
GOLD_D = (138, 101, 32, 255)
GOLD = (217, 164, 65, 255)
GOLD_L = (242, 208, 137, 255)
VIO_D = (74, 58, 107, 255)
VIO = (138, 111, 196, 255)
VIO_L = (192, 168, 224, 255)
WHITE = (255, 255, 255, 255)
PALETTE = {c[:3] for c in (
    INK, INK_1, INK_2, INK_3, PAPER, PAPER_D, PAPER_DD,
    JADE_D, JADE, JADE_L, RED_D, RED, RED_L,
    GOLD_D, GOLD, GOLD_L, VIO_D, VIO, VIO_L, WHITE)}

RARITY_COLOR = {"common": INK_3, "rare": JADE, "legend": GOLD, "curse": RED}
RARITY_PIPS = {"common": 1, "rare": 2, "legend": 3, "curse": 4}
SIGIL_COLOR = {
    "dmg": RED, "attr": JADE_D, "mech": VIO,
    "res": GOLD_D, "surv": JADE_L, "syn": RED_D,
}

W, H = 96, 144


# ---------------------------------------------------------------- 卡框

def make_frame(rarity: str) -> Image.Image:
    """96x144 卡框。不含任何文字（R9 字体未核验，文字全部由 UI 文字层渲染）。"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base = RED_D if rarity == "curse" else PAPER
    # 八边切角外轮廓，四周留 1px
    pts = [(4, 1), (91, 1), (94, 4), (94, 139), (91, 142),
           (4, 142), (1, 139), (1, 4)]
    d.polygon(pts, fill=base)
    d.line(pts + [pts[0]], fill=INK, width=1)

    col = RARITY_COLOR[rarity]
    if rarity == "common":                       # 1px 墨亮单线
        d.rectangle((3, 3, 92, 140), outline=col, width=1)
    elif rarity == "rare":                       # 2px 青玉双线 + 云角
        d.rectangle((3, 3, 92, 140), outline=col, width=1)
        d.rectangle((5, 5, 90, 138), outline=col, width=1)
        for x0, y0 in ((3, 3), (92, 3), (3, 140), (92, 140)):
            d.point((x0, y0), fill=GOLD_L)
    elif rarity == "legend":                     # 3px 金线 + 顶边亮线 + 云角
        for i, c in enumerate((GOLD_D, GOLD, GOLD_L)):
            d.rectangle((3 + i, 3 + i, 92 - i, 140 - i), outline=c, width=1)
        d.line((8, 4, 88, 4), fill=GOLD_L, width=1)
        d.line((8, 139, 88, 139), fill=GOLD_D, width=1)
    else:                                        # curse：朱砂断线（四边各留断点）
        for seg in (((8, 3, 42, 3), (54, 3, 88, 3)),
                    ((8, 140, 42, 140), (54, 140, 88, 140)),
                    ((3, 8, 3, 66), (3, 78, 3, 136)),
                    ((92, 8, 92, 66), (92, 78, 92, 136))):
            for (x0, y0, x1, y1) in seg:
                d.line((x0, y0, x1, y1), fill=RED, width=2)
        d.line((4, 4, 12, 4), fill=RED_L, width=1)
        d.line((83, 139, 91, 139), fill=RED_L, width=1)

    # 分区线（实色 1px，不用半透明）
    line = PAPER_D if rarity == "curse" else INK_3
    d.line((5, 16, 90, 16), fill=line, width=1)          # 类别条 / 插画区
    d.line((5, 77, 90, 77), fill=line, width=1)          # 插画区 / 卡名条
    d.line((5, 94, 90, 94), fill=line, width=1)          # 卡名 / 描述
    d.line((5, 128, 90, 128), fill=line, width=1)        # 描述 / 信息条
    # 插画区（纹样居中 24x24 ×2 = 48x48，位于 x=24..71 / y=28..75）
    d.rectangle((6, 19, 89, 75), outline=line, width=1)
    # 底部稀有度色带
    d.rectangle((5, 138, 90, 139), fill=col)

    # 右上 4x4 角标点阵（1–4 点，复用 07 §2.3 语法）
    for i in range(RARITY_PIPS[rarity]):
        x, y = 86 + (i % 2) * 2, 5 + (i // 2) * 2
        d.point((x, y), fill=GOLD if rarity != "curse" else RED_L)
    return im


# ---------------------------------------------------------------- 纹样

def make_sigil(cat: str) -> Image.Image:
    """24x24 类别纹样：6 种剪影互不相同，颜色只作辅助（04 R12）。"""
    im = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = SIGIL_COLOR[cat]
    if cat == "dmg":                              # 横向弯月弧 + 剑尖
        d.arc((3, 5, 21, 22), 195, 345, fill=INK, width=3)
        d.arc((5, 8, 19, 20), 195, 345, fill=c, width=2)
        d.polygon([(19, 4), (22, 2), (21, 7)], fill=GOLD_L, outline=INK)
    elif cat == "attr":                          # 三阶立柱（高低递进）
        for x, top in ((4, 15), (10, 10), (16, 5)):
            d.rectangle((x, top, x + 4, 20), fill=c, outline=INK)
            d.line((x + 1, top + 1, x + 3, top + 1), fill=WHITE, width=1)
        d.line((2, 21, 22, 21), fill=INK, width=1)
    elif cat == "mech":                          # 六边齿轮 + 咬合齿
        p = [(8, 2), (16, 2), (22, 12), (16, 22), (8, 22), (2, 12)]
        d.polygon(p, fill=c, outline=INK)
        d.ellipse((9, 9, 15, 15), fill=PAPER, outline=INK)
        for x, y in ((11, 1), (11, 22), (1, 11), (22, 11)):
            d.point((x, y), fill=GOLD_L)
    elif cat == "res":                           # 水滴 + 两道波纹
        d.polygon([(12, 2), (18, 11), (12, 17), (6, 11)], fill=c, outline=INK)
        d.point((11, 9), fill=WHITE)
        d.arc((3, 15, 21, 23), 200, 340, fill=JADE_L, width=2)
        d.arc((6, 18, 18, 23), 200, 340, fill=JADE_D, width=1)
    elif cat == "surv":                          # 盾形 + 中缝
        d.polygon([(3, 3), (21, 3), (21, 14), (12, 22), (3, 14)],
                  fill=c, outline=INK)
        d.line((12, 5, 12, 19), fill=PAPER, width=2)
        d.line((5, 9, 19, 9), fill=INK, width=1)
    else:                                        # syn：交叠双菱 + 中心结
        p1 = [(12, 1), (20, 9), (12, 17), (4, 9)]
        p2 = [(12, 7), (20, 15), (12, 22), (4, 15)]
        d.line(p1 + [p1[0]], fill=GOLD_D, width=2)
        d.line(p2 + [p2[0]], fill=c, width=2)
        d.rectangle((10, 10, 14, 14), fill=RED_L, outline=INK)
    return im


# ---------------------------------------------------------------- 自检

def check_png(im: Image.Image, label: str) -> dict:
    px = im.load()
    semi = out = opaque = 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if 0 < a < 255:
                semi += 1
            if a > 0:
                opaque += 1
                if (r, g, b) not in PALETTE:
                    out += 1
    return {"id": label, "size": [im.width, im.height],
            "semiAlpha": semi, "outOfPalette": out,
            "coverage": round(opaque / (im.width * im.height), 4)}


def validate_lib(lib: dict) -> tuple[list[str], dict]:
    errors: list[str] = []
    cards = lib["cards"]
    ids = [c["id"] for c in cards]
    if len(ids) != len(set(ids)):
        errors.append("卡 ID 有重复")
    idset = set(ids)
    cats = {c["key"] for c in lib["categories"]}
    rarities = {r["key"] for r in lib["rarities"]}
    types = set(lib["effectTypes"])
    hooks = set(lib["hookWhitelist"])

    # R32：卡牌不得声明突破 compute_damage 四个上界
    ceilings = {"realm_ratio": 1.60, "extra_pool": 600,
                "combo_multiplier": 2.5, "crit_multiplier": 1.8}
    for c in cards:
        if c["cat"] not in cats:
            errors.append(f"{c['id']}: 未知类别 {c['cat']}")
        if c["rarity"] not in rarities:
            errors.append(f"{c['id']}: 未知稀有度 {c['rarity']}")
        if c["type"] not in types:
            errors.append(f"{c['id']}: 未知效果类型 {c['type']}")
        if c["hook"] not in hooks:
            errors.append(f"{c['id']}: 未知实现钩子 {c['hook']}")
        if not isinstance(c["stack"], int) or c["stack"] < 1:
            errors.append(f"{c['id']}: stack 非法")
        for x in c["excl"]:
            if x not in idset:
                errors.append(f"{c['id']}: 悬空互斥引用 {x}")
        for r in c["req"]:
            if not (":" in r or ">=" in r):
                errors.append(f"{c['id']}: req 格式非法 {r}")
        for k, v in c["params"].items():
            if k in ceilings and isinstance(v, (int, float)) and v > ceilings[k]:
                errors.append(f"{c['id']}: params.{k}={v} 突破上界 {ceilings[k]}（R32）")
        if not c["text"].strip():
            errors.append(f"{c['id']}: 效果文案为空")

    by_cat = Counter(c["cat"] for c in cards)
    by_rarity = Counter(c["rarity"] for c in cards)
    by_type = Counter(c["type"] for c in cards)
    numeric = by_type.get("numeric", 0)
    ratio = round(numeric / len(cards), 4)
    if ratio > 1 / 3:
        errors.append(f"纯数值卡占比 {ratio:.1%} 超过 1/3（02 P0-2 硬约束）")
    if len(cards) < 64:
        errors.append(f"卡池只有 {len(cards)} 张，未达到用户要求的 ≥64")

    stats = {
        "totalCards": len(cards),
        "byCategory": dict(by_cat),
        "byRarity": dict(by_rarity),
        "byEffectType": dict(by_type),
        "numericCount": numeric,
        "numericRatio": ratio,
        "numericCap": round(1 / 3, 4),
        "offeredPerStage": lib["drawRule"]["offered"],
        "picksPerStage": lib["drawRule"]["pick"],
        "stagesWithPick": 8,
        "naiveSequenceUpperBound": lib["drawRule"]["offered"] ** 8,
        "naiveBoundNote": "3^8 只是数学上界，含去重/同类限制/前置/互斥，实际远小；且 η=0.10 折扣后不等于可感知差异，见 11 §6",
    }
    return errors, stats


# ---------------------------------------------------------------- 拼图

def contact_sheet(frames: dict, sigils: dict) -> Image.Image:
    """M10 并排目检图；标签一律 ASCII，避免中文字体缺字变方块。"""
    cw, ch = 116, 172
    rows = 3
    sheet = Image.new("RGB", (6 * cw + 20, rows * ch + 20), (245, 242, 232))
    d = ImageDraw.Draw(sheet)
    for i, (r, im) in enumerate(frames.items()):
        x, y = 10 + i * cw, 24
        sheet.paste(im.convert("RGB"), (x, y))
        d.text((x, 8), f"frame_{r}", fill=(20, 20, 20))
    for i, (cat, im) in enumerate(sigils.items()):
        x, y = 10 + i * cw, ch + 40
        big = im.resize((im.width * 4, im.height * 4), Image.NEAREST)
        bg = Image.new("RGBA", big.size, INK_1)
        bg.alpha_composite(big)
        sheet.paste(bg.convert("RGB"), (x, y))
        d.text((x, ch + 24), f"sigil_{cat}", fill=(20, 20, 20))
    # 第三行：3 张合成样卡（框 + 纹样），验证纹样居中
    for i, (r, cat) in enumerate((("common", "dmg"), ("legend", "mech"), ("curse", "syn"))):
        x, y = 10 + i * cw * 2, 2 * ch + 30
        comp = frames[r].copy()
        s = sigils[cat].resize((48, 48), Image.NEAREST)
        comp.alpha_composite(s, (24, 26))
        sheet.paste(comp.convert("RGB"), (x, y))
        d.text((x, 2 * ch + 12), f"sample_{r}_{cat}", fill=(20, 20, 20))
    return sheet


# ---------------------------------------------------------------- HTML

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>塔层三选一 · 卡牌 UI 预览（72 张）</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#12161F;color:#E8DFC8;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:18px}
h1{font-size:18px;color:#F2D089;font-weight:600;margin-bottom:4px}
.sub{font-size:12px;color:#C9BFA3;line-height:1.6;margin-bottom:12px}
.bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
button{background:#2A3140;color:#E8DFC8;border:1px solid #4A5568;padding:5px 12px;font-size:12px;cursor:pointer;font-family:inherit}
button:hover{border-color:#D9A441;color:#F2D089}
button.on{background:#8A6520;border-color:#D9A441;color:#F2D089}
input{background:#2A3140;color:#E8DFC8;border:1px solid #4A5568;padding:5px 8px;font-size:12px;width:110px;font-family:inherit}
.tag{font-size:11px;color:#9BD4CC;border:1px solid #2F6E6A;padding:3px 8px}
#pickOuter{width:960px;height:540px;position:relative;overflow:hidden;border:1px solid #4A5568;margin-bottom:10px}
#pickStage{width:480px;height:270px;position:relative;transform:scale(2);transform-origin:top left;background:#12161F}
#codexOuter{width:960px;height:620px;overflow:auto;position:relative;border:1px solid #4A5568}
#codexStage{width:480px;position:relative;transform:scale(2);transform-origin:top left}
.hidden{display:none}
.hd{position:absolute;left:8px;top:9px;font-size:11px;color:#E8DFC8;letter-spacing:1px}
.hdR{position:absolute;right:8px;top:9px;font-size:10px;color:#9BD4CC}
.rule{position:absolute;left:8px;right:8px;top:28px;height:1px;background:#4A5568}
.ft{position:absolute;left:8px;top:216px;font-size:9px;color:#8A8268}
.ftR{position:absolute;right:8px;top:216px;font-size:9px;color:#8A8268}
.confirm{position:absolute;left:180px;top:222px;width:120px;height:20px;background:#2A3140;border:1px solid #4A5568;color:#C9BFA3;font-size:10px;text-align:center;line-height:18px;cursor:pointer}
.confirm.ready{background:#8A6520;border-color:#D9A441;color:#F2D089}
.card{position:absolute;width:96px;height:144px;background-size:100% 100%;image-rendering:pixelated;cursor:pointer;transition:none}
.card:hover{transform:translateY(-4px)}
.card.sel{outline:2px solid #D9A441;outline-offset:0;transform:translateY(-4px)}
.card .sigBig{position:absolute;left:24px;top:26px;width:48px;height:48px;image-rendering:pixelated}
.card .cat{position:absolute;left:16px;top:4px;font-size:8px;color:#2A3140;letter-spacing:1px}
.card .nm{position:absolute;left:4px;right:4px;top:79px;text-align:center;font-size:11px;font-weight:700;color:#12161F;line-height:13px;white-space:nowrap;overflow:hidden}
.card .tx{position:absolute;left:7px;right:7px;top:97px;font-size:8px;color:#2A3140;line-height:10px;height:30px;overflow:hidden}
.card .info{position:absolute;left:7px;right:7px;top:131px;font-size:7px;color:#4A5568;display:flex;justify-content:space-between}
.card.curse .cat,.card.curse .nm,.card.curse .tx,.card.curse .info{color:#E8DFC8}
.card .idx{position:absolute;left:-1px;top:-1px;width:11px;height:11px;background:#4A5568;color:#E8DFC8;font-size:8px;text-align:center;line-height:11px}
.codexCard{margin:0 4px 8px 0;float:left;position:relative;width:96px;height:144px}
.codexCard .card{left:0;top:0}
.codexCard .card:hover{transform:none}
.filters{position:absolute;left:8px;top:8px;width:464px;font-size:9px;color:#C9BFA3;line-height:22px}
.filters button{font-size:9px;padding:2px 6px;margin:0 3px 3px 0}
#grid{position:absolute;left:36px;top:78px;width:408px}
#detail{position:fixed;right:24px;top:80px;width:300px;background:#2A3140;border:2px solid #D9A441;padding:14px;font-size:12px;line-height:1.7;z-index:9}
#detail h3{font-size:15px;color:#F2D089;margin-bottom:6px}
#detail .k{color:#9BD4CC}
#detail button{margin-top:8px}
.note{font-size:11px;color:#8A8268;line-height:1.7;margin-top:10px;max-width:960px}
#toast{position:fixed;left:24px;bottom:24px;background:#8A6520;border:1px solid #D9A441;color:#F2D089;padding:8px 14px;font-size:12px;z-index:10}
</style></head><body>
<h1>塔层三选一 · 卡牌 UI 预览</h1>
<div class="sub">72 张卡 · 6 类 × 12 · 480×270 逻辑画布按 2× 显示 · 卡面 PNG 不含文字，文字由 UI 层渲染<br>
<b>预览字体 ≠ 实机字体</b>（R9 凤凰点阵体授权/缺字未核验）· 全部数值/概率/时长标待实测 · 本页只验证视觉与版式，不验证 Godot 渲染</div>
<div class="bar">
  <button id="bPick" class="on">三选一界面</button>
  <button id="bCodex">72 张图鉴</button>
  <span class="tag" id="stat"></span>
  <span style="font-size:11px;color:#8A8268">层</span><input id="stage" value="3">
  <span style="font-size:11px;color:#8A8268">局号</span><input id="runid" value="1001">
  <button id="bRedraw">换一批 (R)</button>
  <span style="font-size:11px;color:#8A8268">1/2/3 选卡 · Enter 确认 · Esc 图鉴</span>
</div>
<div id="pickOuter"><div id="pickStage">
  <div class="hd" id="hdL">第 3 层 · 择一机缘</div><div class="hdR" id="hdR">已选 0/8 · 道行 +0</div>
  <div class="rule"></div>
  <div id="slots"></div>
  <div class="ft">1 / 2 / 3 切换</div><div class="ftR">Esc 查看已有卡</div>
  <div class="confirm" id="confirm">确认 (Enter)</div>
</div></div>
<div id="codexOuter" class="hidden"><div id="codexStage">
  <div class="filters" id="filters"></div>
  <div id="grid"></div>
</div><div id="codexPhantom" style="width:1px;height:0"></div></div>
<div id="detail" class="hidden"></div>
<div id="toast" class="hidden"></div>
<div class="note" id="note"></div>
<script>
const LIB = __LIB__;
const FR = __FRAMES__;
const SG = __SIGILS__;
const CAT = {}, RAR = {}, TYP = {numeric:'纯数值',hybrid:'条件数值',mechanical:'机制'};
LIB.categories.forEach(c=>CAT[c.key]=c.name);
LIB.rarities.forEach(r=>RAR[r.key]=r.name);
const cards = LIB.cards, byId = {}; cards.forEach(c=>byId[c.id]=c);
let view='pick', stage=3, runid=1001, offered=[], sel=-1, picked=[], fltCat='all', fltRar='all', q='';

function hash(a,b){let h=(a*73856093 ^ b*19349663 ^ 0x9e3779b9)>>>0;return ()=>{h=(h*1664525+1013904223)>>>0;return h/4294967296;};}
function draw(){
  const rnd=hash(runid,stage), pool=cards.filter(c=>!picked.includes(c.id));
  const weighted=[]; pool.forEach(c=>{const w=c.weight||10;for(let i=0;i<w;i++)weighted.push(c);});
  const out=[], usedCat=new Set();
  for(let guard=0; guard<4000 && out.length<3; guard++){
    const c=weighted[Math.floor(rnd()*weighted.length)];
    if(!c||out.some(x=>x.id===c.id)||usedCat.has(c.cat))continue;
    if(c.excl.some(x=>picked.includes(x)))continue;
    out.push(c);usedCat.add(c.cat);
  }
  // 池不足时按类别补齐
  if(out.length<3){for(const c of pool){if(out.length>=3)break;if(!out.some(x=>x.id===c.id))out.push(c);}}
  return out.slice(0,3);
}
function cardHTML(c,idx,codex){
  const bg=FR[c.rarity], sg=SG[c.cat];
  const cls='card'+(c.rarity==='curse'?' curse':'')+(idx>=0&&idx===sel&&!codex?' sel':'');
  const extra=codex?'':'<div class="idx">'+(idx+1)+'</div>';
  return '<div class="'+cls+'" data-id="'+c.id+'" style="background-image:url('+bg+')">'+
    extra+
    '<img class="sigBig" src="'+sg+'">'+
    '<div class="cat">'+CAT[c.cat]+'</div>'+
    '<div class="nm">'+c.name+'</div>'+
    '<div class="tx">'+c.text+'</div>'+
    '<div class="info"><span>'+RAR[c.rarity]+'</span><span>x'+c.stack+'</span><span>'+TYP[c.type]+'</span></div>'+
  '</div>';
}
function renderPick(){
  document.getElementById('hdL').textContent='第 '+stage+' 层 · 择一机缘';
  document.getElementById('hdR').textContent='已选 '+picked.length+'/8 · 道行 +'+(picked.length*15);
  const box=document.getElementById('slots'); box.innerHTML='';
  offered.forEach((c,i)=>{
    const el=document.createElement('div'); el.innerHTML=cardHTML(c,i,false);
    const node=el.firstChild; node.style.left=(80+i*112)+'px'; node.style.top='52px';
    node.onclick=()=>{sel=i;renderPick();};
    box.appendChild(node);
  });
  document.getElementById('confirm').className='confirm'+(sel>=0?' ready':'');
  document.getElementById('stat').textContent='候选 '+offered.length+' 张 / 卡池 '+cards.length+' 张';
}
function confirmPick(){
  if(sel<0||!offered[sel]){toast('先用 1/2/3 选一张');return;}
  const c=offered[sel]; picked.push(c.id); toast('第 '+stage+' 层已选：'+c.name+'（'+CAT[c.cat]+'）');
  if(stage<8){stage++;offered=draw();sel=-1;}
  renderPick();
}
function toast(t){const e=document.getElementById('toast');e.textContent=t;e.classList.remove('hidden');clearTimeout(window._tt);window._tt=setTimeout(()=>e.classList.add('hidden'),2200);}
function renderFilters(){
  const f=document.getElementById('filters');
  let h='类别 ';
  h+='<button data-fc="all" class="'+(fltCat==='all'?'on':'')+'">全部</button>';
  LIB.categories.forEach(c=>h+='<button data-fc="'+c.key+'" class="'+(fltCat===c.key?'on':'')+'">'+c.name+'</button>');
  h+='<br>稀有度 ';
  h+='<button data-fr="all" class="'+(fltRar==='all'?'on':'')+'">全部</button>';
  LIB.rarities.forEach(r=>h+='<button data-fr="'+r.key+'" class="'+(fltRar===r.key?'on':'')+'">'+r.name+'</button>');
  h+='<br>搜索 <input id="q" value="'+q+'" placeholder="名称 / 效果 / ID" style="width:180px"> <span id="cnt"></span>';
  f.innerHTML=h;
  f.querySelectorAll('[data-fc]').forEach(b=>b.onclick=()=>{fltCat=b.dataset.fc;renderCodex();});
  f.querySelectorAll('[data-fr]').forEach(b=>b.onclick=()=>{fltRar=b.dataset.fr;renderCodex();});
  const qi=document.getElementById('q');
  qi.oninput=()=>{q=qi.value;renderCodexGrid();};
}
function filtered(){return cards.filter(c=>(fltCat==='all'||c.cat===fltCat)&&(fltRar==='all'||c.rarity===fltRar)&&(!q||(c.name+c.text+c.id).includes(q)));}
function renderCodexGrid(){
  const g=document.getElementById('grid'), list=filtered(); g.innerHTML='';
  list.forEach(c=>{const el=document.createElement('div');el.className='codexCard';el.innerHTML=cardHTML(c,-1,true);
    el.firstChild.onclick=()=>showDetail(c.id);g.appendChild(el);});
  document.getElementById('cnt').textContent=list.length+' / '+cards.length;
  const st=document.getElementById('codexStage');
  st.style.height=Math.max(270,78+Math.ceil(list.length/4)*152+16)+'px';
  // transform:scale(2) 不参与布局；phantom 补足另一倍高度，使外层滚动长度等于视觉长度
  document.getElementById('codexPhantom').style.height=st.style.height;
}
function renderCodex(){renderFilters();renderCodexGrid();}
function showDetail(id){
  const c=byId[id], e=document.getElementById('detail');
  const req=c.req.length?c.req.join(' / '):'无';
  const ex=c.excl.length?c.excl.map(x=>byId[x]?byId[x].name:x).join(' / '):'无';
  e.innerHTML='<h3>'+c.name+'</h3>'+
    '<div><span class="k">ID</span> '+c.id+'</div>'+
    '<div><span class="k">类别 / 稀有度</span> '+CAT[c.cat]+' · '+RAR[c.rarity]+'</div>'+
    '<div><span class="k">效果类型</span> '+TYP[c.type]+'</div>'+
    '<div><span class="k">效果</span> '+c.text+'</div>'+
    '<div><span class="k">堆叠上限</span> x'+c.stack+'</div>'+
    '<div><span class="k">实现钩子</span> '+c.hook+'</div>'+
    '<div><span class="k">前置</span> '+req+'</div>'+
    '<div><span class="k">互斥</span> '+ex+'</div>'+
    '<div><span class="k">权重 / 解锁</span> '+c.weight+' / '+c.unlock+'</div>'+
    '<div><span class="k">参数</span> '+JSON.stringify(c.params)+'</div>'+
    '<button onclick="document.getElementById(\'detail\').classList.add(\'hidden\')">关闭</button>';
  e.classList.remove('hidden');
}
function setView(v){
  view=v;
  document.getElementById('pickOuter').classList.toggle('hidden',v!=='pick');
  document.getElementById('codexOuter').classList.toggle('hidden',v!=='codex');
  document.getElementById('bPick').classList.toggle('on',v==='pick');
  document.getElementById('bCodex').classList.toggle('on',v==='codex');
  if(v==='codex')renderCodex();
}
document.getElementById('bPick').onclick=()=>setView('pick');
document.getElementById('bCodex').onclick=()=>setView('codex');
document.getElementById('bRedraw').onclick=()=>{runid++;offered=draw();sel=-1;renderPick();};
document.getElementById('confirm').onclick=confirmPick;
document.getElementById('stage').onchange=e=>{stage=Math.max(1,Math.min(8,parseInt(e.target.value)||1));offered=draw();sel=-1;renderPick();};
document.getElementById('runid').onchange=e=>{runid=parseInt(e.target.value)||1;offered=draw();sel=-1;renderPick();};
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT')return;
  if(e.key==='Escape'){setView(view==='pick'?'codex':'pick');return;}
  if(view==='codex')return;
  if('123'.includes(e.key)){sel=parseInt(e.key)-1;renderPick();return;}
  if(e.key==='ArrowLeft'){sel=(sel+2)%3;renderPick();return;}
  if(e.key==='ArrowRight'){sel=(sel+1)%3;renderPick();return;}
  if(e.key==='Enter'){confirmPick();return;}
  if(e.key==='r'||e.key==='R'){runid++;offered=draw();sel=-1;renderPick();return;}
});
document.getElementById('note').innerHTML=
  '说明：预览抽卡只模拟「同类最多 1 张 / 已选去重 / 互斥」三条规则，<b>未模拟 build 前置（流派 / 技能 / 词缀 / 装备）与层数解锁</b>，'+
  '完整规则见 docs/11 §6。卡框与纹样为程序化 PNG（24 色锁定、硬边），文字为 CSS 渲染，仅示意排版。<br>'+
  '数值红线：卡牌不得提高 realm_ratio≤1.60 / extra_pool≤600 / combo_multiplier≤2.5 / crit_multiplier≤1.8（docs/11 §4，R32）。'+
  'Q1 Godot 小版本未填，硬门禁 3/4，未建工程、未冻结设计。';
offered=draw();renderPick();
</script></body></html>
"""


def data_uri(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> int:
    lib = json.loads(LIB_PATH.read_text(encoding="utf-8"))
    errors, stats = validate_lib(lib)
    if errors:
        print("卡库自检未通过，拒绝生成：")
        for e in errors:
            print("  ✗ " + e)
        return 1

    CARD_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    frames, sigils, checks = {}, {}, []
    for r in ("common", "rare", "legend", "curse"):
        im = make_frame(r)
        im.save(CARD_DIR / f"frame_{r}.png")
        frames[r] = im
        checks.append(check_png(im, f"frame_{r}"))
    for c in lib["categories"]:
        im = make_sigil(c["key"])
        im.save(CARD_DIR / f"sigil_{c['key']}.png")
        sigils[c["key"]] = im
        checks.append(check_png(im, f"sigil_{c['key']}"))

    bad = [c for c in checks if c["semiAlpha"] or c["outOfPalette"]]
    if bad:
        print("PNG 自检未通过：", json.dumps(bad, ensure_ascii=False))
        return 1
    contact_sheet(frames, sigils).save(SHEET_OUT)

    # CSV（策划核对表，用 csv 模块正确处理文案里的逗号）
    cat_name = {c["key"]: c["name"] for c in lib["categories"]}
    rar_name = {r["key"]: r["name"] for r in lib["rarities"]}
    with CSV_OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "名称", "类别键", "类别", "稀有度键", "稀有度", "效果类型",
                    "效果文案", "堆叠上限", "实现钩子", "抽取权重", "解锁条件",
                    "互斥卡", "前置条件", "参数JSON"])
        for c in lib["cards"]:
            w.writerow([c["id"], c["name"], c["cat"], cat_name[c["cat"]],
                        c["rarity"], rar_name[c["rarity"]], c["type"], c["text"],
                        c["stack"], c["hook"], c["weight"], c["unlock"],
                        ";".join(c["excl"]), ";".join(c["req"]),
                        json.dumps(c["params"], ensure_ascii=False, separators=(",", ":"))])

    # 自包含 HTML
    html = (HTML.replace("__LIB__", json.dumps(lib, ensure_ascii=False, separators=(",", ":")))
                .replace("__FRAMES__", json.dumps({k: data_uri(v) for k, v in frames.items()}))
                .replace("__SIGILS__", json.dumps({k: data_uri(v) for k, v in sigils.items()})))
    HTML_OUT.write_text(html, encoding="utf-8")

    report = {
        "version": "v0.1",
        "round": 12,
        "source": "docs/buff-card-library.json",
        "spec": ["docs/11-塔层三选一卡牌系统.md", "docs/12-卡牌UI规格.md"],
        "status": "PROPOSAL · 数值/概率待实测；不是冻结规格",
        "validation": {"errors": [], "passed": True},
        "stats": stats,
        "offenseCeiling": lib["offenseCeiling"],
        "pngAssets": checks,
        "outputs": {
            "frames": [f"assets/ui/cards/frame_{r}.png" for r in frames],
            "sigils": [f"assets/ui/cards/sigil_{k}.png" for k in sigils],
            "contactSheet": "assets/_preview/buff_cards_contact_sheet.png",
            "preview": "assets/_preview/buff-card-preview.html",
            "csv": "docs/卡牌库.csv",
        },
        "previewKB": round(HTML_OUT.stat().st_size / 1024, 1),
        "credits": 0,
        "sourceImages": 0,
        "caveats": [
            "预览抽卡未模拟 build 前置与层数解锁，见 11 §6",
            "卡面 PNG 不含文字；预览字体 ≠ 实机字体（R9 未核验）",
            "卡牌全生效后 01 §8.1 极值验算未重跑（R32，待实测）",
            "Q1 未填，硬门禁 3/4，未建工程、未冻结",
        ],
    }
    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": True, "stats": stats, "pngAssets": len(checks),
                      "previewKB": report["previewKB"], "csvRows": len(lib["cards"]),
                      "credits": 0}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
