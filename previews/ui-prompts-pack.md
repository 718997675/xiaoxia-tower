# UI 提示词包（第 22 轮 · 可整段复制）

> 本文件由 `tools/build_ui_prompt_pack.py` 从 `docs/19-UI界面设计规格与外发提示词.md` 自动抽取，**不要手改**。
> 用法：先出「⓪ 风格锚点板」，确认风格后再一次出 1 个界面；出图后把 PNG 丢进 `previews/ui/`，运行
> `python3 tools/check_ui_art.py previews/ui/` 做调色板 / 尺寸 / 半透明体检。


## 1. ⓪ 风格锚点板（先出这张）· 中文
<!-- anchor:zh -->
```text
东方修真题材 2D 像素游戏「风格锚点板」（style sheet），一张 1920×1080 的横版像素画稿，逻辑画布 480×270 整数 4 倍放大，像素颗粒清晰锐利、无抗锯齿、无渐变、1px 纯黑硬描边。

画面从左到右分为四栏，用 1px 黑线分隔，栏与栏之间留 16px 空隙：

第 1 栏「色板」：把 24 色锁定板画成 6 组 × 3 阶的小方块矩阵，每组一行，自上而下 墨、宣纸、青玉、朱砂、金、紫，每行下方用小字标出组名；最后单独一行放 2 个方块：纯黑描边色、纯白闪白色。

第 2 栏「纹样」：6 个 24×24 的像素纹样，剪影两两明显不同，依次为：横向弯月弧带剑尖（技能伤害）、三阶高低递进立柱（属性提升）、六边咬合齿轮（机制改变）、水滴带两道波纹（资源灵力）、盾形带中缝（生存回复）、交叠双菱中心打结（构筑风险）。纹样只允许用青玉、紫、金三色。

第 3 栏「边框层次」：4 组卡框缩略，从简到繁：第一组 1px 墨线四角平切；第二组 2px 青玉双线四角云纹缺角；第三组 3px 金线加金色云角、顶边一条亮金线；第四组朱砂色四边各留一处断点、四角斜切。边框内部一律宣纸色底 #E8DFC8。

第 4 栏「界面语汇」：4 个并排的像素控件样本——一个九宫格像素按钮（墨底 #2A3140 + 宣纸色文字 + 1px 黑描边 + 底部 1px 金色基线表示悬浮）、一个横向血条（墨底 + 朱砂填充 + 1px 黑描边）、一个八角切角技能图标框（内含一个横弧符号）、一个菱形小徽记（朱砂色描边）。

整体质感：东方水墨的「留白与墨色浓淡」概念，转译成像素色块与硬边；安静、克制、有重量感，不要华丽。背景统一墨底 #12161F。
配色严格限定在 24 色锁定板内（墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF）。
禁止：写实渲染、3D、赛博朋克霓虹、玻璃拟态、毛玻璃、柔和投影、模糊光晕、渐变、半透明叠色、圆角卡片、照片质感、水墨淡彩渲染、英文大标题、调色板以外的颜色、多余人物立绘。
输出：单张 PNG，1920×1080，不透明背景。
```

## 2. ⓪ Style sheet (do this one first) · English
<!-- anchor:en -->
```text
A pixel-art style sheet for a 2D eastern-xianxia cultivation game. One 1920x1080 landscape PNG, logical canvas 480x270 scaled by an exact integer factor of 4. Crisp visible pixels, no anti-aliasing, no gradients, 1px solid black outlines.

Four columns separated by 1px black lines, 16px gutter between columns:

Column 1 "PALETTE": a 6x3 matrix of small color swatches, one row per hue family - ink, rice-paper, jade, cinnabar, gold, violet - each row in dark / mid / light steps; below that two isolated swatches: pure black for outlines and pure white for hit flash.

Column 2 "PATTERNS": six 24x24 pixel glyphs with clearly different silhouettes - a horizontal crescent arc with a blade tip (skill damage), three ascending columns of different heights (attribute), a hexagonal cog (mechanic), a water drop with two ripples (resource), a shield with a center seam (survival), two overlapping diamonds tied at the center (risk). Only jade, violet and gold allowed.

Column 3 "BORDERS": four card-frame thumbnails from simple to ornate - (1) 1px ink line, square corners; (2) 2px jade double line, corners cut with cloud motifs; (3) 3px gold line with gold cloud corners and a bright gold top edge; (4) cinnabar frame broken once per side with diagonal corner cuts. Frame interior is rice-paper color #E8DFC8.

Column 4 "UI LANGUAGE": four pixel widget samples - a nine-slice pixel button (ink base #2A3140, rice-paper text, 1px black outline, 1px gold baseline at the bottom for hover), a horizontal health bar (ink base, cinnabar fill, 1px black outline), an octagonal skill icon frame containing a horizontal arc symbol, a small diamond badge with a cinnabar outline.

Overall mood: the concept of ink-wash negative space and tonal density translated into pixel color blocks and hard edges. Quiet, restrained, weighty. Solid ink background #12161F.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF.

Negative: photorealism, 3D render, cyberpunk neon, glassmorphism, frosted glass, soft drop shadows, radial glow, depth of field, gradients, translucent overlays, anti-aliasing, rounded cards, photoreal materials, glossy metal, flat modern material design, English headline typography, ukiyo-e, pastel ink-wash painting, extra character illustrations, any color outside the palette.
Output: single PNG, 1920x1080, opaque background.
```

## 3. ① MainMenu 主菜单 · 中文
<!-- menu:zh -->
```text
东方修真题材 2D 像素游戏「主菜单」界面设计稿，横版，1920×1080 输出（逻辑画布 480×270 整数 4 倍放大），像素颗粒清晰锐利、无抗锯齿、无渐变、1px 纯黑硬描边。

背景：墨色夜空 #12161F 铺满；画面中央偏右是一道远处的九重塔剪影，塔身用墨 #2A3140 分层，塔腰有青玉 #5FA8A0 的窄横带；塔脚与画面下缘是云雾，用宣纸暗 #8A8268 的实色横向色块分层表现（不要半透明、不要柔边）。

前景 UI 分左右两栏，中间留空给塔身：
左侧上方是一张竖向宣纸卷轴面板（x 约占画面 5%–42%，y 约占 12%–44%），宣纸底 #E8DFC8、1px 黑描边、四角有墨色云纹卷边；面板内竖排四个大字「九重天梯」，字为墨色 #12161F 点阵字风格，下方一行小字副标题。
左侧下方是一张横向卷轴框（宽扁、两端云纹卷边），里面写「金丹」二字，旁边一道青色 #5FA8A0 的横向修为进度条，进度条约六成满，条内有黑色 1px 描边。

右侧上方竖排四个像素按钮，高度一致、间隔均匀，依次是「开始入塔」「境界总览」「传承灵韵」「设置」。按钮为九宫格像素样式：底色墨 #2A3140、1px 纯黑描边、宣纸色 #E8DFC8 点阵字。第一个「开始入塔」处于选中态：外加一圈金 #D9A441 双线边框，按钮底下方一条 1px 金色基线。

右侧下方是「传承灵韵」栏：6 个左右尖角的六边框小槽横向排开，其中前 2 个槽里有简化的内嵌纹样并带一点金色 #D9A441 亮边，后 4 个为空槽（只画框）。

画面最底部居中一行小字：左半「九重天梯 · 像素验证版 v0.2」，右半「本地存档：已存在」。

配色严格限定 24 色锁定板：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。

禁止：写实渲染、3D、赛博朋克霓虹、玻璃拟态、毛玻璃、柔和投影、模糊光晕、渐变、半透明叠色、圆角卡片、照片质感、水墨淡彩渲染、现代扁平英文排版、多余人物立绘与吉祥物、调色板以外的颜色。
输出：单张 PNG，1920×1080，背景不透明。
```

## 4. ① MainMenu · English
<!-- menu:en -->
```text
A pixel-art main menu screen for a 2D eastern-xianxia cultivation game. Landscape, 1920x1080 PNG (logical canvas 480x270, exact 4x integer upscale). Crisp pixels, no anti-aliasing, no gradients, 1px solid black outlines.

Background: solid ink-night #12161F. Center-right stands a distant nine-tier pagoda silhouette in ink #2A3140 with narrow jade #5FA8A0 bands at the tower waist. Layered mist at the tower base and along the bottom edge, drawn as solid horizontal blocks of rice-paper dark #8A8268 - no translucency, no soft edges.

Foreground UI in two columns with the middle left open for the pagoda.
Upper left: a vertical rice-paper scroll panel (about x 5%-42%, y 12%-44% of the frame), paper fill #E8DFC8, 1px black outline, ink cloud-scroll curls at the four corners. Inside, four large characters stacked vertically: "九重天梯", ink #12161F dot-matrix type, with a small subtitle line below.
Lower left: a horizontal scroll frame (wide and flat, cloud curls at both ends) containing the two characters "金丹" and a jade #5FA8A0 cultivation progress bar, filled to about 60 percent, 1px black outline.

Upper right: four pixel buttons stacked vertically, equal height, even spacing, labeled "开始入塔" (start run), "境界总览" (realms overview), "传承灵韵" (legacy spirits), "设置" (settings). Nine-slice pixel buttons: ink #2A3140 fill, 1px pure black outline, rice-paper #E8DFC8 dot-matrix label. The first button is selected: a gold #D9A441 double-line frame plus a 1px gold baseline under the button.

Lower right: a "传承灵韵" row of six hexagonal slots with pointed left and right edges; the first two contain simplified inner glyphs with a touch of gold #D9A441 highlight, the other four are empty frames.

Bottom center: one line of small text, left half "九重天梯 · 像素验证版 v0.2", right half "本地存档：已存在".

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF.

Negative: photorealism, 3D, cyberpunk neon, glassmorphism, frosted glass, soft drop shadows, blur glow, gradients, translucent overlays, rounded cards, photoreal materials, ink-wash painting, flat modern material design, English headline typography, extra character art or mascots, any color outside the palette.
Output: single PNG, 1920x1080, opaque background.
```

## 5. ② TowerHUD 横版战斗 HUD · 中文
<!-- hud:zh -->
```text
东方修真题材 2D 像素横版动作游戏「战斗 HUD 界面层」设计稿，1920×1080 输出（逻辑画布 480×270 整数 4 倍放大），像素颗粒锐利、无抗锯齿、无渐变、1px 纯黑硬描边。

这是一张**叠在战斗场景之上的 HUD 图层稿**：背景是透明的（输出 PNG 带 alpha，只在 HUD 元素处不透明），不要画场景、地面、角色、敌人。

HUD 元素清单：
左上角三条竖直堆叠的状态条：第一条最长，是血条，黑色底槽 + 朱砂 #C8453B 填充到八成，右端小数字「276/300」；第二条稍短，是灵力条，青玉 #5FA8A0 填充，右端小数字；第三条最短，是体力条，宣纸暗 #8A8268 填充。三条槽都只有 1px 纯黑描边，没有圆角、没有阴影。

右上角：右对齐的文字「第 4 层 / 9」，下方一排 9 个 4×4 的小方格表示难度波形，前 4 格已点亮为金 #D9A441，后 5 格是墨 #2A3140 空槽。右上方再往下一行是一个横向卷轴框小徽记（宽扁、两端云纹卷边），内写「金丹」，框边有 3 道短刻痕纹样。

画面顶部正中偏下：一条居中的横条血条（Boss 血条），墨底 + 朱砂 #C8453B 填充约七成，条右端有三道刻度把条分成三段表示三阶段，条上方小字写 Boss 名。

画面底部正中：4 个 24×24 的八角切角技能槽横向排列，间距 4px。每个槽里是一个 16×16 的极简技能符号（从左到右分别是：横向弯月弧、三道斜向细剑、纵向折线雷、实心圆火团），符号下方各有一个键位小字「J」「K」「L」「I」；第 2 个槽处于冷却中，底部有一条青玉色进度条只走了三分之一。

画面左下角：两行小字，第一行「共享池 22 / 600」，第二行一行更小的说明字。

配色严格限定 24 色锁定板：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。

禁止：写实渲染、3D、赛博朋克霓虹、玻璃拟态、毛玻璃、柔和投影、模糊光晕、渐变、半透明叠色、圆角卡片、照片质感、场景与角色、现代扁平英文排版、超过 4 个技能槽、技能选择列表面板、调色板以外的颜色。
输出：单张 PNG，1920×1080，背景透明。
```

## 6. ② TowerHUD · English
<!-- hud:en -->
```text
A pixel-art combat HUD overlay design for a 2D eastern-xianxia side-scrolling action game. 1920x1080 PNG (logical canvas 480x270, exact 4x upscale). Crisp pixels, no anti-aliasing, no gradients, 1px solid black outlines.

This is a HUD layer sheet meant to sit on top of gameplay: transparent background (PNG with alpha, only the HUD elements opaque). Do not draw the scene, ground, characters or enemies.

Elements:
Top-left, three stacked horizontal bars: the longest is the health bar - black slot with cinnabar #C8453B fill to about 80 percent and small numerals "276/300" at its right end; the second, shorter, is the spirit bar filled jade #5FA8A0 with small numerals; the third, shortest, is the stamina bar filled rice-paper dark #8A8268. All slots have 1px pure black outlines, no rounded corners, no shadows.

Top-right: right-aligned text "第 4 层 / 9", and below it a row of nine 4x4 squares showing the difficulty wave - the first four lit gold #D9A441, the remaining five empty ink #2A3140. Under that, a small horizontal scroll badge (wide and flat, cloud curls at both ends) reading "金丹", with three short notch marks on its frame.

Top center, slightly lower: a centered boss health bar - ink slot with cinnabar #C8453B fill to about 70 percent, three notches dividing it into three phases, small boss name above it.

Bottom center: four 24x24 octagonal (corners cut) skill slots in a row with 4px gaps. Each holds a tiny 16x16 symbol - left to right: a horizontal crescent arc, three diagonal thin swords, a vertical lightning zigzag, a solid round flame - and each has a small key label beneath: "J" "K" "L" "I". The second slot is on cooldown with a jade progress bar one third filled along its bottom edge.

Bottom-left: two lines of small text, the first "共享池 22 / 600", the second a smaller line.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF.

Negative: photorealism, 3D, cyberpunk neon, glassmorphism, frosted glass, soft drop shadows, blur glow, gradients, translucent overlays, rounded cards, photoreal materials, scenes or characters, flat modern material design, English headline typography, more than four skill slots, skill-selection list panels, any color outside the palette.
Output: single PNG, 1920x1080, transparent background.
```

## 7. ③ RewardPicker 层间三选一 · 中文
<!-- draft:zh -->
```text
东方修真题材 2D 像素游戏「层间三选一」界面设计稿，1920×1080 输出（逻辑画布 480×270 整数 4 倍放大），像素颗粒锐利、无抗锯齿、无渐变、1px 纯黑硬描边。

这是一张**独立场景**，不是战斗画面上的浮层：整幅背景是实色墨底 #12161F，**不要叠在战斗画面上、不要半透明遮罩**。

画面正中偏上是一条横向标题带：左边写「第 4 层 · 择一机缘」，右边写「已选 3/8 · 道行 +120」，字号为 12px 点阵字，标题带下沿一条 1px 墨亮 #4A5568 分隔线。标题带左右两端各有一道竖直的云纹装饰线。

画面中部并排三张竖直卡牌，每张 96×144 逻辑像素，三张之间留 16px 空白，整体居中（左边一张 x=80、中间 x=192、右边 x=304 的位置关系）。每张卡的结构完全一致：
- 外框 1px 纯黑描边；左卡是凡品（1px 墨线、四角平切、宣纸底 #E8DFC8），中卡是灵品（2px 青玉 #5FA8A0 双线、四角云纹缺角、宣纸底），右卡是仙品（3px 金 #D9A441 线 + 金色云角、顶边一条亮金 #F2D089 线、宣纸底带金色类别条）。
- 卡片上部是一条类别条：左边一个 8×8 的小纹样（三个卡分别是：横向弯月弧、三阶立柱、六边齿轮），右边是类别小字（技能伤害 / 属性提升 / 机制改变）。
- 卡片中部是插画区，宣纸暗 #C9BFA3 底，居中放两个 24×24 的极简纹样并排（形状与类别条同族但更简）。
- 插画区下方是卡名条，居中一行点阵字（不超过 5 个汉字），三个卡依次是「剑气斩」「厚土桩」「齿轮咬合」。
- 再下面是三行小字描述（每行不超过 8 个汉字），描述下方是信息条：左边是稀有度点阵（1 / 2 / 3 个金点阵），中间是「x2」堆叠数，右边是类别小 chip。
- 卡片右上角有一小块 4×4 的金色点阵角标，点数分别为 1 / 2 / 3。
右卡处于**选中态**：整张卡外再加一圈金 #D9A441 双框，卡底部有一条 1px 金色基线。

画面底部是一条操作条：左边「1 / 2 / 3 切换」，中间一个方框按钮写「确认 (Enter)」（这个按钮用金 #D9A441 双线框 + 亮金底表示已亮起），右边「Esc 查看已有卡」；操作条最下沿一条 1px 金线，只有中间按钮对应的位置是亮的，其余是暗的。

配色严格限定 24 色锁定板：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。

禁止：写实渲染、3D、赛博朋克霓虹、玻璃拟态、毛玻璃、柔和投影、模糊光晕、渐变、半透明叠色、圆角卡片、照片质感、现代扁平英文排版、卡牌数量不是 3 张、浮层叠在战斗画面上、调色板以外的颜色。
输出：单张 PNG，1920×1080，背景不透明。
```

## 8. ③ RewardPicker · English
<!-- draft:en -->
```text
A pixel-art "pick one of three" reward screen for a 2D eastern-xianxia game. 1920x1080 PNG (logical canvas 480x270, exact 4x upscale). Crisp pixels, no anti-aliasing, no gradients, 1px solid black outlines.

This is a standalone screen, not an overlay on gameplay: the entire background is solid ink #12161F. Do not composite it over a battle scene and do not use a translucent scrim.

Top band, centered: a horizontal title strip. Left side "第 4 层 · 择一机缘", right side "已选 3/8 · 道行 +120", 12px dot-matrix type, with a 1px ink-bright #4A5568 divider line under it and a vertical cloud-scroll ornament at each end.

Center: three vertical cards side by side, each 96x144 logical pixels with 16px gutters, the trio centered as a whole. All three cards share the same internal structure:
- 1px pure black outer frame. Left card is common rarity (1px ink line, square corners, rice-paper #E8DFC8 fill); middle card is rare (2px jade #5FA8A0 double line, corners cut with cloud motifs, rice-paper fill); right card is legendary (3px gold #D9A441 line plus gold cloud corners and a bright #F2D089 top edge, rice-paper fill with a gold category bar).
- A category bar across the top of each card: a small 8x8 glyph on the left (respectively a horizontal crescent arc, three stepped columns, a hexagonal cog) and a small category label on the right (skill damage / attribute / mechanic).
- An illustration area with a rice-paper dark #C9BFA3 fill holding two simplified 24x24 glyphs side by side.
- Below that, a centered card name in dot-matrix type, no more than five characters: "剑气斩", "厚土桩", "齿轮咬合".
- Then three lines of small description text (no more than eight characters per line), then an info strip: rarity dot-matrix on the left (one, two and three gold dots), a stack count "x2" in the middle, a small category chip on the right.
- A 4x4 gold dot-matrix corner badge at the top-right of each card, with one, two and three dots.
The right card is selected: an additional gold #D9A441 double frame around the whole card and a 1px gold baseline under it.

Bottom: an action strip - left "1 / 2 / 3 切换", center a rectangular button reading "确认 (Enter)" in a gold #D9A441 double frame with a bright gold fill (lit), right "Esc 查看已有卡". Along the very bottom a 1px gold line that is only lit under the center button, dim elsewhere.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF.

Negative: photorealism, 3D, cyberpunk neon, glassmorphism, frosted glass, soft drop shadows, blur glow, gradients, translucent overlays, rounded cards, photoreal materials, flat modern material design, English headline typography, any number of cards other than three, an overlay composited over a battle scene, any color outside the palette.
Output: single PNG, 1920x1080, opaque background.
```

## 9. ④ RunResult 单局结算 · 中文
<!-- result:zh -->
```text
东方修真题材 2D 像素游戏「单局结算」界面设计稿，1920×1080 输出（逻辑画布 480×270 整数 4 倍放大），像素颗粒锐利、无抗锯齿、无渐变、1px 纯黑硬描边。

背景：墨底 #12161F；画面正中一道竖直光柱，颜色从上到下由青玉 #5FA8A0 过渡为金 #D9A441（用分段实色色块表达，不要平滑渐变），光柱边缘有金色 #F2D089 的碎屑小方块向上飘（画成几个离散的小方点，不要粒子光晕）。

画面正中偏上是一张大幅宣纸卷轴面板（横向宽幅、约占画面 1/6 到 5/6 宽、3/10 到 9/10 高），宣纸底 #E8DFC8、1px 纯黑描边、四角墨色云纹卷边。

卷轴内从上到下：
- 顶部居中一行大字「通关 · 第 9 层」，墨色 #12161F 点阵字，字号明显大于其它文字。
- 下面一行「修为 +180」，其中「+180」用金 #D9A441。
- 再下面一条道行进度条：墨底槽 + 青玉 #5FA8A0 填充约七成，条两端有 1px 黑描边，条右侧小字「金丹 → 元婴」。
- 下面一段小标题「固化传承灵韵（1 条）」，后面是横向排开的 6 个六边框小槽（左右尖角），对应剑痕 / 符印 / 丹息 / 铁骨 / 疾影 / 灵泉；其中第 3 个槽被选中，亮金 #D9A441 双线边框，槽内有一个简化的丹炉纹样；其余 5 个槽是暗的墨 #4A5568 框。
- 底部并排两个九宫格像素按钮：左「返回主菜单」，右「再来一局」（右按钮选中态，金双线 + 底部 1px 金基线）。

配色严格限定 24 色锁定板：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。

禁止：写实渲染、3D、赛博朋克霓虹、玻璃拟态、毛玻璃、柔和投影、模糊光晕、平滑渐变、半透明叠色、圆角卡片、照片质感、现代扁平英文排版、多余人物立绘、调色板以外的颜色。
输出：单张 PNG，1920×1080，背景不透明。
```

## 10. ④ RunResult · English
<!-- result:en -->
```text
A pixel-art run-result screen for a 2D eastern-xianxia game. 1920x1080 PNG (logical canvas 480x270, exact 4x upscale). Crisp pixels, no anti-aliasing, no gradients, 1px solid black outlines.

Background: ink #12161F. A vertical beam of light rises in the center, stepping from jade #5FA8A0 at the top to gold #D9A441 at the bottom as discrete solid color blocks - no smooth gradient. A few detached gold #F2D089 square motes drift upward along its edges - hard little squares, not a particle glow.

Centered, a large horizontal rice-paper scroll panel (about one sixth to five sixths of the width, three tenths to nine tenths of the height), rice-paper #E8DFC8 fill, 1px pure black outline, ink cloud-scroll curls at the corners.

Inside the scroll, top to bottom:
- Centered large line "通关 · 第 9 层" in ink #12161F dot-matrix type, clearly larger than the other text.
- Below it "修为 +180", with "+180" in gold #D9A441.
- Below that a path progress bar: ink slot, jade #5FA8A0 fill to about 70 percent, 1px black outline, small text on the right "金丹 → 元婴".
- Below that a small heading "固化传承灵韵（1 条）" followed by six hexagonal slots (pointed left and right edges) in a row, representing 剑痕 / 符印 / 丹息 / 铁骨 / 疾影 / 灵泉. The third slot is selected with a gold #D9A441 double frame and a simplified furnace glyph inside; the other five are dim ink #4A5568 frames.
- At the bottom, two nine-slice pixel buttons side by side: left "返回主菜单", right "再来一局" - the right one in the selected state with a gold double frame and a 1px gold baseline.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF.

Negative: photorealism, 3D, cyberpunk neon, glassmorphism, frosted glass, soft drop shadows, blur glow, smooth gradients, translucent overlays, rounded cards, photoreal materials, flat modern material design, English headline typography, extra character art, any color outside the palette.
Output: single PNG, 1920x1080, opaque background.
```

## 11. ⑤ Pause 暂停界面 · 中文
<!-- pause:zh -->
```text
东方修真题材 2D 像素游戏「暂停」界面设计稿，1920×1080 输出（逻辑画布 480×270 整数 4 倍放大），像素颗粒锐利、无抗锯齿、无渐变、1px 纯黑硬描边。

画面正中是一个居中的暂停面板（横向约占 1/2 宽、竖向约占 3/5 高），面板底为墨 #2A3140，1px 纯黑描边，四角是墨色云纹，底部一条 1px 金 #D9A441 亮线。
面板上方居中一行小字「暂停」。
面板中间竖排三个九宫格像素按钮，依次是「继续 (Esc)」「设置」「放弃本局」。三个按钮底色都是更深的墨 #12161F，1px 纯黑描边，宣纸色 #E8DFC8 点阵字；第一个「继续 (Esc)」是选中态：外面套一圈金 #D9A441 双线框，按钮底部一条 1px 金色基线。第三个「放弃本局」不做红色警示，保持中性色（只有文字用朱砂 #C8453B 提示色）。
面板底部一行更小的提示字：「放弃本局将不产出传承灵韵」。

面板之外：整幅画面用**实色墨底 #12161F 填满**，但四周留出约 24px 的窄边框，边框里露出上一帧的战斗画面（只用极简的墨色剪影暗示，不要画清楚角色），用来表示「还在这一局里」。

配色严格限定 24 色锁定板：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。

禁止：半透明遮罩、模糊背景、写实渲染、3D、赛博朋克霓虹、玻璃拟态、毛玻璃、柔和投影、模糊光晕、渐变、圆角卡片、照片质感、现代扁平英文排版、调色板以外的颜色。
输出：单张 PNG，1920×1080，背景不透明。
```

## 12. ⑤ Pause · English
<!-- pause:en -->
```text
A pixel-art pause screen for a 2D eastern-xianxia game. 1920x1080 PNG (logical canvas 480x270, exact 4x upscale). Crisp pixels, no anti-aliasing, no gradients, 1px solid black outlines.

Centered is a pause panel, roughly half the frame width and three fifths of the height. Panel fill ink #2A3140, 1px pure black outline, ink cloud motifs at the corners, and a 1px gold #D9A441 highlight line along its bottom edge.
Above the panel, centered, a small line "暂停".
Inside the panel, three nine-slice pixel buttons stacked vertically: "继续 (Esc)" (resume), "设置" (settings), "放弃本局" (abandon run). All three use a deeper ink #12161F fill, 1px pure black outline, rice-paper #E8DFC8 dot-matrix labels. The first one is selected: wrapped in a gold #D9A441 double frame with a 1px gold baseline under the button. The third one is NOT made red - keep it neutral, only its label may use the cinnabar #C8453B alert tint.
Under the buttons, one smaller line of text: "放弃本局将不产出传承灵韵".

Outside the panel: the whole frame is filled with solid ink #12161F, except for a narrow border about 24px wide around the edges where the previous battle frame shows through as a minimal ink silhouette - do not draw clear characters - to signal that the run is still live.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF.

Negative: translucent scrim, blurred backdrop, photorealism, 3D, cyberpunk neon, glassmorphism, frosted glass, soft drop shadows, blur glow, gradients, rounded cards, photoreal materials, flat modern material design, English headline typography, any color outside the palette.
Output: single PNG, 1920x1080, opaque background.
```

## 13. ⑥ AffixPicker 天劫词缀自选 · 中文
<!-- affix:zh -->
```text
东方修真题材 2D 像素游戏「天劫词缀自选」界面设计稿，1920×1080 输出（逻辑画布 480×270 整数 4 倍放大），像素颗粒锐利、无抗锯齿、无渐变、1px 纯黑硬描边。

背景整幅为实色墨底 #12161F。

顶部一条标题带：左侧写「天劫词缀 · 自选 0–3 条」，右侧写「已选 2 / 3」，下沿一条 1px 墨亮 #4A5568 分隔线。

画面左中部是一张 4 列 × 3 行、共 12 枚小徽记的网格。每枚徽记是一个 16×16 的菱形框（上下尖角），1px 纯黑描边，内含一个极简像素符号，12 枚符号各不相同（例如：心形裂纹、折线雷、断裂的锁环、三道风线、盾面纹样、镜面反射、吞噬的漩涡、空心圆环、错位三角、逆向箭头、雾中人形、共用圆环）。徽记右上角有 4×4 金色点阵角标表示阶数。第 2 枚与第 7 枚处于**已选中**状态：菱形外再套一圈金 #D9A441 双线，框内符号换成亮阶色 #F2D089，其余 10 枚是墨 #4A5568 暗框。

画面右侧是一块竖向面板：上面写「已选」，下面两行小字，分别是词缀名「雷劫」和「无相」，每行左边配一枚选中态的菱形徽记；再下面一个区块写「奖励倍率预览」，是一条墨底 + 青玉 #5FA8A0 填充约六成的横条，右侧标「×1.35」。

底部一条操作条：中间一个方框按钮「确认（Enter）」用金 #D9A441 双线框 + 亮金底；左侧小字「词缀自选上限 3 条」；最下沿一条 1px 金线，仅按钮对应位置亮起。

配色严格限定 24 色锁定板：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。

禁止：写实渲染、3D、赛博朋克霓虹、玻璃拟态、毛玻璃、柔和投影、模糊光晕、渐变、半透明叠色、圆角卡片、照片质感、现代扁平英文排版、徽记数量不是 12 枚、调色板以外的颜色。
输出：单张 PNG，1920×1080，背景不透明。
```

## 14. ⑥ AffixPicker · English
<!-- affix:en -->
```text
A pixel-art affix-selection screen for a 2D eastern-xianxia game. 1920x1080 PNG (logical canvas 480x270, exact 4x upscale). Crisp pixels, no anti-aliasing, no gradients, 1px solid black outlines.

Background: solid ink #12161F across the whole frame.

Top title band: left "天劫词缀 · 自选 0–3 条", right "已选 2 / 3", with a 1px ink-bright #4A5568 divider line underneath.

Left-center: a grid of twelve small badges, four columns by three rows. Each badge is a 16x16 diamond frame with pointed top and bottom, 1px pure black outline, containing one minimal pixel symbol - all twelve different (a cracked heart, a lightning zigzag, a broken chain ring, three wind lines, a shield pattern, a mirror reflection, a devouring vortex, a hollow ring, a misaligned triangle, a reversed arrow, a figure in fog, a shared ring). Each carries a 4x4 gold dot-matrix corner badge for its tier. Badges two and seven are selected: an extra gold #D9A441 double frame around the diamond and the inner symbol switches to the bright step #F2D089; the other ten are dim ink #4A5568 frames.

Right side: a vertical panel. Heading "已选", then two rows of small text naming the chosen affixes "雷劫" and "无相", each preceded by its selected diamond badge. Below that a block titled "奖励倍率预览" with a horizontal bar, ink slot and jade #5FA8A0 fill to about 60 percent, labelled "×1.35" on the right.

Bottom action strip: a centered rectangular button "确认（Enter）" with a gold #D9A441 double frame and bright gold fill; small text on the left "词缀自选上限 3 条"; along the very bottom a 1px gold line lit only beneath the button.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF.

Negative: photorealism, 3D, cyberpunk neon, glassmorphism, frosted glass, soft drop shadows, blur glow, gradients, translucent overlays, rounded cards, photoreal materials, flat modern material design, English headline typography, any badge count other than twelve, any color outside the palette.
Output: single PNG, 1920x1080, opaque background.
```

## 15. ⑦ Codex 卡牌图鉴（可选）· 中文
<!-- codex:zh -->
```text
东方修真题材 2D 像素游戏「卡牌图鉴」界面设计稿，1920×1080 输出（逻辑画布 480×270 整数 4 倍放大），像素颗粒锐利、无抗锯齿、无渐变、1px 纯黑硬描边。

背景整幅实色墨底 #12161F。

顶部一条筛选行（高度约占画面 1/10）：左侧 6 个类别小 chip（技能伤害 / 属性提升 / 机制改变 / 资源灵力 / 生存回复 / 构筑风险），每个 chip 是一个小方框 + 简笔纹样；中间 4 个稀有度 chip（凡品 / 灵品 / 仙品 / 劫品）；右侧一个空的搜索框（方框 + 一条下划线）。第 1 个类别 chip 与第 2 个稀有度 chip 为选中态，金 #D9A441 双线框。

中部是一张卡牌网格：每行 4 张卡、卡与卡之间留 8px 空白，网格整体从画面 x≈7% 处开始（4 张 96 宽卡 + 3 个 8px 间隔正好占 408 逻辑像素宽）；行与行之间留 8px，纵向可滚动（只画 4 行表示可滚动）。每张卡仍是 96×144 的完整结构：外框、类别条、插画区（24×24 纹样 ×2）、卡名条、描述、信息条、右上角标，**不要缩放**。网格里能看出明显差别：第 1 行为凡品（1px 墨线），第 2 行为灵品（2px 青玉双线），第 3 行出现一张仙品（3px 金线 + 金云角），第 4 行有一张劫品（朱砂断线框 + 朱砂暗底卡面 + 宣纸色文字）。

画面右侧留一条详情栏：显示被点开那张卡的完整效果文字、参数名、堆叠上限、互斥提示。右下角小字「24 / 72」。

配色严格限定 24 色锁定板：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。

禁止：写实渲染、3D、赛博朋克霓虹、玻璃拟态、毛玻璃、柔和投影、模糊光晕、渐变、半透明叠色、圆角卡片、照片质感、现代扁平英文排版、缩小的卡牌、调色板以外的颜色。
输出：单张 PNG，1920×1080，背景不透明。
```

## 16. ⑦ Codex (optional) · English
<!-- codex:en -->
```text
A pixel-art card codex screen for a 2D eastern-xianxia game. 1920x1080 PNG (logical canvas 480x270, exact 4x upscale). Crisp pixels, no anti-aliasing, no gradients, 1px solid black outlines.

Background: solid ink #12161F.

Top filter row (about one tenth of the frame height): on the left six category chips - skill damage / attribute / mechanic / resource / survival / risk - each a small framed box with a minimal glyph; in the middle four rarity chips - common / rare / legendary / curse; on the right an empty search field, a box with an underline. The first category chip and the second rarity chip are selected, drawn with gold #D9A441 double frames.

Center: a card grid, four cards per row with 8px gutters, the grid starting at about x 7 percent of the frame (four 96-wide cards plus three 8px gaps come to 408 logical pixels). Rows are 8px apart and scroll vertically - draw four rows to imply scrolling. Every card keeps its full 96x144 structure: outer frame, category bar, illustration area (two 24x24 glyphs), name bar, description, info strip, corner badge. Do not scale the cards down. Make the rarity progression readable: row one all common (1px ink line), row two rare (2px jade double line), row three contains one legendary card (3px gold line with gold cloud corners), row four contains one curse card (cinnabar broken frame, cinnabar dark card face, rice-paper text).

Right side: a narrow detail panel showing the full effect text, parameter names, stack limit and mutual-exclusion hints of the opened card. Bottom-right small text "24 / 72".

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF.

Negative: photorealism, 3D, cyberpunk neon, glassmorphism, frosted glass, soft drop shadows, blur glow, gradients, translucent overlays, rounded cards, photoreal materials, flat modern material design, English headline typography, shrunken cards, any color outside the palette.
Output: single PNG, 1920x1080, opaque background.
```

## 17. ⑧ 图标系统样式表（可选）· 中文
<!-- icons:zh -->
```text
东方修真题材 2D 像素游戏「图标系统样式表」，1920×1080 输出（逻辑画布 480×270 整数 4 倍放大），像素颗粒锐利、无抗锯齿、无渐变、1px 纯黑硬描边。

一张图标样式表，背景为实色墨底 #12161F，图标按外框类型分成 6 组，每组一行，行首用小字标出组名，每组 4 到 12 枚图标横向排列，图标之间留 4px：

第 1 组「技能 · 八角切角框 · 32×32」：8 枚，内部符号依次为 横向弯月弧 / 三道斜向细长剑 / 纵向折线雷 + 方形符箓 / 方形符纸 + 田字朱印 / 实心圆火团 / 空心圆环 / 短距扇形波 / 六边形金罩。
第 2 组「流派 · 正圆框 · 32×32」：4 枚，内部符号为 竖直剑身加十字护手 / 竖符纸加朱印 / 梯形丹炉加三足 / 拳套加指节。
第 3 组「词缀 · 菱形框 · 16×16」：12 枚，符号为 心形裂纹 / 折线雷 / 断裂锁环 / 三道风线 / 盾面纹 / 镜面反射 / 吞噬漩涡 / 空心圆环 / 错位三角 / 逆向箭头 / 雾中人影 / 共用圆环。
第 4 组「境界 · 横向卷轴框 · 32×32」：9 枚，从左到右 4 段色递增（墨亮 / 青玉 / 紫 / 金），边框纹样刻痕数依次 1 到 9 道。
第 5 组「装备 · 盾形框 · 32×32」：8 枚，内部为 剑 / 甲 / 冠 / 佩 / 靴 / 囊 / 印 / 环 的简笔。
第 6 组「灵韵 · 六边框 · 32×32」：6 枚，内部为 剑痕 / 符印 / 丹息 / 铁骨 / 疾影 / 灵泉 六种不同纹样。

所有图标：1px 纯黑描边、四周至少 1px 透明留白、外框不贴边、不做阴影、不做渐变；右上角可带 4×4 金色点阵角标。

配色严格限定 24 色锁定板：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。

禁止：写实渲染、3D、赛博朋克霓虹、玻璃拟态、毛玻璃、柔和投影、模糊光晕、渐变、半透明叠色、圆角卡片、照片质感、现代扁平英文排版、仅靠换色区分的图标组、调色板以外的颜色。
输出：单张 PNG，1920×1080，背景不透明。
```

## 18. ⑧ Icon style sheet (optional) · English
<!-- icons:en -->
```text
A pixel-art icon-system style sheet for a 2D eastern-xianxia game. 1920x1080 PNG (logical canvas 480x270, exact 4x upscale). Crisp pixels, no anti-aliasing, no gradients, 1px solid black outlines.

A style sheet on solid ink #12161F. Icons are grouped by frame type into six rows, each row labelled in small text at its left, four to twelve icons per row with 4px gaps.

Row 1 "skill / octagon 32x32": eight icons with inner symbols - a horizontal crescent arc / three diagonal thin swords / a vertical lightning zigzag with a square talisman / a square paper puppet with a red seal grid / a solid round flame / a hollow ring / a short fan-shaped shockwave / a hexagonal gold shield.
Row 2 "school / circle 32x32": four icons - an upright sword with a crossguard / a vertical talisman with a red seal / a trapezoid furnace on three legs / a fist with knuckles.
Row 3 "affix / diamond 16x16": twelve icons - cracked heart / lightning zigzag / broken chain ring / three wind lines / shield pattern / mirror reflection / devouring vortex / hollow ring / misaligned triangle / reversed arrow / figure in fog / shared ring.
Row 4 "realm / horizontal scroll 32x32": nine icons, four color steps increasing left to right (ink-bright, jade, violet, gold) with frame notch marks counting 1 through 9.
Row 5 "equipment / shield frame 32x32": eight icons, simple glyphs for sword / armor / crown / pendant / boots / pouch / seal / ring.
Row 6 "legacy / hexagon 32x32": six icons, six distinct inner glyphs.

Every icon: 1px pure black outline, at least 1px transparent margin all around, frame not touching the edge, no shadow, no gradient, optional 4x4 gold dot-matrix corner badge.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF.

Negative: photorealism, 3D, cyberpunk neon, glassmorphism, frosted glass, soft drop shadows, blur glow, gradients, translucent overlays, rounded cards, photoreal materials, flat modern material design, English headline typography, icon groups distinguished by color alone, any color outside the palette.
Output: single PNG, 1920x1080, opaque background.
```

---

> 生成时间：2026-11-08 17:11:29　共 18 段提示词。
