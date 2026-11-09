# 13 · Godot 导入与本机配置指南（阶段二预备）

> **状态：阶段二导入指南（工程已交付）。** 第 13 轮产出本指南、第 14 轮确认 `Q1=4.7.2`、**第 15 轮用户「策划案整体确认」→ 已合并 `01` v0.2、已产出 `docs/design-freeze.json`（`frozen`）、已建最小验证工程**。§1–§11 保留第 13/14 轮历史问答；**当前可执行的清单以 §12 为准**。
> 触发：用户说明「没有 Godot 开发经验，但想用 Godot 引擎、觉得比 three.js 效果更好」，并问「你做好后会不会指导我导入？还有没有需要我自己配置的地方？」
> 适用口径：`04` 像素国风规格、`01` 策划案、`asset-manifest-pixel.json`（v2）。文中路径一律为项目内相对路径或 Godot 通用路径写法，**不写机器绝对路径**。
> 全部引擎 API 以 Godot 官方文档对应版本为准；本指南的操作步骤尚未在用户本机实机走通，标「待实测」。

---

## 1. 三个问题的直答

| 问题 | 答案 |
|---|---|
| 会不会指导我导入？ | **会，而且这是阶段二的第一步交付。** 我会把导入做成「按顺序点几下」的清单，并附自检脚本；遇到报错你把控制台原文或截图发我，我改文件，不需要你写代码。 |
| 有没有要我自己配置的地方？ | **有，但都是一次性的本机操作，共 7 件（§5），没有一件要写 GDScript。** 其中只有「安装导出模板」是真正必须你动手装的东西，其余是拖一下 app、点几下菜单、按 F5。 |
| 我完全没用过 Godot，能行吗？ | 能。项目把 90% 的配置写死在工程文件里了（§6）；你只需要会三个操作：**导入项目、按 F5、看画面**。但有两件我替不了：实机目检（§9）和字体授权的法律决定（R9）。 |

**⚠️ 一个必须先说清的前提**：现在**还没有「做好」的工程**。按你自己定的硬门禁，项目仍处于阶段一（策划标准）。顺序是：
`✅ 确认 Q1（第 14 轮已完成）→ 用户整体确认策划案 → 合并 01 v0.2 → design-freeze.json 置 frozen → 建工程 → 按本指南导入`。
**当前只差「整体确认策划案」这一句**；在此之前不合并 v0.2、不置 frozen、不建工程，动工程会违反你自己立的规矩。
（第 13 轮初稿此处把「合并 v0.2」写在「整体确认」之前，与 `00` §9 不一致，第 14 轮已按 `00` 口径校正。）

---

## 2. 引擎选型判断（先纠一个说法）

你说「相比 three.js 可能效果更好」。这里我想直说：**对这款游戏，差别主要不在「画面效果」，而在「你要自己造多少轮子」**——而且 three.js 的花活对像素画反而是负资产。

| 维度 | Godot 4.x（当前案） | three.js |
|---|---|---|
| 渲染定位 | 原生 2D 管线（`CanvasItem` / `Sprite2D` / `AnimatedSprite2D`） | WebGL 3D 库，做 2D 需自建正交相机 + 精灵图集 + 批处理 |
| 像素保真 | 纹理过滤设 `Nearest`、关 mipmap、整数倍缩放、`viewport` 拉伸模式，都是内建项 | 需自己处理纹理采样、`devicePixelRatio`、着色器插值，一不小心就糊 |
| 动作 / 碰撞 | `CharacterBody2D` + `Area2D` 判定框 + `SpriteFrames` 动画 + 信号，现成 | 碰撞、状态机、帧动画、输入映射全要自己搭 |
| 关卡 / 数据 | `TileMap`、`.tres` 资源、Autoload 单例、`user://` 本地存档、CSV/JSON 直接读 | 用 `localStorage` / `IndexedDB` 代替存档，资源加载与打包自建 |
| 分发 | 编辑器一键导出桌面 `.app` / `.exe`（需导出模板，见 §3） | 起 HTTP 服务或套 Electron；浏览器还有音频自动播放、字体加载策略 |
| 强项 | 单机桌面 2D、看得见的节点树、报错直观 | **浏览器即点即玩、发个链接就能给别人试**；自定义后处理 / shader 更自由 |

**判断**：本项目是「单机桌面 + 2D 像素国风 + 横版即时战斗 + 本地元进度存档」，且 `04` 把风格锁死成 **24 色 / 硬边 / 无抗锯齿 / 整数 4 倍**。three.js 擅长的 bloom、自定义 shader、透视/光照在这里不但用不上，还会破坏「不插值」的像素纪律；而 Godot 把像素对齐、动画、判定、存档、导出都做成了内建项。**维持 Godot 原案，不改引擎。**

唯一值得保留的备选：如果将来目标变成「发个链接给朋友点开就玩」，再单独评估 Godot 的 Web 导出（对像素游戏有音频策略、字体、包体积的坑）或 three.js。**这是二期话题，不进一期，也不改 `04`。**

**代价也要说清**：Godot 的门槛不是写代码，是**编辑器操作**（项目管理器、导入、文件系统面板、按 F5、看输出面板）；three.js 的门槛则是前端工程（Node、打包、浏览器调试）。对零基础，前者明显更平缓。

---

## 3. 本机环境实测（第 13 轮，只读探测，未改动任何系统文件）

| 项 | 探测结果 | 对 Q1 的影响 |
|---|---|---|
| Godot 版本 | **`4.7.2.stable.official.ed1daf0bf`**（`--version` 实测） | Q1 的技术部分已有确定值 |
| 构建类型 | **标准版**，非 .NET/Mono 版（可执行文件只有 `Godot`） | 用 GDScript 即可，不需要 C# SDK |
| app 位置 | 在**本机下载目录**中的 `Godot.app`，不在系统 Applications 目录 | 建议拖进 Applications（§5 ①），否则容易被当下载垃圾清掉 |
| 首次打开 | 带 Safari 下载的隔离属性（`com.apple.quarantine`） | 首次可能弹「无法验证开发者」，需右键 → 打开（§5 ②） |
| **导出模板** | Godot 用户数据目录下的 `export_templates/` **是空目录 → 未安装** | **Q1 第二问的答案：没装。** 不装不影响编辑器里按 F5 跑，只是无法导出独立 app（§5 ③） |
| 项目历史 | 编辑器的 `projects.cfg` 为 0 字节 | 本机从未建过 / 打开过项目，与「没有开发经验」一致，无需担心旧配置冲突 |

> **第 14 轮更新（Q1 已解除）**：用户回「**没错是 4.7.2**」，正式回执写入 `Q1=4.7.2.stable`（数字来自用户答复、`.stable` 来自本机探测的发布通道，**助手未代填**）。`apply_decisions.py --apply` 重跑结果：**16/16 项已答、硬门禁 4/4、错误 0、告警 1**（R29/R30 的 `01` 正文修订）。证据：`docs/decision-receipt.json` / `decision-plan.json` / `decision-receipt-user.txt`。
> 探测值保留在上表，避免换账号后重复排查；**导出模板仍未安装**（不装也能在编辑器按 F5 运行）。
> 另：拿到版本号**不等于** `docs/SkillCaster.gd` 已验证——脚本里的信号、`clampf/clampi`、`Autoload` 写法仍需在 4.7.2 编辑器里跑一遍，「Godot 编辑器验证」依旧是待办（见 `00` §6「未完成」）。

---

## 4. 责任边界（本指南的核心）

### 4.1 我写文件，你零操作

| 交付物 | 内容 |
|---|---|
| `project.godot` | 窗口 1920×1080、`viewport` 480×270、拉伸模式 `viewport` + `keep` 比例、默认纹理过滤 `Nearest`、输入映射（移动 / 技能 1–4 / 交互 / 暂停）、Autoload 名单（`MetaSave` 等）、主场景、渲染与 2D 像素对齐设置 |
| 目录结构 + `.tscn` / `.gd` / `.tres` | 场景树、节点、脚本、资源；`SkillCaster.gd` 的 4 个信号挂接点；CSV/JSON 数据表读法 |
| **每张图的 `.import` 预设** | `Nearest` / 关 mipmap / 无压缩 / 不修改 alpha / 不缩放。⭐ 见 §7 坑 1 |
| 卡面文字层 | 字体确认后按 `12` 的 6 区坐标渲染（当前卡面 PNG 不含文字，避开 R9） |
| 导入清单 + 自检脚本 | 逐步操作清单、目录核对、命名/尺寸/色板复核，复用现有 `qc_sprites.py` / `check_traceability.py` |
| 报错修订 | 你发来控制台报错或截图 → 我改对应文件 → 你重新 F5 |

### 4.2 只能你在本机做（都不用写代码）

| # | 事项 | 次数 | 是否必需 |
|---|---|---|---|
| ① | 把 `Godot.app` 从下载目录拖进系统 Applications 目录 | 一次 | 建议，非必需 |
| ② | 首次打开解除 macOS 隔离（右键 → 打开 → 打开） | 一次 | 必需（否则打不开） |
| ③ | 安装**导出模板**（编辑器 → Manage Export Templates → Download and Install，需联网） | 一次 | **只在要导出独立 app 时必需**；只在编辑器里跑可以跳过 |
| ④ | 导入项目（双击 `project.godot`，或项目管理器 Import → 选目录） | 一次 | 必需 |
| ⑤ | 按 F5 跑起来，按 §9 清单目检 | 每次改动 | **必需，且我替不了** |
| ⑥ | 字体授权最终拍板（凤凰点阵体 CC0 候选 / Zpix 商用收费且禁改） | 一次 | **必需，属法律决定**（R9） |
| ⑦ | 若要把游戏发给别人：选导出平台、处理 macOS 签名/公证 | 分发时 | 可选，二期 |

> **我明确做不到的**：我不能直接操控你屏幕上的 Godot 编辑器 GUI，不能替你按 F5，也不能凭空判断「像素有没有糊」「阴兵在深背景里看得清吗」「8fps 节奏对不对」——这些必须靠你的眼睛和本机显示器。我能做的是把配置写死、把检查项列清楚，让你按顺序点、按项看。

---

## 5. 用户侧逐步操作（阶段二开工时照做）

**① 安放 app（建议）**：把下载目录里的 `Godot.app` 拖到系统 Applications 目录。理由：下载目录常被清理，且带隔离属性。

**② 首次启动**：在 Applications 里**右键 Godot → 打开 → 再点「打开」**（或系统设置 → 隐私与安全性 → 「仍要打开」）。这是因为 app 从 Safari 下载带隔离标记，正常现象，一次即可。成功后会看到 Godot 项目管理器。

**③ 装导出模板（要导出才装）**：编辑器菜单 `Editor → Manage Export Templates` → `Download and Install`，选择与 **4.7.2.stable 完全匹配**的模板包（版本不匹配会报错），需联网、体积数百 MB。**不装也能 F5 在编辑器里玩**；只是 `Project → Export` 会提示缺模板、导不出可双击的 `.app` / `.exe`。

**④ 导入项目**：我交付工程后，双击工程目录里的 `project.godot`；或项目管理器 → `Import` → 选到工程目录 → `Import & Edit`。Godot 会首次扫描资源并生成 `.godot/` 缓存（这是正常的，别删）。⚠️ 不要选到 `xianxia-tower/` 的父目录，也不要把 `docs/` 当工程目录。

**⑤ 运行**：按 `F5`（或右上角播放键）→ 选主场景。第一次若弹「未设置主场景」，告诉我，我改 `project.godot`。

**⑥ 目检**：按 §9 逐项看。有报错就把**输出面板（Output）的红色文字**复制给我，或截个图。

**⑦ 导出（可选）**：`Project → Export` → 添加 macOS / Windows 预设 → 选路径 → Export Project。macOS 上自己本机双击能跑；发给别人可能被 Gatekeeper 拦，需要签名/公证，那是一期之后的事。

---

## 6. 我会写死在 `project.godot` 里的关键设置（供核对）

| 设置 | 值 | 来源 |
|---|---|---|
| 显示窗口宽高 | 1920 × 1080 | `01` A2 / `04` §2 |
| 基础 viewport | 480 × 270，`×4` 整数放大 | `04` §2、`asset-manifest-pixel.json` |
| 拉伸模式 | `viewport` / `keep`（letterbox，禁止非整数缩放） | `04` R10 |
| 纹理默认过滤 | `Nearest`（**逐张 `.import` 也要覆盖**） | `04` §2、24 色硬边 |
| mipmap / 压缩 | 关闭 / 无损 | 像素硬边纪律 |
| 2D 像素对齐 | 开启 `snap 2D transforms to pixel` 类设置，锚点统一整数行 | `00` M7 |
| 输入映射 | 左右移动、跳跃、技能 1–4、交互、暂停、层间选卡 1/2/3 + Enter | `01` / `11` / `12` |
| Autoload | `MetaSave` 等（Q8 已按回执定为 Autoload + JSON） | `docs/decision-receipt.json` |
| 本地存档 | `user://`（含 M6 本地日志 `user://telemetry/runs.jsonl`，不联网不上传） | Q28 / R29 |
| 语言 / 字体 | 简中；字体待 R9 授权核验后挂 UI 文字层 | `12` §4 |

> **第 15 轮更新**：上表是第 13 轮的计划值；实际落地值由 `tools/bootstrap_project.gd` 交给 **4.7.2 引擎自己写进 `project.godot`**，并已用 headless 实测核对（键名、合法枚举、默认值见 §12）。**最小验证工程只实现了「显示宽高 / viewport / 拉伸 / 纹理过滤 / 左右输入」这几项**；技能 1–4、跳跃、Autoload、字体、层间选卡输入属于正式工程，本轮**未写**，不要误以为已全部落地。

---

## 7. 三个最容易踩的坑（新手必看）

1. **Godot 默认纹理过滤是 Linear，会把像素画插值成糊团。** 4.7.2 实测 `rendering/textures/canvas_textures/default_texture_filter` 默认就是 **1（Linear）**，合法枚举 `Nearest / Linear / Linear Mipmap / Nearest Mipmap`；已显式设为 **0（Nearest）**（§12 附引擎输出为证）。`.import` 由编辑器导入时自己生成，我**不手写引擎生成物**；交付前已用 `--headless --editor --quit` 导入过一次（229 项；**第 16 轮清理预览目录与画板后现 196 项**），所以你打开工程时资源已可用。若 F5 后角色边缘仍发虚，八成是这一项，把截图发我。
2. **非整数缩放 / 窗口拉伸**。480×270 必须 ×4 = 1920×1080；若窗口被拖成任意尺寸且拉伸模式设错，像素会不等比。用 `keep` + letterbox，黑边是正常的，别为了填满窗口改比例。
3. **朝右一套 + `scale.x` 镜像**（`04`）：镜像只作用于角色与特效节点，光源统一顶光，否则左右朝向会出现「阴阳脸」（R11）。另外 `hitboxOffsetX=16px` 小于特效半宽 32px，能量弧可能盖住角色主体——`00` §5 已记录，**必须实机目检**，必要时改 40px 口径。

---

## 8. 我的建议：先做「最小验证工程」，别一次全导

你没用过 Godot，我建议**不要**第一步就把 142 项素材 + 72 张卡 + 全部数据表一口气灌进去。先做一个 10 分钟能跑通的小工程：

- 只放 `project.godot` + 1 个场景 + 主角 15 帧 + 一个能左右跑的脚本；
- 目的只验三件事：**像素是否 Nearest 不糊、480×270×4 对齐、左右镜像是否正确**；
- 顺带把 `② 首次启动` / `④ 导入` / `⑤ F5` 这三个操作练熟，并建立「报错 → 发我 → 我改文件」的协作节奏；
- 验证通过后再导入全量素材与卡牌系统，出错范围小得多。

这也正好对齐项目里挂了很久的 **R22 引擎实测**（阴兵深色场景对比度、`hitboxOffsetX=16px`、剑魂 8fps 试播）——这些本来就只能靠实机看，用最小工程先看一遍最省事。

**第 15 轮更新**：门禁已全部解除，这个最小验证工程**已按本节描述建好并交付**，见 §12。范围与本节一致：只放主角 `idle 3 + run 4` 共 7 帧、左右跑、朝右镜像，不灌 142 项素材与 72 张卡。

---

## 9. 导入后的目检清单（F5 之后逐项打勾）

| # | 检查项 | 通过标准 | 关联 |
|---|---|---|---|
| 1 | 像素边缘 | 放大到 4× 仍是硬边方块，无发虚 / 无插值渐变 | §7 坑 1、M7 |
| 2 | 窗口比例 | 1920×1080 满屏；拖小窗口是等比 letterbox，不拉伸 | R10 |
| 3 | 角色镜像 | 向左跑时轮廓正确、光向不穿帮、挂件跟手 | R11 |
| 4 | 帧表播放 | idle3 / run4 / cast4 / hit1 / death3 切换无跳帧；剑魂 8fps 节奏是否可读 | `00` §6 |
| 5 | 判定框 | `hitboxOffsetX=16px` 下能量弧不盖住角色；必要时试 40px | `00` §5 |
| 6 | 阴兵辨识度 | 深色塔内场景里墨 + 深青的阴兵仍能一眼认出 | R22 |
| 7 | 24 色板 | 无越界色、无半透明像素（离线已由 `qc_report.json` 保证，实机看调色是否被渲染改掉） | M7 |
| 8 | 卡牌三选一 | 96×144 卡面 4× 排版不错位；文字层不糊；6 s 窗口是否够读 | `12`、R33 |
| 9 | 本地存档 | 关掉再开，元进度 / 灵韵仍在；`user://` 无联网请求 | Q28、R29 |
| 10 | 控制台 | Output 面板无红色报错（黄色警告逐条判断） | — |

> **第 15 轮状态区分**：第 1 / 2 / 3 / 4（部分）/ 7 / 10 的**配置与资源加载**已在 4.7.2 headless 通过（见 §12 验证输出），但「画面是否真的不糊、镜像是否穿帮、24 色是否被渲染改掉」必须靠你的眼睛按 F5 看，**仍标待实测**。第 5 / 6 / 8 / 9 项（判定框 / 阴兵 / 卡牌三选一 / 本地存档）在最小验证工程里根本没有对应内容，**本轮不适用**，等正式工程再做。不得把 headless 通过写成「画面已验证」。

---

## 10. 出问题时的配合方式

1. 复制 **Output 面板红色报错全文**（含文件路径与行号），或截图；
2. 说明「刚才做了哪一步」和「期望看到什么 / 实际看到什么」；
3. 我定位后改对应文件（`.import` / `project.godot` / `.gd` / `.tscn`），告诉你重跑哪一步；
4. 不建议你自己手改脚本或 `.import`——容易和 `04` 的 24 色 / 硬边纪律冲突，改完也难复现。

---

## 11. 当前状态（第 15 轮，不要误读历史段落）

| 状态 | 内容 |
|---|---|
| ✅ **已做** | 合并 `01` v0.2（`docs/01-策划案.md`；v0.1 全文归档）、产出 `docs/design-freeze.json`（`frozen`）、建最小验证工程、让 **4.7.2 引擎自己**生成 `project.godot` 与 229 项 `.import`（现 196 项）、headless 加载验证、离线结构自检 |
| ❌ **未做** | 在**图形界面**里按 F5 看画面、装导出模板、导出独立 `.app`、R9 字体授权拍板、R22 阴兵对比度 / `hitboxOffsetX` / 剑魂 8fps 实机目检、B3 Boss 与 B4 剩余技能素材、正式战斗工程与卡牌运行时 |
| 🔒 **未变** | 引擎选型维持 Godot 4.7.2；`04` 像素规格、24 色锁定板、既有全部素材与 72 张卡设计一律不受影响；导出模板仍未装（不装也能 F5） |
| ⚠️ **仍在** | R37（用户零引擎经验，需分步可视化指导）→ 对策就是 §8 的最小验证工程 + §9 清单 + 报错回收闭环 |

- `docs/design-freeze-draft.json` 仍是 `draft`（阶段一历史快照），**不是**冻结清单；当前权威是 `docs/design-freeze.json`。
- 本文所有引擎 API、菜单名、默认值均以 Godot 4.7.2 官方文档为准；已在 headless 实测的部分见 §12，GUI 走通后回填差异。

---

## 12. 最小验证工程交付说明（第 15 轮，可直接照做）

### 12.1 交付了哪些文件

| 文件 | 作用 |
|---|---|
| `project.godot` | **由 Godot 4.7.2 引擎自己生成**（`tools/bootstrap_project.gd` 调 `ProjectSettings.save()`），不是我手写猜键名 |
| `.gitignore` | 忽略 `.godot/` 引擎缓存与构建产物 |
| `scenes/MinimalRun.tscn` | 主场景：`MinimalRun` → `Backdrop` / `Ground` / `GroundBody(StaticBody2D)` / `Player(CharacterBody2D)` → `AnimatedSprite2D` + `Body(CollisionShape2D)` + `Feet(Marker2D)` |
| `scripts/PlayerProbe.gd` | 主角 `idle 3 + run 4` 帧、左右跑、`scale.x=±1` 镜像；`# @trace DF-04, DF-12, DF-13, DF-15` |
| `previews/` | 三个 miora 预览画板（`首批/第二批/第三批像素素材.miora`）及其素材副本，**已加 `.gdignore`，引擎不扫描**；纯交付物，不参与运行时 |
| `tools/bootstrap_project.gd` | 幂等重建工程配置；换账号可直接重跑 |
| `tools/verify_minimal_run.gd` | headless 加载验证脚本 |
| `docs/project-spec.json` | 工程规格（`requireFrozenDesign=true`） |
| `docs/asset-manifest-godot.json` | **v2 像素生效规格**，供结构自检核对资源（v1 水墨 256px 清单是归档基线，不得拿来判本工程） |
| `docs/godot-project-check.json` | 结构自检报告 |
| `docs/design-freeze.json` | 冻结清单 `status=frozen`、22 条 DF 编号 |

### 12.2 引擎实测证据（不是「应该能跑」）

配置取证（引导器让引擎自己打印）：

```
BOOTSTRAP|display/window/stretch/mode|default=disabled|hint=disabled,canvas_items,viewport
BOOTSTRAP|rendering/textures/canvas_textures/default_texture_filter|default=1|hint=Nearest,Linear,Linear Mipmap,Nearest Mipmap
BOOTSTRAP|save_err=0
```

→ 拉伸模式 `viewport` 合法；纹理过滤**默认 1（Linear）**，已显式改成 `0（Nearest）`；引擎保存成功。

加载验证（导入资源后；第 16 轮起含碰撞体断言）：

```
VERIFY|scene=MinimalRun|children=4
VERIFY|player=Player|script_attached=true
VERIFY|collision=Player/Body+GroundBody/Shape present|player_shape=RectangleShape2D|player_bottom=216.0|ground_top=216.0
VERIFY|sprite_node=AnimatedSprite2D|frames_before=false
VERIFY|idle_frames=3|run_frames=4|idle_fps=6.0|run_fps=8.0
VERIFY|main_scene=res://scenes/MinimalRun.tscn
VERIFY|viewport=480x270
VERIFY|window_override=1920x1080
VERIFY|stretch_mode=viewport
VERIFY|texture_filter=0 (0=Nearest)
VERIFY|input_move_left=true|input_move_right=true
VERIFY|PASS
```

> **`player_bottom = ground_top = 216.0`**：主角碰撞形状底边与地面碰撞体顶边**严格对齐**，离线已验证不会陷地或悬空。**画面上脚底是否与地面线贴合仍要你 F5 看**（像素帧内脚的实际位置）。

> **一个要如实说明的细节**：`--headless --script` 模式下 `root.add_child()` 不自动触发节点的 `_ready()`，验证脚本显式调了一次才拿到 `SpriteFrames`。**编辑器里按 F5 时由引擎正常触发**，这不是工程缺陷。
> 另一处：编辑器 headless 导入退出时打过一条 `rename_error != 0`（写编辑器布局的临时文件），属 headless 退出噪音，资源导入 `[DONE] reimport` 已完成、229 项 `.import` 齐全（第 16 轮清理预览目录与画板后现 196 项）。

### 12.3 结构自检结论

`check_godot_project.py --freeze docs/design-freeze.json` → **通过，错误 0 项 / 警告 2 项**：

| 警告 | 判读 |
|---|---|
| 冻结条目 22 个，工程引用覆盖率 **4/22 = 18%** | **真实进度**。最小验证工程只实现 DF-04 / DF-12 / DF-13 / DF-15；其余属正式工程。按纪律**不塞标记凑数**，两套追溯脚本口径已统一为只认 `@trace` |
| `docs/godot-project-check.json` 疑似含机器绝对路径 | 检查器把自己的工程绝对路径写进了 JSON 报告，属**自指**。工程其他文件绝对路径 0 处（已独立复核），不是工程里残留了路径 |

项目自有 `tools/check_traceability.py` 同期 PASS：draft 仍 `frozen=false`、正式清单 `frozen`、22 条合法唯一、覆盖率同为 4/22。

### 12.4 你现在只要做 4 步

1. （建议）把 `Godot.app` 从下载目录拖进「应用程序」；首次打开若弹「无法验证开发者」，**右键 → 打开**。
2. **双击工程根目录的 `project.godot`**（就是本项目的 `xianxia-tower/` 文件夹里那个）。资源已在交付前导入过，不用等它慢慢扫。
3. **切到 2D 视图**：首次打开默认停在 **3D 视图**（看到网格地面 + 红绿蓝坐标轴，是正常的）。按键盘 **`2`**，或点视口左上角的 **「透视 / 正交」切换按钮旁的「2D」标签**，画面应变成 480×270 的纯色背景 + 地面色块。
4. 按 **F5**（或右上角 ▶ 运行）→ 弹出游戏窗口，用 `A/D` 或 `←/→` 跑主角，按 §9 清单目检。**窗口是 1920×1080 满屏、像素硬边方块**，就是你该看到的画面。

> 第 16 轮补充：编辑器节点面板上 `Player` 曾经带一个黄色三角警告（`CharacterBody2D` 没有碰撞形状子节点）。**已修复**：场景改为 `Player` → `AnimatedSprite2D` + `Body(CollisionShape2D)`，并新增 `GroundBody(StaticBody2D)` 作为真实地面。你在编辑器里可能需要**右键场景 → 重载 / 或关闭标签页重新打开**才能看到新节点树。

导出模板仍不用装：不装也能在编辑器里 F5；只有想导出可双击的 `.app` 时才需要（编辑器 → Manage Export Templates → Download and Install）。

### 12.5 边界（必须说清）

- **没有在图形界面里按过 F5**。headless 只验证了「场景能解析、脚本能编译、7 张 PNG 能加载、配置值正确」；**像素糊不糊、镜像穿不穿帮、深背景对比度，只能靠你的眼睛**。
- 这个工程**不是游戏**：没有战斗、没有卡牌、没有存档、没有 Boss。它只是把门禁跑通的一块样板。正式工程按 `01` §12 节点树另建。
- 报错时按 §10 把 Output 面板红字全文或截图发我，我改对应文件后你重跑；不建议自己手改 `.gd` / `.import`。

### 12.6 交付后收口（R39 / 全量自检）

- **`docs/.gdignore` 是空文件，别删**：它让 Godot 编辑器**跳过整个 `docs/` 目录**扫描。原因：4.7 把 `docs/卡牌库.csv` / `docs/数值框架.csv` 当成 CSV 翻译表导入，生成了 24 个 `.translation` / `.csv.import` 垃圾文件。这两份是设计数值源、不参与运行时，已清理并在 `.gitignore` 加了兜底规则。`res://assets/` 与 `res://scenes/` 不在 `docs/` 下，资源导入与加载不受影响，headless 复验仍 PASS。
- `tools/final_selfcheck.py` / `docs/final-selfcheck.json` 是交付前的全量静态自检（JSON / CSV / 脚本编译 / 冻结 / 红线 / 产物 / 绝对路径 / 过期状态 / `.gdignore`），动态侧另跑伤害验算、两套追溯、工程结构检查与 4.7.2 headless 加载。**全部 PASS 仍不等于 GUI 画面通过**，§12.5 边界不变。
- **四路动态复验实测结果**：伤害验算 PASS（3996 < 4400 / 违规 0）、追溯核对 PASS（4/22 = 18.18%）、工程结构自检**错误 0 / 警告 2 / 通过**、4.7.2 headless `VERIFY|PASS`。复跑时曾因 `design-freeze-draft.json` 两处占位符编号报 1 错误（**R40**），已按描述性文字修正、未删条目也未抑制检查，复跑归零；`final_selfcheck.py` 加了防回归断言。静态自检最终 **20/20 PASS**。
### 12.7 第 16 轮：首次打开后修的两处（R41 / R42）

**你在编辑器里看到的两个现象，来源如下：**

| 现象 | 真实原因 | 处置 |
|---|---|---|
| `Player` 节点上的**黄色三角警告**「该节点没有描述其形状的子节点」 | `Player` 是 `CharacterBody2D`，却只有 `AnimatedSprite2D` 子节点，**没有 `CollisionShape2D`**。Godot 因此挂警告，且 `move_and_slide()` 不会与任何物体碰撞 | 场景改为 `Player` → `AnimatedSprite2D` + **`Body(CollisionShape2D)`**（32×56），并新增 **`GroundBody(StaticBody2D)`** 作为真实地面（480×54，顶 y=216）+ `Feet(Marker2D)` 标脚底。headless 断言 `player_bottom == ground_top == 216.0` |
| 文件面板里出现 `首批/第二批/第三批像素素材_assets` | 三个 miora 预览画板连同素材副本被直接放在**工程根目录**，引擎会当资源扫描并生成多余 `.import` | 整体移入 **`previews/`** 并加空 `previews/.gdignore`（**别删**）；`assets/_preview/` 同样加 `.gdignore` 并清理 31 个拼图 `.import`。画板仍可正常打开，游戏资源 181 项导入不受影响 |

**另外**：首次打开默认停在 **3D 视图**（网格地面 + 红绿蓝坐标轴），这是正常的。按 **`2`** 键或点视口左上角 **`2D`** 标签切到 2D 视图再 F5。

**改完文件后编辑器不会自动重载场景**：右键场景标签 → **重载**，或关掉 `MinimalRun` 标签页重新打开。
### 12.8 第 16 轮（续）· R43：帧改成真正的 SpriteFrames 资源

**你在编辑器里看到的第三个现象**：`Sprite` 节点报「必须先在『Sprite Frames』属性中新建或设置 SpriteFrames 资源，才能让 AnimatedSprite2D 显示动画帧」。

- **原因**：原实现的 `SpriteFrames` 是 `PlayerProbe.gd` 在 `_ready()` 里用 `SpriteFrames.new()` + `add_frame()` **动态拼**出来的，运行时才有，编辑器静态视图拿不到 → 既报警告又预览不到帧。
- **处置**：新增 `tools/build_sprite_frames.gd`，由 **4.7.2 引擎自己** `ResourceSaver.save()` 写出 `assets/char/player_frames.tres`（**不手写引擎资源格式**；生成后回读校验 `idle=3 / run=4`）。`scenes/MinimalRun.tscn` 的 `AnimatedSprite2D` 直接挂这个资源并设 `animation = &"idle"`；脚本保留「资源缺失才动态构建」的兜底分支。
- **现在应该看到**：选中 `Sprite` 节点，Inspector 的 **Sprite Frames** 处不再是空，而是一个含 `idle`（3 帧 / 6fps）与 `run`（4 帧 / 8fps）两组动画的资源；视口里能直接看到角色贴图（切 2D 视图后）。**节点面板不再有黄色警告。**
- **headless 复验**：`VERIFY|sprite_node=AnimatedSprite2D|frames_before=true`（帧来自资源而非脚本）。

> **正式工程沿用这条规矩**：所有角色的帧都要做成 `SpriteFrames` 资源并挂到场景，**不要在脚本里动态拼帧**——否则编辑器无法预览、也无法在 Inspector 里核对帧表。
