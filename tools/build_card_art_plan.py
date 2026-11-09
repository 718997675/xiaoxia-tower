#!/usr/bin/env python3
"""第 34/35 轮 · 72 卡「一卡一插画」映射表与 6 张拼版外发提示词生成器。

用户设计决策：每张卡一张独立插画，让三选一时三张卡画面不重样，突出选卡的重量感。
第 35 轮追加决策：**一张图里画 12 张卡**，72 / 12 = 6 次生成即可，节省 gpt-image2 额度，
由 `tools/split_card_art_sheets.py` 按固定坐标裁成 72 张单卡原稿。

本脚本不产图、不改冻结规格、不替换 assets/ui/cards/ 的 10 张卡面，只做：

  1. 从冻结卡库 docs/卡牌库.csv + docs/buff-card-library.json 读出 72 张卡；
  2. 给每张卡绑定一个**由效果文案派生**的唯一视觉母题 / 剪影 / 构图 / 主色段；
  3. 按 6 个类别分组（每类恰好 12 张），每组一张 1536×1024 拼版 sheet，3 列 × 4 行；
  4. 产出 docs/card-art-plan.json（含 sheetSpec / 格位 / 裁切框 + 唯一性统计 + 边界）；
  5. 产出 previews/card-art-prompts-pack.md（6 组中文 + 6 组英文，可整段复制）；
  6. 产出 previews/card-art-plan-overview.html（72 行人工核对页）。

用法：
    python3 tools/build_card_art_plan.py            # 重建三个产物
    python3 tools/build_card_art_plan.py --check   # 只复算，不改文件；供 final_selfcheck 调用

纪律：所有产物 status 均为「待外发 / 候选 / 不得直接入库」；Q17 未拍板、GUI F5 未跑。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html as html_lib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs"
PREV = ROOT / "previews"
PLAN_PATH = DOC / "card-art-plan.json"
PACK_PATH = PREV / "card-art-prompts-pack.md"
OVERVIEW_PATH = PREV / "card-art-plan-overview.html"
CSV_PATH = DOC / "卡牌库.csv"
LIB_PATH = DOC / "buff-card-library.json"
SHEET_DIR = PREV / "card_art_sheets"        # 6 张拼版回稿（用户外发产物）
ART_DIR = PREV / "card_art"                  # 72 张裁剪出的单卡原稿
TRANSCRIPT_DIR = ROOT / "assets" / "ui" / "card_art"  # 转录产物（24 色吸附后）

# ---- 第 35 轮拼版规格：一张 sheet 12 格，6 张 sheet 覆盖 72 卡 ----
# 1536×1024 是 gpt-image2 常用横版尺寸；3 列 × 4 行等分，每格 512×256。
# 每格再中心裁 384×256（3:2），与 docs/12 插画区 84×56 同比例，左右各弃 64px 安全边。
SHEET_W, SHEET_H = 1536, 1024
SHEET_COLS, SHEET_ROWS = 3, 4
CELL_W, CELL_H = SHEET_W // SHEET_COLS, SHEET_H // SHEET_ROWS   # 512 × 256
CROP_W, CROP_H = 384, 256
CROP_PAD_X = (CELL_W - CROP_W) // 2                              # 64
SHEET_COUNT = 6
CELLS_PER_SHEET = SHEET_COLS * SHEET_ROWS                        # 12
CAT_ORDER = ("dmg", "attr", "mech", "res", "surv", "syn")

PAL_INK = ["#12161F", "#2A3140", "#4A5568"]
PAL_PAPER = ["#8A8268", "#C9BFA3", "#E8DFC8"]
PAL_JADE = ["#2F6E6A", "#5FA8A0", "#9BD4CC"]
PAL_CINNABAR = ["#7A2420", "#C8453B", "#E8806F"]
PAL_GOLD = ["#8A6520", "#D9A441", "#F2D089"]
PAL_VIOLET = ["#4A3A6B", "#8A6FC4", "#C0A8E0"]
PALETTE = (PAL_INK + PAL_PAPER + PAL_JADE + PAL_CINNABAR
           + PAL_GOLD + PAL_VIOLET + ["#000000", "#FFFFFF"])

BANDS = {
    "ink": ("墨", "ink", PAL_INK),
    "paper": ("宣纸", "rice-paper", PAL_PAPER),
    "jade": ("青玉", "jade", PAL_JADE),
    "cinnabar": ("朱砂", "cinnabar", PAL_CINNABAR),
    "gold": ("金", "gold", PAL_GOLD),
    "violet": ("紫", "violet", PAL_VIOLET),
}

COMPOSITIONS = {
    "diagonal": "斜向对角线", "symmetry": "左右对称", "vertical": "纵向立柱",
    "radial": "中心放射", "grid": "方阵网格", "arc": "同心弧带",
    "split": "中缝对分", "fan": "扇形展开", "pierce": "水平贯穿",
    "ring": "闭合环", "chain": "链式串接", "point": "单点收束",
    "circle": "正圆居中", "branch": "分岔生长", "swing": "垂摆弧线",
    "stack": "层叠堆积", "target": "靶心聚焦", "still": "静物正面",
    "lift": "上扬抬升", "forge": "砧上锻打", "peel": "逐层剥离",
    "reverse": "双向倒转", "swap": "换位交错", "dual": "双体并列",
    "motion": "移动残影", "sequence": "序号轨道", "seal": "封印留空",
    "expand": "向外撑开", "banner": "令旗垂挂", "scroll": "卷轴展读",
    "merge": "双流归一", "clamp": "边界钳制", "funnel": "漏斗收窄",
    "gauge": "刻度容器", "wisp": "细缕上升", "wave": "浪头翻卷",
    "dots": "散点计数", "vessel": "空器留白", "curl": "反卷回旋",
    "fall": "自上坠落", "burst": "一次引爆", "sprout": "新芽舒展",
    "window": "窗口框定", "step": "阶梯折线", "puppet": "替身立像",
    "armor": "包壳剖面", "threshold": "阈值门线", "stealth": "淡入轮廓",
    "rebirth": "灰烬重生", "drop": "单滴下坠", "vortex": "罩内气旋",
    "sacrifice": "缺角割舍", "notch": "刻度降档", "chance": "概率亮点",
    "radius": "近身圈定", "reveal": "第四张浮出", "slots": "槽位增减",
    "twin": "一刀两刃", "insert": "插入第五槽", "oath": "朱印誓约",
    "abstain": "空手退让", "outlier": "异色离群", "amplify": "断流放大",
}

CATEGORY_LABEL = {
    "dmg": "技能伤害", "attr": "属性提升", "mech": "机制改变",
    "res": "资源灵力", "surv": "生存回复", "syn": "构筑风险",
}
RARITY_LABEL = {
    "common": "凡品", "rare": "灵品", "legend": "仙品", "curse": "劫品",
}

# 风格锚点：用户明确「之前按提示词生成的卡片图鉴最符合审美，就以那个为基础」。
# 因此 07-codex original 是**第一基准**，不是三张并列参考之一；其余三张为辅助。
STYLE_ANCHORS = [
    "previews/ui/07-codex-gpt-image2_original.png",     # 第一基准：用户审美原稿
    "previews/ui/07-codex-gpt-image2_palette24.png",    # 同稿 24 色吸附版
    "previews/ui/00-anchor-gpt-image2_palette24.png",   # 辅助：色板 / 笔触
    "previews/ui/08-icons-gpt-image2_palette24.png",    # 辅助：纹样密度 / 1px 硬描边
]

# 从 07-codex 原稿逐格提取的 16 个「画法样板」。
# 只取画法（底 / 环 / 星点 / 剪影 / 光效），绝不沿用示意稿里的假卡名与假数值。
CODEX_SAMPLES = {
    "r1c1": ("第 1 行第 1 张", "清风诀", "青白螺旋气旋居中，四周散布菱形小星点，深墨蓝底，细放射线", "a centered cyan-white spiral vortex with small diamond star points around it on deep ink-blue ground"),
    "r1c2": ("第 1 行第 2 张", "金光术", "金色八角星芒居中，硬边细放射线向外，暗棕底，四角星点", "a centered gold eight-point starburst with hard-edged thin rays on dark brown ground"),
    "r1c3": ("第 1 行第 3 张", "回春术", "青绿双叶新芽居中，四周菱形星点，深墨绿底，柔和但不模糊的圆形背光", "a centered jade two-leaf sprout with diamond star points on deep ink-green ground"),
    "r1c4": ("第 1 行第 4 张", "御剑术", "斜置飞剑居中，青蓝斜向速度线，深墨蓝底，剑身高对比硬边", "a centered diagonal flying sword with cyan diagonal speed lines on deep ink-blue ground"),
    "r2c1": ("第 2 行第 1 张", "聚灵阵", "青玉双层圆环法阵居中，环上八个光点，中心阴阳，深墨青底", "a centered jade double-ring array with eight light nodes and a yin-yang core on deep ink-teal ground"),
    "r2c2": ("第 2 行第 2 张", "炼丹术", "青玉丹瓶居中，上浮气泡光点，深墨青底，瓶口一圈亮边", "a centered jade pill flask with rising bubble glints on deep ink-teal ground"),
    "r2c3": ("第 2 行第 3 张", "化气诀", "青玉打坐人形剪影居中，背后圆形背光与两侧气旋，深墨绿底", "a centered jade seated human silhouette with a round backlight on deep ink-green ground"),
    "r2c4": ("第 2 行第 4 张", "风行术", "奔跑人形剪影居中，横向青蓝速度线，深墨蓝底，四肢硬边", "a centered running human silhouette with horizontal cyan speed lines on deep ink-blue ground"),
    "r3c1": ("第 3 行第 1 张", "天雷诀", "紫色分岔雷电居中，放射碎光，深紫黑底，雷枝折线硬边", "a centered violet forked lightning with hard-edged radial shards on deep violet-black ground"),
    "r3c2": ("第 3 行第 2 张", "玄冰诀", "青蓝冰晶簇居中，冷光碎点，深蓝底，晶体棱面分明", "a centered cyan ice crystal cluster with cold glints on deep blue ground"),
    "r3c3": ("第 3 行第 3 张", "星晨变", "金色行星环居中，中心亮星，四周菱形星点，深棕金底", "a centered gold ringed planet with a bright core star and diamond star points on dark brown-gold ground"),
    "r3c4": ("第 3 行第 4 张", "太虚咒", "紫色同心螺旋法阵居中，多层环带，深紫底，环带硬边", "a centered violet concentric spiral array with layered ring bands on deep violet ground"),
    "r4c1": ("第 4 行第 1 张", "万劫灭", "朱红火焰包裹人形剪影居中，朱砂暗底，火舌硬边分叉", "a cinnabar flame wrapping a centered human silhouette on dark cinnabar ground"),
    "r4c2": ("第 4 行第 2 张", "天罚劫", "朱红环形剑气居中，一道斜剑穿过，朱砂暗底，环带断口", "a cinnabar ring of sword-qi crossed by one diagonal blade on dark cinnabar ground"),
    "r4c3": ("第 4 行第 3 张", "混沌诀", "紫金阴阳旋涡居中，四周菱形星点，朱砂暗底", "a violet-gold yin-yang vortex with diamond star points on dark cinnabar ground"),
    "r4c4": ("第 4 行第 4 张", "无尽劫", "朱红拱形火门居中，门内人形剪影，朱砂暗底", "a cinnabar arched flame gate with a human silhouette inside on dark cinnabar ground"),
}

# 72 张卡各绑定一个 07-codex 画法样板：按母题形态就近匹配，16 个样板全部会被用到。
CODEX_REF = {
    # dmg 技能伤害
    "card_jianfeng": "r1c4", "card_poyun": "r1c2", "card_leizhuan": "r3c1",
    "card_danbao": "r4c1", "card_fuzhen": "r3c4", "card_quanfeng": "r1c1",
    "card_huiling": "r1c3", "card_jingang": "r1c2", "card_jianyi": "r1c4",
    "card_wuxing": "r2c1", "card_lianhuan": "r3c4", "card_zhanxing": "r3c3",
    # attr 属性提升
    "card_cuijing": "r3c2", "card_ningdan": "r2c2", "card_lingmai": "r1c1",
    "card_buyao": "r2c2", "card_tiepi": "r3c2", "card_huixin": "r1c2",
    "card_poyu": "r1c4", "card_shouyuan": "r2c2", "card_qingling": "r1c3",
    "card_juxi": "r2c1", "card_zhongzhu": "r1c2", "card_jingpo": "r3c4",
    # mech 机制改变
    "card_nianzhuan": "r1c1", "card_huanshi": "r3c4", "card_shuangxiu": "r4c3",
    "card_yuqi": "r2c4", "card_daoyin": "r3c4", "card_jieyin": "r4c2",
    "card_wuxiangpo": "r1c2", "card_chongzhu": "r1c2", "card_tianren": "r3c3",
    "card_sheli": "r2c1", "card_lunhui": "r1c1", "card_pojing": "r4c2",
    # res 资源灵力
    "card_juling": "r2c1", "card_shengxi": "r2c2", "card_huanling": "r2c2",
    "card_danxiang": "r1c3", "card_lingchao": "r1c1", "card_jieqi": "r3c3",
    "card_kongzhan": "r2c2", "card_fanyong": "r2c1", "card_zhulian": "r3c4",
    "card_wugen": "r1c3", "card_tianlu": "r3c3", "card_shouyin": "r4c3",
    # surv 生存回复
    "card_huichun": "r1c3", "card_huti": "r3c2", "card_bishui": "r2c4",
    "card_duanxu": "r1c1", "card_jiaren": "r2c3", "card_tiegu": "r3c2",
    "card_guisuo": "r4c4", "card_yinbi": "r2c3", "card_zhuansheng": "r4c1",
    "card_qinglu": "r2c2", "card_hunyuan": "r2c1", "card_sheshi": "r4c4",
    # syn 构筑风险
    "card_jianxin": "r3c3", "card_fuhun": "r3c3", "card_danxin": "r4c1",
    "card_tipo": "r2c4", "card_tongyuan": "r1c2", "card_jiezeng": "r4c2",
    "card_shuangren": "r4c2", "card_duozhu": "r3c4", "card_zhongshi": "r4c4",
    "card_shouzhuo": "r2c3", "card_yiyu": "r4c3", "card_wuxin": "r3c4",
}

COMMON_ZH = """东方修真题材 2D 像素游戏「卡牌插画拼版」，单张 1536×1024 不透明 PNG 横版。整图严格分成 3 列 × 4 行 = 12 个等大横格，每格 512×256 像素；格位按「从上到下、每行从左到右」编号 01–12（01=第1行第1格，04=第2行第1格，12=第4行第3格）。整图不留白边、不加外框。

【每格 = 一张独立完整插画】每格只画一个明确的视觉母题，主体居中占该格 45–60%，四周留 35% 以上的空墨底（大量留白）；主体、光效、星点一律不得越出本格边界。相邻格之间不要画格线、分隔线、格子边框、格号或任何标记 —— 后续按固定像素坐标硬裁，画线反而会被裁进画面。格号只是下方清单的顺序编号，禁止把任何数字或编号画进图里。
12 格共用同一套画法、同一墨底、同样像素密度与描边粗细，但 12 个母题、12 个主体剪影两两不同；下方【12 格逐格清单】给出每格唯一的母题、剪影、构图、主色段与画法样板，严格一一对应，不要自行调换顺序或合并母题。

【风格第一基准 · 必须照此画】把 previews/ui/07-codex-gpt-image2_original.png 附作参考图。这是用户已确认「最符合审美」的 gpt-image2 卡牌图鉴回稿。本拼版只复刻其中**卡片插画区**的画法：深墨小横窗里放一个干净的主体，四周大面积留白，安静克制。以下以该原稿的实际画面为准，不要用更华丽的方式去「优化」它：
· 底：实色墨底 #12161F（深墨蓝），不是纯黑 #000000，不是亮底，不要渐变。
· 构图：每格只画一个主体且居中，占该格 45–60%，四周留 35% 以上空墨底。原稿 16 张插画绝大多数是「一个简洁符号直接放在墨底上」，无环、无背光、细线、少装饰。
· 【最重要 · 做减法】原稿 16 张里只有「聚灵阵」「太虚咒」等 2–3 张是圆环 / 法阵构图，其余都是无环的。因此除非该格清单的母题本身就是环、阵、太极、旋涡或连锁，否则**不要**画圆形或双层圆环法阵把主体包住，不要给每格加圆形背光或环上光点，不要画成对称满版的徽章。
· 星点：每格最多 2–4 枚很小的四角星，零星点缀在主体旁；不要四角铺满 4–8 枚菱形星点。
· 线条：细线、少装饰。放射线 / 速度线只在该格母题是「爆发 / 冲击 / 飞行 / 雷击」时用 3–5 道，不要每格都铺。
· 主体：单一高对比剪影或具象符号，棱面分明、实色平涂、1px 纯黑硬描边；用亮阶做硬边高光，靠色阶对比制造「亮」，不用渐变 / 发光滤镜。
· 整体气质：安静、克制、有重量感，不要华丽。禁止叠加多层装饰环、多重描边、满版光点。
整稿像素颗粒锐利、无抗锯齿；禁止渐变、半透明叠色、雾气、柔和投影、模糊光晕、圆角卡片、3D、写实与照片质感。

【参考图使用边界 · 严禁照抄示意卡主体】参考图只提供：墨底色、留白比例、星点大小与数量、线条密度、1px 硬描边与色阶节奏。参考图里 16 张示意卡画的具体东西——螺旋气旋、八角星芒、双叶新芽、斜飞剑、丹瓶、打坐人形、奔跑人形、分岔雷电、冰晶簇、带环行星、紫色螺旋、火焰人形、双层圆环法阵、阴阳旋涡、拱形火门——**一律不是本拼版任何一格的母题，禁止照抄或改色复用**。每格画什么，只由下方【12 格逐格清单】决定；清单优先级高于参考图与上方所有风格说明。

画面内禁止出现任何文字、数字、字母、卡名、卡框、边框、角标、稀有度点、水印、Logo 与 UI 控件；只画 12 个插画母题本身。整卡外框与右上数字角标不要画，卡框与稀有度边框由游戏另一层绘制。示意稿里的假卡名与假数值（清风诀 / 获得 15 点灵气 / 24 / 72 之类）一律不要照抄。少量星点按上面【做减法】规则可画；圆环只在母题本身是环 / 阵时才画。
配色严格限定 24 色锁定板：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF；不得使用板外颜色。
底色用墨段三阶；每格主体用该格清单指定的【主色段】三阶并以亮阶作硬边高光，点缀不超过 2 个其它色段。
辅助参考（只取色板 / 笔触 / 纹样密度）：previews/ui/00-anchor-gpt-image2_palette24.png、previews/ui/08-icons-gpt-image2_palette24.png；24 色吸附版为 previews/ui/07-codex-gpt-image2_palette24.png。"""

COMMON_EN = """A 12-cell contact sheet of card illustrations for a 2D eastern-xianxia pixel game. One opaque 1536x1024 landscape PNG. Divide the whole canvas into EXACTLY 3 columns x 4 rows = 12 equal horizontal cells of 512x256 px each. Cell order is top-to-bottom, and within each row left-to-right: 01 = row1/col1, 04 = row2/col1, 12 = row4/col3. No outer margin, no outer frame.

EACH CELL IS ONE COMPLETE, SELF-CONTAINED CARD ILLUSTRATION. Exactly ONE clear visual motif per cell, centered, filling only 45-60% of that cell, leaving 35%+ empty ink ground inside the cell (generous negative space). Subject, highlights and sparse star points must NOT cross the cell boundary. Do NOT draw grid lines, separators, cell borders, cell numbers or any marker between cells - the sheet is cropped later at fixed pixel coordinates, so drawn lines would end up inside the art. Cell numbers below are only list ordering; never draw any digit or label into the image.
All 12 cells share the same painting method, ink ground, pixel density and outline weight, yet all 12 motifs and all 12 main silhouettes must be distinct. The 12-cell list below gives each cell its unique motif, silhouette, composition, focal band and style sample - match them one-to-one; do not reorder or merge motifs.

PRIMARY STYLE REFERENCE - attach previews/ui/07-codex-gpt-image2_original.png as the reference image. It is the gpt-image2 codex sheet the user explicitly approved as the visual target. Reproduce ONLY the art-window painting: one clean subject on dark ink with generous empty space, quiet and restrained. Follow the actual reference, do not make it more ornate:
- Ground: solid ink #12161F (deep ink-blue), NOT pure black #000000, not a light ground, no gradient.
- Composition: ONE centered subject per cell, occupying only 45-60% of the cell, with 35%+ empty ink around it. In the reference, most of the 16 cards are simply one clean emblem placed directly on the ink ground - no ring, no backlight, thin lines, sparse ornament.
- MOST IMPORTANT - SUBTRACT, DO NOT ADD: only 2-3 of the 16 reference cards (the yin-yang array and the spiral array) use a circular ring composition. All the others have NO ring. So unless the cell's own motif IS a ring / array / yin-yang / spiral / chain, DO NOT wrap the subject in a circular or double-ring array, DO NOT add a round backlight or nodes on a ring, and DO NOT build a symmetrical badge-like emblem.
- Star points: at most 2-4 very small four-point stars scattered near the subject; NEVER fill all four corners with 4-8 diamond stars.
- Lines: thin and sparse. Use 3-5 rays or speed lines ONLY when that cell's motif is a burst / impact / flight / lightning strike; never cover every cell with rays.
- Subject: one high-contrast silhouette or concrete emblem, crisp facets, flat color blocks, 1px solid black outline; bright-step hard-edged highlights, brightness from palette steps only, no gradients or glow filters.
- Overall mood: quiet, restrained, weighty, never ornate. No stacked decorative rings, no multiple outlines, no all-over light nodes.
Crisp visible pixels, no anti-aliasing, flat opaque blocks. No gradients, no translucency, no fog, no soft shadows, no blur glow, no rounded cards, no 3D, no photoreal texture.

REFERENCE USAGE BOUNDARY - DO NOT COPY THE SAMPLE CARD SUBJECTS. The reference supplies ONLY: ink ground color, negative-space ratio, star point size/count, line density, 1px hard outline and palette-step rhythm. The concrete things depicted in its 16 sample cards - spiral vortex, eight-point starburst, two-leaf sprout, flying sword, elixir flask, seated figure, running figure, forked lightning, ice crystal cluster, ringed planet, violet spiral, flame figure, double-ring array, yin-yang vortex, arched fire gate - are NOT the motif of any cell in this sheet. Never copy or recolor them. What each cell depicts is decided ONLY by the 12-CELL LIST below; that list overrides the reference image and every style note above.

ABSOLUTELY NO text, digits, letters, card names, frames, borders, corner pips, rarity dots, watermarks, logos or UI widgets anywhere on the sheet. A few small star points may be drawn under the SUBTRACT rule above, and a circular array ONLY when the motif itself is a ring/array; the outer card frame and the top-right number badge must NOT be drawn - another layer draws those. Do not copy the sample sheet's fake card names or fake numbers.
Strict 24-color locked palette only: ink #12161F #2A3140 #4A5568, paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF. No off-palette colors.
Ink-band ground. Each cell's main subject uses its own FOCAL BAND from the list with its bright step for hard-edged highlights; at most two other bands as accents.
Secondary references (palette / brush / glyph density only): previews/ui/00-anchor-gpt-image2_palette24.png, previews/ui/08-icons-gpt-image2_palette24.png; 24-color-snapped version: previews/ui/07-codex-gpt-image2_palette24.png."""

# (id, 唯一母题中文, 唯一母题英文, 主体剪影, 构图键, 主色段键)
# 母题全部从 docs/卡牌库.csv 的效果文案派生，不套用 07-codex 示意稿的假卡名。
MOTIFS: list[tuple[str, str, str, str, str, str]] = [
    # ---------------- 技能伤害 dmg 12 ----------------
    ("card_jianfeng", "磨石上淬出一道笔直火花的剑刃", "a blade quenched on a whetstone throwing one straight spark line", "斜置长剑与一道直线火花", "diagonal", "cinnabar"),
    ("card_poyun", "一柄剑裂成两道对称剑光且总光量守恒", "one sword splitting into two symmetric beams with conserved total light", "对称双剑与中间断开的剑柄", "symmetry", "cinnabar"),
    ("card_leizhuan", "两道雷柱落在重描过的符篆上", "two thunder columns landing on a redrawn talisman seal", "双雷柱与方形符篆", "vertical", "violet"),
    ("card_danbao", "丹炉爆燃后火舌回卷自噬炉身", "a pill furnace erupting with fire tongues curling back onto itself", "圆腹丹炉与回卷火舌", "radial", "cinnabar"),
    ("card_fuzhen", "符纸层层叠印成一座方阵", "talisman papers overprinted into a square formation", "四张错叠符纸组成的方阵", "grid", "gold"),
    ("card_quanfeng", "三段递进的拳风同心弧", "three ascending concentric arcs of a fist shockwave", "三道由小到大的同心弧", "arc", "cinnabar"),
    ("card_huiling", "一片叶子的左半化为刀刃", "a leaf whose left half turns into a blade", "半叶半刃的同体剪影", "split", "jade"),
    ("card_jingang", "金刚罩碎裂后向外释放扇形冲击", "a vajra barrier shattering into a fan-shaped shockwave", "破裂钟罩与扇形碎片", "fan", "gold"),
    ("card_jianyi", "一剑水平贯穿整列敌人剪影", "one sword piercing horizontally through a row of enemy silhouettes", "长直剑与三个被贯穿的剪影", "pierce", "cinnabar"),
    ("card_wuxing", "五行环破开一面铁壁盾", "a five-element ring cracking an iron-wall shield", "五段色环与裂开的方盾", "ring", "gold"),
    ("card_lianhuan", "三枚符环相扣成链且末端重接", "three talisman rings chained together with the end re-linking", "三环相扣的闭合符链", "chain", "violet"),
    ("card_zhanxing", "斜剑斩落一颗坠星", "a diagonal sword cutting down a falling star", "斜剑与带尾迹的坠星", "diagonal", "gold"),
    # ---------------- 属性提升 attr 12 ----------------
    ("card_cuijing", "一点精光在晶体内向内收束", "a single glint converging inward inside a crystal", "尖顶晶体与中心一点", "point", "jade"),
    ("card_ningdan", "一粒丹丸在掌心凝成实圆", "a pill pellet condensing into a solid circle above a palm", "正圆丹丸与托起的掌心", "circle", "jade"),
    ("card_lingmai", "灵脉河道由一分为三地拓宽", "a spirit-vein river widening from one channel into three", "分岔成三股的河道", "branch", "jade"),
    ("card_buyao", "步摇坠饰摆出的一道垂弧轨迹", "a hanging hairpin pendant tracing one swaying arc", "细链垂坠与弧形残影", "swing", "jade"),
    ("card_tiepi", "四片铁甲错位叠成硬边方块", "four iron plates offset-stacked into a hard-edged square", "四层错位叠甲方片", "stack", "ink"),
    ("card_huixin", "靶心正中一点被放大命中", "a bullseye center point enlarged on impact", "同心靶环与放大的中心点", "target", "gold"),
    ("card_poyu", "一道直线劈开封闭的边界方框", "one straight line splitting a closed boundary frame", "断开的方框与一道直线", "split", "jade"),
    ("card_shouyuan", "寿桃上多出一道减损刻痕", "a longevity peach marked with one subtractive notch", "桃形静物与斜刻痕", "still", "jade"),
    ("card_qingling", "一根羽毛逆风上扬", "a single feather lifting against the wind", "上扬羽片与三道风线", "lift", "jade"),
    ("card_juxi", "脱战后气息汇成一圈静环", "breath gathering into one still ring after combat", "闭合气息环与静止符号", "ring", "jade"),
    ("card_zhongzhu", "一件装备在砧上被重铸成方坯", "a piece of gear recast into a square billet on an anvil", "铁砧与方形坯料", "forge", "gold"),
    ("card_jingpo", "三枚魂魄层叠且最外层正在剥落", "three soul layers stacked with the outermost peeling away", "三层魂环与剥落的一角", "peel", "violet"),
    # ---------------- 机制改变 mech 12 ----------------
    ("card_nianzhuan", "击杀符号倒转成为命中符号", "a kill glyph reversing into an on-hit glyph", "首尾互指的双向箭头", "reverse", "violet"),
    ("card_huanshi", "两个技能槽之间的换位箭头", "two skill slots exchanging places along crossed arrows", "两格槽位与交叉换位箭头", "swap", "violet"),
    ("card_shuangxiu", "两道流派标签并在一枚主印上", "two school tags merging onto one dominant seal", "双印叠合且一印压前一印", "dual", "violet"),
    ("card_yuqi", "边移动边出招的三段残影", "three motion afterimages of casting while moving", "三级递进的人形残影", "motion", "violet"),
    ("card_daoyin", "技能顺序被重排的序号轨道", "a reordered sequence track of skill slots", "带序号刻度的弯曲轨道", "sequence", "violet"),
    ("card_jieyin", "一枚印章封住旧卡并腾出空位", "a seal stamping an old card away and leaving an empty slot", "朱印与空出的卡位", "seal", "violet"),
    ("card_wuxiangpo", "两张候选被撑开成三张", "two candidate cards being pushed apart into three", "二到三的展开扇形", "expand", "violet"),
    ("card_chongzhu", "令旗悬在免费一次的铁砧上", "a command banner hanging above a free-use anvil", "垂挂令旗与砧台", "banner", "violet"),
    ("card_tianren", "进层前显影敌人构成的卷轴", "a scroll revealing the enemy lineup before entering a floor", "展开卷轴与三枚敌人剪影", "scroll", "violet"),
    ("card_sheli", "舍利子复活一次后卡牌流断开", "a relic reviving once while the card stream is cut", "舍利圆珠与断开的卡流", "still", "gold"),
    ("card_lunhui", "两条灵韵候选汇成一条固化", "two legacy candidate streams merging into one fixed line", "双流归一的分岔合流", "merge", "violet"),
    ("card_pojing", "两枚道途目标同挂并被边界钳住", "two path goals hanging together inside a clamped boundary", "双目标牌与上下界横线", "clamp", "gold"),
    # ---------------- 资源灵力 res 12 ----------------
    ("card_juling", "击杀魂火汇入阵眼", "kill flames converging into an array eye", "八角阵眼与四缕魂火", "radial", "gold"),
    ("card_shengxi", "灵力漏斗被收窄一格", "a spirit funnel narrowed by one notch", "上宽下窄的收口漏斗", "funnel", "gold"),
    ("card_huanling", "刻度瓶按层回灌四分之一", "a graduated flask refilled by one quarter per floor", "带四格刻度的灵力瓶", "gauge", "gold"),
    ("card_danxiang", "一缕丹香替下半份灵耗", "one wisp of pill incense replacing half the spirit cost", "细长上升的香缕", "wisp", "jade"),
    ("card_lingchao", "满潮浪头托起一次不耗灵的出招", "a full-tide wave crest carrying one free cast", "翻卷浪头与托起的剑光", "wave", "gold"),
    ("card_jieqi", "受击瞬间截下四点灵光", "four spirit sparks intercepted at the moment of being hit", "四个等距光点与一道斜截线", "dots", "gold"),
    ("card_kongzhan", "空盏杯底最后一滴被放大", "the last drop in an empty cup enlarged", "空杯与杯底一滴", "vessel", "gold"),
    ("card_fanyong", "溢出的灵力反卷成一层护盾", "overflowing spirit curling back into a shield", "反卷液流与弧形盾面", "curl", "jade"),
    ("card_zhulian", "三珠连成一线后第六点回灵", "three beads in a line with a sixth returning spark", "三珠串线与末端一点", "chain", "gold"),
    ("card_wugen", "无根之木被削去两成灵力", "a rootless tree with one fifth of its spirit cut away", "断根树形与削去的缺口", "still", "cinnabar"),
    ("card_tianlu", "每层首杀落下六枚灵石", "six spirit stones dropping from the first kill of a floor", "六枚下坠方石", "fall", "gold"),
    ("card_shouyin", "三枚印叠满后一次引爆", "three seals stacking to a single detonation", "三枚叠印与一次放射", "burst", "gold"),
    # ---------------- 生存回复 surv 12 ----------------
    ("card_huichun", "回春光晕里舒展的新芽", "a new sprout unfolding inside a healing halo", "双叶新芽与环形光晕", "sprout", "jade"),
    ("card_huti", "护盾值格被填满三层", "three rows of shield gauge cells filling up", "三行方格盾槽", "grid", "jade"),
    ("card_bishui", "受击后拉长的无敌时间窗", "an invulnerability time window stretched after a hit", "被拉长的矩形时间窗", "window", "jade"),
    ("card_duanxu", "按层回血的断续阶梯折线", "a broken step line of per-floor healing", "三段断续上升折线", "step", "jade"),
    ("card_jiaren", "纸傀儡替身挡下一击", "a paper puppet taking a lethal hit in place", "方形纸傀儡与斜来的一击", "puppet", "jade"),
    ("card_tiegu", "骨节外包一层铁壳的剖面", "a bone joint wrapped in an iron shell, cross-section", "骨节与外层铁壳剖面", "armor", "ink"),
    ("card_guisuo", "低血线触发自动回春的阈值门", "a threshold gate below which healing auto-triggers", "横贯阈值线与一道门", "threshold", "jade"),
    ("card_yinbi", "静止一秒后淡入墨底的人形轮廓", "a human outline fading into the ink ground after one still second", "半隐人形轮廓", "stealth", "ink"),
    ("card_zhuansheng", "灰烬中重生并重置的 CD 环", "rebirth from ashes with a reset cooldown ring", "灰烬人形与闭合重置环", "rebirth", "gold"),
    ("card_qinglu", "叶尖一滴露水将坠未坠", "one dewdrop about to fall from a leaf tip", "叶尖与单滴露水", "drop", "jade"),
    ("card_hunyuan", "金刚罩内一层混元气旋", "a primal vortex inside a vajra barrier", "钟罩轮廓与内部气旋", "vortex", "jade"),
    ("card_sheshi", "命盘被削去一角换取 CD 收缩", "a life disc with one corner cut away to shorten cooldown", "缺角命盘与收缩环", "sacrifice", "cinnabar"),
    # ---------------- 构筑风险 syn 12 ----------------
    ("card_jianxin", "剑修质变刻度从四件降到三件", "a sword-ascension gauge dropping from four to three notches", "带一格被抹去的刻度尺", "notch", "cinnabar"),
    ("card_fuhun", "符纸 CD 环上 10% 的概率亮点", "a ten-percent chance glint on a talisman cooldown ring", "CD 环与一枚孤立亮点", "chance", "violet"),
    ("card_danxin", "灼伤印记叠三层而不刷新", "three burn marks stacking instead of refreshing", "三层错叠的灼印", "stack", "cinnabar"),
    ("card_tipo", "近身 32 像素圈内被放大的拳", "a fist enlarged inside a close-range radius circle", "半径圆圈与放大的拳形", "radius", "cinnabar"),
    ("card_tongyuan", "三槽装满时浮出第四张候选", "a fourth candidate surfacing when three slots are full", "三格满槽与浮出的第四格", "reveal", "cinnabar"),
    ("card_jiezeng", "天劫词缀由三格涨到四格", "tribulation slots growing from three to four", "四格词缀槽与新增一格", "slots", "cinnabar"),
    ("card_shuangren", "一刀两刃一侧伤人一侧伤己", "one blade with two edges, one outward and one inward", "双向开刃的对称刀", "twin", "cinnabar"),
    ("card_duozhu", "第五个技能槽插入待重算的空位", "a fifth skill slot inserted into an empty recompute space", "四槽之外插入的第五槽", "insert", "gold"),
    ("card_zhongshi", "禁用回春的朱印与道行倍率", "a cinnabar oath seal banning healing with a dao multiplier", "朱红誓印与倍率折线", "oath", "cinnabar"),
    ("card_shouzhuo", "空手退让三选一并逐层叠起减伤梯", "an empty hand declining the draft beside a rising defense stair", "空掌与四级上升阶梯", "abstain", "cinnabar"),
    ("card_yiyu", "三张候选中一枚异色离群卡", "one off-palette outlier card among three candidates", "两同色一异色的三卡组", "outlier", "violet"),
    ("card_wuxin", "卡牌流断开而已选卡整体放大一圈", "the card stream cut while chosen cards enlarge by one ring", "断开的卡流与放大外环", "amplify", "gold"),
]


def read_cards() -> list[dict]:
    rows = list(csv.reader(CSV_PATH.read_text(encoding="utf-8").splitlines()))
    header, body = rows[0], rows[1:]
    idx = {name: i for i, name in enumerate(header)}
    return [{
        "id": r[idx["id"]],
        "name": r[idx["名称"]],
        "category": r[idx["类别键"]],
        "rarity": r[idx["稀有度键"]],
        "effect": r[idx["效果文案"]],
        "stack": r[idx["堆叠上限"]],
    } for r in body]


def render_overview(plan: dict) -> str:
    """72 个母题的人工核对页：用户唯一需要肉眼判断的是「母题合不合意」。"""
    e = html_lib.escape
    css = """
:root{--ink:#12161F;--paper:#E8DFC8;--line:#C9BFA3;--gold:#8A6520;--jade:#2F6E6A;--red:#7A2420}
*{box-sizing:border-box}
body{margin:0;padding:28px 32px 48px;background:#F5F2EA;color:var(--ink);
 font:14px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
h1{font-size:24px;margin:0 0 6px}h2{font-size:17px;margin:30px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--line)}
.sub{color:#5A5A52;font-size:13px;margin-bottom:18px}
.banner{background:#FFF6DC;border-left:4px solid var(--gold);padding:10px 14px;margin:14px 0 20px;font-size:13px}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.stat{background:#fff;border:1px solid var(--line);border-radius:4px;padding:9px 14px;min-width:118px}
.stat b{display:block;font-size:20px;color:var(--gold)}.stat span{font-size:11px;color:#6A6A60}
#q{width:min(420px,100%);padding:9px 12px;border:1px solid var(--line);border-radius:4px;
 background:#fff;font-size:14px;outline:none}
#q:focus{border-color:var(--gold)}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);font-size:12.5px}
th{background:#EFE9D8;text-align:left;padding:8px 9px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:8px 9px;border-bottom:1px solid #EDE7D7;vertical-align:top}
tr:hover td{background:#FAF6EA}
.id{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11.5px;color:var(--jade)}
.motif{font-weight:600}.sil{color:#4A4A42}.eff{color:#77776E;font-size:11.5px}
.rar{display:inline-block;padding:1px 7px;border-radius:3px;font-size:11px;color:#fff;white-space:nowrap}
.rar.common{background:#4A5568}.rar.rare{background:#2F6E6A}.rar.legend{background:#8A6520}.rar.curse{background:#7A2420}
.sw{display:inline-block;width:11px;height:11px;border:1px solid #000;margin-right:2px;vertical-align:-1px}
.comp{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;color:#8A6FC4}
.out{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:10.5px;color:#8A8268}
.ex{font-size:11px;color:#9A9A90}
footer{margin-top:32px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:#6A6A60}
code{background:#EFE9D8;padding:1px 4px;border-radius:2px}
"""
    js = """
const q = document.getElementById('q');
q.addEventListener('input', () => {
  const s = q.value.trim().toLowerCase();
  document.querySelectorAll('tbody tr').forEach(tr => {
    tr.style.display = (!s || tr.dataset.search.toLowerCase().includes(s)) ? '' : 'none';
  });
  document.querySelectorAll('.group').forEach(g => {
    const vis = [...g.querySelectorAll('tbody tr')].some(tr => tr.style.display !== 'none');
    g.style.display = (!s || vis) ? '' : 'none';
  });
});
"""
    st = plan["stats"]
    head = [
        "<!doctype html>", '<html lang="zh-CN">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<title>72 卡独立插画 · 母题核对页</title>",
        "<style>", css, "</style>", "</head>", "<body>",
        "<h1>72 卡独立插画 · 一卡一母题核对页</h1>",
        '<div class="sub">第 34–35 轮 · 由 <code>tools/build_card_art_plan.py</code> 生成 · '
        '母题全部从 <code>docs/卡牌库.csv</code> 的效果文案派生 · '
        '<b>第一风格基准 = <code>previews/ui/07-codex-gpt-image2_original.png</code></b>（用户已确认审美的图鉴回稿）</div>',
        '<div class="banner"><b>状态：PROPOSAL / 待外发 / 未回稿 / 候选规格；不得直接入库。</b>'
        ' Q17 未拍板、GUI F5 未跑。<b>一共只需 6 次生成</b>：6 张 1536×1024 拼版，每张 3 列 × 4 行 = 12 格，'
        ' 按固定坐标裁成 72 张单卡原稿（<code>tools/split_card_art_sheets.py</code>），无需你手动切图。'
        ' 出图用 <code>previews/card-art-prompts-pack.md</code>，边界见 <code>docs/27</code>。</div>',
        '<div class="stats">',
        f'<div class="stat"><b>{st["total"]}</b><span>张卡全覆盖</span></div>',
        f'<div class="stat"><b>{st["uniqueMotifs"]}</b><span>个唯一母题</span></div>',
        f'<div class="stat"><b>{st["uniqueSignatures"]}</b><span>个唯一签名</span></div>',
        '<div class="stat"><b>6 × 12</b><span>张拼版 sheet / 类内剪影互异</span></div>',
        f'<div class="stat"><b>{st["generations"]}</b><span>次 gpt-image2 生成</span></div>',
        f'<div class="stat"><b>{st["codexSampleCoverage"]}/16</b><span>图鉴画法样板覆盖</span></div>',
        f'<div class="stat"><b>{st["sheetsReceived"]}/6</b><span>张拼版回稿（如实）</span></div>',
        f'<div class="stat"><b>{st["artReceived"]}</b><span>张单卡原稿（裁出）</span></div>',
        "</div>",
        '<input id="q" type="search" placeholder="搜卡 ID / 卡名 / 母题 / 效果，例如 破云式、card_poyun、雷">',
    ]
    cat_titles = {
        "dmg": "① 技能伤害", "attr": "② 属性提升", "mech": "③ 机制改变",
        "res": "④ 资源灵力", "surv": "⑤ 生存回复", "syn": "⑥ 构筑风险",
    }
    body: list[str] = []
    n = 0
    for si, cat in enumerate(CAT_ORDER, 1):
        group = [c for c in plan["cards"] if c["category"] == cat]
        body += [
            f'<div class="group"><h2>{cat_titles[cat]} · {len(group)} 张 · '
            f'第 {si} 次生成 <code>sheet-{si:02d}.png</code></h2>',
            "<table><thead><tr>",
            "<th>#</th><th>卡 ID</th><th>卡名 / 稀有度</th><th>卡面效果</th>",
            "<th>唯一母题</th><th>主体剪影</th><th>构图</th><th>主色段</th>",
            "<th>拼版格位 / 裁切框</th>"
            "<th>07-codex 画法样板（第一基准）</th><th>排除项（不得画成）</th><th>输出命名</th>",
            "</tr></thead><tbody>",
        ]
        for c in group:
            n += 1
            sw = "".join(f'<i class="sw" style="background:{col}"></i>'
                         for col in BANDS[c["focalBand"]][2])
            search = " ".join((c["id"], c["name"], c["motif"], c["motifEn"],
                               c["effect"], c["silhouette"], c["composition"]))
            ex = " / ".join(x["motif"] for x in c["excludes"])
            body.append(
                f'<tr data-search="{e(search, quote=True)}">'
                f'<td>{n:02d}</td><td class="id">{e(c["id"])}</td>'
                f'<td><b>{e(c["name"])}</b><br><span class="rar {c["rarity"]}">{e(c["rarityName"])}</span></td>'
                f'<td class="eff">{e(c["effect"])}</td>'
                f'<td class="motif">{e(c["motif"])}<br><span class="ex">{e(c["motifEn"])}</span></td>'
                f'<td class="sil">{e(c["silhouette"])}</td>'
                f'<td class="comp">{e(c["composition"])}<br><span class="ex">{e(COMPOSITIONS[c["composition"]])}</span></td>'
                f'<td>{sw}<br><span class="ex">{e(BANDS[c["focalBand"]][0])}</span></td>'
                f'<td class="out"><b>sheet-{c["sheetIndex"]:02d}.png</b><br>'
                f'格 {c["cell"]:02d} · {e(c["cellLabel"])}（行{c["cellRow"]} 列{c["cellCol"]}）<br>'
                f'<span class="ex">裁 {c["cropBox"][0]},{c["cropBox"][1]} → '
                f'{c["cropBox"][2]},{c["cropBox"][3]}</span></td>'
                f'<td class="ex"><b>{e(c["codexRef"])}</b> {e(c["codexRefPos"])}「{e(c["codexRefSample"])}」<br>'
                f'{e(c["codexRefTechnique"])}</td>'
                f'<td class="ex">{e(ex)}</td>'
                f'<td class="out">{e(c["outputName"])}</td></tr>')
        body += ["</tbody></table></div>"]
    tail = [
        "<footer>唯一性契约：72 个 <code>signature = 母题|剪影|构图|主色段</code> 两两不同 ⇒ 任取 3 张候选签名必互异，"
        "三选一同屏不撞脸。稀有度仍由 4 张卡框 + 边框层次表达，插画不因稀有度变华丽。"
        "风格基准：<b>07-codex original 为第一基准</b>，16 张示意卡的画法（深墨底 / 圆环法阵 / 四角星点 / 硬边高光 / 1px 黑描边）"
        "被 72 张卡各沿用其一且 16/16 全覆盖；00-anchor 与 08-icons 仅作辅助，示意稿假卡名与假数值不沿用。"
        "第 35 轮出图方式：<b>6 张拼版 sheet（每张 12 格，1536×1024，格 512×256，中心裁 384×256）</b>，"
        "6 次生成覆盖 72 卡，节省 gpt-image2 额度；12 格共画法不共母题、不画格线 / 编号、元素不得跨格（R58），"
        "裁剪按固定像素坐标而非视觉检测。插画区 84×56 为 PROPOSAL，待 4× 实机复核；"
        "docs/12 冻结口径与 10 张卡面本轮未改。</footer>",
        "<script>", js, "</script>", "</body></html>", "",
    ]
    return "\n".join(head + body + tail)


def build() -> tuple[str, str, str]:
    cards = read_cards()
    lib = json.loads(LIB_PATH.read_text(encoding="utf-8"))
    motif_map = {m[0]: m for m in MOTIFS}

    csv_ids = [c["id"] for c in cards]
    motif_ids = [m[0] for m in MOTIFS]
    if len(csv_ids) != 72 or len(set(csv_ids)) != 72:
        raise RuntimeError("冻结卡库不是 72 张唯一卡")
    if csv_ids != motif_ids:
        missing = sorted(set(csv_ids) - set(motif_ids))
        extra = sorted(set(motif_ids) - set(csv_ids))
        raise RuntimeError(f"母题表与卡库 ID/顺序不一致：缺 {missing} / 多 {extra}")
    if len(set(motif_ids)) != 72:
        raise RuntimeError("母题表 ID 重复")

    entries: list[dict] = []
    for c in cards:
        _, motif_zh, motif_en, silhouette, composition, band = motif_map[c["id"]]
        if composition not in COMPOSITIONS:
            raise RuntimeError(f"未知构图键：{composition}")
        if band not in BANDS:
            raise RuntimeError(f"未知色段键：{band}")
        if c["category"] not in CATEGORY_LABEL or c["rarity"] not in RARITY_LABEL:
            raise RuntimeError(f"未知类别/稀有度：{c['id']}")
        ref_key = CODEX_REF.get(c["id"])
        if ref_key not in CODEX_SAMPLES:
            raise RuntimeError(f"缺 07-codex 画法样板映射：{c['id']}")
        ref_pos, ref_card, ref_zh, ref_en = CODEX_SAMPLES[ref_key]
        entries.append({
            "id": c["id"], "name": c["name"],
            "category": c["category"], "categoryName": CATEGORY_LABEL[c["category"]],
            "rarity": c["rarity"], "rarityName": RARITY_LABEL[c["rarity"]],
            "effect": c["effect"],
            "motif": motif_zh, "motifEn": motif_en,
            "silhouette": silhouette, "composition": composition,
            "focalBand": band,
            "signature": f"{motif_zh}|{silhouette}|{composition}|{band}",
            "codexRef": ref_key, "codexRefPos": ref_pos,
            "codexRefSample": ref_card,
            "codexRefTechnique": ref_zh, "codexRefTechniqueEn": ref_en,
            "promptId": c["id"],
            "outputName": f"{c['id']}-cardart-original.png",
            "status": "待外发 · 未回稿 · 候选资产；不得直接入库",
        })

    # 排除项：同类上一张 / 下一张的母题，用来在提示词里显式压制「同类别长一个样」。
    by_cat: dict[str, list[dict]] = {}
    for e in entries:
        by_cat.setdefault(e["category"], []).append(e)
    for group in by_cat.values():
        n = len(group)
        for i, e in enumerate(group):
            e["excludes"] = [
                {"id": group[(i - 1) % n]["id"], "motif": group[(i - 1) % n]["motif"],
                 "motifEn": group[(i - 1) % n]["motifEn"]},
                {"id": group[(i + 1) % n]["id"], "motif": group[(i + 1) % n]["motif"],
                 "motifEn": group[(i + 1) % n]["motifEn"]},
            ]

    # ---- 第 35 轮：6 个类别 = 6 张拼版 sheet，每类 12 格，按行优先排布 ----
    sheet_titles = {
        "dmg": "技能伤害（朱砂主调）", "attr": "属性提升（青玉主调）",
        "mech": "机制改变（紫主调）", "res": "资源灵力（金主调）",
        "surv": "生存回复（青玉/淡青主调）", "syn": "构筑风险（朱砂暗主调）",
    }
    sheets: list[dict] = []
    for si, cat in enumerate(CAT_ORDER, 1):
        group = by_cat[cat]
        if len(group) != CELLS_PER_SHEET:
            raise RuntimeError(f"sheet {si} 的 {cat} 不是 12 张：{len(group)}")
        cells: list[dict] = []
        for ci, card in enumerate(group):
            row, col = divmod(ci, SHEET_COLS)
            x0, y0 = col * CELL_W, row * CELL_H
            cell_box = [x0, y0, x0 + CELL_W, y0 + CELL_H]
            crop_box = [x0 + CROP_PAD_X, y0, x0 + CROP_PAD_X + CROP_W, y0 + CROP_H]
            label = f"r{row + 1}c{col + 1}"
            card.update({
                "sheetIndex": si,
                "sheetFile": f"sheet-{si:02d}.png",
                "cell": ci + 1,
                "cellLabel": label,
                "cellRow": row + 1, "cellCol": col + 1,
                "cellBox": cell_box, "cropBox": crop_box,
            })
            cells.append({
                "cell": ci + 1, "label": label, "row": row + 1, "col": col + 1,
                "cardId": card["id"], "cardName": card["name"],
                "cellBox": cell_box, "cropBox": crop_box,
                "outputName": card["outputName"],
            })
        sheets.append({
            "index": si, "file": f"sheet-{si:02d}.png",
            "category": cat, "title": sheet_titles[cat],
            "cellCount": len(cells), "cells": cells,
        })
    if sum(s["cellCount"] for s in sheets) != 72:
        raise RuntimeError("6 张 sheet 的格位合计不是 72")
    cell_keys = [(c["sheetIndex"], c["cellLabel"]) for c in entries]
    if len(set(cell_keys)) != 72:
        raise RuntimeError("sheet 格位出现重复或漏格")

    # ---- 唯一性硬断言（这就是「不能有重复感」的机器可复算落点） ----
    def dup(key: str) -> list[str]:
        vals = [e[key] for e in entries]
        return sorted({v for v in vals if vals.count(v) > 1})

    for key in ("motif", "motifEn", "signature", "silhouette", "outputName"):
        d = dup(key)
        if d:
            raise RuntimeError(f"{key} 出现重复，违反一卡一母题：{d[:5]}")
    for cat, group in by_cat.items():
        if len(group) != 12:
            raise RuntimeError(f"{cat} 不是 12 张：{len(group)}")
        sigs = [g["silhouette"] for g in group]
        if len(set(sigs)) != 12:
            raise RuntimeError(f"{cat} 类内剪影重复，三选一会同屏撞脸")

    covered_refs = {e["codexRef"] for e in entries}
    if covered_refs != set(CODEX_SAMPLES):
        raise RuntimeError(
            f"07-codex 16 个画法样板未被全部用作基础：缺 {sorted(set(CODEX_SAMPLES) - covered_refs)}")
    if STYLE_ANCHORS[0] != "previews/ui/07-codex-gpt-image2_original.png":
        raise RuntimeError("07-codex 原稿不是第一风格基准")

    received = []
    if ART_DIR.is_dir():
        received = sorted(p.name for p in ART_DIR.glob("*-cardart-original.png"))
    unknown = [n for n in received if n not in {e["outputName"] for e in entries}]
    if unknown:
        raise RuntimeError(f"裁剪输出目录出现未登记命名：{unknown}")
    sheet_received = []
    if SHEET_DIR.is_dir():
        sheet_received = sorted(p.name for p in SHEET_DIR.glob("sheet-*.png"))
    unknown_sheets = [n for n in sheet_received
                      if n not in {s["file"] for s in sheets}]
    if unknown_sheets:
        raise RuntimeError(f"拼版回稿目录出现未登记命名：{unknown_sheets}")

    src_hash = hashlib.sha256(
        CSV_PATH.read_bytes() + b"\n" + LIB_PATH.read_bytes()).hexdigest()[:16]

    plan = {
        "version": 2,
        "generatedBy": "tools/build_card_art_plan.py",
        "round": "34–35",
        "status": "PROPOSAL · 第 34 轮「一卡一插画」+ 第 35 轮「6 张拼版 sheet（每张 12 格）出图」；待 Q17 拍板与 GUI F5 目检；不得直接入库",
        "designPrinciple": "OMPC / 一卡一母题：72 个由效果文案派生的母题两两不同，任取 3 张候选签名必互异，从规格上消除三选一同屏重复感",
        "generationPrinciple": "用户第 35 轮决策：一张图里画 12 张卡，72 / 12 = 6 次生成（6 张 1536×1024 拼版 sheet），节省 gpt-image2 额度；由 tools/split_card_art_sheets.py 按固定坐标裁成 72 张单卡原稿，画面效果不变",
        "sourceOfTruth": {
            "cards": "docs/卡牌库.csv", "library": "docs/buff-card-library.json",
            "uiSpec": "docs/12-卡牌UI规格.md", "sourceHash": src_hash,
        },
        "primaryStyleReference": {
            "file": "previews/ui/07-codex-gpt-image2_original.png",
            "reason": "用户第 34 轮追加指令「之前按提示词生成的卡片图鉴那个就很符合我的审美，就按照那个为基础」；第 36 轮重新贴出同一张稿并强调「我特别喜欢这版风格，我希望按照这版风格来生成」，逐像素比对确认与 previews/ui/07-codex-gpt-image2_original.png 完全一致",
            "visualDNA": [
                "实色墨底 #12161F（深墨蓝），不是纯黑 #000000 也不是亮底",
                "主体居中且只画一个，占该格 45–60%，四周留 35% 以上空墨底（大面积留白）",
                "16 张里只有聚灵阵/太虚咒等 2–3 张是圆环法阵，其余无环；只有母题本身是环/阵/太极/旋涡/连锁才画环",
                "最多 2–4 枚很小的四角星零星点缀；放射线/速度线只在爆发/冲击/飞行/雷击类母题用 3–5 道",
                "单一高对比剪影或具象符号，棱面分明、实色平涂、1px 纯黑硬描边",
                "亮阶做硬边高光，靠色阶对比而非渐变/发光滤镜；整体安静克制有重量感，不要华丽",
                "稀有度靠卡框色段与边框层次，不靠插画更华丽",
            ],
            "sampleCount": 16,
            "samplePolicy": "只取该张示意卡的主体形态与线条密度；描述里出现的圆环/背光/星点/放射线只是那一张的局部特征，按【做减法】规则处理，不是每格通用装饰；绝不沿用示意稿的假卡名与假数值",
        },
        "styleAnchors": STYLE_ANCHORS,
        "sheetSpec": {
            "sheetCount": SHEET_COUNT,
            "cellsPerSheet": CELLS_PER_SHEET,
            "generations": SHEET_COUNT,
            "sheetSize": [SHEET_W, SHEET_H],
            "grid": [SHEET_COLS, SHEET_ROWS],
            "cellSize": [CELL_W, CELL_H],
            "cropSize": [CROP_W, CROP_H],
            "cropPadX": CROP_PAD_X,
            "cellOrder": "行优先：从上到下、每行从左到右；01=第1行第1格，12=第4行第3格",
            "sheetDir": "previews/card_art_sheets/",
            "sheetNaming": "sheet-01.png … sheet-06.png",
            "splitTool": "tools/split_card_art_sheets.py",
            "cropRule": "每格先按 cellBox 取 512×256，再中心裁 384×256（左右各弃 64px 安全边）；3:2 与 84×56 插画区同比例",
            "noDrawnGrid": "禁止在图上画格线/编号；裁剪按像素坐标（默认固定，--adaptive 自动探测真实行/列空隙），不依赖视觉检测格线",
        },
        "sheets": sheets,
        "outputSpec": {
            "external": "6 张 1536×1024 拼版 PNG，每张 3 列 × 4 行 = 12 格（512×256/格）；每格一张独立插画，#12161F 墨底、主体占该格 45–60% 且四周留 35%+ 空墨底、安静克制，不含任何文字/边框/角标/格线",
            "split": "裁 72 张 384×256 单卡原稿 → previews/card_art/<card_id>-cardart-original.png；默认固定坐标，推荐 --adaptive 自动对齐真实格位（第 36 轮实测行边界漂移 +33/+22/+11px）",
            "transcription": "最近邻降采样 + 24 色吸附 → 84×56 插画区（docs/12 §2 的 x6–89 / y19–75 为 84×57，最终像素对齐待 4× 实机复核）",
            "framePolicy": "4 张稀有度卡框 + 6 张类别纹样继续复用；只替换插画区，卡框不重出 72 次",
            "textPolicy": "卡名/描述/数量仍由 UI 文字层绘制，插画不含文字（R9 字体授权未结案）",
            "naming": "sheet-0N.png → <card_id>-cardart-original.png → <card_id>-cardart_palette24.png → assets/ui/card_art/<card_id>.png",
        },
        "constraints": [
            "72 个 motif / motifEn / signature / silhouette / outputName 两两不同",
            "每类 12 张且类内 12 个剪影两两不同；一类对应一张 sheet，格位 (sheetIndex, cellLabel) 72 个两两不同",
            "稀有度只靠卡框色段与边框层次表达，不靠插画华丽程度，避免同档撞脸",
            "配色严格 24 色锁定板；禁止文字、边框、角标、水印、渐变、半透明、柔边",
            "07-codex 原稿为第一风格基准；72 张卡各绑定其 16 张示意卡之一的画法样板且 16/16 全覆盖，只取画法不沿用假卡名",
            "辅助参考 00-anchor（色板/笔触）与 08-icons（纹样密度/硬描边），不得反客为主",
            "拼版纪律：12 格共画法不共母题；不画格线/编号；主体与光效不得跨格；格位顺序严格对应提示词清单",
            "第 36 轮 R59 克制风格：#12161F 墨底 / 45–60% 主体 / 35%+ 留白 / 最多 2–4 枚星点 / 只有母题是环或阵才画圆环 / 做减法不要华丽；旧「每格双层圆环 + 四角铺满星点」口径已废弃",
        ],
        "cards": entries,
        "stats": {
            "total": len(entries),
            "byCategory": {k: len(v) for k, v in sorted(by_cat.items())},
            "byRarity": {k: sum(1 for e in entries if e["rarity"] == k)
                         for k in RARITY_LABEL},
            "uniqueMotifs": len({e["motif"] for e in entries}),
            "uniqueSignatures": len({e["signature"] for e in entries}),
            "uniqueSilhouettes": len({e["silhouette"] for e in entries}),
            "codexSampleCoverage": len(covered_refs),
            "sheetsTotal": SHEET_COUNT,
            "cellsPerSheet": CELLS_PER_SHEET,
            "generations": SHEET_COUNT,
            "sheetsReceived": len(sheet_received),
            "sheetsPending": SHEET_COUNT - len(sheet_received),
            "artReceived": len(received), "artPending": 72 - len(received),
        },
        "knownExceptions": [
            "docs/12 §5 现行冻结口径是「72 卡只需 4 卡框 + 6 纹样共 10 张小图」；本决策与之冲突，记为 R57，Q17 拍板前不改写该文档",
            "07-codex 稿内 16 张示意卡的卡名与冻结 72 卡库不是一套，且含文字，不得直接当卡面入库",
            "R58 拼版风险：AI 可能画成一张整图、格位漂移、元素跨格、格间风格漂移或擅画格线；先出 1 张 sheet 试裁目检再批量",
            "拼版后每格有效分辨率为 384×256（原单张方案为 1024×1024），目标插画区仅 84×56 / 4× 约 336×224，够用但不等于单张细节密度",
            "回稿未到齐；sheetsReceived / artReceived 如实统计，不伪造 6/6 或 72/72",
        ],
        "boundary": "本表只是外发规格与映射，不是美术资产、不是已入库资源、不改任何冻结数值与规则；Q17 未拍板、GUI F5 未跑、未接 Godot 场景。",
    }
    plan_text = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"

    # ---- 提示词包：6 张拼版 sheet，每组 12 格 ----
    lines = [
        "# 72 卡独立插画 · 6 组拼版外发提示词包（第 35 轮 · 可整段复制）",
        "",
        "> 本文件由 `tools/build_card_art_plan.py` 自动生成，**不要手改**；改母题请改脚本里的 `MOTIFS` 后重跑。",
        "> 设计依据：第 34 轮「每张卡一张独立插画，不能有重复感，突出选卡的重要性」+「以 07-codex 图鉴稿为审美基础」；"
        "第 35 轮「**一张图里画 12 张卡，72 / 12 = 6 次生成，节省 gpt-image2 额度，裁剪由 AI 负责**」。",
        "> **一共只需生成 6 次**：6 张 1536×1024 拼版 PNG，每张 3 列 × 4 行 = 12 格；6 × 12 = 72 张卡，一次不多一次不少。",
        "> **尺寸务必在平台手选 3:2 / 1536×1024**：第 24 轮实测「提示词里写尺寸不生效」，只靠文字容易得到 1024×1024 方图。裁剪脚本对非 1536×1024 回稿会**直接拒绝**，避免固定坐标裁歪；若平台只能出别的比例，先告诉我改网格再出图。",
        "> **第一风格基准 = `previews/ui/07-codex-gpt-image2_original.png`**（用户已确认审美的 gpt-image2 图鉴回稿，本身就是一张图排多张卡）。每次出图都把这张稿一起附作参考图。",
        "> **⚠️ 第 36 轮风格更正（重要）**：此前版本把原稿误读成「每格都套圆形 / 双层圆环法阵 + 四角铺满 4–8 枚菱形星点」，生成结果是 12 个华丽徽章，与用户要的**不是一版**。原稿真正的特点是「#12161F 深墨底 + 一个简洁符号 + 大面积留白 + 安静克制」，16 张里只有 2–3 张是圆环构图。**本版提示词已改回克制画法，按本版重出；不要沿用旧版提示词。**",
        "> **⚠️ 第 37 轮内容更正（同样重要）**：第 36 轮提示词在通用规格里列举了参考稿的 12 个示意卡主体名，gpt-image2 把它们当成「12 格该画什么」直接照抄了 —— 风格对了但**12 格母题与 12 张卡全部对不上**。本版已删掉该列举、加【参考图使用边界】黑名单、把「12 格清单」声明为唯一内容依据，并把画法样板改成只借密度不留主体名。**必须按本版重出；复制代码块时仍附 07-codex 原稿，但它是风格参考，不是内容清单。**",
        "> 用法：每组中文（或英文）代码块**自包含通用规格 + 12 格清单**，整段复制给 gpt-image2；**建议先只出第 1 组试裁**，确认 12 格各独立、格位对齐、无格线文字后再出剩余 5 组。",
        "> 回稿命名严格用组内 `【命名】`，丢进 `previews/card_art_sheets/`。**你不用切图**：`tools/split_card_art_sheets.py` 按固定坐标裁成 72 张单卡原稿。",
        "> 辅助参考：`00-anchor`（色板/笔触）、`08-icons`（24×24 纹样密度）、`07-codex_palette24`（24 色吸附版）。示意稿里的假卡名与假数值一律不沿用。",
        "",
        "| 组 | 类别 | 张数 | 拼版文件 | 生成次数 |",
        "|---|---|---|---|---|",
    ]
    for si, cat in enumerate(CAT_ORDER, 1):
        lines.append(f"| 第 {si} 组 | {CATEGORY_LABEL[cat]} | 12 | `sheet-{si:02d}.png` | 1 |")
    lines += [
        "",
        "## 0. 通用规格（6 组已内嵌，这里单列便于核对）",
        "",
        "```text",
        COMMON_ZH,
        "```",
        "",
        "```text",
        COMMON_EN,
        "```",
        "",
        "| 色段键 | 中文 | 三阶色值 |",
        "|---|---|---|",
    ]
    for key, (zh, en, colors) in BANDS.items():
        lines.append(f"| `{key}` | {zh} / {en} | {' / '.join(colors)} |")
    lines += [
        "",
        "24 色锁定板合计：" + " ".join(PALETTE),
        "",
        "## 0b. 07-codex 原稿的 16 个画法样板（72 张卡各沿用其一）",
        "",
        "> 下表是从用户已确认审美的图鉴原稿逐格提取的**画法**，不是卡名映射。示意卡名只用于定位格子位置，不作为目标卡名。",
        "> **只取该张的主体形态与线条密度**：描述里若出现圆环、圆形背光、星点、放射线，那只是那一张的局部特征，**不是每格通用装饰**，一律按通用规格的【做减法】规则处理。",
        "",
        "| 样板键 | 稿内位置 | 示意卡名（仅定位用） | 要沿用的画法 |",
        "|---|---|---|---|",
    ]
    for key, (pos, sample, tech, _tech_en) in CODEX_SAMPLES.items():
        lines.append(f"| `{key}` | {pos} | {sample} | {tech} |")
    lines += [
        "",
        "> 16 个样板全部被 72 张卡引用（16/16 全覆盖），由 `docs/card-art-plan.json` 的 `codexRef` 字段与 `--check` 断言保证。",
        "",
        "> **唯一性契约**：6 张 sheet 共 72 格，72 个母题 / 剪影 / 签名两两不同；每组 12 格内也不得撞脸。"
        " **风格一致由「第一基准 + 画法样板 + 同张拼版」保证，差异化由「唯一母题 + 唯一剪影」保证。**",
        "> 拼版纪律：12 格**共画法不共母题**，不画格线 / 格号 / 编号，主体与光效不得跨格；格位按「从上到下、每行从左到右」严格对应清单，"
        "因为裁剪按固定像素坐标（每格 512×256，中心裁 384×256），不依赖视觉检测。",
        "",
        "---",
        "",
    ]

    sheet_titles = {
        "dmg": "① 技能伤害（朱砂主调）", "attr": "② 属性提升（青玉主调）",
        "mech": "③ 机制改变（紫主调）", "res": "④ 资源灵力（金主调）",
        "surv": "⑤ 生存回复（青玉/淡青主调）", "syn": "⑥ 构筑风险（朱砂暗主调）",
    }

    def cell_list_zh(group: list[dict]) -> list[str]:
        out = ["【12 格逐格清单 · 本拼版唯一的内容依据，优先级高于参考图与上方所有风格说明】格号 → 唯一画面，严格一一对应，不要调换顺序或合并母题。",
              "【严禁照抄参考图】每格引用的 07-codex 示意卡只用来对齐线条密度、留白比例与色阶节奏；示意卡里画的具体符号一律不要画，主体形状必须按本格母题重新设计。不得把参考图里 16 张示意卡的任何一张搬进本拼版。"]
        for i, e in enumerate(group, 1):
            row, col = divmod(i - 1, SHEET_COLS)
            band_zh, _band_en, colors = BANDS[e["focalBand"]]
            ex_a, ex_b = e["excludes"]
            out.append(
                f"格 {i:02d}（第 {row + 1} 行第 {col + 1} 格 / {e['cellLabel']}）→ {e['id']}｜"
                f"唯一母题：{e['motif']}；主体剪影：{e['silhouette']}；"
                f"构图：{COMPOSITIONS[e['composition']]}；"
                f"主色段：{band_zh} {' / '.join(colors)}；"
                f"画法样板：07-codex {e['codexRefPos']}「{e['codexRefSample']}」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；"
                f"不得画成「{ex_a['motif']}」或「{ex_b['motif']}」。")
        return out

    def cell_list_en(group: list[dict]) -> list[str]:
        out = ["12-CELL LIST - THE ONLY CONTENT SPEC FOR THIS SHEET; it overrides the reference image and every style note above. One UNIQUE picture per cell, strict 1:1 order, do not reorder or merge motifs:",
              "NEVER COPY THE REFERENCE. Each cited 07-codex sample is used ONLY for line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif. Do not bring any of the 16 sample-card symbols into this sheet."]
        for i, e in enumerate(group, 1):
            row, col = divmod(i - 1, SHEET_COLS)
            _bz, band_en, colors = BANDS[e["focalBand"]]
            ex_a, ex_b = e["excludes"]
            out.append(
                f"Cell {i:02d} (row {row + 1}, col {col + 1} / {e['cellLabel']}) -> {e['id']}: "
                f"motif = {e['motifEn']}; silhouette = {e['silhouette']}; "
                f"composition = {e['composition']}; focal band = {band_en} {' / '.join(colors)}; "
                f"style sample = 07-codex {e['codexRef']}: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; "
                f"do NOT depict \"{ex_a['motifEn']}\" or \"{ex_b['motifEn']}\".")
        return out

    for si, cat in enumerate(CAT_ORDER, 1):
        group = by_cat[cat]
        sheet_file = f"sheet-{si:02d}.png"
        lines += [
            f"## 第 {si} 组（第 {si} / 6 次生成）· {sheet_titles[cat]}",
            "",
            f"> 类别 `{cat}` · 12 张卡 = 1 张 {SHEET_W}×{SHEET_H} 拼版（{SHEET_COLS} 列 × {SHEET_ROWS} 行）。",
            f"> **【命名】{sheet_file}** → 放 `previews/card_art_sheets/`。裁剪由 `tools/split_card_art_sheets.py` 完成，你不用切图。",
            "",
            f"### 第 {si} 组 · 中文提示词（整段复制）",
            f"<!-- sheet-{si:02d}:zh -->",
            "```text",
            COMMON_ZH,
            "",
        ] + cell_list_zh(group) + [
            "",
            "【格位与画法的强制关系】12 格共用同一套克制画法与第一基准；每格只换中心母题，#12161F 墨底 / 大面积留白 / 亮阶硬边高光 / 1px 纯黑硬描边保持一致。圆环只在母题本身是环 / 阵时才画，星点最多 2–4 枚。禁止把 12 格画成一张连续大场景，禁止元素跨格，禁止画格线或格号。",
            f"【输出】单张 {SHEET_W}×{SHEET_H} 不透明 PNG，命名 {sheet_file}；画面内无任何文字与编号。",
            "```",
            "",
            f"### Group {si} · English (copy as one block)",
            f"<!-- sheet-{si:02d}:en -->",
            "```text",
            COMMON_EN,
            "",
        ] + cell_list_en(group) + [
            "",
            "HARD RULE: all 12 cells share the same RESTRAINED painting method and the single primary 07-codex reference; only the central motif changes per cell. Keep #12161F ink ground, generous negative space, bright-step hard highlights and 1px black outlines identical. Draw a ring ONLY when the motif itself is a ring/array, and never more than 2-4 star points. Never merge the 12 cells into one continuous scene, never let an element cross a cell boundary, never draw grid lines or cell numbers.",
            f"Output: one opaque {SHEET_W}x{SHEET_H} PNG named {sheet_file}, with no text or numbers anywhere.",
            "```",
            "",
            "---",
            "",
        ]

    lines += [
        "## 交付与验收顺序",
        "",
        "1. **先只出第 1 组** `sheet-01.png`，放 `previews/card_art_sheets/`；跑一次裁剪脚本试裁，目检 12 格是否各独立、格位是否对齐、有无格线 / 文字 / 跨格元素（R58）。",
        "2. 确认观感一致后再出剩余 5 组；6 张齐了总共也就 **6 次生成**。原稿不改写。",
        "3. `python3 tools/split_card_art_sheets.py`：按固定坐标裁出 72 张 384×256 单卡原稿到 `previews/card_art/`，并写 `docs/card-art-split-report.json`（含每张 sheet 的 sha256 与格位映射）。",
        "4. 逐张体检：不透明 / 24 色锁定板越界色 0 / 无文字与边框 / 水印修补（沿用第 31 轮 A2R 口径）。",
        "5. 转录为 84×56 插画区：`24 色吸附 + 最近邻`，落到 `assets/ui/card_art/<card_id>.png`；卡框仍复用现有 4+6 张。",
        "6. 三选一同屏目检：任取 3 张并排，剪影 / 构图 / 主色段不得撞脸；图鉴 72 张整屏并排不得出现明显复用感。",
        "7. 全部标「待目检与合规确认；不得直接入库」；Q17 拍板 + GUI F5 目检后才谈替换 `assets/ui/cards/` 的 10 张冻结卡面。",
        "",
        "> **状态：待外发 / 未回稿 / 候选规格，不是已入库资源。** 本包不改 `docs/12` 冻结口径、不改任何冻结数值与规则。",
        "",
    ]
    pack_text = "\n".join(lines)
    return plan_text, pack_text, render_overview(plan)


def check() -> str:
    plan_text, pack_text, overview_text = build()
    if not PLAN_PATH.is_file() or PLAN_PATH.read_text(encoding="utf-8") != plan_text:
        raise AssertionError("docs/card-art-plan.json 与生成器复算不一致，请重跑生成")
    if not PACK_PATH.is_file() or PACK_PATH.read_text(encoding="utf-8") != pack_text:
        raise AssertionError("previews/card-art-prompts-pack.md 与生成器复算不一致，请重跑生成")
    if not OVERVIEW_PATH.is_file() or OVERVIEW_PATH.read_text(encoding="utf-8") != overview_text:
        raise AssertionError("previews/card-art-plan-overview.html 与生成器复算不一致，请重跑生成")
    if overview_text.count('data-search=') != 72:
        raise AssertionError("母题核对页不是 72 行")
    if overview_text.count("07-codex 画法样板（第一基准）") != 6:
        raise AssertionError("母题核对页 6 组表头缺 07-codex 画法样板列")

    plan = json.loads(plan_text)
    cards = plan["cards"]
    if len(cards) != 72 or plan["stats"]["total"] != 72:
        raise AssertionError("映射表不是 72 张")
    if plan["stats"]["uniqueMotifs"] != 72 or plan["stats"]["uniqueSignatures"] != 72:
        raise AssertionError("母题或签名不唯一，违反一卡一母题")
    if plan["stats"]["uniqueSilhouettes"] != 72:
        raise AssertionError("剪影全局不唯一")
    for cat, count in plan["stats"]["byCategory"].items():
        if count != 12:
            raise AssertionError(f"{cat} 不是 12 张")
    for pth in STYLE_ANCHORS:
        if not (ROOT / pth).is_file():
            raise AssertionError(f"风格锚点原稿缺失：{pth}")
    if plan["styleAnchors"][0] != "previews/ui/07-codex-gpt-image2_original.png":
        raise AssertionError("07-codex 原稿不是第一风格基准")
    if plan["stats"]["codexSampleCoverage"] != 16:
        raise AssertionError("07-codex 16 个画法样板未全覆盖")
    if len({c["codexRef"] for c in cards}) != 16:
        raise AssertionError("72 卡引用的 07-codex 画法样板不足 16 个")
    if "## 0b. 07-codex 原稿的 16 个画法样板" not in pack_text:
        raise AssertionError("提示词包缺 16 个画法样板速查表")
    for key, (_pos, _sample, tech, _en) in CODEX_SAMPLES.items():
        if f"| `{key}` |" not in pack_text or tech not in pack_text:
            raise AssertionError(f"提示词包缺画法样板 {key}")

    # ---- 第 35 轮：拼版规格 / 6 次生成 / 72 格位 ----
    spec = plan["sheetSpec"]
    if spec["sheetCount"] != 6 or spec["cellsPerSheet"] != 12 or spec["generations"] != 6:
        raise AssertionError("拼版规格不是 6 张 × 12 格 / 6 次生成")
    if spec["sheetSize"] != [SHEET_W, SHEET_H] or spec["grid"] != [SHEET_COLS, SHEET_ROWS]:
        raise AssertionError("拼版尺寸或网格与生成器常量不一致")
    if spec["cellSize"] != [CELL_W, CELL_H] or spec["cropSize"] != [CROP_W, CROP_H]:
        raise AssertionError("格尺寸或裁切尺寸与生成器常量不一致")
    if SHEET_COLS * CELL_W != SHEET_W or SHEET_ROWS * CELL_H != SHEET_H:
        raise AssertionError("3×4 网格不能整除 1536×1024")
    if CROP_W + 2 * CROP_PAD_X != CELL_W or CROP_H != CELL_H:
        raise AssertionError("中心裁切框数学不自洽")
    if CROP_W / CROP_H != 1.5:
        raise AssertionError("裁切框不是 3:2，与 84×56 插画区不同比例")
    sheets = plan["sheets"]
    if len(sheets) != 6 or [s["cellCount"] for s in sheets] != [12] * 6:
        raise AssertionError("6 张 sheet 不是各 12 格")
    grid_keys = [(c["sheetIndex"], c["cellLabel"]) for c in cards]
    if len(set(grid_keys)) != 72:
        raise AssertionError("72 个 sheet 格位不唯一")
    for s in sheets:
        labels = [c["label"] for c in s["cells"]]
        if labels != [f"r{r}c{col}" for r in range(1, SHEET_ROWS + 1)
                      for col in range(1, SHEET_COLS + 1)]:
            raise AssertionError(f"{s['file']} 格位顺序不是行优先 3×4")
    for c in cards:
        x0 = (c["cellCol"] - 1) * CELL_W
        y0 = (c["cellRow"] - 1) * CELL_H
        if c["cellBox"] != [x0, y0, x0 + CELL_W, y0 + CELL_H]:
            raise AssertionError(f"{c['id']} 的 cellBox 复算不符")
        if c["cropBox"] != [x0 + CROP_PAD_X, y0, x0 + CROP_PAD_X + CROP_W, y0 + CROP_H]:
            raise AssertionError(f"{c['id']} 的 cropBox 复算不符")
        if c["sheetFile"] != f"sheet-{c['sheetIndex']:02d}.png":
            raise AssertionError(f"{c['id']} 的 sheet 文件名不符")

    # ---- 提示词包：6 组中文 + 6 组英文，逐组 12 格清单 ----
    if pack_text.count(":zh -->") != 6 or pack_text.count(":en -->") != 6:
        raise AssertionError("提示词包不是 6 组中文 + 6 组英文")
    # §0 通用规格单列 1 次 + 6 组各内嵌 1 次 = 7 次
    if pack_text.count("【风格第一基准 · 必须照此画】") != 7:
        raise AssertionError("中文提示词不是 §0 + 6 组都以 07-codex 为第一基准")
    if pack_text.count("PRIMARY STYLE REFERENCE - attach previews/ui/07-codex-gpt-image2_original.png") != 7:
        raise AssertionError("英文提示词不是 §0 + 6 组都以 07-codex 为第一基准")
    if pack_text.count("【12 格逐格清单 · 本拼版唯一的内容依据") != 6 \
            or pack_text.count("12-CELL LIST - THE ONLY CONTENT SPEC") != 6:
        raise AssertionError("6 组提示词缺 12 格逐格清单")
    # 第 37 轮：参考图边界须内嵌进 §0 单列 + 6 组，共 7 次；旧主体名列举零残留
    if pack_text.count("【参考图使用边界 · 严禁照抄示意卡主体】") != 7 \
            or pack_text.count("REFERENCE USAGE BOUNDARY - DO NOT COPY THE SAMPLE CARD SUBJECTS") != 7:
        raise AssertionError("6 组提示词缺第 37 轮参考图使用边界")
    for bad in ("原稿 16 张插画绝大多数是「一个符号直接放在墨底上」——螺旋气旋",
                "In the reference, most of the 16 cards are simply one emblem placed directly "
                "on the ink ground - spiral"):
        if bad in pack_text:
            raise AssertionError("提示词仍残留会被引擎当成 12 格内容的参考稿主体名列举")
    if "第 37 轮内容更正" not in pack_text:
        raise AssertionError("提示词包头部缺第 37 轮更正说明")
    for si in range(1, 7):
        if f"【命名】sheet-{si:02d}.png" not in pack_text:
            raise AssertionError(f"提示词包缺 sheet-{si:02d}.png 的命名")
    parts = pack_text.split("<!-- sheet-")[1:]
    if len(parts) != 12:
        raise AssertionError("提示词包不是 12 个中英代码块")
    by_cat = {}
    for c in cards:
        by_cat.setdefault(c["category"], []).append(c)
    for part in parts:
        si = int(part[:2])
        zh = part.startswith(f"{si:02d}:zh -->")
        group = by_cat[CAT_ORDER[si - 1]]
        for c in group:
            cid = c["id"]
            if cid not in part:
                raise AssertionError(f"sheet-{si:02d} 缺 {cid} 的格位条目")
            key = c["motif"] if zh else c["motifEn"]
            if key not in part:
                raise AssertionError(f"sheet-{si:02d} 缺 {cid} 的{'中文' if zh else '英文'}母题")
            if zh and "只借鉴该张的线条密度、留白比例与色阶节奏" not in part:
                raise AssertionError(f"sheet-{si:02d} 缺第 37 轮中性画法样板句")
            if not zh and "borrow ONLY line density, negative-space ratio" not in part:
                raise AssertionError(f"sheet-{si:02d} 缺第 37 轮英文中性画法样板句")
    for _pos, _sample, tech, tech_en in CODEX_SAMPLES.values():
        for part in parts:
            if tech in part or tech_en in part:
                raise AssertionError("逐格清单代码块仍含参考稿示意卡的具体主体描述，会被照抄")
    for c in cards:
        cid = c["id"]
        if c["codexRef"] not in CODEX_SAMPLES:
            raise AssertionError(f"{cid} 的 07-codex 画法样板键非法")
        if c["codexRefTechnique"] not in overview_text:
            raise AssertionError(f"母题核对页缺 {cid} 的画法样板")
        if len(c["excludes"]) != 2:
            raise AssertionError(f"{cid} 缺排除项")
    for hex_color in PALETTE:
        if hex_color not in COMMON_ZH:
            raise AssertionError(f"通用规格缺色板色值 {hex_color}")
    for banned in ("禁止出现任何文字", "不得直接入库", "Q17", "6 次生成", "【命名】",
                  "严禁照抄示意卡主体", "唯一的内容依据", "NEVER COPY THE REFERENCE"):
        if banned not in pack_text:
            raise AssertionError(f"提示词包缺规格/边界：{banned}")
    for path in (DOC / "27-72卡独立插画设计决议与外发规格.md",):
        if not path.is_file():
            raise AssertionError(f"缺决议文档：{path.name}")
        t = path.read_text(encoding="utf-8")
        for token in ("R57", "R58", "R59", "R60", "Q17", "不得直接入库", "不替换",
                      "24 色", "6 次生成", "第 37 轮"):
            if token not in t:
                raise AssertionError(f"决议文档缺边界：{token}")
    split_tool = ROOT / "tools" / "split_card_art_sheets.py"
    if not split_tool.is_file():
        raise AssertionError("缺拼版裁剪脚本 tools/split_card_art_sheets.py")
    res = subprocess.run([sys.executable, str(split_tool), "--check"],
                         cwd=ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        raise AssertionError(f"裁剪脚本 --check 失败：{res.stdout[-200:]} {res.stderr[-200:]}")
    return (f"6 张拼版 / 6 次生成 / 72 格位一一对应 / 72 卡母题·签名·剪影唯一 / "
            f"6 组中英提示词 + 72 行核对页 / 07-codex 第一基准 16/16 样板全覆盖 / "
            f"4 张 gpt-image2 锚点真实存在 / 拼版回稿 {plan['stats']['sheetsReceived']}/6、"
            f"单卡原稿 {plan['stats']['artReceived']}/72（如实披露）")


def main() -> int:
    ap = argparse.ArgumentParser(description="72 卡独立插画映射表与提示词包")
    ap.add_argument("--check", action="store_true", help="只复算，不改文件")
    args = ap.parse_args()
    try:
        if args.check:
            print("PASS | " + check())
        else:
            plan_text, pack_text, overview_text = build()
            PLAN_PATH.write_text(plan_text, encoding="utf-8")
            PACK_PATH.write_text(pack_text, encoding="utf-8")
            OVERVIEW_PATH.write_text(overview_text, encoding="utf-8")
            print(f"WROTE | {PLAN_PATH.relative_to(ROOT)} ({len(plan_text)} chars)")
            print(f"WROTE | {PACK_PATH.relative_to(ROOT)} ({len(pack_text)} chars)")
            print(f"WROTE | {OVERVIEW_PATH.relative_to(ROOT)} ({len(overview_text)} chars)")
            print("PASS | " + check())
    except Exception as exc:
        print(f"FAIL | {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
