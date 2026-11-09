# 场景 / Boss / 特效提示词包（第 26 轮 · 可整段复制）

> 本文件由 `tools/build_asset_prompt_pack.py` 从 `docs/20-场景与Boss外发提示词.md` 自动抽取，**不要手改**。
> 源文档说明见 `docs/20`：UI 9 张已齐、角色 / 怪物 / 图标均已 SHIP，这批只补**塔层背景 / Boss 概念 / 形状语言**三块空白。
> 出图顺序：A 组（一次 1 个塔层）→ B 组 → C 组；**一次只出 1 组**，别把多组塞进一张图。
> 背景稿在生成平台**手动选 16:9**、导出 PNG；Boss / VFX / overlay 用方图即可。
> **A2 / A3 / A4 出图时，必须把最后两段「通用补充句」整段追加到对应背景提示词末尾**（第 27 轮 A1 回稿暴露了方图与四层不可切的问题）；B / C 组不用加。
> 回稿存 `<名字>_original.png` → `tools/snap_ui_palette.py` 吸附 → `tools/check_ui_art.py` 体检。
> **全部只算参考稿（R55），不入库**；`assets/boss/` 与 `assets/vfx/overlay/` 仍为空。


## 1. A1 常规塔层背景（第 1–3 层）· 中文
<!-- bgnormal:zh -->
```text
东方修真题材 2D 像素游戏的「塔层战斗背景」全景参考稿，一张 16:9 横版像素画，逻辑画布 480×270 整数 4 倍放大。方形像素块、硬边、无抗锯齿、无渐变、无模糊、无光晕，1px 纯黑硬描边，像素颗粒清晰锐利。

题材：九重天梯第 1–3 层的常规石塔内部。一条横向石阶平台从左到右贯穿画面下部，背后是层层向上收窄的塔身木石结构、几根立柱、垂下的经幡与两盏方形灯笼，远处透出一线天光与静止的云带。安静、克制、有重量感，不要华丽，不要仙气飘飘的光效。

画面必须自上而下明确分成四个可独立切出的深度层，层与层之间用色阶与 1px 黑描边分开，绝不使用半透明、雾气或渐变混合：
L1 远景（画面上部约 1/4）：塔身剪影与静止云带，用最亮的宣纸 #E8DFC8 与墨亮阶 #4A5568，对比度最低；
L2 中景（画面中部约 1/2）：立柱、经幡、栏杆、方形灯笼，用墨中阶 #2A3140 与金 #8A6520，中对比；
L3 地面（画面下部 1/4）：横向石阶平台，角色站立面，用宣纸中阶 #C9BFA3 铺底、墨 #2A3140 勾缝，最实最清晰；
L4 前景（画面最下缘与左右边缘）：少量遮挡物剪影，用墨暗阶 #12161F，占画面比例小于 10%，不得挡住中部战斗区。

重要对比度约束：禁止用纯墨 #12161F 大面积铺满中部战斗区（角色是墨甲深色，会糊成一团）；中景与地面必须明显浅于角色，深色物件一律加 1px 宣纸或金描边。

配色严格限定在 24 色锁定板内：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。本稿主用墨 / 宣纸 / 金三组，青玉仅作极少量灵力点缀。

禁止：写实渲染、3D、赛博霓虹、玻璃拟态、柔和投影、径向光晕、景深、渐变、雾气、半透明叠色、抗锯齿、模糊、照片质感、水墨淡彩渲染、写意笔触、圆角卡片、日式和风、韩式手游风、任何文字与汉字、水印、logo、签名、UI 元素（血条 / 按钮 / HUD / 图标框）、人物角色立绘、卡通吉祥物、调色板以外的颜色、彩色描边。

输出：单张不透明 PNG，16:9 横版画幅，无文字无 UI，画面里不出现任何角色。
```

## 2. A1 Normal tower floor (1-3) · English
<!-- bgnormal:en -->
```text
A 16:9 landscape pixel-art background reference for a 2D eastern-xianxia cultivation game. Logical canvas 480x270 scaled by an exact integer factor of 4. Square pixel blocks, hard edges, no anti-aliasing, no gradients, no blur, no glow, 1px solid black outlines, crisp visible pixels.

Subject: interior of a stone pagoda, floors 1-3 of a nine-floor tower. A horizontal stone-step platform runs across the lower part of the frame; behind it, tiered timber-and-stone pagoda structure narrowing upward, several pillars, hanging sutra banners and two square lanterns; a sliver of sky light and a still cloud band in the far distance. Quiet, restrained, weighty. No ornate magical glow.

The image MUST read as four independently sliceable depth bands, separated by tonal steps and 1px black outlines, never by translucency, fog or gradient blending:
L1 FAR (upper quarter): pagoda silhouettes and a still cloud band, in the brightest rice-paper #E8DFC8 and light ink #4A5568, lowest contrast.
L2 MID (middle half): pillars, banners, railings, square lanterns, in mid ink #2A3140 and gold #8A6520, medium contrast.
L3 GROUND (lower quarter): the horizontal stone platform where characters stand, rice-paper mid #C9BFA3 with ink #2A3140 seams, sharpest and most solid.
L4 FOREGROUND (bottom edge and left/right edges): a few occluder silhouettes in dark ink #12161F, under 10% of the frame, never covering the central combat area.

Critical contrast rule: never fill the central combat zone with large areas of pure ink #12161F (the armored enemies are dark and would disappear). Mid-ground and ground must be visibly lighter than the characters; give dark objects a 1px rice-paper or gold outline.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF. This piece uses mainly ink / rice-paper / gold, with jade only as tiny spirit-energy accents.

Negative: photorealism, 3D render, cyberpunk neon, glassmorphism, soft shadows, radial glow, depth of field, gradients, fog, translucent overlays, anti-aliasing, blur, photo textures, pastel ink-wash painting, painterly brushwork, rounded cards, ukiyo-e, Korean mobile-game style, any text or lettering, watermark, logo, signature, UI elements (health bars, buttons, HUD, icon frames), character illustrations, mascots, any color outside the palette, colored outlines.

Output: a single opaque 16:9 PNG, no text, no UI, no characters in frame.
```

## 3. A2 喘息层背景（第 3 / 6 / 8 层）· 中文
<!-- bgrest:zh -->
```text
东方修真题材 2D 像素游戏的「喘息层背景」全景参考稿，一张 16:9 横版像素画，逻辑画布 480×270 整数 4 倍放大。方形像素块、硬边、无抗锯齿、无渐变、无模糊、无光晕，1px 纯黑硬描边。

题材：九重天梯第 3 / 6 / 8 层的喘息平台——没有敌人、没有战斗。云海之上的一座露天石台，一根残碑、一座小丹炉（第 6 层回血）或一座铸器台（第 8 层铸器）居中偏右，左侧留大面积空白云气表现「留白」，画面比常规塔层更亮、更空、更安静。禁止出现敌人、宝箱、奖励弹窗、按钮。

画面必须自上而下明确分成四个可独立切出的深度层，层间用色阶与 1px 黑描边分开，不用半透明、雾气或渐变混合：
L1 远景（上部约 1/3）：宣纸亮阶 #E8DFC8 的静云带与极淡墨影 #4A5568 远山，最低对比；
L2 中景（中部约 1/3）：残碑 / 丹炉 / 铸器台与短栏，用墨中阶 #2A3140 与金 #8A6520，中对比；
L3 地面（下部约 1/4）：浅色石板平台，宣纸中阶 #C9BFA3 铺底、墨 #2A3140 勾缝；
L4 前景（最下缘与边缘）：极少量墨暗阶 #12161F 剪影，占比小于 8%，不挡中部。

重要对比度约束：本层是全塔最亮的场景，禁止纯墨 #12161F 大面积铺底；浅宣纸底要占画面一半以上，保证深色角色站上去一眼可辨。云带用**分段色块 + 1px 黑描边**表现，不许用半透明或柔边。

配色严格限定在 24 色锁定板内：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。本稿主用宣纸三阶 + 墨亮阶，金与青玉只作小面积点缀。

禁止：写实渲染、3D、赛博霓虹、玻璃拟态、柔和投影、径向光晕、景深、渐变、雾气、半透明叠色、抗锯齿、模糊、照片质感、水墨淡彩渲染、写意笔触、日式和风、韩式手游风、任何文字与汉字、水印、logo、签名、UI 元素、奖励弹窗、宝箱、敌人、人物角色立绘、卡通吉祥物、调色板以外的颜色、彩色描边。

输出：单张不透明 PNG，16:9 横版画幅，无文字无 UI，画面里不出现任何角色。
```

## 4. A2 Rest floor (3 / 6 / 8) · English
<!-- bgrest:en -->
```text
A 16:9 landscape pixel-art "rest floor" background reference for a 2D eastern-xianxia cultivation game. Logical canvas 480x270 at exactly 4x integer scale. Square pixel blocks, hard edges, no anti-aliasing, no gradients, no blur, no glow, 1px solid black outlines.

Subject: a breather platform on floors 3 / 6 / 8 of a nine-floor tower - no enemies, no combat. An open-air stone terrace above a sea of clouds, one weathered stele, and a small alchemy furnace (floor 6 healing) or a forging bench (floor 8 crafting) placed right of center. The left half is largely empty cloud negative space. Brighter, emptier and quieter than the normal combat floors. No enemies, treasure chests, reward popups or buttons.

The image MUST read as four independently sliceable depth bands separated by tonal steps and 1px black outlines, never by translucency, fog or gradient blending:
L1 FAR (upper third): still cloud bands in bright rice-paper #E8DFC8 and very light ink #4A5568 distant peaks, lowest contrast.
L2 MID (middle third): stele / furnace / forging bench and a short railing in mid ink #2A3140 and gold #8A6520, medium contrast.
L3 GROUND (lower quarter): pale stone slabs in rice-paper mid #C9BFA3 with ink #2A3140 seams.
L4 FOREGROUND (bottom and side edges): a few dark ink #12161F silhouettes, under 8% of the frame, never covering the center.

Critical contrast rule: this is the brightest location in the tower; never fill large areas with pure ink #12161F. Light rice-paper tones must cover more than half the frame so dark characters stay readable. Cloud bands are built from stepped color blocks with 1px black outlines - no translucency, no soft edges.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF. Mainly the three rice-paper steps plus light ink; gold and jade only as small accents.

Negative: photorealism, 3D render, cyberpunk neon, glassmorphism, soft shadows, radial glow, depth of field, gradients, fog, translucent overlays, anti-aliasing, blur, photo textures, pastel ink-wash painting, painterly brushwork, ukiyo-e, Korean mobile-game style, any text or lettering, watermark, logo, signature, UI elements, reward popups, chests, enemies, character illustrations, mascots, any color outside the palette, colored outlines.

Output: a single opaque 16:9 PNG, no text, no UI, no characters in frame.
```

## 5. A3 高层复合敌群背景（第 7 层）· 中文
<!-- bghigh:zh -->
```text
东方修真题材 2D 像素游戏的「高层复合敌群背景」全景参考稿，一张 16:9 横版像素画，逻辑画布 480×270 整数 4 倍放大。方形像素块、硬边、无抗锯齿、无渐变、无模糊、无光晕，1px 纯黑硬描边。

题材：九重天梯第 7 层「天劫词缀」高压层。破损的悬空石桥、断裂的栏杆、倾斜的塔身石柱，天幕上有数道细而硬的紫 / 朱砂色裂隙（词缀印文的视觉暗示），地面散落方形符纸残片。气氛比常规层更紧、更冷，但仍保持像素色块与留白，不要画成魔幻特效大场面。

画面必须自上而下明确分成四个可独立切出的深度层，层间用色阶与 1px 黑描边分开，不用半透明、雾气或渐变混合：
L1 远景（上部约 1/4）：墨亮阶 #4A5568 的天幕 + 紫 #4A3A6B / #8A6FC4 的硬边裂隙，裂隙是折线色块不是发光；
L2 中景（中部约 1/2）：断裂石柱与倾斜塔身，墨中阶 #2A3140 + 紫暗阶 #4A3A6B，中对比；
L3 地面（下部约 1/4）：悬空石桥桥面，宣纸中阶 #C9BFA3 铺底、墨 #2A3140 勾缝、朱砂 #7A2420 少量符纸残片；
L4 前景（最下缘与边缘）：墨暗阶 #12161F 断栏剪影，占比小于 10%，不挡中部战斗区。

重要对比度约束：禁止纯墨 #12161F 大面积铺满中部战斗区；紫色只用于天幕裂隙与中景暗部，地面与角色站立面必须是浅宣纸，保证墨甲阴兵与青玉剑魂都能读清。天幕裂隙不许用光晕 / 辉光 / 半透明。

配色严格限定在 24 色锁定板内：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。

禁止：写实渲染、3D、赛博霓虹、玻璃拟态、柔和投影、径向光晕、辉光、景深、渐变、雾气、半透明叠色、抗锯齿、模糊、照片质感、水墨淡彩渲染、写意笔触、日式和风、韩式手游风、任何文字与汉字、水印、logo、签名、UI 元素（血条 / 按钮 / HUD / 词缀面板）、敌人、人物角色立绘、卡通吉祥物、调色板以外的颜色、彩色描边。

输出：单张不透明 PNG，16:9 横版画幅，无文字无 UI，画面里不出现任何角色。
```

## 6. A3 High-floor mixed wave (7) · English
<!-- bghigh:en -->
```text
A 16:9 landscape pixel-art "high-floor mixed-enemy wave" background reference for a 2D eastern-xianxia cultivation game. Logical canvas 480x270 at exactly 4x integer scale. Square pixel blocks, hard edges, no anti-aliasing, no gradients, no blur, no glow, 1px solid black outlines.

Subject: floor 7 of a nine-floor tower, the high-pressure "tribulation affix" floor. A broken suspended stone bridge, snapped railings, leaning pagoda pillars, and several thin hard-edged violet / cinnabar cracks across the sky (a visual hint of affix seals), with square talisman-paper scraps scattered on the ground. Tenser and colder than the normal floors, but still built from restrained pixel color blocks and negative space - not a magical VFX spectacle.

The image MUST read as four independently sliceable depth bands separated by tonal steps and 1px black outlines, never by translucency, fog or gradient blending:
L1 FAR (upper quarter): sky in light ink #4A5568 with hard-edged violet #4A3A6B / #8A6FC4 cracks - angular color blocks, not glowing light.
L2 MID (middle half): broken pillars and leaning pagoda masonry in mid ink #2A3140 and dark violet #4A3A6B, medium contrast.
L3 GROUND (lower quarter): suspended bridge deck in rice-paper mid #C9BFA3 with ink #2A3140 seams and a few cinnabar #7A2420 talisman scraps.
L4 FOREGROUND (bottom and side edges): dark ink #12161F broken-railing silhouettes, under 10% of the frame, never covering the central combat area.

Critical contrast rule: never fill the central combat zone with pure ink #12161F. Violet belongs only to sky cracks and mid-ground shadow; the ground and the characters' standing surface must stay light rice-paper so both the dark-ink armored soldier and the jade sword wraith remain readable. No glow, bloom or translucency on the sky cracks.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF.

Negative: photorealism, 3D render, cyberpunk neon, glassmorphism, soft shadows, radial glow, bloom, depth of field, gradients, fog, translucent overlays, anti-aliasing, blur, photo textures, pastel ink-wash painting, painterly brushwork, ukiyo-e, Korean mobile-game style, any text or lettering, watermark, logo, signature, UI elements (health bars, buttons, HUD, affix panels), enemies, character illustrations, mascots, any color outside the palette, colored outlines.

Output: a single opaque 16:9 PNG, no text, no UI, no characters in frame.
```

## 7. A4 Boss 层背景（第 5 / 9 层）· 中文
<!-- bgboss:zh -->
```text
东方修真题材 2D 像素游戏的「Boss 层背景」全景参考稿，一张 16:9 横版像素画，逻辑画布 480×270 整数 4 倍放大。方形像素块、硬边、无抗锯齿、无渐变、无模糊、无光晕，1px 纯黑硬描边。

题材：九重天梯第 5 层「锁血判官」与第 9 层「天梯之主」共用的殿宇式战场。一座对称的石殿内部，深处一尊无面判官像轮廓（只作建筑剪影，不是可互动 Boss）、两排高柱、地面圆形法阵纹样（用硬边几何色块画，不许发光）、顶部垂下的巨幅经幡。威严、静止、压迫感来自对称构图与体量，不来自光效。

画面必须自上而下明确分成四个可独立切出的深度层，层间用色阶与 1px 黑描边分开，不用半透明、雾气或渐变混合：
L1 远景（上部约 1/4）：墨亮阶 #4A5568 + 宣纸亮阶 #E8DFC8 的高窗与殿顶暗部；
L2 中景（中部约 1/2）：对称高柱、判官像建筑剪影、经幡，墨中阶 #2A3140 + 金 #8A6520 / #D9A441，中对比；
L3 地面（下部约 1/4）：石砖 + 圆形法阵纹样，宣纸中阶 #C9BFA3 铺底、墨 #2A3140 勾缝、朱砂 #7A2420 描法阵内圈；
L4 前景（最下缘与边缘）：墨暗阶 #12161F 柱基剪影，占比小于 10%，不挡中部战斗区。

重要对比度约束：禁止纯墨 #12161F 大面积铺满中部战斗区；Boss 与角色站立面必须是浅宣纸石砖，深色柱体一律加 1px 金或宣纸描边，保证 128×128 的 Boss 与墨甲杂兵都能读清。法阵是几何色块，不许发光 / 辉光 / 半透明。

配色严格限定在 24 色锁定板内：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，闪白 #FFFFFF。本稿主用墨 / 宣纸 / 金，朱砂只用于法阵内圈。

禁止：写实渲染、3D、赛博霓虹、玻璃拟态、柔和投影、径向光晕、辉光、景深、渐变、雾气、半透明叠色、抗锯齿、模糊、照片质感、水墨淡彩渲染、写意笔触、日式和风、韩式手游风、任何文字与汉字、水印、logo、签名、UI 元素（Boss 血条 / 阶段条 / 按钮 / HUD）、人物角色立绘、Boss 立绘、卡通吉祥物、调色板以外的颜色、彩色描边。

输出：单张不透明 PNG，16:9 横版画幅，无文字无 UI，画面里不出现任何角色或 Boss。
```

## 8. A4 Boss floor (5 / 9) · English
<!-- bgboss:en -->
```text
A 16:9 landscape pixel-art "boss floor" background reference for a 2D eastern-xianxia cultivation game. Logical canvas 480x270 at exactly 4x integer scale. Square pixel blocks, hard edges, no anti-aliasing, no gradients, no blur, no glow, 1px solid black outlines.

Subject: the hall-style arena shared by floor 5 (the Blood-Lock Judge) and floor 9 (the Lord of the Tower). A symmetrical stone hall interior: a faceless judge statue silhouette deep in the background (architecture only, not an interactive boss), two rows of tall pillars, a circular formation pattern on the floor drawn as hard-edged geometric color blocks (must not glow), and huge sutra banners hanging from the ceiling. Solemn, still; the sense of pressure comes from symmetry and scale, not from lighting effects.

The image MUST read as four independently sliceable depth bands separated by tonal steps and 1px black outlines, never by translucency, fog or gradient blending:
L1 FAR (upper quarter): high windows and ceiling shadow in light ink #4A5568 and bright rice-paper #E8DFC8.
L2 MID (middle half): symmetrical pillars, the architectural judge silhouette and banners in mid ink #2A3140 with gold #8A6520 / #D9A441, medium contrast.
L3 GROUND (lower quarter): stone tiles and a circular formation, rice-paper mid #C9BFA3 with ink #2A3140 seams and a cinnabar #7A2420 inner ring.
L4 FOREGROUND (bottom and side edges): dark ink #12161F pillar-base silhouettes, under 10% of the frame, never covering the central combat area.

Critical contrast rule: never fill the central combat zone with pure ink #12161F. The boss and character standing surface must be pale rice-paper tiles; give dark pillars a 1px gold or rice-paper outline so a 128x128 boss and dark-armored minions both stay readable. The formation is geometric color blocks - no glow, bloom or translucency.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, flash #FFFFFF. Mainly ink / rice-paper / gold, with cinnabar only on the formation's inner ring.

Negative: photorealism, 3D render, cyberpunk neon, glassmorphism, soft shadows, radial glow, bloom, depth of field, gradients, fog, translucent overlays, anti-aliasing, blur, photo textures, pastel ink-wash painting, painterly brushwork, ukiyo-e, Korean mobile-game style, any text or lettering, watermark, logo, signature, UI elements (boss health bar, phase bar, buttons, HUD), character illustrations, boss illustrations, mascots, any color outside the palette, colored outlines.

Output: a single opaque 16:9 PNG, no text, no UI, no characters or bosses in frame.
```

## 9. B 两个 Boss 概念立绘 · 中文
<!-- boss:zh -->
```text
东方修真题材 2D 像素游戏的「两个 Boss 概念立绘」参考稿，一张方图，画面左右等分为两格，每格放一个 128×128 内容区的 Boss 单帧全身像素立绘，两格之间留 16px 纯白间隔。背景统一纯白 #FFFFFF（生成后规整为透明底）。方形像素块、硬边、无抗锯齿、无渐变、无模糊、无光晕、1px 纯黑硬描边，脚底锚点两格落在同一水平像素行，底部留至少 1px 透明边。

左格「锁血判官」（第 5 层小 Boss）：中等体量的冥府判官，方角官帽、宽袖墨色官袍、胸前一块方形朱砂印牌、手持一支竖向朱笔；姿态静止、正面朝右，轮廓以横向宽肩 + 下垂长袍的梯形为主，气质冷硬克制，不狰狞。

右格「天梯之主」（第 9 层塔主）：明显更高更宽，层叠高冠、金线勾边的宽袍、背后一圈由硬边几何色块构成的半环背光（不许发光）、双手交叠于身前；轮廓以高耸纵向 + 外扩肩甲为主，与左格的横向梯形一眼可分。三阶段靠色段与纹样区分，本稿只画第一阶段的青玉 + 墨 + 金配色，不要画三个形态。

两个 Boss 都必须与已有 64×64 的 4 种小怪（山魈 / 纸傀 / 阴兵 / 剑魂）在体量与剪影上明确拉开差距；不要画动作帧、不要画血条、不要画背景场景、不要画坐骑或武器特效。

配色严格限定在 24 色锁定板内：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，底色 #FFFFFF。

禁止：写实渲染、3D、赛博霓虹、柔和投影、径向光晕、辉光、渐变、半透明叠色、抗锯齿、模糊、照片质感、水墨淡彩渲染、写意笔触、日式和风、韩式手游风、任何文字与汉字、水印、logo、签名、UI 元素（血条 / 阶段条 / 名字牌）、多格动作序列帧、背景场景、人物小怪立绘、卡通吉祥物、调色板以外的颜色、彩色描边。

输出：单张 PNG，纯白底，只有两个并排的 Boss 单帧立绘，无文字无 UI。本图是概念参考稿，不入库；正式 18 / 24 帧帧表另按素材工单产出。
```

## 10. B Two boss concepts · English
<!-- boss:en -->
```text
A square pixel-art "two boss concept" reference sheet for a 2D eastern-xianxia cultivation game. Split the frame into equal left and right cells, each holding one full-body 128x128 boss sprite, with a 16px pure-white gutter between cells. Uniform pure white #FFFFFF background (to be regularized into transparency later). Square pixel blocks, hard edges, no anti-aliasing, no gradients, no blur, no glow, 1px solid black outlines. Both sprites' foot anchors sit on the same horizontal pixel row, with at least 1px clear padding below.

LEFT cell - "Blood-Lock Judge" (floor 5 mini-boss): a medium-build underworld magistrate with a square-cornered official hat, wide-sleeved ink robe, a square cinnabar seal plaque on the chest, and a vertical vermilion brush. Static pose, facing right. Silhouette dominated by broad horizontal shoulders and a trapezoidal hanging robe. Cold, stern, restrained - not monstrous.

RIGHT cell - "Lord of the Tower" (floor 9 final boss): visibly taller and wider, layered tall crown, wide robe edged with gold lines, a half-halo behind built from hard-edged geometric color blocks (must not glow), hands folded in front. Silhouette dominated by a tall vertical axis and flared shoulder plates - instantly distinguishable from the left cell's horizontal trapezoid. The three phases are differentiated by color segments and motif counts; draw only the phase-1 jade + ink + gold palette here, not three forms.

Both bosses must clearly outscale and out-silhouette the four existing 64x64 mobs (shanxiao / paper puppet / yin soldier / sword wraith). No animation frames, no health bars, no background scenery, no mounts, no weapon VFX.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, background #FFFFFF.

Negative: photorealism, 3D render, cyberpunk neon, soft shadows, radial glow, bloom, gradients, translucent overlays, anti-aliasing, blur, photo textures, pastel ink-wash painting, painterly brushwork, ukiyo-e, Korean mobile-game style, any text or lettering, watermark, logo, signature, UI elements (health bar, phase bar, nameplate), multi-frame animation sheets, background scenery, mob illustrations, mascots, any color outside the palette, colored outlines.

Output: a single PNG on pure white, containing only the two side-by-side single-frame boss sprites, no text and no UI. This is a concept reference, not an in-game asset; the formal 18 / 24 frame tables are produced separately from the asset work order.
```

## 11. C1 剩余 4 技能形状语言板 · 中文
<!-- vfx:zh -->
```text
东方修真题材 2D 像素游戏的「技能特效形状语言参考板」，一张方图，2×2 四格，每格一个 64×64 内容区的单帧像素特效，格与格之间留 8px 纯白间隔，背景统一纯白 #FFFFFF（生成后规整为透明底）。方形像素块、硬边、无抗锯齿、无渐变、无模糊、无光晕、1px 纯黑硬描边，特效四周留至少 1px 透明边，每格特效居中、不出血。

四格从左到右、从上到下依次为四个尚未定义形状的技能的「峰值帧」，只画形状与方向，不画施法者、不画角色、不画伤害数字：
第 1 格「御剑诀」：**斜向**三道细长飞剑，左下到右上平行排列，青玉 #5FA8A0 为主、宣纸 #E8DFC8 勾剑脊，三把剑长度略有递进；
第 2 格「纸傀术」：**方形**符纸逐层旋转展开成傀儡剪影，宣纸 #C9BFA3 底 + 朱砂 #7A2420 方形印文，外轮廓是明确的正方形 / 阶梯方形；
第 3 格「破山拳罡」：**短距扇形**冲击波贴地推进，墨 #2A3140 与金 #D9A441 交替的硬边扇面，扇形开口朝右，底边平贴地面；
第 4 格「金刚不坏」：**六边形**金罩包裹一个空的人形轮廓位置，金 #D9A441 / #F2D089 的 1px 六边网格 + 宣纸 #E8DFC8 内部留白，罩内不画角色。

形状语言铁律：这 4 个形状必须与项目已有的 4 个形状（横向弯月弧 / 纵向落雷 / 实心圆火 / 空心环光）在**轮廓与方向**上一眼可分，两两不得重复；颜色只作辅助，不许靠加新颜色区分。全部形状用少量色阶平涂，不许渐变、辉光或粒子噪声。

配色严格限定在 24 色锁定板内：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，底色 #FFFFFF。

禁止：写实渲染、3D、赛博霓虹、柔和投影、径向光晕、辉光、渐变、半透明叠色、抗锯齿、模糊、粒子噪声、照片质感、水墨淡彩渲染、写意笔触、任何文字与汉字、水印、logo、签名、UI 元素、人物角色立绘、敌人、伤害数字、动作序列帧、背景场景、调色板以外的颜色、彩色描边。

输出：单张 PNG，纯白底，只有 2×2 四个形状，无文字无 UI。本图只用于定义形状语言 / 给程序化特效配参数，不铺序列帧、不入库。
```

## 12. C1 Remaining 4 VFX shape sheet · English
<!-- vfx:en -->
```text
A square pixel-art "skill VFX shape language" reference sheet for a 2D eastern-xianxia cultivation game. A 2x2 grid, each cell one 64x64 single-frame pixel effect, 8px pure-white gutters between cells, uniform pure white #FFFFFF background (to be regularized into transparency later). Square pixel blocks, hard edges, no anti-aliasing, no gradients, no blur, no glow, 1px solid black outlines, at least 1px clear padding around each effect, centered and not bleeding out of its cell.

The four cells are the PEAK frames of the four skills whose shapes are not yet defined, reading left-to-right then top-to-bottom. Draw only shape and direction - no caster, no character, no damage numbers:
Cell 1 "Flying Sword": THREE thin long swords on a DIAGONAL, parallel from lower-left to upper-right, jade #5FA8A0 with rice-paper #E8DFC8 blade ridges, slightly progressive lengths.
Cell 2 "Paper Puppet": a SQUARE talisman sheet rotating open layer by layer into a puppet silhouette, rice-paper #C9BFA3 base with cinnabar #7A2420 square seal marks; the outer contour is an explicit square / stepped square.
Cell 3 "Mountain-Breaking Fist Force": a SHORT FAN-SHAPED shockwave pushing along the ground, hard-edged fan in alternating ink #2A3140 and gold #D9A441, opening to the right, flat bottom edge flush with the ground.
Cell 4 "Vajra Body": a HEXAGONAL gold shell around an EMPTY humanoid silhouette position, a 1px hexagonal lattice in gold #D9A441 / #F2D089 with rice-paper #E8DFC8 inner negative space; no character inside.

Shape-language rule: these four shapes must be instantly distinguishable in SILHOUETTE and DIRECTION from the project's four existing shapes (horizontal crescent arc / vertical lightning bolt / solid circular fire / hollow ring), with no two alike. Color is only a supporting cue - do not introduce new colors to tell them apart. Flat fills with few tonal steps; no gradients, glow or particle noise.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, background #FFFFFF.

Negative: photorealism, 3D render, cyberpunk neon, soft shadows, radial glow, bloom, gradients, translucent overlays, anti-aliasing, blur, particle noise, photo textures, pastel ink-wash painting, painterly brushwork, any text or lettering, watermark, logo, signature, UI elements, character illustrations, enemies, damage numbers, animation frame sequences, background scenery, any color outside the palette, colored outlines.

Output: a single PNG on pure white, containing only the 2x2 shape grid, no text and no UI. This sheet only defines the shape language / feeds procedural VFX parameters - no frame sequences, not an in-game asset.
```

## 13. C2 5 组状态 overlay 形状板 · 中文
<!-- overlay:zh -->
```text
东方修真题材 2D 像素游戏的「状态 overlay 形状参考板」，一张方图，5 行 × 2 列共 10 格，每格一个 64×64 内容区的单帧像素 overlay，格与格之间留 8px 纯白间隔，背景统一纯白 #FFFFFF（生成后规整为透明底）。方形像素块、硬边、无抗锯齿、无渐变、无模糊、无光晕、1px 纯黑硬描边；overlay 本身是**空心 / 线框**结构，中心必须留出透明区域，不画被覆盖的角色。

5 行从上到下依次为 5 组状态，每行两格是同一状态的第 1 / 第 2 帧，只做轻微脉动（轮廓缩放 1px 或纹样位移 1px），形状完全一致：
第 1 行 `ovl_shield` 护盾：青玉 #5FA8A0 / #9BD4CC 的六边网格空心光罩轮廓，中心空；
第 2 行 `ovl_elite` 霸体 / 精英：金 #D9A441 / #F2D089 的 1px 外描边 + 四角斜切角标，沿一个空的人形外轮廓走，中心空；
第 3 行 `ovl_burn` 灼烧：朱砂 #C8453B / #E8806F 的三簇方形火苗，贴底部边缘分布，中心空；
第 4 行 `ovl_chill` 迟缓：青玉 #2F6E6A / #9BD4CC 的硬边六角冰晶碎片，贴底部与两侧分布，中心空；
第 5 行 `ovl_affix` 天劫词缀：朱砂 #7A2420 的方形印文 + 四角小菱形标记，位于画面上方与四角，中心空。

形状语言铁律：5 组状态靠**轮廓形状与位置**区分，不靠加新颜色；两帧之间只允许 1px 级脉动，不许出现渐变、半透明、辉光或粒子噪声。全部 overlay 必须能叠在 64×64 角色身上而不遮住主体，所以内部留白面积 ≥ 70%。

配色严格限定在 24 色锁定板内：墨 #12161F #2A3140 #4A5568，宣纸 #8A8268 #C9BFA3 #E8DFC8，青玉 #2F6E6A #5FA8A0 #9BD4CC，朱砂 #7A2420 #C8453B #E8806F，金 #8A6520 #D9A441 #F2D089，紫 #4A3A6B #8A6FC4 #C0A8E0，描边 #000000，底色 #FFFFFF。

禁止：写实渲染、3D、赛博霓虹、柔和投影、径向光晕、辉光、渐变、半透明叠色、抗锯齿、模糊、粒子噪声、照片质感、水墨淡彩渲染、写意笔触、任何文字与汉字、水印、logo、签名、UI 元素、人物角色立绘、敌人、实心色块填满中心、背景场景、调色板以外的颜色、彩色描边。

输出：单张 PNG，纯白底，只有 5×2 十个 overlay 形状，无文字无 UI。本图只作形状参考；程序化案可直接用 shader 实现，不铺序列帧、不入库。
```

## 14. C2 Five status overlay shapes · English
<!-- overlay:en -->
```text
A square pixel-art "status overlay shape" reference sheet for a 2D eastern-xianxia cultivation game. A 5-row x 2-column grid of 10 cells, each holding one 64x64 single-frame pixel overlay, 8px pure-white gutters between cells, uniform pure white #FFFFFF background (to be regularized into transparency later). Square pixel blocks, hard edges, no anti-aliasing, no gradients, no blur, no glow, 1px solid black outlines. Each overlay is a HOLLOW / WIREFRAME structure - the center MUST stay empty; do not draw the character being covered.

The five rows are five status groups, top to bottom. The two cells in each row are frame 1 and frame 2 of the same state, differing only by a subtle pulse (1px contour scale or 1px motif shift), with identical silhouettes:
Row 1 `ovl_shield`: hollow hexagonal-lattice dome outline in jade #5FA8A0 / #9BD4CC, empty center.
Row 2 `ovl_elite`: a 1px gold #D9A441 / #F2D089 outer outline plus four diagonally cut corner marks, following an EMPTY humanoid contour, empty center.
Row 3 `ovl_burn`: three clusters of square cinnabar #C8453B / #E8806F flames along the bottom edge, empty center.
Row 4 `ovl_chill`: hard-edged hexagonal ice shards in jade #2F6E6A / #9BD4CC along the bottom and sides, empty center.
Row 5 `ovl_affix`: a square cinnabar #7A2420 seal mark plus small diamond corner marks, placed at the top and four corners, empty center.

Shape-language rule: the five states are told apart by CONTOUR SHAPE and PLACEMENT, never by new colors. Only 1px-level pulsing between the two frames; no gradients, translucency, glow or particle noise. Every overlay must sit on a 64x64 character without hiding it, so at least 70% of each cell stays empty.

Strictly limited to the 24-color locked palette: ink #12161F #2A3140 #4A5568, rice-paper #8A8268 #C9BFA3 #E8DFC8, jade #2F6E6A #5FA8A0 #9BD4CC, cinnabar #7A2420 #C8453B #E8806F, gold #8A6520 #D9A441 #F2D089, violet #4A3A6B #8A6FC4 #C0A8E0, outline #000000, background #FFFFFF.

Negative: photorealism, 3D render, cyberpunk neon, soft shadows, radial glow, bloom, gradients, translucent overlays, anti-aliasing, blur, particle noise, photo textures, pastel ink-wash painting, painterly brushwork, any text or lettering, watermark, logo, signature, UI elements, character illustrations, enemies, solid fills covering the center, background scenery, any color outside the palette, colored outlines.

Output: a single PNG on pure white, containing only the 5x2 overlay shapes, no text and no UI. This is a shape reference only; the procedural approach may implement these directly in a shader - no frame sequences, not an in-game asset.
```

## 15. A2/A3/A4 通用补充句（第 27 轮回稿后必加）· 中文
<!-- bgpatch:zh -->
```text
【通用补充句 · 追加到 A2 / A3 / A4 背景提示词末尾，与上文同时使用；以下硬指标优先于题材描述】

画幅与四深度层比例严格按下列指标执行：
- 画幅必须是 16:9 横版。生成平台若有画幅选项，手动选 16:9，不要出方图。
- 画面自上而下四层严格按「上部 1/4 远景 / 中部 1/2 中景 / 下部 1/4 地面 / 最下缘与左右边缘前景」分配；四层之间必须有清晰的水平色阶分界，能沿水平线各自独立切图。
- L1 远景以浅宣纸 #E8DFC8 为主，深色像素在该带内不超过 20%；远处塔身 / 山影剪影只出现在 L1 内，绝不向下贯穿到 L2 战斗区。
- L2 中景的立柱、栏杆、经幡彼此之间要留浅色缝隙，不许连成一整块深色；画面中部 x 20%–80% 的战斗区里，浅宣纸色块要占一半以上，深色像素不超过 30%，保证墨甲深色角色站上去一眼可辨。
- L3 地面石阶平台必须完整占据下部 1/4，用宣纸中阶 #C9BFA3 铺底，是全场最实最亮的一带。
- L4 前景剪影只允许出现在最下缘窄条与左右边缘，总面积小于 10%；禁止在画面下部画大面积深色台基、拱洞、链条或柱头剪影，禁止把下方 1/4 整片压成暗色。
- 全图深墨系（#12161F / #2A3140 / #4A5568 / #000000）合计不超过 55%，浅宣纸系（#8A8268 / #C9BFA3 / #E8DFC8）合计不低于 30%。

禁止：上下深色夹击中部、对称巨大深色塔影占据画面中央、下部整片暗色前景、任何跨层的连续深色块。四层之间不许用半透明、雾气或渐变过渡，只许用色阶与 1px 黑描边分界。
```

## 16. A2/A3/A4 General addendum (round 27, required) · English
<!-- bgpatch:en -->
```text
[GENERAL ADDENDUM - append to the END of the A2 / A3 / A4 background prompts and use together with the text above; these hard rules override the subject description]

Aspect ratio and four depth bands must follow these rules:
- The frame MUST be 16:9 landscape. If the generation platform offers an aspect-ratio control, select 16:9 manually; do not output a square image.
- Allocate the four bands top-to-bottom strictly as: upper quarter FAR / middle half MID / lower quarter GROUND / bottom edge and left-right edges FOREGROUND. The bands must have clear horizontal tonal boundaries so each can be sliced out independently along a horizontal line.
- L1 FAR is dominated by bright rice-paper #E8DFC8, with dark pixels under 20% within that band. Distant pagoda or mountain silhouettes appear ONLY in L1 and must never extend down into the L2 combat zone.
- In L2 MID, pillars, railings and banners must leave light gaps between them - never merge into one continuous dark mass. In the central combat zone (x 20%-80% of the frame), light rice-paper blocks must cover more than half and dark pixels must stay under 30%, so dark armored characters remain readable.
- L3 GROUND: the stone platform must occupy the full lower quarter, filled with rice-paper mid #C9BFA3, and be the most solid and brightest band in the frame.
- L4 FOREGROUND silhouettes appear only as a narrow strip at the very bottom and at the left/right edges, under 10% of total area. No large dark plinths, arches, chains or pillar-cap silhouettes in the lower part; never press the whole lower quarter into darkness.
- Across the whole frame, dark ink tones (#12161F / #2A3140 / #4A5568 / #000000) must stay under 55% combined, while light rice-paper tones (#8A8268 / #C9BFA3 / #E8DFC8) must reach at least 30% combined.

Negative: dark bands squeezing the middle from above and below, a huge symmetrical dark pagoda silhouette filling the center, a fully dark lower foreground, any continuous dark mass crossing band boundaries. Bands are separated ONLY by tonal steps and 1px black outlines - never by translucency, fog or gradients.
```

---

> 生成时间：2026-11-09 00:10:21　共 16 段提示词。
