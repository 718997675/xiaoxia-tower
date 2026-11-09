# 72 卡独立插画 · 6 组拼版外发提示词包（第 35 轮 · 可整段复制）

> 本文件由 `tools/build_card_art_plan.py` 自动生成，**不要手改**；改母题请改脚本里的 `MOTIFS` 后重跑。
> 设计依据：第 34 轮「每张卡一张独立插画，不能有重复感，突出选卡的重要性」+「以 07-codex 图鉴稿为审美基础」；第 35 轮「**一张图里画 12 张卡，72 / 12 = 6 次生成，节省 gpt-image2 额度，裁剪由 AI 负责**」。
> **一共只需生成 6 次**：6 张 1536×1024 拼版 PNG，每张 3 列 × 4 行 = 12 格；6 × 12 = 72 张卡，一次不多一次不少。
> **尺寸务必在平台手选 3:2 / 1536×1024**：第 24 轮实测「提示词里写尺寸不生效」，只靠文字容易得到 1024×1024 方图。裁剪脚本对非 1536×1024 回稿会**直接拒绝**，避免固定坐标裁歪；若平台只能出别的比例，先告诉我改网格再出图。
> **第一风格基准 = `previews/ui/07-codex-gpt-image2_original.png`**（用户已确认审美的 gpt-image2 图鉴回稿，本身就是一张图排多张卡）。每次出图都把这张稿一起附作参考图。
> **⚠️ 第 36 轮风格更正（重要）**：此前版本把原稿误读成「每格都套圆形 / 双层圆环法阵 + 四角铺满 4–8 枚菱形星点」，生成结果是 12 个华丽徽章，与用户要的**不是一版**。原稿真正的特点是「#12161F 深墨底 + 一个简洁符号 + 大面积留白 + 安静克制」，16 张里只有 2–3 张是圆环构图。**本版提示词已改回克制画法，按本版重出；不要沿用旧版提示词。**
> **⚠️ 第 37 轮内容更正（同样重要）**：第 36 轮提示词在通用规格里列举了参考稿的 12 个示意卡主体名，gpt-image2 把它们当成「12 格该画什么」直接照抄了 —— 风格对了但**12 格母题与 12 张卡全部对不上**。本版已删掉该列举、加【参考图使用边界】黑名单、把「12 格清单」声明为唯一内容依据，并把画法样板改成只借密度不留主体名。**必须按本版重出；复制代码块时仍附 07-codex 原稿，但它是风格参考，不是内容清单。**
> 用法：每组中文（或英文）代码块**自包含通用规格 + 12 格清单**，整段复制给 gpt-image2；**建议先只出第 1 组试裁**，确认 12 格各独立、格位对齐、无格线文字后再出剩余 5 组。
> 回稿命名严格用组内 `【命名】`，丢进 `previews/card_art_sheets/`。**你不用切图**：`tools/split_card_art_sheets.py` 按固定坐标裁成 72 张单卡原稿。
> 辅助参考：`00-anchor`（色板/笔触）、`08-icons`（24×24 纹样密度）、`07-codex_palette24`（24 色吸附版）。示意稿里的假卡名与假数值一律不沿用。

| 组 | 类别 | 张数 | 拼版文件 | 生成次数 |
|---|---|---|---|---|
| 第 1 组 | 技能伤害 | 12 | `sheet-01.png` | 1 |
| 第 2 组 | 属性提升 | 12 | `sheet-02.png` | 1 |
| 第 3 组 | 机制改变 | 12 | `sheet-03.png` | 1 |
| 第 4 组 | 资源灵力 | 12 | `sheet-04.png` | 1 |
| 第 5 组 | 生存回复 | 12 | `sheet-05.png` | 1 |
| 第 6 组 | 构筑风险 | 12 | `sheet-06.png` | 1 |

## 0. 通用规格（6 组已内嵌，这里单列便于核对）

```text
东方修真题材 2D 像素游戏「卡牌插画拼版」，单张 1536×1024 不透明 PNG 横版。整图严格分成 3 列 × 4 行 = 12 个等大横格，每格 512×256 像素；格位按「从上到下、每行从左到右」编号 01–12（01=第1行第1格，04=第2行第1格，12=第4行第3格）。整图不留白边、不加外框。

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
辅助参考（只取色板 / 笔触 / 纹样密度）：previews/ui/00-anchor-gpt-image2_palette24.png、previews/ui/08-icons-gpt-image2_palette24.png；24 色吸附版为 previews/ui/07-codex-gpt-image2_palette24.png。
```

```text
A 12-cell contact sheet of card illustrations for a 2D eastern-xianxia pixel game. One opaque 1536x1024 landscape PNG. Divide the whole canvas into EXACTLY 3 columns x 4 rows = 12 equal horizontal cells of 512x256 px each. Cell order is top-to-bottom, and within each row left-to-right: 01 = row1/col1, 04 = row2/col1, 12 = row4/col3. No outer margin, no outer frame.

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
Secondary references (palette / brush / glyph density only): previews/ui/00-anchor-gpt-image2_palette24.png, previews/ui/08-icons-gpt-image2_palette24.png; 24-color-snapped version: previews/ui/07-codex-gpt-image2_palette24.png.
```

| 色段键 | 中文 | 三阶色值 |
|---|---|---|
| `ink` | 墨 / ink | #12161F / #2A3140 / #4A5568 |
| `paper` | 宣纸 / rice-paper | #8A8268 / #C9BFA3 / #E8DFC8 |
| `jade` | 青玉 / jade | #2F6E6A / #5FA8A0 / #9BD4CC |
| `cinnabar` | 朱砂 / cinnabar | #7A2420 / #C8453B / #E8806F |
| `gold` | 金 / gold | #8A6520 / #D9A441 / #F2D089 |
| `violet` | 紫 / violet | #4A3A6B / #8A6FC4 / #C0A8E0 |

24 色锁定板合计：#12161F #2A3140 #4A5568 #8A8268 #C9BFA3 #E8DFC8 #2F6E6A #5FA8A0 #9BD4CC #7A2420 #C8453B #E8806F #8A6520 #D9A441 #F2D089 #4A3A6B #8A6FC4 #C0A8E0 #000000 #FFFFFF

## 0b. 07-codex 原稿的 16 个画法样板（72 张卡各沿用其一）

> 下表是从用户已确认审美的图鉴原稿逐格提取的**画法**，不是卡名映射。示意卡名只用于定位格子位置，不作为目标卡名。
> **只取该张的主体形态与线条密度**：描述里若出现圆环、圆形背光、星点、放射线，那只是那一张的局部特征，**不是每格通用装饰**，一律按通用规格的【做减法】规则处理。

| 样板键 | 稿内位置 | 示意卡名（仅定位用） | 要沿用的画法 |
|---|---|---|---|
| `r1c1` | 第 1 行第 1 张 | 清风诀 | 青白螺旋气旋居中，四周散布菱形小星点，深墨蓝底，细放射线 |
| `r1c2` | 第 1 行第 2 张 | 金光术 | 金色八角星芒居中，硬边细放射线向外，暗棕底，四角星点 |
| `r1c3` | 第 1 行第 3 张 | 回春术 | 青绿双叶新芽居中，四周菱形星点，深墨绿底，柔和但不模糊的圆形背光 |
| `r1c4` | 第 1 行第 4 张 | 御剑术 | 斜置飞剑居中，青蓝斜向速度线，深墨蓝底，剑身高对比硬边 |
| `r2c1` | 第 2 行第 1 张 | 聚灵阵 | 青玉双层圆环法阵居中，环上八个光点，中心阴阳，深墨青底 |
| `r2c2` | 第 2 行第 2 张 | 炼丹术 | 青玉丹瓶居中，上浮气泡光点，深墨青底，瓶口一圈亮边 |
| `r2c3` | 第 2 行第 3 张 | 化气诀 | 青玉打坐人形剪影居中，背后圆形背光与两侧气旋，深墨绿底 |
| `r2c4` | 第 2 行第 4 张 | 风行术 | 奔跑人形剪影居中，横向青蓝速度线，深墨蓝底，四肢硬边 |
| `r3c1` | 第 3 行第 1 张 | 天雷诀 | 紫色分岔雷电居中，放射碎光，深紫黑底，雷枝折线硬边 |
| `r3c2` | 第 3 行第 2 张 | 玄冰诀 | 青蓝冰晶簇居中，冷光碎点，深蓝底，晶体棱面分明 |
| `r3c3` | 第 3 行第 3 张 | 星晨变 | 金色行星环居中，中心亮星，四周菱形星点，深棕金底 |
| `r3c4` | 第 3 行第 4 张 | 太虚咒 | 紫色同心螺旋法阵居中，多层环带，深紫底，环带硬边 |
| `r4c1` | 第 4 行第 1 张 | 万劫灭 | 朱红火焰包裹人形剪影居中，朱砂暗底，火舌硬边分叉 |
| `r4c2` | 第 4 行第 2 张 | 天罚劫 | 朱红环形剑气居中，一道斜剑穿过，朱砂暗底，环带断口 |
| `r4c3` | 第 4 行第 3 张 | 混沌诀 | 紫金阴阳旋涡居中，四周菱形星点，朱砂暗底 |
| `r4c4` | 第 4 行第 4 张 | 无尽劫 | 朱红拱形火门居中，门内人形剪影，朱砂暗底 |

> 16 个样板全部被 72 张卡引用（16/16 全覆盖），由 `docs/card-art-plan.json` 的 `codexRef` 字段与 `--check` 断言保证。

> **唯一性契约**：6 张 sheet 共 72 格，72 个母题 / 剪影 / 签名两两不同；每组 12 格内也不得撞脸。 **风格一致由「第一基准 + 画法样板 + 同张拼版」保证，差异化由「唯一母题 + 唯一剪影」保证。**
> 拼版纪律：12 格**共画法不共母题**，不画格线 / 格号 / 编号，主体与光效不得跨格；格位按「从上到下、每行从左到右」严格对应清单，因为裁剪按固定像素坐标（每格 512×256，中心裁 384×256），不依赖视觉检测。

---

## 第 1 组（第 1 / 6 次生成）· ① 技能伤害（朱砂主调）

> 类别 `dmg` · 12 张卡 = 1 张 1536×1024 拼版（3 列 × 4 行）。
> **【命名】sheet-01.png** → 放 `previews/card_art_sheets/`。裁剪由 `tools/split_card_art_sheets.py` 完成，你不用切图。

### 第 1 组 · 中文提示词（整段复制）
<!-- sheet-01:zh -->
```text
东方修真题材 2D 像素游戏「卡牌插画拼版」，单张 1536×1024 不透明 PNG 横版。整图严格分成 3 列 × 4 行 = 12 个等大横格，每格 512×256 像素；格位按「从上到下、每行从左到右」编号 01–12（01=第1行第1格，04=第2行第1格，12=第4行第3格）。整图不留白边、不加外框。

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
辅助参考（只取色板 / 笔触 / 纹样密度）：previews/ui/00-anchor-gpt-image2_palette24.png、previews/ui/08-icons-gpt-image2_palette24.png；24 色吸附版为 previews/ui/07-codex-gpt-image2_palette24.png。

【12 格逐格清单 · 本拼版唯一的内容依据，优先级高于参考图与上方所有风格说明】格号 → 唯一画面，严格一一对应，不要调换顺序或合并母题。
【严禁照抄参考图】每格引用的 07-codex 示意卡只用来对齐线条密度、留白比例与色阶节奏；示意卡里画的具体符号一律不要画，主体形状必须按本格母题重新设计。不得把参考图里 16 张示意卡的任何一张搬进本拼版。
格 01（第 1 行第 1 格 / r1c1）→ card_jianfeng｜唯一母题：磨石上淬出一道笔直火花的剑刃；主体剪影：斜置长剑与一道直线火花；构图：斜向对角线；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 1 行第 4 张「御剑术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「斜剑斩落一颗坠星」或「一柄剑裂成两道对称剑光且总光量守恒」。
格 02（第 1 行第 2 格 / r1c2）→ card_poyun｜唯一母题：一柄剑裂成两道对称剑光且总光量守恒；主体剪影：对称双剑与中间断开的剑柄；构图：左右对称；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 1 行第 2 张「金光术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「磨石上淬出一道笔直火花的剑刃」或「两道雷柱落在重描过的符篆上」。
格 03（第 1 行第 3 格 / r1c3）→ card_leizhuan｜唯一母题：两道雷柱落在重描过的符篆上；主体剪影：双雷柱与方形符篆；构图：纵向立柱；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 3 行第 1 张「天雷诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一柄剑裂成两道对称剑光且总光量守恒」或「丹炉爆燃后火舌回卷自噬炉身」。
格 04（第 2 行第 1 格 / r2c1）→ card_danbao｜唯一母题：丹炉爆燃后火舌回卷自噬炉身；主体剪影：圆腹丹炉与回卷火舌；构图：中心放射；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 4 行第 1 张「万劫灭」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「两道雷柱落在重描过的符篆上」或「符纸层层叠印成一座方阵」。
格 05（第 2 行第 2 格 / r2c2）→ card_fuzhen｜唯一母题：符纸层层叠印成一座方阵；主体剪影：四张错叠符纸组成的方阵；构图：方阵网格；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 3 行第 4 张「太虚咒」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「丹炉爆燃后火舌回卷自噬炉身」或「三段递进的拳风同心弧」。
格 06（第 2 行第 3 格 / r2c3）→ card_quanfeng｜唯一母题：三段递进的拳风同心弧；主体剪影：三道由小到大的同心弧；构图：同心弧带；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 1 行第 1 张「清风诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「符纸层层叠印成一座方阵」或「一片叶子的左半化为刀刃」。
格 07（第 3 行第 1 格 / r3c1）→ card_huiling｜唯一母题：一片叶子的左半化为刀刃；主体剪影：半叶半刃的同体剪影；构图：中缝对分；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 1 行第 3 张「回春术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「三段递进的拳风同心弧」或「金刚罩碎裂后向外释放扇形冲击」。
格 08（第 3 行第 2 格 / r3c2）→ card_jingang｜唯一母题：金刚罩碎裂后向外释放扇形冲击；主体剪影：破裂钟罩与扇形碎片；构图：扇形展开；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 1 行第 2 张「金光术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一片叶子的左半化为刀刃」或「一剑水平贯穿整列敌人剪影」。
格 09（第 3 行第 3 格 / r3c3）→ card_jianyi｜唯一母题：一剑水平贯穿整列敌人剪影；主体剪影：长直剑与三个被贯穿的剪影；构图：水平贯穿；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 1 行第 4 张「御剑术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「金刚罩碎裂后向外释放扇形冲击」或「五行环破开一面铁壁盾」。
格 10（第 4 行第 1 格 / r4c1）→ card_wuxing｜唯一母题：五行环破开一面铁壁盾；主体剪影：五段色环与裂开的方盾；构图：闭合环；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 2 行第 1 张「聚灵阵」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一剑水平贯穿整列敌人剪影」或「三枚符环相扣成链且末端重接」。
格 11（第 4 行第 2 格 / r4c2）→ card_lianhuan｜唯一母题：三枚符环相扣成链且末端重接；主体剪影：三环相扣的闭合符链；构图：链式串接；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 3 行第 4 张「太虚咒」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「五行环破开一面铁壁盾」或「斜剑斩落一颗坠星」。
格 12（第 4 行第 3 格 / r4c3）→ card_zhanxing｜唯一母题：斜剑斩落一颗坠星；主体剪影：斜剑与带尾迹的坠星；构图：斜向对角线；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 3 行第 3 张「星晨变」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「三枚符环相扣成链且末端重接」或「磨石上淬出一道笔直火花的剑刃」。

【格位与画法的强制关系】12 格共用同一套克制画法与第一基准；每格只换中心母题，#12161F 墨底 / 大面积留白 / 亮阶硬边高光 / 1px 纯黑硬描边保持一致。圆环只在母题本身是环 / 阵时才画，星点最多 2–4 枚。禁止把 12 格画成一张连续大场景，禁止元素跨格，禁止画格线或格号。
【输出】单张 1536×1024 不透明 PNG，命名 sheet-01.png；画面内无任何文字与编号。
```

### Group 1 · English (copy as one block)
<!-- sheet-01:en -->
```text
A 12-cell contact sheet of card illustrations for a 2D eastern-xianxia pixel game. One opaque 1536x1024 landscape PNG. Divide the whole canvas into EXACTLY 3 columns x 4 rows = 12 equal horizontal cells of 512x256 px each. Cell order is top-to-bottom, and within each row left-to-right: 01 = row1/col1, 04 = row2/col1, 12 = row4/col3. No outer margin, no outer frame.

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
Secondary references (palette / brush / glyph density only): previews/ui/00-anchor-gpt-image2_palette24.png, previews/ui/08-icons-gpt-image2_palette24.png; 24-color-snapped version: previews/ui/07-codex-gpt-image2_palette24.png.

12-CELL LIST - THE ONLY CONTENT SPEC FOR THIS SHEET; it overrides the reference image and every style note above. One UNIQUE picture per cell, strict 1:1 order, do not reorder or merge motifs:
NEVER COPY THE REFERENCE. Each cited 07-codex sample is used ONLY for line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif. Do not bring any of the 16 sample-card symbols into this sheet.
Cell 01 (row 1, col 1 / r1c1) -> card_jianfeng: motif = a blade quenched on a whetstone throwing one straight spark line; silhouette = 斜置长剑与一道直线火花; composition = diagonal; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r1c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a diagonal sword cutting down a falling star" or "one sword splitting into two symmetric beams with conserved total light".
Cell 02 (row 1, col 2 / r1c2) -> card_poyun: motif = one sword splitting into two symmetric beams with conserved total light; silhouette = 对称双剑与中间断开的剑柄; composition = symmetry; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r1c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a blade quenched on a whetstone throwing one straight spark line" or "two thunder columns landing on a redrawn talisman seal".
Cell 03 (row 1, col 3 / r1c3) -> card_leizhuan: motif = two thunder columns landing on a redrawn talisman seal; silhouette = 双雷柱与方形符篆; composition = vertical; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r3c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "one sword splitting into two symmetric beams with conserved total light" or "a pill furnace erupting with fire tongues curling back onto itself".
Cell 04 (row 2, col 1 / r2c1) -> card_danbao: motif = a pill furnace erupting with fire tongues curling back onto itself; silhouette = 圆腹丹炉与回卷火舌; composition = radial; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r4c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "two thunder columns landing on a redrawn talisman seal" or "talisman papers overprinted into a square formation".
Cell 05 (row 2, col 2 / r2c2) -> card_fuzhen: motif = talisman papers overprinted into a square formation; silhouette = 四张错叠符纸组成的方阵; composition = grid; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r3c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a pill furnace erupting with fire tongues curling back onto itself" or "three ascending concentric arcs of a fist shockwave".
Cell 06 (row 2, col 3 / r2c3) -> card_quanfeng: motif = three ascending concentric arcs of a fist shockwave; silhouette = 三道由小到大的同心弧; composition = arc; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r1c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "talisman papers overprinted into a square formation" or "a leaf whose left half turns into a blade".
Cell 07 (row 3, col 1 / r3c1) -> card_huiling: motif = a leaf whose left half turns into a blade; silhouette = 半叶半刃的同体剪影; composition = split; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r1c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "three ascending concentric arcs of a fist shockwave" or "a vajra barrier shattering into a fan-shaped shockwave".
Cell 08 (row 3, col 2 / r3c2) -> card_jingang: motif = a vajra barrier shattering into a fan-shaped shockwave; silhouette = 破裂钟罩与扇形碎片; composition = fan; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r1c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a leaf whose left half turns into a blade" or "one sword piercing horizontally through a row of enemy silhouettes".
Cell 09 (row 3, col 3 / r3c3) -> card_jianyi: motif = one sword piercing horizontally through a row of enemy silhouettes; silhouette = 长直剑与三个被贯穿的剪影; composition = pierce; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r1c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a vajra barrier shattering into a fan-shaped shockwave" or "a five-element ring cracking an iron-wall shield".
Cell 10 (row 4, col 1 / r4c1) -> card_wuxing: motif = a five-element ring cracking an iron-wall shield; silhouette = 五段色环与裂开的方盾; composition = ring; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r2c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "one sword piercing horizontally through a row of enemy silhouettes" or "three talisman rings chained together with the end re-linking".
Cell 11 (row 4, col 2 / r4c2) -> card_lianhuan: motif = three talisman rings chained together with the end re-linking; silhouette = 三环相扣的闭合符链; composition = chain; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r3c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a five-element ring cracking an iron-wall shield" or "a diagonal sword cutting down a falling star".
Cell 12 (row 4, col 3 / r4c3) -> card_zhanxing: motif = a diagonal sword cutting down a falling star; silhouette = 斜剑与带尾迹的坠星; composition = diagonal; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r3c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "three talisman rings chained together with the end re-linking" or "a blade quenched on a whetstone throwing one straight spark line".

HARD RULE: all 12 cells share the same RESTRAINED painting method and the single primary 07-codex reference; only the central motif changes per cell. Keep #12161F ink ground, generous negative space, bright-step hard highlights and 1px black outlines identical. Draw a ring ONLY when the motif itself is a ring/array, and never more than 2-4 star points. Never merge the 12 cells into one continuous scene, never let an element cross a cell boundary, never draw grid lines or cell numbers.
Output: one opaque 1536x1024 PNG named sheet-01.png, with no text or numbers anywhere.
```

---

## 第 2 组（第 2 / 6 次生成）· ② 属性提升（青玉主调）

> 类别 `attr` · 12 张卡 = 1 张 1536×1024 拼版（3 列 × 4 行）。
> **【命名】sheet-02.png** → 放 `previews/card_art_sheets/`。裁剪由 `tools/split_card_art_sheets.py` 完成，你不用切图。

### 第 2 组 · 中文提示词（整段复制）
<!-- sheet-02:zh -->
```text
东方修真题材 2D 像素游戏「卡牌插画拼版」，单张 1536×1024 不透明 PNG 横版。整图严格分成 3 列 × 4 行 = 12 个等大横格，每格 512×256 像素；格位按「从上到下、每行从左到右」编号 01–12（01=第1行第1格，04=第2行第1格，12=第4行第3格）。整图不留白边、不加外框。

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
辅助参考（只取色板 / 笔触 / 纹样密度）：previews/ui/00-anchor-gpt-image2_palette24.png、previews/ui/08-icons-gpt-image2_palette24.png；24 色吸附版为 previews/ui/07-codex-gpt-image2_palette24.png。

【12 格逐格清单 · 本拼版唯一的内容依据，优先级高于参考图与上方所有风格说明】格号 → 唯一画面，严格一一对应，不要调换顺序或合并母题。
【严禁照抄参考图】每格引用的 07-codex 示意卡只用来对齐线条密度、留白比例与色阶节奏；示意卡里画的具体符号一律不要画，主体形状必须按本格母题重新设计。不得把参考图里 16 张示意卡的任何一张搬进本拼版。
格 01（第 1 行第 1 格 / r1c1）→ card_cuijing｜唯一母题：一点精光在晶体内向内收束；主体剪影：尖顶晶体与中心一点；构图：单点收束；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 3 行第 2 张「玄冰诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「三枚魂魄层叠且最外层正在剥落」或「一粒丹丸在掌心凝成实圆」。
格 02（第 1 行第 2 格 / r1c2）→ card_ningdan｜唯一母题：一粒丹丸在掌心凝成实圆；主体剪影：正圆丹丸与托起的掌心；构图：正圆居中；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 2 行第 2 张「炼丹术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一点精光在晶体内向内收束」或「灵脉河道由一分为三地拓宽」。
格 03（第 1 行第 3 格 / r1c3）→ card_lingmai｜唯一母题：灵脉河道由一分为三地拓宽；主体剪影：分岔成三股的河道；构图：分岔生长；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 1 行第 1 张「清风诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一粒丹丸在掌心凝成实圆」或「步摇坠饰摆出的一道垂弧轨迹」。
格 04（第 2 行第 1 格 / r2c1）→ card_buyao｜唯一母题：步摇坠饰摆出的一道垂弧轨迹；主体剪影：细链垂坠与弧形残影；构图：垂摆弧线；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 2 行第 2 张「炼丹术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「灵脉河道由一分为三地拓宽」或「四片铁甲错位叠成硬边方块」。
格 05（第 2 行第 2 格 / r2c2）→ card_tiepi｜唯一母题：四片铁甲错位叠成硬边方块；主体剪影：四层错位叠甲方片；构图：层叠堆积；主色段：墨 #12161F / #2A3140 / #4A5568；画法样板：07-codex 第 3 行第 2 张「玄冰诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「步摇坠饰摆出的一道垂弧轨迹」或「靶心正中一点被放大命中」。
格 06（第 2 行第 3 格 / r2c3）→ card_huixin｜唯一母题：靶心正中一点被放大命中；主体剪影：同心靶环与放大的中心点；构图：靶心聚焦；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 1 行第 2 张「金光术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「四片铁甲错位叠成硬边方块」或「一道直线劈开封闭的边界方框」。
格 07（第 3 行第 1 格 / r3c1）→ card_poyu｜唯一母题：一道直线劈开封闭的边界方框；主体剪影：断开的方框与一道直线；构图：中缝对分；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 1 行第 4 张「御剑术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「靶心正中一点被放大命中」或「寿桃上多出一道减损刻痕」。
格 08（第 3 行第 2 格 / r3c2）→ card_shouyuan｜唯一母题：寿桃上多出一道减损刻痕；主体剪影：桃形静物与斜刻痕；构图：静物正面；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 2 行第 2 张「炼丹术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一道直线劈开封闭的边界方框」或「一根羽毛逆风上扬」。
格 09（第 3 行第 3 格 / r3c3）→ card_qingling｜唯一母题：一根羽毛逆风上扬；主体剪影：上扬羽片与三道风线；构图：上扬抬升；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 1 行第 3 张「回春术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「寿桃上多出一道减损刻痕」或「脱战后气息汇成一圈静环」。
格 10（第 4 行第 1 格 / r4c1）→ card_juxi｜唯一母题：脱战后气息汇成一圈静环；主体剪影：闭合气息环与静止符号；构图：闭合环；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 2 行第 1 张「聚灵阵」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一根羽毛逆风上扬」或「一件装备在砧上被重铸成方坯」。
格 11（第 4 行第 2 格 / r4c2）→ card_zhongzhu｜唯一母题：一件装备在砧上被重铸成方坯；主体剪影：铁砧与方形坯料；构图：砧上锻打；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 1 行第 2 张「金光术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「脱战后气息汇成一圈静环」或「三枚魂魄层叠且最外层正在剥落」。
格 12（第 4 行第 3 格 / r4c3）→ card_jingpo｜唯一母题：三枚魂魄层叠且最外层正在剥落；主体剪影：三层魂环与剥落的一角；构图：逐层剥离；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 3 行第 4 张「太虚咒」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一件装备在砧上被重铸成方坯」或「一点精光在晶体内向内收束」。

【格位与画法的强制关系】12 格共用同一套克制画法与第一基准；每格只换中心母题，#12161F 墨底 / 大面积留白 / 亮阶硬边高光 / 1px 纯黑硬描边保持一致。圆环只在母题本身是环 / 阵时才画，星点最多 2–4 枚。禁止把 12 格画成一张连续大场景，禁止元素跨格，禁止画格线或格号。
【输出】单张 1536×1024 不透明 PNG，命名 sheet-02.png；画面内无任何文字与编号。
```

### Group 2 · English (copy as one block)
<!-- sheet-02:en -->
```text
A 12-cell contact sheet of card illustrations for a 2D eastern-xianxia pixel game. One opaque 1536x1024 landscape PNG. Divide the whole canvas into EXACTLY 3 columns x 4 rows = 12 equal horizontal cells of 512x256 px each. Cell order is top-to-bottom, and within each row left-to-right: 01 = row1/col1, 04 = row2/col1, 12 = row4/col3. No outer margin, no outer frame.

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
Secondary references (palette / brush / glyph density only): previews/ui/00-anchor-gpt-image2_palette24.png, previews/ui/08-icons-gpt-image2_palette24.png; 24-color-snapped version: previews/ui/07-codex-gpt-image2_palette24.png.

12-CELL LIST - THE ONLY CONTENT SPEC FOR THIS SHEET; it overrides the reference image and every style note above. One UNIQUE picture per cell, strict 1:1 order, do not reorder or merge motifs:
NEVER COPY THE REFERENCE. Each cited 07-codex sample is used ONLY for line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif. Do not bring any of the 16 sample-card symbols into this sheet.
Cell 01 (row 1, col 1 / r1c1) -> card_cuijing: motif = a single glint converging inward inside a crystal; silhouette = 尖顶晶体与中心一点; composition = point; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r3c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "three soul layers stacked with the outermost peeling away" or "a pill pellet condensing into a solid circle above a palm".
Cell 02 (row 1, col 2 / r1c2) -> card_ningdan: motif = a pill pellet condensing into a solid circle above a palm; silhouette = 正圆丹丸与托起的掌心; composition = circle; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r2c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a single glint converging inward inside a crystal" or "a spirit-vein river widening from one channel into three".
Cell 03 (row 1, col 3 / r1c3) -> card_lingmai: motif = a spirit-vein river widening from one channel into three; silhouette = 分岔成三股的河道; composition = branch; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r1c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a pill pellet condensing into a solid circle above a palm" or "a hanging hairpin pendant tracing one swaying arc".
Cell 04 (row 2, col 1 / r2c1) -> card_buyao: motif = a hanging hairpin pendant tracing one swaying arc; silhouette = 细链垂坠与弧形残影; composition = swing; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r2c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a spirit-vein river widening from one channel into three" or "four iron plates offset-stacked into a hard-edged square".
Cell 05 (row 2, col 2 / r2c2) -> card_tiepi: motif = four iron plates offset-stacked into a hard-edged square; silhouette = 四层错位叠甲方片; composition = stack; focal band = ink #12161F / #2A3140 / #4A5568; style sample = 07-codex r3c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a hanging hairpin pendant tracing one swaying arc" or "a bullseye center point enlarged on impact".
Cell 06 (row 2, col 3 / r2c3) -> card_huixin: motif = a bullseye center point enlarged on impact; silhouette = 同心靶环与放大的中心点; composition = target; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r1c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "four iron plates offset-stacked into a hard-edged square" or "one straight line splitting a closed boundary frame".
Cell 07 (row 3, col 1 / r3c1) -> card_poyu: motif = one straight line splitting a closed boundary frame; silhouette = 断开的方框与一道直线; composition = split; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r1c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a bullseye center point enlarged on impact" or "a longevity peach marked with one subtractive notch".
Cell 08 (row 3, col 2 / r3c2) -> card_shouyuan: motif = a longevity peach marked with one subtractive notch; silhouette = 桃形静物与斜刻痕; composition = still; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r2c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "one straight line splitting a closed boundary frame" or "a single feather lifting against the wind".
Cell 09 (row 3, col 3 / r3c3) -> card_qingling: motif = a single feather lifting against the wind; silhouette = 上扬羽片与三道风线; composition = lift; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r1c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a longevity peach marked with one subtractive notch" or "breath gathering into one still ring after combat".
Cell 10 (row 4, col 1 / r4c1) -> card_juxi: motif = breath gathering into one still ring after combat; silhouette = 闭合气息环与静止符号; composition = ring; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r2c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a single feather lifting against the wind" or "a piece of gear recast into a square billet on an anvil".
Cell 11 (row 4, col 2 / r4c2) -> card_zhongzhu: motif = a piece of gear recast into a square billet on an anvil; silhouette = 铁砧与方形坯料; composition = forge; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r1c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "breath gathering into one still ring after combat" or "three soul layers stacked with the outermost peeling away".
Cell 12 (row 4, col 3 / r4c3) -> card_jingpo: motif = three soul layers stacked with the outermost peeling away; silhouette = 三层魂环与剥落的一角; composition = peel; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r3c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a piece of gear recast into a square billet on an anvil" or "a single glint converging inward inside a crystal".

HARD RULE: all 12 cells share the same RESTRAINED painting method and the single primary 07-codex reference; only the central motif changes per cell. Keep #12161F ink ground, generous negative space, bright-step hard highlights and 1px black outlines identical. Draw a ring ONLY when the motif itself is a ring/array, and never more than 2-4 star points. Never merge the 12 cells into one continuous scene, never let an element cross a cell boundary, never draw grid lines or cell numbers.
Output: one opaque 1536x1024 PNG named sheet-02.png, with no text or numbers anywhere.
```

---

## 第 3 组（第 3 / 6 次生成）· ③ 机制改变（紫主调）

> 类别 `mech` · 12 张卡 = 1 张 1536×1024 拼版（3 列 × 4 行）。
> **【命名】sheet-03.png** → 放 `previews/card_art_sheets/`。裁剪由 `tools/split_card_art_sheets.py` 完成，你不用切图。

### 第 3 组 · 中文提示词（整段复制）
<!-- sheet-03:zh -->
```text
东方修真题材 2D 像素游戏「卡牌插画拼版」，单张 1536×1024 不透明 PNG 横版。整图严格分成 3 列 × 4 行 = 12 个等大横格，每格 512×256 像素；格位按「从上到下、每行从左到右」编号 01–12（01=第1行第1格，04=第2行第1格，12=第4行第3格）。整图不留白边、不加外框。

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
辅助参考（只取色板 / 笔触 / 纹样密度）：previews/ui/00-anchor-gpt-image2_palette24.png、previews/ui/08-icons-gpt-image2_palette24.png；24 色吸附版为 previews/ui/07-codex-gpt-image2_palette24.png。

【12 格逐格清单 · 本拼版唯一的内容依据，优先级高于参考图与上方所有风格说明】格号 → 唯一画面，严格一一对应，不要调换顺序或合并母题。
【严禁照抄参考图】每格引用的 07-codex 示意卡只用来对齐线条密度、留白比例与色阶节奏；示意卡里画的具体符号一律不要画，主体形状必须按本格母题重新设计。不得把参考图里 16 张示意卡的任何一张搬进本拼版。
格 01（第 1 行第 1 格 / r1c1）→ card_nianzhuan｜唯一母题：击杀符号倒转成为命中符号；主体剪影：首尾互指的双向箭头；构图：双向倒转；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 1 行第 1 张「清风诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「两枚道途目标同挂并被边界钳住」或「两个技能槽之间的换位箭头」。
格 02（第 1 行第 2 格 / r1c2）→ card_huanshi｜唯一母题：两个技能槽之间的换位箭头；主体剪影：两格槽位与交叉换位箭头；构图：换位交错；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 3 行第 4 张「太虚咒」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「击杀符号倒转成为命中符号」或「两道流派标签并在一枚主印上」。
格 03（第 1 行第 3 格 / r1c3）→ card_shuangxiu｜唯一母题：两道流派标签并在一枚主印上；主体剪影：双印叠合且一印压前一印；构图：双体并列；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 4 行第 3 张「混沌诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「两个技能槽之间的换位箭头」或「边移动边出招的三段残影」。
格 04（第 2 行第 1 格 / r2c1）→ card_yuqi｜唯一母题：边移动边出招的三段残影；主体剪影：三级递进的人形残影；构图：移动残影；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 2 行第 4 张「风行术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「两道流派标签并在一枚主印上」或「技能顺序被重排的序号轨道」。
格 05（第 2 行第 2 格 / r2c2）→ card_daoyin｜唯一母题：技能顺序被重排的序号轨道；主体剪影：带序号刻度的弯曲轨道；构图：序号轨道；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 3 行第 4 张「太虚咒」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「边移动边出招的三段残影」或「一枚印章封住旧卡并腾出空位」。
格 06（第 2 行第 3 格 / r2c3）→ card_jieyin｜唯一母题：一枚印章封住旧卡并腾出空位；主体剪影：朱印与空出的卡位；构图：封印留空；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 4 行第 2 张「天罚劫」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「技能顺序被重排的序号轨道」或「两张候选被撑开成三张」。
格 07（第 3 行第 1 格 / r3c1）→ card_wuxiangpo｜唯一母题：两张候选被撑开成三张；主体剪影：二到三的展开扇形；构图：向外撑开；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 1 行第 2 张「金光术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一枚印章封住旧卡并腾出空位」或「令旗悬在免费一次的铁砧上」。
格 08（第 3 行第 2 格 / r3c2）→ card_chongzhu｜唯一母题：令旗悬在免费一次的铁砧上；主体剪影：垂挂令旗与砧台；构图：令旗垂挂；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 1 行第 2 张「金光术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「两张候选被撑开成三张」或「进层前显影敌人构成的卷轴」。
格 09（第 3 行第 3 格 / r3c3）→ card_tianren｜唯一母题：进层前显影敌人构成的卷轴；主体剪影：展开卷轴与三枚敌人剪影；构图：卷轴展读；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 3 行第 3 张「星晨变」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「令旗悬在免费一次的铁砧上」或「舍利子复活一次后卡牌流断开」。
格 10（第 4 行第 1 格 / r4c1）→ card_sheli｜唯一母题：舍利子复活一次后卡牌流断开；主体剪影：舍利圆珠与断开的卡流；构图：静物正面；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 2 行第 1 张「聚灵阵」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「进层前显影敌人构成的卷轴」或「两条灵韵候选汇成一条固化」。
格 11（第 4 行第 2 格 / r4c2）→ card_lunhui｜唯一母题：两条灵韵候选汇成一条固化；主体剪影：双流归一的分岔合流；构图：双流归一；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 1 行第 1 张「清风诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「舍利子复活一次后卡牌流断开」或「两枚道途目标同挂并被边界钳住」。
格 12（第 4 行第 3 格 / r4c3）→ card_pojing｜唯一母题：两枚道途目标同挂并被边界钳住；主体剪影：双目标牌与上下界横线；构图：边界钳制；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 4 行第 2 张「天罚劫」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「两条灵韵候选汇成一条固化」或「击杀符号倒转成为命中符号」。

【格位与画法的强制关系】12 格共用同一套克制画法与第一基准；每格只换中心母题，#12161F 墨底 / 大面积留白 / 亮阶硬边高光 / 1px 纯黑硬描边保持一致。圆环只在母题本身是环 / 阵时才画，星点最多 2–4 枚。禁止把 12 格画成一张连续大场景，禁止元素跨格，禁止画格线或格号。
【输出】单张 1536×1024 不透明 PNG，命名 sheet-03.png；画面内无任何文字与编号。
```

### Group 3 · English (copy as one block)
<!-- sheet-03:en -->
```text
A 12-cell contact sheet of card illustrations for a 2D eastern-xianxia pixel game. One opaque 1536x1024 landscape PNG. Divide the whole canvas into EXACTLY 3 columns x 4 rows = 12 equal horizontal cells of 512x256 px each. Cell order is top-to-bottom, and within each row left-to-right: 01 = row1/col1, 04 = row2/col1, 12 = row4/col3. No outer margin, no outer frame.

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
Secondary references (palette / brush / glyph density only): previews/ui/00-anchor-gpt-image2_palette24.png, previews/ui/08-icons-gpt-image2_palette24.png; 24-color-snapped version: previews/ui/07-codex-gpt-image2_palette24.png.

12-CELL LIST - THE ONLY CONTENT SPEC FOR THIS SHEET; it overrides the reference image and every style note above. One UNIQUE picture per cell, strict 1:1 order, do not reorder or merge motifs:
NEVER COPY THE REFERENCE. Each cited 07-codex sample is used ONLY for line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif. Do not bring any of the 16 sample-card symbols into this sheet.
Cell 01 (row 1, col 1 / r1c1) -> card_nianzhuan: motif = a kill glyph reversing into an on-hit glyph; silhouette = 首尾互指的双向箭头; composition = reverse; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r1c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "two path goals hanging together inside a clamped boundary" or "two skill slots exchanging places along crossed arrows".
Cell 02 (row 1, col 2 / r1c2) -> card_huanshi: motif = two skill slots exchanging places along crossed arrows; silhouette = 两格槽位与交叉换位箭头; composition = swap; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r3c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a kill glyph reversing into an on-hit glyph" or "two school tags merging onto one dominant seal".
Cell 03 (row 1, col 3 / r1c3) -> card_shuangxiu: motif = two school tags merging onto one dominant seal; silhouette = 双印叠合且一印压前一印; composition = dual; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r4c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "two skill slots exchanging places along crossed arrows" or "three motion afterimages of casting while moving".
Cell 04 (row 2, col 1 / r2c1) -> card_yuqi: motif = three motion afterimages of casting while moving; silhouette = 三级递进的人形残影; composition = motion; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r2c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "two school tags merging onto one dominant seal" or "a reordered sequence track of skill slots".
Cell 05 (row 2, col 2 / r2c2) -> card_daoyin: motif = a reordered sequence track of skill slots; silhouette = 带序号刻度的弯曲轨道; composition = sequence; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r3c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "three motion afterimages of casting while moving" or "a seal stamping an old card away and leaving an empty slot".
Cell 06 (row 2, col 3 / r2c3) -> card_jieyin: motif = a seal stamping an old card away and leaving an empty slot; silhouette = 朱印与空出的卡位; composition = seal; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r4c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a reordered sequence track of skill slots" or "two candidate cards being pushed apart into three".
Cell 07 (row 3, col 1 / r3c1) -> card_wuxiangpo: motif = two candidate cards being pushed apart into three; silhouette = 二到三的展开扇形; composition = expand; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r1c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a seal stamping an old card away and leaving an empty slot" or "a command banner hanging above a free-use anvil".
Cell 08 (row 3, col 2 / r3c2) -> card_chongzhu: motif = a command banner hanging above a free-use anvil; silhouette = 垂挂令旗与砧台; composition = banner; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r1c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "two candidate cards being pushed apart into three" or "a scroll revealing the enemy lineup before entering a floor".
Cell 09 (row 3, col 3 / r3c3) -> card_tianren: motif = a scroll revealing the enemy lineup before entering a floor; silhouette = 展开卷轴与三枚敌人剪影; composition = scroll; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r3c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a command banner hanging above a free-use anvil" or "a relic reviving once while the card stream is cut".
Cell 10 (row 4, col 1 / r4c1) -> card_sheli: motif = a relic reviving once while the card stream is cut; silhouette = 舍利圆珠与断开的卡流; composition = still; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r2c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a scroll revealing the enemy lineup before entering a floor" or "two legacy candidate streams merging into one fixed line".
Cell 11 (row 4, col 2 / r4c2) -> card_lunhui: motif = two legacy candidate streams merging into one fixed line; silhouette = 双流归一的分岔合流; composition = merge; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r1c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a relic reviving once while the card stream is cut" or "two path goals hanging together inside a clamped boundary".
Cell 12 (row 4, col 3 / r4c3) -> card_pojing: motif = two path goals hanging together inside a clamped boundary; silhouette = 双目标牌与上下界横线; composition = clamp; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r4c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "two legacy candidate streams merging into one fixed line" or "a kill glyph reversing into an on-hit glyph".

HARD RULE: all 12 cells share the same RESTRAINED painting method and the single primary 07-codex reference; only the central motif changes per cell. Keep #12161F ink ground, generous negative space, bright-step hard highlights and 1px black outlines identical. Draw a ring ONLY when the motif itself is a ring/array, and never more than 2-4 star points. Never merge the 12 cells into one continuous scene, never let an element cross a cell boundary, never draw grid lines or cell numbers.
Output: one opaque 1536x1024 PNG named sheet-03.png, with no text or numbers anywhere.
```

---

## 第 4 组（第 4 / 6 次生成）· ④ 资源灵力（金主调）

> 类别 `res` · 12 张卡 = 1 张 1536×1024 拼版（3 列 × 4 行）。
> **【命名】sheet-04.png** → 放 `previews/card_art_sheets/`。裁剪由 `tools/split_card_art_sheets.py` 完成，你不用切图。

### 第 4 组 · 中文提示词（整段复制）
<!-- sheet-04:zh -->
```text
东方修真题材 2D 像素游戏「卡牌插画拼版」，单张 1536×1024 不透明 PNG 横版。整图严格分成 3 列 × 4 行 = 12 个等大横格，每格 512×256 像素；格位按「从上到下、每行从左到右」编号 01–12（01=第1行第1格，04=第2行第1格，12=第4行第3格）。整图不留白边、不加外框。

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
辅助参考（只取色板 / 笔触 / 纹样密度）：previews/ui/00-anchor-gpt-image2_palette24.png、previews/ui/08-icons-gpt-image2_palette24.png；24 色吸附版为 previews/ui/07-codex-gpt-image2_palette24.png。

【12 格逐格清单 · 本拼版唯一的内容依据，优先级高于参考图与上方所有风格说明】格号 → 唯一画面，严格一一对应，不要调换顺序或合并母题。
【严禁照抄参考图】每格引用的 07-codex 示意卡只用来对齐线条密度、留白比例与色阶节奏；示意卡里画的具体符号一律不要画，主体形状必须按本格母题重新设计。不得把参考图里 16 张示意卡的任何一张搬进本拼版。
格 01（第 1 行第 1 格 / r1c1）→ card_juling｜唯一母题：击杀魂火汇入阵眼；主体剪影：八角阵眼与四缕魂火；构图：中心放射；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 2 行第 1 张「聚灵阵」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「三枚印叠满后一次引爆」或「灵力漏斗被收窄一格」。
格 02（第 1 行第 2 格 / r1c2）→ card_shengxi｜唯一母题：灵力漏斗被收窄一格；主体剪影：上宽下窄的收口漏斗；构图：漏斗收窄；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 2 行第 2 张「炼丹术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「击杀魂火汇入阵眼」或「刻度瓶按层回灌四分之一」。
格 03（第 1 行第 3 格 / r1c3）→ card_huanling｜唯一母题：刻度瓶按层回灌四分之一；主体剪影：带四格刻度的灵力瓶；构图：刻度容器；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 2 行第 2 张「炼丹术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「灵力漏斗被收窄一格」或「一缕丹香替下半份灵耗」。
格 04（第 2 行第 1 格 / r2c1）→ card_danxiang｜唯一母题：一缕丹香替下半份灵耗；主体剪影：细长上升的香缕；构图：细缕上升；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 1 行第 3 张「回春术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「刻度瓶按层回灌四分之一」或「满潮浪头托起一次不耗灵的出招」。
格 05（第 2 行第 2 格 / r2c2）→ card_lingchao｜唯一母题：满潮浪头托起一次不耗灵的出招；主体剪影：翻卷浪头与托起的剑光；构图：浪头翻卷；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 1 行第 1 张「清风诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一缕丹香替下半份灵耗」或「受击瞬间截下四点灵光」。
格 06（第 2 行第 3 格 / r2c3）→ card_jieqi｜唯一母题：受击瞬间截下四点灵光；主体剪影：四个等距光点与一道斜截线；构图：散点计数；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 3 行第 3 张「星晨变」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「满潮浪头托起一次不耗灵的出招」或「空盏杯底最后一滴被放大」。
格 07（第 3 行第 1 格 / r3c1）→ card_kongzhan｜唯一母题：空盏杯底最后一滴被放大；主体剪影：空杯与杯底一滴；构图：空器留白；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 2 行第 2 张「炼丹术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「受击瞬间截下四点灵光」或「溢出的灵力反卷成一层护盾」。
格 08（第 3 行第 2 格 / r3c2）→ card_fanyong｜唯一母题：溢出的灵力反卷成一层护盾；主体剪影：反卷液流与弧形盾面；构图：反卷回旋；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 2 行第 1 张「聚灵阵」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「空盏杯底最后一滴被放大」或「三珠连成一线后第六点回灵」。
格 09（第 3 行第 3 格 / r3c3）→ card_zhulian｜唯一母题：三珠连成一线后第六点回灵；主体剪影：三珠串线与末端一点；构图：链式串接；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 3 行第 4 张「太虚咒」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「溢出的灵力反卷成一层护盾」或「无根之木被削去两成灵力」。
格 10（第 4 行第 1 格 / r4c1）→ card_wugen｜唯一母题：无根之木被削去两成灵力；主体剪影：断根树形与削去的缺口；构图：静物正面；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 1 行第 3 张「回春术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「三珠连成一线后第六点回灵」或「每层首杀落下六枚灵石」。
格 11（第 4 行第 2 格 / r4c2）→ card_tianlu｜唯一母题：每层首杀落下六枚灵石；主体剪影：六枚下坠方石；构图：自上坠落；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 3 行第 3 张「星晨变」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「无根之木被削去两成灵力」或「三枚印叠满后一次引爆」。
格 12（第 4 行第 3 格 / r4c3）→ card_shouyin｜唯一母题：三枚印叠满后一次引爆；主体剪影：三枚叠印与一次放射；构图：一次引爆；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 4 行第 3 张「混沌诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「每层首杀落下六枚灵石」或「击杀魂火汇入阵眼」。

【格位与画法的强制关系】12 格共用同一套克制画法与第一基准；每格只换中心母题，#12161F 墨底 / 大面积留白 / 亮阶硬边高光 / 1px 纯黑硬描边保持一致。圆环只在母题本身是环 / 阵时才画，星点最多 2–4 枚。禁止把 12 格画成一张连续大场景，禁止元素跨格，禁止画格线或格号。
【输出】单张 1536×1024 不透明 PNG，命名 sheet-04.png；画面内无任何文字与编号。
```

### Group 4 · English (copy as one block)
<!-- sheet-04:en -->
```text
A 12-cell contact sheet of card illustrations for a 2D eastern-xianxia pixel game. One opaque 1536x1024 landscape PNG. Divide the whole canvas into EXACTLY 3 columns x 4 rows = 12 equal horizontal cells of 512x256 px each. Cell order is top-to-bottom, and within each row left-to-right: 01 = row1/col1, 04 = row2/col1, 12 = row4/col3. No outer margin, no outer frame.

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
Secondary references (palette / brush / glyph density only): previews/ui/00-anchor-gpt-image2_palette24.png, previews/ui/08-icons-gpt-image2_palette24.png; 24-color-snapped version: previews/ui/07-codex-gpt-image2_palette24.png.

12-CELL LIST - THE ONLY CONTENT SPEC FOR THIS SHEET; it overrides the reference image and every style note above. One UNIQUE picture per cell, strict 1:1 order, do not reorder or merge motifs:
NEVER COPY THE REFERENCE. Each cited 07-codex sample is used ONLY for line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif. Do not bring any of the 16 sample-card symbols into this sheet.
Cell 01 (row 1, col 1 / r1c1) -> card_juling: motif = kill flames converging into an array eye; silhouette = 八角阵眼与四缕魂火; composition = radial; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r2c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "three seals stacking to a single detonation" or "a spirit funnel narrowed by one notch".
Cell 02 (row 1, col 2 / r1c2) -> card_shengxi: motif = a spirit funnel narrowed by one notch; silhouette = 上宽下窄的收口漏斗; composition = funnel; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r2c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "kill flames converging into an array eye" or "a graduated flask refilled by one quarter per floor".
Cell 03 (row 1, col 3 / r1c3) -> card_huanling: motif = a graduated flask refilled by one quarter per floor; silhouette = 带四格刻度的灵力瓶; composition = gauge; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r2c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a spirit funnel narrowed by one notch" or "one wisp of pill incense replacing half the spirit cost".
Cell 04 (row 2, col 1 / r2c1) -> card_danxiang: motif = one wisp of pill incense replacing half the spirit cost; silhouette = 细长上升的香缕; composition = wisp; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r1c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a graduated flask refilled by one quarter per floor" or "a full-tide wave crest carrying one free cast".
Cell 05 (row 2, col 2 / r2c2) -> card_lingchao: motif = a full-tide wave crest carrying one free cast; silhouette = 翻卷浪头与托起的剑光; composition = wave; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r1c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "one wisp of pill incense replacing half the spirit cost" or "four spirit sparks intercepted at the moment of being hit".
Cell 06 (row 2, col 3 / r2c3) -> card_jieqi: motif = four spirit sparks intercepted at the moment of being hit; silhouette = 四个等距光点与一道斜截线; composition = dots; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r3c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a full-tide wave crest carrying one free cast" or "the last drop in an empty cup enlarged".
Cell 07 (row 3, col 1 / r3c1) -> card_kongzhan: motif = the last drop in an empty cup enlarged; silhouette = 空杯与杯底一滴; composition = vessel; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r2c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "four spirit sparks intercepted at the moment of being hit" or "overflowing spirit curling back into a shield".
Cell 08 (row 3, col 2 / r3c2) -> card_fanyong: motif = overflowing spirit curling back into a shield; silhouette = 反卷液流与弧形盾面; composition = curl; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r2c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "the last drop in an empty cup enlarged" or "three beads in a line with a sixth returning spark".
Cell 09 (row 3, col 3 / r3c3) -> card_zhulian: motif = three beads in a line with a sixth returning spark; silhouette = 三珠串线与末端一点; composition = chain; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r3c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "overflowing spirit curling back into a shield" or "a rootless tree with one fifth of its spirit cut away".
Cell 10 (row 4, col 1 / r4c1) -> card_wugen: motif = a rootless tree with one fifth of its spirit cut away; silhouette = 断根树形与削去的缺口; composition = still; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r1c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "three beads in a line with a sixth returning spark" or "six spirit stones dropping from the first kill of a floor".
Cell 11 (row 4, col 2 / r4c2) -> card_tianlu: motif = six spirit stones dropping from the first kill of a floor; silhouette = 六枚下坠方石; composition = fall; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r3c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a rootless tree with one fifth of its spirit cut away" or "three seals stacking to a single detonation".
Cell 12 (row 4, col 3 / r4c3) -> card_shouyin: motif = three seals stacking to a single detonation; silhouette = 三枚叠印与一次放射; composition = burst; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r4c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "six spirit stones dropping from the first kill of a floor" or "kill flames converging into an array eye".

HARD RULE: all 12 cells share the same RESTRAINED painting method and the single primary 07-codex reference; only the central motif changes per cell. Keep #12161F ink ground, generous negative space, bright-step hard highlights and 1px black outlines identical. Draw a ring ONLY when the motif itself is a ring/array, and never more than 2-4 star points. Never merge the 12 cells into one continuous scene, never let an element cross a cell boundary, never draw grid lines or cell numbers.
Output: one opaque 1536x1024 PNG named sheet-04.png, with no text or numbers anywhere.
```

---

## 第 5 组（第 5 / 6 次生成）· ⑤ 生存回复（青玉/淡青主调）

> 类别 `surv` · 12 张卡 = 1 张 1536×1024 拼版（3 列 × 4 行）。
> **【命名】sheet-05.png** → 放 `previews/card_art_sheets/`。裁剪由 `tools/split_card_art_sheets.py` 完成，你不用切图。

### 第 5 组 · 中文提示词（整段复制）
<!-- sheet-05:zh -->
```text
东方修真题材 2D 像素游戏「卡牌插画拼版」，单张 1536×1024 不透明 PNG 横版。整图严格分成 3 列 × 4 行 = 12 个等大横格，每格 512×256 像素；格位按「从上到下、每行从左到右」编号 01–12（01=第1行第1格，04=第2行第1格，12=第4行第3格）。整图不留白边、不加外框。

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
辅助参考（只取色板 / 笔触 / 纹样密度）：previews/ui/00-anchor-gpt-image2_palette24.png、previews/ui/08-icons-gpt-image2_palette24.png；24 色吸附版为 previews/ui/07-codex-gpt-image2_palette24.png。

【12 格逐格清单 · 本拼版唯一的内容依据，优先级高于参考图与上方所有风格说明】格号 → 唯一画面，严格一一对应，不要调换顺序或合并母题。
【严禁照抄参考图】每格引用的 07-codex 示意卡只用来对齐线条密度、留白比例与色阶节奏；示意卡里画的具体符号一律不要画，主体形状必须按本格母题重新设计。不得把参考图里 16 张示意卡的任何一张搬进本拼版。
格 01（第 1 行第 1 格 / r1c1）→ card_huichun｜唯一母题：回春光晕里舒展的新芽；主体剪影：双叶新芽与环形光晕；构图：新芽舒展；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 1 行第 3 张「回春术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「命盘被削去一角换取 CD 收缩」或「护盾值格被填满三层」。
格 02（第 1 行第 2 格 / r1c2）→ card_huti｜唯一母题：护盾值格被填满三层；主体剪影：三行方格盾槽；构图：方阵网格；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 3 行第 2 张「玄冰诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「回春光晕里舒展的新芽」或「受击后拉长的无敌时间窗」。
格 03（第 1 行第 3 格 / r1c3）→ card_bishui｜唯一母题：受击后拉长的无敌时间窗；主体剪影：被拉长的矩形时间窗；构图：窗口框定；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 2 行第 4 张「风行术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「护盾值格被填满三层」或「按层回血的断续阶梯折线」。
格 04（第 2 行第 1 格 / r2c1）→ card_duanxu｜唯一母题：按层回血的断续阶梯折线；主体剪影：三段断续上升折线；构图：阶梯折线；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 1 行第 1 张「清风诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「受击后拉长的无敌时间窗」或「纸傀儡替身挡下一击」。
格 05（第 2 行第 2 格 / r2c2）→ card_jiaren｜唯一母题：纸傀儡替身挡下一击；主体剪影：方形纸傀儡与斜来的一击；构图：替身立像；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 2 行第 3 张「化气诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「按层回血的断续阶梯折线」或「骨节外包一层铁壳的剖面」。
格 06（第 2 行第 3 格 / r2c3）→ card_tiegu｜唯一母题：骨节外包一层铁壳的剖面；主体剪影：骨节与外层铁壳剖面；构图：包壳剖面；主色段：墨 #12161F / #2A3140 / #4A5568；画法样板：07-codex 第 3 行第 2 张「玄冰诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「纸傀儡替身挡下一击」或「低血线触发自动回春的阈值门」。
格 07（第 3 行第 1 格 / r3c1）→ card_guisuo｜唯一母题：低血线触发自动回春的阈值门；主体剪影：横贯阈值线与一道门；构图：阈值门线；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 4 行第 4 张「无尽劫」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「骨节外包一层铁壳的剖面」或「静止一秒后淡入墨底的人形轮廓」。
格 08（第 3 行第 2 格 / r3c2）→ card_yinbi｜唯一母题：静止一秒后淡入墨底的人形轮廓；主体剪影：半隐人形轮廓；构图：淡入轮廓；主色段：墨 #12161F / #2A3140 / #4A5568；画法样板：07-codex 第 2 行第 3 张「化气诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「低血线触发自动回春的阈值门」或「灰烬中重生并重置的 CD 环」。
格 09（第 3 行第 3 格 / r3c3）→ card_zhuansheng｜唯一母题：灰烬中重生并重置的 CD 环；主体剪影：灰烬人形与闭合重置环；构图：灰烬重生；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 4 行第 1 张「万劫灭」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「静止一秒后淡入墨底的人形轮廓」或「叶尖一滴露水将坠未坠」。
格 10（第 4 行第 1 格 / r4c1）→ card_qinglu｜唯一母题：叶尖一滴露水将坠未坠；主体剪影：叶尖与单滴露水；构图：单滴下坠；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 2 行第 2 张「炼丹术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「灰烬中重生并重置的 CD 环」或「金刚罩内一层混元气旋」。
格 11（第 4 行第 2 格 / r4c2）→ card_hunyuan｜唯一母题：金刚罩内一层混元气旋；主体剪影：钟罩轮廓与内部气旋；构图：罩内气旋；主色段：青玉 #2F6E6A / #5FA8A0 / #9BD4CC；画法样板：07-codex 第 2 行第 1 张「聚灵阵」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「叶尖一滴露水将坠未坠」或「命盘被削去一角换取 CD 收缩」。
格 12（第 4 行第 3 格 / r4c3）→ card_sheshi｜唯一母题：命盘被削去一角换取 CD 收缩；主体剪影：缺角命盘与收缩环；构图：缺角割舍；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 4 行第 4 张「无尽劫」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「金刚罩内一层混元气旋」或「回春光晕里舒展的新芽」。

【格位与画法的强制关系】12 格共用同一套克制画法与第一基准；每格只换中心母题，#12161F 墨底 / 大面积留白 / 亮阶硬边高光 / 1px 纯黑硬描边保持一致。圆环只在母题本身是环 / 阵时才画，星点最多 2–4 枚。禁止把 12 格画成一张连续大场景，禁止元素跨格，禁止画格线或格号。
【输出】单张 1536×1024 不透明 PNG，命名 sheet-05.png；画面内无任何文字与编号。
```

### Group 5 · English (copy as one block)
<!-- sheet-05:en -->
```text
A 12-cell contact sheet of card illustrations for a 2D eastern-xianxia pixel game. One opaque 1536x1024 landscape PNG. Divide the whole canvas into EXACTLY 3 columns x 4 rows = 12 equal horizontal cells of 512x256 px each. Cell order is top-to-bottom, and within each row left-to-right: 01 = row1/col1, 04 = row2/col1, 12 = row4/col3. No outer margin, no outer frame.

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
Secondary references (palette / brush / glyph density only): previews/ui/00-anchor-gpt-image2_palette24.png, previews/ui/08-icons-gpt-image2_palette24.png; 24-color-snapped version: previews/ui/07-codex-gpt-image2_palette24.png.

12-CELL LIST - THE ONLY CONTENT SPEC FOR THIS SHEET; it overrides the reference image and every style note above. One UNIQUE picture per cell, strict 1:1 order, do not reorder or merge motifs:
NEVER COPY THE REFERENCE. Each cited 07-codex sample is used ONLY for line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif. Do not bring any of the 16 sample-card symbols into this sheet.
Cell 01 (row 1, col 1 / r1c1) -> card_huichun: motif = a new sprout unfolding inside a healing halo; silhouette = 双叶新芽与环形光晕; composition = sprout; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r1c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a life disc with one corner cut away to shorten cooldown" or "three rows of shield gauge cells filling up".
Cell 02 (row 1, col 2 / r1c2) -> card_huti: motif = three rows of shield gauge cells filling up; silhouette = 三行方格盾槽; composition = grid; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r3c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a new sprout unfolding inside a healing halo" or "an invulnerability time window stretched after a hit".
Cell 03 (row 1, col 3 / r1c3) -> card_bishui: motif = an invulnerability time window stretched after a hit; silhouette = 被拉长的矩形时间窗; composition = window; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r2c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "three rows of shield gauge cells filling up" or "a broken step line of per-floor healing".
Cell 04 (row 2, col 1 / r2c1) -> card_duanxu: motif = a broken step line of per-floor healing; silhouette = 三段断续上升折线; composition = step; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r1c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "an invulnerability time window stretched after a hit" or "a paper puppet taking a lethal hit in place".
Cell 05 (row 2, col 2 / r2c2) -> card_jiaren: motif = a paper puppet taking a lethal hit in place; silhouette = 方形纸傀儡与斜来的一击; composition = puppet; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r2c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a broken step line of per-floor healing" or "a bone joint wrapped in an iron shell, cross-section".
Cell 06 (row 2, col 3 / r2c3) -> card_tiegu: motif = a bone joint wrapped in an iron shell, cross-section; silhouette = 骨节与外层铁壳剖面; composition = armor; focal band = ink #12161F / #2A3140 / #4A5568; style sample = 07-codex r3c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a paper puppet taking a lethal hit in place" or "a threshold gate below which healing auto-triggers".
Cell 07 (row 3, col 1 / r3c1) -> card_guisuo: motif = a threshold gate below which healing auto-triggers; silhouette = 横贯阈值线与一道门; composition = threshold; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r4c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a bone joint wrapped in an iron shell, cross-section" or "a human outline fading into the ink ground after one still second".
Cell 08 (row 3, col 2 / r3c2) -> card_yinbi: motif = a human outline fading into the ink ground after one still second; silhouette = 半隐人形轮廓; composition = stealth; focal band = ink #12161F / #2A3140 / #4A5568; style sample = 07-codex r2c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a threshold gate below which healing auto-triggers" or "rebirth from ashes with a reset cooldown ring".
Cell 09 (row 3, col 3 / r3c3) -> card_zhuansheng: motif = rebirth from ashes with a reset cooldown ring; silhouette = 灰烬人形与闭合重置环; composition = rebirth; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r4c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a human outline fading into the ink ground after one still second" or "one dewdrop about to fall from a leaf tip".
Cell 10 (row 4, col 1 / r4c1) -> card_qinglu: motif = one dewdrop about to fall from a leaf tip; silhouette = 叶尖与单滴露水; composition = drop; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r2c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "rebirth from ashes with a reset cooldown ring" or "a primal vortex inside a vajra barrier".
Cell 11 (row 4, col 2 / r4c2) -> card_hunyuan: motif = a primal vortex inside a vajra barrier; silhouette = 钟罩轮廓与内部气旋; composition = vortex; focal band = jade #2F6E6A / #5FA8A0 / #9BD4CC; style sample = 07-codex r2c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "one dewdrop about to fall from a leaf tip" or "a life disc with one corner cut away to shorten cooldown".
Cell 12 (row 4, col 3 / r4c3) -> card_sheshi: motif = a life disc with one corner cut away to shorten cooldown; silhouette = 缺角命盘与收缩环; composition = sacrifice; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r4c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a primal vortex inside a vajra barrier" or "a new sprout unfolding inside a healing halo".

HARD RULE: all 12 cells share the same RESTRAINED painting method and the single primary 07-codex reference; only the central motif changes per cell. Keep #12161F ink ground, generous negative space, bright-step hard highlights and 1px black outlines identical. Draw a ring ONLY when the motif itself is a ring/array, and never more than 2-4 star points. Never merge the 12 cells into one continuous scene, never let an element cross a cell boundary, never draw grid lines or cell numbers.
Output: one opaque 1536x1024 PNG named sheet-05.png, with no text or numbers anywhere.
```

---

## 第 6 组（第 6 / 6 次生成）· ⑥ 构筑风险（朱砂暗主调）

> 类别 `syn` · 12 张卡 = 1 张 1536×1024 拼版（3 列 × 4 行）。
> **【命名】sheet-06.png** → 放 `previews/card_art_sheets/`。裁剪由 `tools/split_card_art_sheets.py` 完成，你不用切图。

### 第 6 组 · 中文提示词（整段复制）
<!-- sheet-06:zh -->
```text
东方修真题材 2D 像素游戏「卡牌插画拼版」，单张 1536×1024 不透明 PNG 横版。整图严格分成 3 列 × 4 行 = 12 个等大横格，每格 512×256 像素；格位按「从上到下、每行从左到右」编号 01–12（01=第1行第1格，04=第2行第1格，12=第4行第3格）。整图不留白边、不加外框。

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
辅助参考（只取色板 / 笔触 / 纹样密度）：previews/ui/00-anchor-gpt-image2_palette24.png、previews/ui/08-icons-gpt-image2_palette24.png；24 色吸附版为 previews/ui/07-codex-gpt-image2_palette24.png。

【12 格逐格清单 · 本拼版唯一的内容依据，优先级高于参考图与上方所有风格说明】格号 → 唯一画面，严格一一对应，不要调换顺序或合并母题。
【严禁照抄参考图】每格引用的 07-codex 示意卡只用来对齐线条密度、留白比例与色阶节奏；示意卡里画的具体符号一律不要画，主体形状必须按本格母题重新设计。不得把参考图里 16 张示意卡的任何一张搬进本拼版。
格 01（第 1 行第 1 格 / r1c1）→ card_jianxin｜唯一母题：剑修质变刻度从四件降到三件；主体剪影：带一格被抹去的刻度尺；构图：刻度降档；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 3 行第 3 张「星晨变」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「卡牌流断开而已选卡整体放大一圈」或「符纸 CD 环上 10% 的概率亮点」。
格 02（第 1 行第 2 格 / r1c2）→ card_fuhun｜唯一母题：符纸 CD 环上 10% 的概率亮点；主体剪影：CD 环与一枚孤立亮点；构图：概率亮点；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 3 行第 3 张「星晨变」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「剑修质变刻度从四件降到三件」或「灼伤印记叠三层而不刷新」。
格 03（第 1 行第 3 格 / r1c3）→ card_danxin｜唯一母题：灼伤印记叠三层而不刷新；主体剪影：三层错叠的灼印；构图：层叠堆积；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 4 行第 1 张「万劫灭」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「符纸 CD 环上 10% 的概率亮点」或「近身 32 像素圈内被放大的拳」。
格 04（第 2 行第 1 格 / r2c1）→ card_tipo｜唯一母题：近身 32 像素圈内被放大的拳；主体剪影：半径圆圈与放大的拳形；构图：近身圈定；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 2 行第 4 张「风行术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「灼伤印记叠三层而不刷新」或「三槽装满时浮出第四张候选」。
格 05（第 2 行第 2 格 / r2c2）→ card_tongyuan｜唯一母题：三槽装满时浮出第四张候选；主体剪影：三格满槽与浮出的第四格；构图：第四张浮出；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 1 行第 2 张「金光术」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「近身 32 像素圈内被放大的拳」或「天劫词缀由三格涨到四格」。
格 06（第 2 行第 3 格 / r2c3）→ card_jiezeng｜唯一母题：天劫词缀由三格涨到四格；主体剪影：四格词缀槽与新增一格；构图：槽位增减；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 4 行第 2 张「天罚劫」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「三槽装满时浮出第四张候选」或「一刀两刃一侧伤人一侧伤己」。
格 07（第 3 行第 1 格 / r3c1）→ card_shuangren｜唯一母题：一刀两刃一侧伤人一侧伤己；主体剪影：双向开刃的对称刀；构图：一刀两刃；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 4 行第 2 张「天罚劫」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「天劫词缀由三格涨到四格」或「第五个技能槽插入待重算的空位」。
格 08（第 3 行第 2 格 / r3c2）→ card_duozhu｜唯一母题：第五个技能槽插入待重算的空位；主体剪影：四槽之外插入的第五槽；构图：插入第五槽；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 3 行第 4 张「太虚咒」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「一刀两刃一侧伤人一侧伤己」或「禁用回春的朱印与道行倍率」。
格 09（第 3 行第 3 格 / r3c3）→ card_zhongshi｜唯一母题：禁用回春的朱印与道行倍率；主体剪影：朱红誓印与倍率折线；构图：朱印誓约；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 4 行第 4 张「无尽劫」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「第五个技能槽插入待重算的空位」或「空手退让三选一并逐层叠起减伤梯」。
格 10（第 4 行第 1 格 / r4c1）→ card_shouzhuo｜唯一母题：空手退让三选一并逐层叠起减伤梯；主体剪影：空掌与四级上升阶梯；构图：空手退让；主色段：朱砂 #7A2420 / #C8453B / #E8806F；画法样板：07-codex 第 2 行第 3 张「化气诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「禁用回春的朱印与道行倍率」或「三张候选中一枚异色离群卡」。
格 11（第 4 行第 2 格 / r4c2）→ card_yiyu｜唯一母题：三张候选中一枚异色离群卡；主体剪影：两同色一异色的三卡组；构图：异色离群；主色段：紫 #4A3A6B / #8A6FC4 / #C0A8E0；画法样板：07-codex 第 4 行第 3 张「混沌诀」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「空手退让三选一并逐层叠起减伤梯」或「卡牌流断开而已选卡整体放大一圈」。
格 12（第 4 行第 3 格 / r4c3）→ card_wuxin｜唯一母题：卡牌流断开而已选卡整体放大一圈；主体剪影：断开的卡流与放大外环；构图：断流放大；主色段：金 #8A6520 / #D9A441 / #F2D089；画法样板：07-codex 第 3 行第 4 张「太虚咒」— 只借鉴该张的线条密度、留白比例与色阶节奏，主体形状按本格母题重画，不要照抄示意卡符号；不得画成「三张候选中一枚异色离群卡」或「剑修质变刻度从四件降到三件」。

【格位与画法的强制关系】12 格共用同一套克制画法与第一基准；每格只换中心母题，#12161F 墨底 / 大面积留白 / 亮阶硬边高光 / 1px 纯黑硬描边保持一致。圆环只在母题本身是环 / 阵时才画，星点最多 2–4 枚。禁止把 12 格画成一张连续大场景，禁止元素跨格，禁止画格线或格号。
【输出】单张 1536×1024 不透明 PNG，命名 sheet-06.png；画面内无任何文字与编号。
```

### Group 6 · English (copy as one block)
<!-- sheet-06:en -->
```text
A 12-cell contact sheet of card illustrations for a 2D eastern-xianxia pixel game. One opaque 1536x1024 landscape PNG. Divide the whole canvas into EXACTLY 3 columns x 4 rows = 12 equal horizontal cells of 512x256 px each. Cell order is top-to-bottom, and within each row left-to-right: 01 = row1/col1, 04 = row2/col1, 12 = row4/col3. No outer margin, no outer frame.

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
Secondary references (palette / brush / glyph density only): previews/ui/00-anchor-gpt-image2_palette24.png, previews/ui/08-icons-gpt-image2_palette24.png; 24-color-snapped version: previews/ui/07-codex-gpt-image2_palette24.png.

12-CELL LIST - THE ONLY CONTENT SPEC FOR THIS SHEET; it overrides the reference image and every style note above. One UNIQUE picture per cell, strict 1:1 order, do not reorder or merge motifs:
NEVER COPY THE REFERENCE. Each cited 07-codex sample is used ONLY for line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif. Do not bring any of the 16 sample-card symbols into this sheet.
Cell 01 (row 1, col 1 / r1c1) -> card_jianxin: motif = a sword-ascension gauge dropping from four to three notches; silhouette = 带一格被抹去的刻度尺; composition = notch; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r3c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "the card stream cut while chosen cards enlarge by one ring" or "a ten-percent chance glint on a talisman cooldown ring".
Cell 02 (row 1, col 2 / r1c2) -> card_fuhun: motif = a ten-percent chance glint on a talisman cooldown ring; silhouette = CD 环与一枚孤立亮点; composition = chance; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r3c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a sword-ascension gauge dropping from four to three notches" or "three burn marks stacking instead of refreshing".
Cell 03 (row 1, col 3 / r1c3) -> card_danxin: motif = three burn marks stacking instead of refreshing; silhouette = 三层错叠的灼印; composition = stack; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r4c1: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a ten-percent chance glint on a talisman cooldown ring" or "a fist enlarged inside a close-range radius circle".
Cell 04 (row 2, col 1 / r2c1) -> card_tipo: motif = a fist enlarged inside a close-range radius circle; silhouette = 半径圆圈与放大的拳形; composition = radius; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r2c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "three burn marks stacking instead of refreshing" or "a fourth candidate surfacing when three slots are full".
Cell 05 (row 2, col 2 / r2c2) -> card_tongyuan: motif = a fourth candidate surfacing when three slots are full; silhouette = 三格满槽与浮出的第四格; composition = reveal; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r1c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a fist enlarged inside a close-range radius circle" or "tribulation slots growing from three to four".
Cell 06 (row 2, col 3 / r2c3) -> card_jiezeng: motif = tribulation slots growing from three to four; silhouette = 四格词缀槽与新增一格; composition = slots; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r4c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a fourth candidate surfacing when three slots are full" or "one blade with two edges, one outward and one inward".
Cell 07 (row 3, col 1 / r3c1) -> card_shuangren: motif = one blade with two edges, one outward and one inward; silhouette = 双向开刃的对称刀; composition = twin; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r4c2: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "tribulation slots growing from three to four" or "a fifth skill slot inserted into an empty recompute space".
Cell 08 (row 3, col 2 / r3c2) -> card_duozhu: motif = a fifth skill slot inserted into an empty recompute space; silhouette = 四槽之外插入的第五槽; composition = insert; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r3c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "one blade with two edges, one outward and one inward" or "a cinnabar oath seal banning healing with a dao multiplier".
Cell 09 (row 3, col 3 / r3c3) -> card_zhongshi: motif = a cinnabar oath seal banning healing with a dao multiplier; silhouette = 朱红誓印与倍率折线; composition = oath; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r4c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a fifth skill slot inserted into an empty recompute space" or "an empty hand declining the draft beside a rising defense stair".
Cell 10 (row 4, col 1 / r4c1) -> card_shouzhuo: motif = an empty hand declining the draft beside a rising defense stair; silhouette = 空掌与四级上升阶梯; composition = abstain; focal band = cinnabar #7A2420 / #C8453B / #E8806F; style sample = 07-codex r2c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "a cinnabar oath seal banning healing with a dao multiplier" or "one off-palette outlier card among three candidates".
Cell 11 (row 4, col 2 / r4c2) -> card_yiyu: motif = one off-palette outlier card among three candidates; silhouette = 两同色一异色的三卡组; composition = outlier; focal band = violet #4A3A6B / #8A6FC4 / #C0A8E0; style sample = 07-codex r4c3: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "an empty hand declining the draft beside a rising defense stair" or "the card stream cut while chosen cards enlarge by one ring".
Cell 12 (row 4, col 3 / r4c3) -> card_wuxin: motif = the card stream cut while chosen cards enlarge by one ring; silhouette = 断开的卡流与放大外环; composition = amplify; focal band = gold #8A6520 / #D9A441 / #F2D089; style sample = 07-codex r3c4: borrow ONLY line density, negative-space ratio and palette-step rhythm; redraw the subject from THIS cell's motif, never copy the sample card's symbol; do NOT depict "one off-palette outlier card among three candidates" or "a sword-ascension gauge dropping from four to three notches".

HARD RULE: all 12 cells share the same RESTRAINED painting method and the single primary 07-codex reference; only the central motif changes per cell. Keep #12161F ink ground, generous negative space, bright-step hard highlights and 1px black outlines identical. Draw a ring ONLY when the motif itself is a ring/array, and never more than 2-4 star points. Never merge the 12 cells into one continuous scene, never let an element cross a cell boundary, never draw grid lines or cell numbers.
Output: one opaque 1536x1024 PNG named sheet-06.png, with no text or numbers anywhere.
```

---

## 交付与验收顺序

1. **先只出第 1 组** `sheet-01.png`，放 `previews/card_art_sheets/`；跑一次裁剪脚本试裁，目检 12 格是否各独立、格位是否对齐、有无格线 / 文字 / 跨格元素（R58）。
2. 确认观感一致后再出剩余 5 组；6 张齐了总共也就 **6 次生成**。原稿不改写。
3. `python3 tools/split_card_art_sheets.py`：按固定坐标裁出 72 张 384×256 单卡原稿到 `previews/card_art/`，并写 `docs/card-art-split-report.json`（含每张 sheet 的 sha256 与格位映射）。
4. 逐张体检：不透明 / 24 色锁定板越界色 0 / 无文字与边框 / 水印修补（沿用第 31 轮 A2R 口径）。
5. 转录为 84×56 插画区：`24 色吸附 + 最近邻`，落到 `assets/ui/card_art/<card_id>.png`；卡框仍复用现有 4+6 张。
6. 三选一同屏目检：任取 3 张并排，剪影 / 构图 / 主色段不得撞脸；图鉴 72 张整屏并排不得出现明显复用感。
7. 全部标「待目检与合规确认；不得直接入库」；Q17 拍板 + GUI F5 目检后才谈替换 `assets/ui/cards/` 的 10 张冻结卡面。

> **状态：待外发 / 未回稿 / 候选规格，不是已入库资源。** 本包不改 `docs/12` 冻结口径、不改任何冻结数值与规则。
