#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标 / 流派挂件程序化生成器（v0.7，规范见 docs/07-图标与挂件形状规范.md）

特点：零出图积分、零源图、可复现，只依赖 Pillow。换账号直接重跑即得同样结果。
用途：产出规则几何符号（图标 / 挂件），与 AI 出图链路（角色 / 怪物 / Boss）互补。

用法：
  /opt/homebrew/bin/python3 tools/build_icons.py

产出：
  assets/ui/icons/icon_<id>.png      skills 8 / schools 4 / realms 9 / gear 8 / affix 12 / legacy 6 = 47 件
  assets/char/acc/acc_<id>.png       16x16，4 件武器挂件
  assets/_preview/icons_contact_sheet.png          首 16 件（技能+流派+挂件）目检图
  assets/_preview/icons_extended_contact_sheet.png 第 10 轮 17 件（境界+装备）目检图
  assets/_preview/icons_final_contact_sheet.png    第 12 轮 18 件（词缀+灵韵）目检图
  docs/icon-catalog.json             47 件全量形状分配与状态（M9 可机器核对）

硬约束：24 色锁定板、1px 墨描边、透明硬边、半透明像素 0、四周留白、无抗锯齿。

v0.5（第 10 轮）：补齐 20 色板子集（R24）、新增 realm_symbol / gear_symbol、
按 docs/07 §7.2 的单件 ID 契约生成 17 件。12 词缀 + 6 灵韵因机制未定稿不做。

v0.7（第 12 轮）：Q25 / Q26 已按推荐值确认（docs/decision-receipt.json），
按 docs/09 §2.5 / §3 的符号分配补齐 18 件，R23 纪律仍适用（先定 ID 再生成）。
09 §2.5 提醒「xinmo 半空心盏与 shiling 空盏加断点同族近似、并排可能不可分」，
本轮直接采纳其备选：shiling 改用「断链三节」，从根上避免同组剪影撞车（M9）。
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT / "assets/ui/icons"
ACC_DIR = ROOT / "assets/char/acc"
PREVIEW_DIR = ROOT / "assets/_preview"
CATALOG_PATH = ROOT / "docs/icon-catalog.json"

# 完整 20 色核心板（与 docs/asset-manifest-pixel.json、tools/qc_sprites.py 一致）
# R24：v0.4 只收了 16 色，缺墨三阶与 #8A8268，境界第 1 段色 #4A5568 会被误判越界。
INK = (0, 0, 0, 255)
INK_1 = (18, 22, 31, 255)          # #12161F
INK_2 = (42, 49, 64, 255)          # #2A3140
INK_3 = (74, 85, 104, 255)         # #4A5568
PAPER = (232, 223, 200, 255)       # #E8DFC8
PAPER_D = (201, 191, 163, 255)     # #C9BFA3
PAPER_DD = (138, 130, 104, 255)    # #8A8268
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

PALETTE = {
    c[:3] for c in (
        INK, INK_1, INK_2, INK_3, PAPER, PAPER_D, PAPER_DD,
        JADE_D, JADE, JADE_L, RED_D, RED, RED_L,
        GOLD_D, GOLD, GOLD_L, VIO_D, VIO, VIO_L, WHITE,
    )
}

SKILLS = ["sword_qi", "flying_sword", "thunder_talisman", "paper_puppet",
          "dan_fire", "rejuvenation", "fist_force", "vajra_body"]
SCHOOLS = ["jian", "fu", "dan", "ti"]

# 9 境：(ID 段, 中文, 序号 1-9, 段色)。严格按 04 §4：颜色只分 4 段，
# 第 4 段「合体/大乘/渡劫」用金的三级亮阶递进，段内靠 1-9 道纹样 + 数字区分。
REALMS = [
    ("lianqi",   "炼气", 1, INK_3),
    ("zhuji",    "筑基", 2, INK_3),
    ("jindan",   "金丹", 3, JADE),
    ("yuanying", "元婴", 4, JADE),
    ("huashen",  "化神", 5, VIO),
    ("lianxu",   "炼虚", 6, VIO),
    ("heti",     "合体", 7, GOLD_D),
    ("dacheng",  "大乘", 8, GOLD),
    ("dujie",    "渡劫", 9, GOLD_L),
]

# 8 装备品类形状（07 §3 已列；R28：8 件是品类，不是槽位）
GEAR = ["sword", "armor", "crown", "pendant", "boots", "pouch", "seal", "ring"]

# 第 12 轮：12 天劫词缀（09 §2.2 / §2.5），16x16 菱形框，靠形状不靠加色。
# (ID 段, 中文名, 符号键)。符号键即 09 §2.5 的最后一列，shiling 按建议改断链三节。
AFFIXES = [
    ("xinmo",    "心魔", "half_cup"),
    ("leijie",   "雷劫", "bolt"),
    ("fengyin",  "封印", "box_slash"),
    ("jifeng",   "疾风", "wind_lines"),
    ("tiebi",    "铁壁", "solid_shield"),
    ("jingfan",  "镜反", "twin_tri"),
    ("shiling",  "噬灵", "broken_chain"),
    ("wuxiang",  "无相", "two_cells"),
    ("wuxu",     "无序", "scatter4"),
    ("nifeng",   "逆风", "twin_arrow"),
    ("wuyin",    "雾隐", "eye_mist"),
    ("gongjie",  "共劫", "cross_diamond"),
]

# 第 12 轮：6 传承灵韵（09 §3），32x32 六边框。
LEGACIES = [
    ("jianhen",   "剑痕", "cross_slash"),
    ("fuyin",     "符印", "seal_grid"),
    ("danxi",     "丹息", "tripod"),
    ("tiegu",     "铁骨", "scale_plates"),
    ("jiying",    "疾影", "speed_lines"),
    ("lingquan",  "灵泉", "drop_ripple"),
]


def F(v: int, n: int) -> int:
    """把 32 基准坐标缩放到 n 尺寸画布（像素取整，保持硬边）。

    钳制到 [1, n-2]：16x16 挂件缩放时 round(0.5)=0 会让剑尖贴到画布边缘，
    破坏「四周 >=1px 透明」的硬约束（第 9 轮实测 acc_jian 踩过）。
    """
    return min(n - 2, max(1, int(round(v * n / 32))))


def frame(d: ImageDraw.ImageDraw, kind: str, n: int) -> None:
    """外框（分类层）：6 类剪影两两可区分，四周留 1px 透明。"""
    if kind == "octagon":
        k = F(6, n)
        pts = [(k, 1), (n - 1 - k, 1), (n - 2, k), (n - 2, n - 1 - k),
               (n - 1 - k, n - 2), (k, n - 2), (1, n - 1 - k), (1, k)]
        d.polygon(pts, fill=PAPER)
        d.line(pts + [pts[0]], fill=INK, width=1)
    elif kind == "circle":
        d.ellipse((1, 1, n - 2, n - 2), fill=PAPER, outline=INK)
    elif kind == "diamond":
        pts = [(n // 2, 1), (n - 2, n // 2), (n // 2, n - 2), (1, n // 2)]
        d.polygon(pts, fill=PAPER)
        d.line(pts + [pts[0]], fill=INK, width=1)
    elif kind == "shield":
        pts = [(2, 2), (n - 3, 2), (n - 3, F(20, n)),
               (n // 2, n - 2), (2, F(20, n))]
        d.polygon(pts, fill=PAPER)
        d.line(pts + [pts[0]], fill=INK, width=1)
    elif kind == "hexagon":
        pts = [(F(9, n), 1), (F(23, n), 1), (n - 2, n // 2),
               (F(23, n), n - 2), (F(9, n), n - 2), (1, n // 2)]
        d.polygon(pts, fill=PAPER)
        d.line(pts + [pts[0]], fill=INK, width=1)
    elif kind == "scroll":
        d.rectangle((2, F(8, n), n - 3, F(24, n)), fill=PAPER, outline=INK)
        d.rectangle((1, F(6, n), F(4, n), F(26, n)), fill=PAPER_D, outline=INK)
        d.rectangle((F(28, n), F(6, n), n - 2, F(26, n)), fill=PAPER_D, outline=INK)
    elif kind == "none":
        return


def skill_symbol(d: ImageDraw.ImageDraw, key: str) -> None:
    """8 技能内部符号 = 06 §4 的 8 个特效形状，玩家看图标即可预判屏幕效果。"""
    if key == "sword_qi":                       # 横向弯月弧
        d.arc((7, 9, 25, 25), 195, 345, fill=JADE_D, width=3)
        d.arc((9, 11, 23, 23), 195, 345, fill=JADE_L, width=2)
        d.point((24, 12), fill=GOLD)
        d.point((22, 9), fill=GOLD_L)
    elif key == "flying_sword":                 # 三道斜向细长飞剑
        for i, c in enumerate((JADE_D, JADE, JADE_L)):
            x = 8 + i * 4
            d.line((x, 23, x + 11, 9), fill=c, width=2)
            d.line((x + 9, 12, x + 13, 8), fill=c, width=2)
        d.rectangle((7, 21, 10, 24), fill=GOLD, outline=INK)
    elif key == "thunder_talisman":             # 纵向折线雷 + 方形符箓
        d.line([(18, 5), (13, 15), (18, 15), (13, 24)], fill=VIO, width=3)
        d.line([(18, 5), (13, 15), (18, 15), (13, 24)], fill=VIO_L, width=1)
        d.rectangle((10, 23, 21, 28), fill=PAPER_D, outline=INK)
        d.line((15, 24, 15, 27), fill=RED, width=1)
    elif key == "paper_puppet":                 # 方形符纸 + 田字朱印
        d.rectangle((10, 7, 22, 25), fill=PAPER_D, outline=INK)
        d.rectangle((13, 13, 19, 19), fill=RED, outline=RED_D)
        d.line((16, 13, 16, 19), fill=PAPER, width=1)
        d.line((13, 16, 19, 16), fill=PAPER, width=1)
    elif key == "dan_fire":                     # 实心圆火团
        d.ellipse((8, 8, 24, 24), fill=RED, outline=RED_D)
        d.ellipse((12, 12, 20, 20), fill=GOLD)
        d.ellipse((14, 14, 18, 18), fill=WHITE)
        d.point((7, 12), fill=RED_L)
        d.point((25, 18), fill=RED_L)
    elif key == "rejuvenation":                 # 空心圆环（不填充）
        d.ellipse((7, 7, 25, 25), outline=JADE, width=3)
        d.ellipse((11, 11, 21, 21), outline=JADE_L, width=1)
        d.point((16, 5), fill=WHITE)
        d.point((27, 16), fill=WHITE)
    elif key == "fist_force":                   # 贴地推进的扇形冲击波
        # 第 9 轮目检返修：原版一个孤立黑方块太突兀，改三层同心弧 + 拳套 + 地面基线
        d.arc((5, 7, 27, 28), 200, 340, fill=GOLD_D, width=2)
        d.arc((8, 10, 24, 26), 200, 340, fill=GOLD, width=2)
        d.arc((11, 13, 21, 24), 200, 340, fill=GOLD_L, width=2)
        d.rectangle((6, 23, 12, 28), fill=JADE_D, outline=INK)
        for x in (7, 9, 11):
            d.line((x, 23, x, 25), fill=JADE_L, width=1)
        d.line((6, 28, 26, 28), fill=INK, width=1)
    elif key == "vajra_body":                   # 空心六边形金罩包裹角色
        # 第 9 轮目检返修：原版实心金块 + 大黑小人把六边形轮廓吃掉了，改空心粗边
        pts = [(12, 4), (20, 4), (26, 16), (20, 28), (12, 28), (6, 16)]
        d.line(pts + [pts[0]], fill=GOLD_D, width=3)
        inner = [(13, 6), (19, 6), (23, 16), (19, 26), (13, 26), (9, 16)]
        d.line(inner + [inner[0]], fill=GOLD, width=1)
        d.ellipse((15, 11, 17, 13), fill=INK)
        d.rectangle((14, 15, 18, 22), fill=INK)


def school_symbol(d: ImageDraw.ImageDraw, key: str, n: int) -> None:
    """4 流派符号，32 图标与 16 挂件共用同一形状（缓解 R17）。"""
    f = lambda v: F(v, n)
    if key == "jian":                            # 竖直剑 + 十字护手
        # 第 9 轮目检返修：16x16 挂件下 2px 剑身会被墨描边吃成一根黑线，
        # 加宽到 3px、小尺寸不描边，让剑身 / 护手 / 剑柄三层都读得出来。
        d.rectangle((f(14), f(3), f(18), f(20)), fill=JADE_L)
        if n >= 32:
            d.line((f(14), f(3), f(14), f(20)), fill=INK, width=1)
            d.line((f(18), f(3), f(18), f(20)), fill=INK, width=1)
        d.polygon([(f(14), f(3)), (f(16), f(1)), (f(18), f(3))], fill=WHITE)
        d.rectangle((f(10), f(20), f(22), f(22)), fill=GOLD, outline=INK)
        d.rectangle((f(15), f(22), f(17), f(29)), fill=RED_D, outline=INK)
    elif key == "fu":                            # 竖符纸 + 朱印
        d.rectangle((f(11), f(3), f(21), f(28)), fill=PAPER_D, outline=INK)
        d.rectangle((f(14), f(10), f(18), f(15)), fill=RED, outline=RED_D)
        d.line((f(13), f(19), f(19), f(19)), fill=INK, width=1)
        d.line((f(13), f(23), f(19), f(23)), fill=INK, width=1)
    elif key == "dan":                           # 梯形丹炉 + 盖 + 三足
        d.polygon([(f(9), f(10)), (f(23), f(10)), (f(21), f(24)), (f(11), f(24))],
                  fill=GOLD_D, outline=INK)
        d.rectangle((f(7), f(7), f(25), f(10)), fill=GOLD, outline=INK)
        for x in (11, 16, 21):
            d.rectangle((f(x - 1), f(24), f(x + 1), f(28)), fill=INK)
        d.ellipse((f(14), f(13), f(18), f(17)), fill=RED, outline=RED_D)
    elif key == "ti":                            # 拳套 + 指节
        d.rectangle((f(8), f(9), f(24), f(24)), fill=JADE_D, outline=INK)
        d.rectangle((f(10), f(5), f(22), f(11)), fill=JADE, outline=INK)
        for x in (12, 16, 20):
            d.line((f(x), f(6), f(x), f(11)), fill=INK, width=1)
        d.rectangle((f(9), f(24), f(23), f(28)), fill=RED_D, outline=INK)


def realm_symbol(d: ImageDraw.ImageDraw, rank: int, band: tuple) -> None:
    """9 境界：卷轴框内一条 4 段色横带 + 从左到右 1-9 道墨色刻痕。

    严格按 04 §4「颜色只分 4 段，段内靠形状（像素印文/边框）和数字区分」。
    数字由 UI 文字层叠加，图标不内置自造像素字体（避开 R9 授权）。
    """
    d.rectangle((5, 11, 27, 20), fill=band, outline=INK)
    for i in range(rank):
        x = 7 + i * 2
        d.line((x, 13, x, 18), fill=INK, width=1)
    # 段色亮阶提示：色带下沿一条 1px 亮线，只加深层次不新增色相
    d.line((6, 21, 26, 21), fill=GOLD_D, width=1)


def gear_symbol(d: ImageDraw.ImageDraw, key: str) -> None:
    """8 装备简笔符号，盾形框内；两两剪影必须可区分（M9）。"""
    if key == "sword":                          # 交叉双剑（与流派单竖剑区分）
        d.line((8, 8, 24, 24), fill=JADE_L, width=3)
        d.line((24, 8, 8, 24), fill=JADE, width=3)
        d.rectangle((13, 13, 19, 19), fill=GOLD, outline=INK)
        d.point((10, 7), fill=WHITE)
        d.point((22, 7), fill=WHITE)
    elif key == "armor":                        # 肩甲 + 中缝
        d.polygon([(7, 9), (25, 9), (23, 25), (9, 25)], fill=INK_2, outline=INK)
        d.rectangle((14, 9, 18, 25), fill=PAPER_D, outline=INK)
        d.line((7, 13, 25, 13), fill=GOLD, width=2)
        d.point((11, 20), fill=GOLD_L)
        d.point((21, 20), fill=GOLD_L)
    elif key == "crown":                        # 三叉冠
        d.rectangle((6, 22, 26, 25), fill=GOLD, outline=INK)
        d.polygon([(7, 22), (11, 10), (14, 22)], fill=GOLD_L, outline=INK)
        d.polygon([(13, 22), (16, 6), (19, 22)], fill=GOLD_L, outline=INK)
        d.polygon([(18, 22), (21, 10), (25, 22)], fill=GOLD_L, outline=INK)
        d.rectangle((14, 14, 18, 17), fill=RED, outline=RED_D)
    elif key == "pendant":                      # 玉佩环 + 三股流苏
        d.ellipse((10, 6, 22, 18), outline=JADE, width=3)
        d.point((16, 6), fill=GOLD)
        d.line((16, 18, 16, 27), fill=RED_D, width=2)
        d.line((12, 21, 12, 26), fill=RED, width=1)
        d.line((20, 21, 20, 26), fill=RED, width=1)
    elif key == "boots":                        # 靴筒 + 翻边 + 鞋头 + 独立鞋底
        # 第 10 轮目检返修：原版一整块深色 L 形读成积木，看不出是靴子。
        # 拆成四层可辨结构；坐标收在 y<=23、x<=24，避免画出盾形框斜边之外。
        d.polygon([(10, 8), (19, 8), (19, 17), (24, 17), (25, 21), (10, 21)],
                  fill=INK_2, outline=INK)
        d.rectangle((9, 6, 20, 9), fill=GOLD_D, outline=INK)       # 筒口翻边
        d.line((10, 13, 19, 13), fill=PAPER_D, width=1)             # 筒身横纹
        d.polygon([(19, 17), (24, 17), (25, 21), (21, 21)],
                  fill=JADE_D, outline=INK)                          # 青玉鞋头
        d.rectangle((9, 21, 24, 23), fill=INK)                      # 鞋底
        d.line((10, 22, 23, 22), fill=PAPER_D, width=1)              # 鞋底高光
    elif key == "pouch":                        # 束口囊袋
        d.polygon([(10, 12), (22, 12), (25, 26), (7, 26)], fill=PAPER_D, outline=INK)
        d.rectangle((12, 8, 20, 12), fill=RED_D, outline=INK)
        d.line((9, 16, 23, 16), fill=GOLD_D, width=1)
        d.ellipse((14, 17, 18, 21), fill=GOLD, outline=INK)
    elif key == "seal":                         # 方印 + 朱文田字
        d.rectangle((9, 9, 23, 23), fill=RED_D, outline=INK)
        d.rectangle((12, 12, 20, 20), fill=PAPER, outline=RED)
        d.line((16, 12, 16, 20), fill=RED, width=1)
        d.line((12, 16, 20, 16), fill=RED, width=1)
        d.rectangle((12, 5, 20, 9), fill=GOLD_D, outline=INK)
    elif key == "ring":                         # 环 + 顶部宝石
        d.ellipse((9, 12, 23, 26), outline=GOLD, width=3)
        d.polygon([(12, 11), (16, 5), (20, 11)], fill=JADE_L, outline=INK)
        d.point((16, 8), fill=WHITE)


def affix_symbol(d: ImageDraw.ImageDraw, key: str, n: int) -> None:
    """12 天劫词缀内符号（09 §2.5），16x16 菱形框内。

    第 12 轮目检返修：初版把 32 基准坐标缩放进 16 画布，细笔画全被吃掉
    （断链 / 四格 / 双箭头糊成色块，雾隐与共劫都读成菱形网格，剑痕第二
    条白斜线在宣纸底上消失）。现改为**直接以 16 为基准**定义像素，每个
    符号只留 2-4 笔高对比粗笔画，收在 x/y = 3..13 的菱形可用区。
    """
    f = lambda v: min(n - 2, max(1, int(round(v * n / 16))))
    if key == "half_cup":                        # 半空心盏：杯壁 + 下半实心液面
        d.line([(f(4), f(4)), (f(4), f(11)), (f(12), f(11)), (f(12), f(4))],
               fill=INK, width=2)
        d.line((f(4), f(4), f(12), f(4)), fill=INK, width=1)
        d.rectangle((f(5), f(8), f(11), f(10)), fill=JADE_D)
    elif key == "bolt":                          # 纵折线
        d.line([(f(10), f(3)), (f(6), f(8)), (f(10), f(8)), (f(6), f(13))],
               fill=VIO, width=2)
        d.line((f(5), f(14), f(11), f(14)), fill=VIO_L, width=1)
    elif key == "box_slash":                     # 方框加斜杠
        d.rectangle((f(4), f(4), f(12), f(12)), outline=INK, width=1)
        d.line((f(4), f(12), f(12), f(4)), fill=RED, width=2)
    elif key == "wind_lines":                    # 三道横风线，长度递减
        for y, x0, x1 in ((5, 3, 13), (8, 4, 12), (11, 6, 10)):
            d.line((f(x0), f(y), f(x1), f(y)), fill=JADE_D, width=2)
            d.line((f(x1), f(y), f(x1), f(y + 2)), fill=JADE_D, width=1)
    elif key == "solid_shield":                  # 实心盾 + 金竖线
        d.polygon([(f(4), f(3)), (f(12), f(3)), (f(12), f(9)),
                   (f(8), f(13)), (f(4), f(9))], fill=INK_2, outline=INK)
        d.line((f(8), f(5), f(8), f(10)), fill=GOLD, width=2)
    elif key == "twin_tri":                      # 对置双三角（尖端相对，沙漏剪影）
        d.polygon([(f(3), f(3)), (f(13), f(3)), (f(8), f(8))],
                  fill=RED_D, outline=INK)
        d.polygon([(f(3), f(13)), (f(13), f(13)), (f(8), f(8))],
                  fill=RED_D, outline=INK)
    elif key == "broken_chain":                  # 断链三节（09 §2.5 备选，避开与 half_cup 同族）
        for x in (3, 7, 11):
            d.rectangle((f(x), f(6), f(x + 2), f(9)), fill=RED_D, outline=INK)
        d.point((f(6), f(7)), fill=INK)
        d.point((f(10), f(7)), fill=INK)
    elif key == "two_cells":                     # 两格缺一角：大小两格一眼可数
        d.rectangle((f(3), f(5), f(7), f(11)), fill=PAPER_D, outline=INK)
        d.rectangle((f(9), f(5), f(13), f(9)), fill=PAPER_D, outline=INK)
        d.line((f(9), f(12), f(13), f(12)), fill=INK, width=1)
    elif key == "scatter4":                      # 打散四格：四个错位实心方块
        for x, y in ((3, 3), (10, 4), (4, 10), (11, 9)):
            d.rectangle((f(x), f(y), f(x + 3), f(y + 3)), fill=GOLD_D, outline=INK)
    elif key == "twin_arrow":                    # 左右双向箭头
        d.line((f(3), f(8), f(13), f(8)), fill=RED_D, width=2)
        d.polygon([(f(3), f(8)), (f(7), f(4)), (f(7), f(12))], fill=RED, outline=INK)
        d.polygon([(f(13), f(8)), (f(9), f(4)), (f(9), f(12))], fill=RED, outline=INK)
    elif key == "eye_mist":                      # 横向椭圆眼 + 瞳孔 + 雾点（与菱形外框不同形）
        d.ellipse((f(3), f(5), f(13), f(11)), outline=INK, width=2)
        d.ellipse((f(7), f(7), f(9), f(9)), fill=VIO, outline=INK)
        for x, y in ((3, 3), (13, 3), (8, 13)):
            d.point((f(x), f(y)), fill=PAPER_DD)
    elif key == "cross_diamond":                 # 交叠双菱（只画两个轮廓，不做网格）
        p1 = [(f(8), f(2)), (f(12), f(6)), (f(8), f(10)), (f(4), f(6))]
        p2 = [(f(8), f(6)), (f(12), f(10)), (f(8), f(14)), (f(4), f(10))]
        d.line(p1 + [p1[0]], fill=GOLD_D, width=2)
        d.line(p2 + [p2[0]], fill=VIO, width=2)


def legacy_symbol(d: ImageDraw.ImageDraw, key: str, n: int) -> None:
    """6 传承灵韵内嵌纹样（09 §3），32x32 六边框内；与 4 流派不同形但呼应。"""
    f = lambda v: F(v, n)
    if key == "cross_slash":                     # 交叠双斜线（第 12 轮目检返修：白斜线在宣纸底不可见 → 改金）
        d.line((f(9), f(23), f(23), f(9)), fill=JADE_L, width=3)
        d.line((f(11), f(9), f(23), f(21)), fill=GOLD_D, width=2)
        d.point((f(16), f(16)), fill=GOLD_L)
    elif key == "seal_grid":                     # 田字朱印
        d.rectangle((f(9), f(9), f(23), f(23)), fill=RED_D, outline=INK)
        d.rectangle((f(12), f(12), f(20), f(20)), outline=PAPER, width=1)
        d.line((f(16), f(12), f(16), f(20)), fill=PAPER, width=1)
        d.line((f(12), f(16), f(20), f(16)), fill=PAPER, width=1)
    elif key == "tripod":                        # 三足炉
        d.polygon([(f(9), f(12)), (f(23), f(12)), (f(21), f(23)), (f(11), f(23))],
                  fill=GOLD_D, outline=INK)
        d.rectangle((f(7), f(9), f(25), f(12)), fill=GOLD, outline=INK)
        for x in (11, 16, 21):
            d.rectangle((f(x - 1), f(23), f(x + 1), f(27)), fill=INK)
        d.ellipse((f(14), f(14), f(18), f(18)), fill=RED, outline=RED_D)
    elif key == "scale_plates":                  # 层叠甲片（三层错落）
        for i, (y, x0, x1) in enumerate(((9, 11, 21), (14, 9, 23), (19, 11, 21))):
            d.rectangle((f(x0), f(y), f(x1), f(y + 5)),
                        fill=(INK_2, JADE_D, GOLD_D)[i], outline=INK)
            d.line((f(x0 + 1), f(y + 1), f(x1 - 1), f(y + 1)), fill=PAPER_D, width=1)
    elif key == "speed_lines":                   # 三道风线
        for i, (y, x0) in enumerate(((10, 8), (16, 11), (22, 8))):
            d.line((f(x0), f(y), f(x0 + 15), f(y)), fill=VIO_L, width=2)
            d.line((f(x0 + 15), f(y), f(x0 + 12), f(y + 3)), fill=VIO, width=1)
    elif key == "drop_ripple":                   # 水滴加波纹
        d.polygon([(f(16), f(7)), (f(21), f(16)), (f(16), f(21)), (f(11), f(16))],
                  fill=JADE, outline=INK)
        d.point((f(15), f(14)), fill=WHITE)
        d.arc((f(7), f(20), f(25), f(28)), 200, 340, fill=JADE_L, width=2)
        d.arc((f(10), f(23), f(22), f(29)), 200, 340, fill=JADE_D, width=1)


def corner_rank(d: ImageDraw.ImageDraw, n: int, rank: int) -> None:
    """角标：右上 4x4 区域内用金点数量表示 1-4 阶；rank=0 留空。"""
    if rank <= 0:
        return
    for i in range(min(4, rank)):
        x = n - 4 - (i % 2) * 2
        y = 3 + (i // 2) * 2
        d.point((x, y), fill=GOLD)


def make_icon(key: str, frame_kind: str, n: int = 32, rank: int = 0,
              draw_symbol=None, symbol_args: tuple = ()) -> Image.Image:
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    frame(d, frame_kind, n)
    if draw_symbol is not None:
        draw_symbol(d, *symbol_args)
    elif n == 32 and key in SKILLS:
        skill_symbol(d, key)
    else:
        school_symbol(d, key, n)
    corner_rank(d, n, rank)
    return im


def check(im: Image.Image) -> dict:
    """自检：尺寸 / 半透明 / 越界色 / 四周留白 / coverage。"""
    px = im.load()
    w, h = im.size
    semi = out = opaque = 0
    edge_pixels = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if 0 < a < 255:
                semi += 1
            if a > 0:
                opaque += 1
                if (r, g, b) not in PALETTE:
                    out += 1
                if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                    edge_pixels += 1
    return {"size": [w, h], "semiAlpha": semi, "outOfPalette": out,
            "coverage": round(opaque / (w * h), 4), "edgePixels": edge_pixels}


def contact_sheet(entries: list, path: Path, cols: int = 4, scale: int = 6) -> None:
    """6x 整数放大并排目检图（保持各素材真实像素尺寸，不做拉伸）。"""
    cell_w, cell_h = 220, 32 * scale + 28
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h + 10), (245, 242, 232))
    sd = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(entries):
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        bg = Image.new("RGBA", big.size, (18, 22, 31, 255))
        bg.alpha_composite(big)
        sheet.paste(bg.convert("RGB"), (x + 8, y + 24))
        sd.text((x + 8, y + 6), label, fill=(20, 20, 20))
    sheet.save(path)


CATALOG = {
    "version": "v0.7",
    "spec": "docs/07-图标与挂件形状规范.md",
    "generator": "tools/build_icons.py",
    "cost": "0 积分（程序化几何绘制，不调用出图模型）",
    "paletteRule": "24 色锁定板（20 核心 + 4 预留），越界色必须为 0",
    "frameGrammar": {
        "skill": {"frame": "octagon", "size": 32, "innerSource": "06 §4 特效形状"},
        "school": {"frame": "circle", "size": 32, "innerSource": "4 流派符号，与挂件同形"},
        "affix": {"frame": "diamond", "size": 16, "innerSource": "09 §2.5：12 个菱形内符号"},
        "realm": {"frame": "scroll", "size": 32, "innerSource": "04 §4：4 段色 + 1-9 道刻痕"},
        "equipment": {"frame": "shield", "size": 32, "innerSource": "剑/甲/冠/佩/靴/囊/印/环"},
        "legacy": {"frame": "hexagon", "size": 32, "innerSource": "09 §3：6 种内嵌纹样"},
    },
    "idContract": {
        "spec": "docs/07 §7.2 + 09 §2.2/§3（R23 纪律：先定 ID 再生成，一经写入不得改名）",
        "realm": [f"icon_realm_{slug}" for slug, _, _, _ in REALMS],
        "equipment": [f"icon_gear_{g}" for g in GEAR],
        "affix": [f"icon_affix_{slug}" for slug, _, _ in AFFIXES],
        "legacy": [f"icon_legacy_{slug}" for slug, _, _ in LEGACIES],
    },
    "sizeConflictR24": "v0.3 工单把词缀 32/境界 16/灵韵 16 标反；按 07 §2.1 校正为词缀 16、境界 32、灵韵 32。qc loose 扫描已允许 icons 目录 {16,32} 两档",
    "producedByRound": {"round9": 12, "round10": 17, "round12": 18},
    "items": [],
    "accessories": [],
    "pending": [],
    "slotContract": {
        "spec": "09 §4（Q27 已按推荐值确认：3 槽位 + 8 品类；R28 更正）",
        "slots": ["slot_1", "slot_2", "slot_3"],
        "unlock": {"slot_1": "初始", "slot_2": "金丹（第 3 境）", "slot_3": "炼虚（第 6 境）"},
        "rule": "每槽可装任意品类，但同品类一局内不可重复；8 件 icon_gear_* 按品类命名，无需改名",
        "gearTypes": [f"gear_type_{g}" for g in GEAR],
    },
    "status": "形状样板，待目检与合规确认；不得直接入库",
    "proposalRef": {
        "spec": "docs/09-内容命名提案.md",
        "status": "CONFIRMED by docs/decision-receipt.json（Q25=proposal_v1 / Q26=proposal_b / Q27=proposal_3slots_8types）",
        "affix": "12 条词缀 ID 与符号已按 09 §2.5 生成；shiling 采纳备选「断链三节」避开与 xinmo 同族",
        "legacy": "6 条灵韵纹样已按 09 §3 生成；R27 按方案 B 新增 legacy_effects，见 docs/10",
        "equipment": "R28：8 个 ID 是品类非槽位；3 个 slot_* 已写入本目录 slotContract",
        "note": "pending 18 件已全部产出，0 积分；Q1 仍未填，不进阶段二",
    },
}


def main():
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    ACC_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    made = []
    # ---- 第 9 轮已有：8 技能 + 4 流派 + 4 挂件 ----
    for key in SKILLS:
        im = make_icon(key, "octagon", 32)
        im.save(ICONS_DIR / f"icon_{key}.png")
        made.append((f"icon_{key}", im))
        CATALOG["items"].append(
            {"id": f"icon_{key}", "group": "skill", "frame": "octagon",
             "size": 32, "innerSymbol": key, "status": "produced", "round": 9})
    for key in SCHOOLS:
        im = make_icon(key, "circle", 32)
        im.save(ICONS_DIR / f"icon_{key}.png")
        made.append((f"icon_{key}", im))
        CATALOG["items"].append(
            {"id": f"icon_{key}", "group": "school", "frame": "circle",
             "size": 32, "innerSymbol": key, "status": "produced", "round": 9})
        # R23：入库文件名必须用 v0.3 工单已定的 4 个挂件 ID，不能按内部短名。
        acc_id = {"jian": "acc_sword", "fu": "acc_talisman",
                  "dan": "acc_pill", "ti": "acc_fist"}[key]
        acc = make_icon(key, "none", 16)
        acc.save(ACC_DIR / f"{acc_id}.png")
        made.append((acc_id, acc))
        CATALOG["accessories"].append(
            {"id": acc_id, "symbolKey": key, "size": 16, "innerSymbol": key,
             "attachTo": "char_player cast 帧手部", "status": "produced", "round": 9})

    base_count = len(made)

    # ---- 第 10 轮新增：9 境界（卷轴框） ----
    for slug, cn, rank, band in REALMS:
        key = f"icon_realm_{slug}"
        im = make_icon(key, "scroll", 32, 0, realm_symbol, (rank, band))
        im.save(ICONS_DIR / f"{key}.png")
        made.append((key, im))
        CATALOG["items"].append(
            {"id": key, "group": "realm", "frame": "scroll", "size": 32,
             "innerSymbol": f"{cn}·{rank} 道刻痕", "bandColor":
             "#%02X%02X%02X" % band[:3], "status": "produced", "round": 10})

    # ---- 第 10 轮新增：8 装备（盾形框，形状样板） ----
    for g in GEAR:
        key = f"icon_gear_{g}"
        im = make_icon(key, "shield", 32, 0, gear_symbol, (g,))
        im.save(ICONS_DIR / f"{key}.png")
        made.append((key, im))
        CATALOG["items"].append(
            {"id": key, "group": "equipment", "frame": "shield", "size": 32,
             "innerSymbol": g, "status": "produced", "round": 10,
             "note": "形状样板；装备槽位 ID 以 01 装备系统最终定稿为准"})

    round10_count = len(made)

    # ---- 第 12 轮新增：12 天劫词缀（16x16 菱形框，Q25 已确认） ----
    for slug, cn, sym in AFFIXES:
        key = f"icon_affix_{slug}"
        im = make_icon(key, "diamond", 16, 0, affix_symbol, (sym, 16))
        im.save(ICONS_DIR / f"{key}.png")
        made.append((key, im))
        CATALOG["items"].append(
            {"id": key, "group": "affix", "frame": "diamond", "size": 16,
             "innerSymbol": sym, "label": cn, "status": "produced", "round": 12})

    # ---- 第 12 轮新增：6 传承灵韵（32x32 六边框，Q26 方案 B） ----
    for slug, cn, sym in LEGACIES:
        key = f"icon_legacy_{slug}"
        im = make_icon(key, "hexagon", 32, 0, legacy_symbol, (sym, 32))
        im.save(ICONS_DIR / f"{key}.png")
        made.append((key, im))
        CATALOG["items"].append(
            {"id": key, "group": "legacy", "frame": "hexagon", "size": 32,
             "innerSymbol": sym, "label": cn, "status": "produced", "round": 12})

    # 三张目检拼图：按轮次分组，便于 M9 逐组核对剪影
    contact_sheet(made[:base_count], PREVIEW_DIR / "icons_contact_sheet.png", cols=4)
    contact_sheet(made[base_count:round10_count],
                  PREVIEW_DIR / "icons_extended_contact_sheet.png", cols=5)
    contact_sheet(made[round10_count:],
                  PREVIEW_DIR / "icons_final_contact_sheet.png", cols=6)

    CATALOG_PATH.write_text(json.dumps(CATALOG, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    failures = []
    for label, im in made:
        r = check(im)
        if r["semiAlpha"] or r["outOfPalette"] or r["edgePixels"] or r["coverage"] < 0.02:
            failures.append({"id": label, **r})
    print(json.dumps({
        "produced": len(made),
        "icons": len(made) - len(SCHOOLS),
        "iconsByGroup": {"skill": 8, "school": 4, "realm": 9, "equipment": 8,
                         "affix": 12, "legacy": 6},
        "accessories": len(SCHOOLS),
        "newThisRound": len(made) - round10_count,
        "pendingItems": sum(p["count"] for p in CATALOG["pending"]),
        "selfCheckFailures": failures,
        "contactSheets": ["assets/_preview/icons_contact_sheet.png",
                          "assets/_preview/icons_extended_contact_sheet.png",
                          "assets/_preview/icons_final_contact_sheet.png"],
        "catalog": "docs/icon-catalog.json",
        "credits": 0,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
