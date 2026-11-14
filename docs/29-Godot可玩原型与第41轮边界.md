# 29 · Godot 可玩原型与第 41 轮边界

> 用户指令：「卡先这样，继续做游戏」。
> 本轮把**游戏本体**从「只有网页验证层」推进到「Godot 里能按 F5 玩」。
> 状态：**PROPOSAL / 可玩原型 / headless 已验证 / GUI 画面未目检 / 不得当作已完成游戏**。

---

## 0. 一句话

此前 Godot 侧只有 `MinimalRun.tscn`（主角 A/D 左右跑，阶段二门禁验证）加三个纯逻辑脚本
（`CardDeck.gd` / `BattleFormula.gd` / `CardArtView.gd`），**没有任何战斗场景、UI、层间循环**；
完整原型一直只存在于 `previews/web-demo.html` 的六视图里。
本轮按 `docs/01` §12 节点树新建 `scenes/TowerRun.tscn`，把主菜单 → 9 层横版战斗 →
层间三选一 → 下一层 → 败/通关结算 → 重开做成一条真闭环，并把 `run/main_scene` 指向它。

**「卡先这样」的理解（明确写死）**：第 40 轮那 4 档 07-codex 风格卡框**仍是候选、不采用**，
`docs/12` §2 冻结口径与 `assets/ui/cards/` 10 张冻结卡面**一个字节不动**（R61 不解除）。
游戏内卡面 = 冻结卡框 + `assets/ui/card_art/` 的 72 张一卡一插画 + 引擎文字层；
第 40 轮的 3 个拍板问题（整卡深墨底、信息条短标签、是否改写冻结规格）**全部搁置，不代为决定**。

---

## 1. 门禁口径（越界即违规）

| 项 | 本轮状态 |
|---|---|
| 冻结文档 `docs/01` / `11` / `12` | **未改**，§12 节点树表与 §2 卡面口径逐字节保留 |
| `assets/ui/cards/` 10 张冻结卡面 | **未改**，sha256 与 `docs/codex-card-frames-report.json` 逐张一致 |
| 冻结数值 / 概率 / 权重 / 规则 | **未改**；9 层波形与伤害公式只读引用 `BattleFormula` |
| 抽取规则 | 完全交给 `CardDeck`（xorshift32 确定性，R47 跨端同源），本轮不改算法 |
| 伤害红线 | `BattleFormula.damage_formula()` 五上界钳制，最坏 `maxHit=3996 < 4400`（R32 / DF-21） |
| 07 候选卡框 | **不引用**；源码里零 `res://previews/card_frames_codex` 引用 |
| Q17 | **未拍板**；用户「继续做游戏」视为「授权做可玩本体」，**不等于**「界面定稿 / 正式工程开工」 |
| GUI F5 目检 | **未跑**；headless 只证明能加载、能编译、状态机能走通，不代表画面已验证 |
| 资源状态 | 仍为「待目检与合规确认；不得直接入库」 |

`project.godot` 只改了 3 行配置：`config/name`、`config/description`、
`run/main_scene="res://scenes/TowerRun.tscn"`。`MinimalRun.tscn` **完整保留**，
编辑器里单独打开它按 **F6（运行当前场景）** 即可回到门禁验证。
**一行回退**：把 `run/main_scene` 改回 `res://scenes/MinimalRun.tscn`。

---

## 2. 节点树与新增文件

按 `docs/01` §12「一个场景一职责」：

```
TowerRun (Node2D)                 scripts/TowerRun.gd        局内根 / 9 层推进 / 结算
├ Stage (Node2D)                  scripts/StageView.gd      单层横版战斗 / 清层判定
│ ├ Backdrop / Player / Enemies / VfxLayer / Floats（运行时构建）
├ HUD (CanvasLayer)               scripts/RunHUD.gd         血量/灵力/层数/技能 CD
├ RewardPicker (CanvasLayer)      scripts/RewardPicker.gd   层间三选一
├ MenuLayer (CanvasLayer)         TowerRun 动态构建          主菜单
└ ResultLayer (CanvasLayer)       TowerRun 动态构建          结算 / 重开
```

辅助：
- `scripts/RunConfig.gd`：所有 PROPOSAL 占位常量、24 色取用色、输入映射、CJK 主题、资源路径。
- `tools/verify_tower_run.gd`：headless 20 项断言，写 `docs/tower-run-verify-report.json`。
- `docs/29`（本文件）、`tools/final_selfcheck.py` 第 39 项 `tower_run_r41`。

**`CardArtView.gd` / `CardArtView.tscn`（第 39 轮）本轮才第一次被真正接进可玩循环**：
`RewardPicker` 逐张 `CardArtView.new()` → `show_card(id, rarity, name, cat)`，
卡框取 `frame_<rarity>.png`、纹样取 `sigil_<cat>.png`、插画取 `<card_id>.png`。

---

## 3. 可玩闭环

| 状态 | 进入方式 | 操作 |
|---|---|---|
| MENU | 启动 / 结算后 | 点「开始入塔」或按 Enter |
| BATTLE | 开局 / 选完卡 | **A/D** 移动、**J/K/L/I** 四技能、**Space** 闪避、**Esc** 暂停 |
| DRAFT | 清层后（第 1–8 层） | 鼠标点 3 张候选之一；无倒计时 |
| RESULT | 第 9 层清层 / HP 归零 | 显示到达层数、本局卡牌、伤害红线；点按钮或 Enter 重开 |

- 战斗：背景按层型取 4 张 480×270 原稿转录合成图；角色 / 敌人 / Boss / 4 技能特效全部用**真帧**，
  按 `facing` 只镜像 Sprite 本身（DF-04）；技能同帧算伤害 + 飘字 + 特效；
  敌人向玩家靠近并按间隔攻击，走位与闪避无敌帧可以躲。
- 清层条件：该层所有敌人 HP 归零 → `stage_cleared(layer)` → 三选一。
  第 9 层后不弹卡，直接结算（`drawRule` / `LAST_DRAW_STAGE=8`）。
- 抽卡：`CardDeck.offer(layer)` 确定性给 3 张（同层同类最多 1 张、本局已选卡不再出现）；
  `CardDeck.pick()` 落地**触碰五上界变量**的效果，下一层立刻反映到伤害与减伤上。
- 封牌 / 舍牌（R49）导致候选为空时**直接推进、不伪造三选一**。
- **不设 6 s 强制窗口**：R33 未拍板，原型允许读完再点；`docs/11` §6 的口径不改。

---

## 4. 数值来源：冻结 vs PROPOSAL（不许混）

**只读冻结**（不在原型里重定义）：
- `BattleFormula.stages()`：9 层 `hp / dps / t / d / type / mobs`（`docs/01` §8.3 逐行照抄）。
- `BattleFormula.damage_formula()`：`raw=(b*r+p)*c*cr*(1-d)` + 六项 clamp + `1..9999`。
- `BattleFormula.skills_frozen()` 对应的 4 技能 id / 名称 / VFX / 方向（`docs/06` §4）。

**PROPOSAL 占位**（全部集中在 `scripts/RunConfig.gd`，与 `tools/battle_sim.js` 的
`PROPOSAL` / `SKILLS` / `MOBS` 同源；**策划案未给值、待设计确认、不是平衡结论**，R51）：

| 组 | 常量 |
|---|---|
| 玩家 | `PLAYER_MAX_HP=300` / `PLAYER_MAX_SPIRIT=100` / `SPIRIT_REGEN=9` / `PLAYER_MAX_STAMINA=100` / `STAMINA_REGEN=12` / `MOVE_SPEED=96` |
| 技能 | 4 槽 `cd / spirit / base / reach / hits / heal`、`CAST_LOCK=0.18` |
| 反馈 | `CRIT_CHANCE=0.10` / `COMBO_GAIN_PER_HIT=0.08` / `COMBO_DECAY=0.12` / `VFX_LIFETIME=0.28` |
| 闪避 | `DODGE_COST=25` / `DODGE_INVULN=0.42` / `DODGE_SPEED=190` |
| 敌人 | `ENEMY_ATTACK_BASE=9` / `ENEMY_ATTACK_PER_STAGE=3.2` / `ENEMY_ATTACK_INTERVAL=1.9` / `ENEMY_MOVE_SPEED=42` / `ENEMY_ATTACK_RANGE=88` / 各怪 `defense / speed` |

暴击判定用本地 xorshift32（与 `CardDeck` 同族），**只作用于表现层**，不参与任何可复算规则；
战斗逐 tick 状态机**仍未跨端对齐**（R56），不得宣称「网页测过 = Godot 一致」。

---

## 5. 明确不实现（写死，不假装已做）

1. **46 张卡的非五上界 hook**（`RunState.*` / `VfxLayer.*` / `signal.*` / `MetaSave.*` / `UI.pick_event`）：
   选中后只登记在 `TowerRun.picks`，不改变战斗表现（`docs/18` / R54）。
2. **M2 境界 / M3 装备·传承灵韵 / 局外存档 / 本地埋点 / 音频**：原型是纯局内单局，重开即清零；
   「每局结束必须产生 ≥1 项长期收益」尚未成立。
3. **6 s 读卡窗口（R33）**、`combo_hash` 区分度（R34）、夺主改 `k` 后重算 `B`（R35）、
   4× 实机排版（R48）、封牌 8 次（R49）、12 项 PROPOSAL 数值（R51）——**一律未拍板、未实测**。
4. **Boss 三阶段色、装备 / 词缀 / 灵韵联动、镜头震动、音效**、以及 `docs/01` §6 的完整 M1 状态表
   （CASTING / DODGING / DEAD 只做了可玩近似，不是穷举实现）。
5. **中文字体**：引擎内置字体不含 CJK（R46 / R9）。GUI 下用 `SystemFont` 运行时调用本机系统字体
   （`PingFang SC` 等），**不打包任何字体资产、不碰 R9 授权**；headless 下跳过以避免 FreeType 空字体报错。
   **导出跨端时仍需另解**，GUI 下中文是否成字仍待用户 F5 核实。

---

## 6. headless 证据

```
Godot --headless --path . --script res://tools/verify_tower_run.gd
```

`docs/tower-run-verify-report.json`：**20/20 PASS**，其中：

| 断言 | 结果 |
|---|---|
| 场景加载 / 6 节点齐 / 主场景指向 / MinimalRun 保留 | PASS |
| 卡库 72 / 72 张插画 / 10 张冻结卡面 / 9 层 / 4 背景 / 4 技能特效首帧 | PASS |
| 伤害红线 `maxHit=3996 / 4400` | PASS |
| `offer(1)` 两次一致（确定性） | `["card_danxiang","card_poyun","card_shouyuan"]` |
| 菜单 → 战斗 → 清层 → 三选一 → 第 2 层 | PASS |
| 完整 9 层循环 → `run_ended` 1 次 → **win** / 到达第 9 层 / 选卡 8 次 / 红线未破 | PASS |

另复跑 `Godot --headless --path . --quit-after 5`（F5 配置路径，无编译错误）
与 `tools/verify_minimal_run.gd`（旧门禁场景仍 PASS）。
`tools/final_selfcheck.py` 新增第 39 项 `tower_run_r41`，**全量 39/39 PASS**。

> headless 不渲染画面。像素硬边、24 色、480×270×4 对齐、中文字形、卡面 4× 排版、
> 手感与平衡**全部仍需用户按 F5 目检**，不得把本表写成「画面已验证」。

---

## 7. 用户侧下一步（最小动作）

1. 用 Godot 4.7.2 打开工程（首次会扫描并注册 `class_name`，本机已跑过一次），按 **F5**：
   主菜单 → 开始入塔 → 打一层 → 看三选一卡面 → 选一张 → 继续，确认没有红字 / 中文不是豆腐块 /
   卡面插画落在框内 / 文字不糊。有红字把 Output 全文发回。
2. 按 `docs/13` §9 的 10 项目检表过一遍（第 8 项正好验 96×144 卡面 4× 排版）。
3. 要回门禁验证：编辑器里单独打开 `scenes/MinimalRun.tscn` 按 **F6**。
4. 仍待拍板：Q17（是否进入界面定稿 / 正式工程）、R61（是否采用 07 候选框并改写 `docs/12`）、
   R33 / R34 / R35 / R48 / R49 / R51。**不点头就不动冻结规格、不替换 10 张卡面。**
