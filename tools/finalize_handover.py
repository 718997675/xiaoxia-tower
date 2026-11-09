#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交接回填脚本（第 15 轮收口 + 第 16 轮 GUI 反馈轮）：文档去自相矛盾 + R39/R40/R41/R42 处置 + 数值源/台账/日志回填。

纪律：
  * 每个替换锚点必须唯一命中 1 次，否则整批中止、不写半成品；
  * 已收口的锚点（新文本已在、旧文本已不在）计为 skipped，可重复运行；
  * 数值源一律「永远追加不覆盖」；
  * 文档里不写机器绝对路径，一律项目内相对路径。
用法：python3 tools/finalize_handover.py
"""
from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs"
HANDOVER = DOC / "00-项目交接与进度.md"
GUIDE = DOC / "13-Godot导入与本机配置指南.md"
DRAFT = DOC / "design-freeze-draft.json"
MANIFEST = DOC / "asset-content-manifest.json"
NUMBERS = DOC / "数值框架.csv"
MEMORY = ROOT.parent / ".workbuddy" / "memory" / f"{date.today().isoformat()}.md"

# (说明, 旧文本, 新文本)；旧文本必须在目标文件里唯一命中
HANDOVER_REPLACES: list[tuple[str, str, str]] = [
    (
        "抬头状态改为第 15 轮收口",
        "> 最后更新：**2026-11-08 10:30**（第 15 轮，用户「**策划案整体确认**」→ 已合并 `01` v0.2、产出 `docs/design-freeze.json`（**frozen**）、**最小验证工程已交付**并由 4.7.2 headless 实测通过；**R32 极值验算已处置**。GUI 按 F5 目检仍需用户做）",
        "> 最后更新：**2026-11-08 10:45**（第 15 轮收口：用户「**策划案整体确认**」→ 已合并 `01` v0.2、`docs/design-freeze.json` 置 **frozen**、R32 极值验算处置、**最小验证工程已交付**并经 Godot 4.7.2 headless 实测 + 工程结构自检双 PASS；新增 `tools/final_selfcheck.py` / `docs/final-selfcheck.json` 全量自检、R39 已处置。**GUI 按 F5 目检仍需用户做，不得写成已通过**）",
    ),
    (
        "§0 接续提示：过期门禁改标历史快照 + 加当前状态",
        """> **第 12 轮接续提示**：回执**已经收到并落地**（`docs/decision-receipt.json` / `decision-plan.json` / `decision-receipt-user.txt`）：15 项按推荐值确认，**Q1 是唯一未答项**。换账号后请先读 `docs/10-决策回执落地与v0.2合并清单.md`（17 行改前/改后对照）与 `docs/11`（卡牌系统）、`docs/12`（卡牌 UI）。
> **第 14 轮门禁更新**：用户已确认 **Q1=4.7.2**，`decision-receipt.json` 重跑为 **16/16 项 / 硬门禁 4/4 / 错误 0 / 告警 1**（R29、R30 正文修订）。Q3/Q5/Q8 第 12 轮解除、Q1 第 14 轮解除，**四条硬门禁全部齐备**。
> **当前唯一阻塞已换成「用户整体确认策划案」**：即确认 `01` 基线 + `02`/`04`/`06`/`07`/`08` 增量 + `docs/10` 的 17 行改前/改后对照（含 R27–R30 处置）与卡牌系统 PROPOSAL。用户没给这句话之前：**不合并 `01` v0.2、不置 frozen、不建工程、不重算 `B`（R35）**。拿到后顺序为 `合并 v0.2 → design-freeze.json 置 frozen → 才建工程 → 按 13 导入`。
> 卡牌系统数值全部标「待实测」；R32 极值验算、R33 层间 6 s 阅读窗口、R34 `combo_hash` 区分度、R35 夺主改 `k` 均未处置。""",
        """> **⚠️ 第 15 轮当前状态（换账号先看这一段）**：四条硬门禁已齐备 + 用户已「策划案整体确认」→ `01` v0.2 已合并、`docs/design-freeze.json` 已 `frozen`（22 条 DF）、**最小验证工程已交付**（`project.godot` / `scenes/MinimalRun.tscn` / `scripts/PlayerProbe.gd`），经 Godot 4.7.2 headless 加载与工程结构自检 **双 PASS**（详见 `docs/13` §12、`docs/final-selfcheck.json`）。**当前唯一待办在用户侧**：按 `docs/13` §12 打开工程按 F5 做画面目检；助手**从未跑过 GUI**，不得标「已通过」。
> 下面三条「第 12 / 14 轮接续提示」与「当时唯一阻塞」都是**历史快照**，第 15 轮起已失效，保留仅为追溯决策过程，**不要照着执行**。
>
> **第 12 轮接续提示（历史）**：回执**已经收到并落地**（`docs/decision-receipt.json` / `decision-plan.json` / `decision-receipt-user.txt`）：15 项按推荐值确认，**Q1 是唯一未答项**。换账号后请先读 `docs/10-决策回执落地与v0.2合并清单.md`（17 行改前/改后对照）与 `docs/11`（卡牌系统）、`docs/12`（卡牌 UI）。
> **第 14 轮门禁更新（历史）**：用户已确认 **Q1=4.7.2**，`decision-receipt.json` 重跑为 **16/16 项 / 硬门禁 4/4 / 错误 0 / 告警 1**（R29、R30 正文修订）。Q3/Q5/Q8 第 12 轮解除、Q1 第 14 轮解除，**四条硬门禁全部齐备**。
> **第 14 轮时的阻塞（已解除）**：当时要求确认 `01` 基线 + `02`/`04`/`06`/`07`/`08` 增量 + `docs/10` 的 17 行改前/改后对照（含 R27–R30 处置）与卡牌系统 PROPOSAL；当时的顺序为 `合并 v0.2 → design-freeze.json 置 frozen → 才建工程 → 按 13 导入`，**第 15 轮已逐步执行完毕**。
> 卡牌系统数值全部标「待实测」；R32 极值验算 ✅ 第 15 轮已处置；R33 层间 6 s 阅读窗口、R34 `combo_hash` 区分度、R35 夺主改 `k` **仍未处置**。""",
    ),
    (
        "§0 本机探测段补第 15 轮引擎实测边界",
        "探测不等于 `SkillCaster.gd` 已验证，Godot 编辑器验证仍待办。",
        "**第 15 轮更新**：工程已由该版本引擎 headless 实测（`project.godot` 由引擎自行写出、229 项资源由编辑器导入），但 **GUI F5 画面仍未验证**；`docs/SkillCaster.gd` 仍只是示范片段，未在编辑器里跑过。",
    ),
    (
        "§6 追加第 15 轮收口小节",
        "- **两套追溯脚本口径统一**：`check_traceability.py` 改为以正式冻结清单为权威、扫描 `scripts/`/`scenes/`、且**只认 `@trace` 后的编号**，与技能包脚本同为 **4/22 = 18%**，不再把说明文字算成回指（R36 同类问题）。",
        """- **两套追溯脚本口径统一**：`check_traceability.py` 改为以正式冻结清单为权威、扫描 `scripts/`/`scenes/`、且**只认 `@trace` 后的编号**，与技能包脚本同为 **4/22 = 18%**，不再把说明文字算成回指（R36 同类问题）。

### 第 15 轮收口（全量自检 / 交接一致性，0 积分 / 0 张源图 / 未做 GUI F5）

- **交接文档去自相矛盾**：§0 的三条「第 12 / 14 轮接续提示」与「当前唯一阻塞已换成用户整体确认策划案」改标为**历史快照**并加第 15 轮当前状态段；§8 的 R27–R30 状态列补「✅ 第 15 轮已处置」；§9 删掉重复的 9/10 编号与「阶段一覆盖率 0 为预期」等过期条目。换账号接手不会照旧门禁误判。
- **R39 处置**：Godot 4.7 编辑器把 `docs/卡牌库.csv` / `docs/数值框架.csv` 当 CSV 翻译表导入，生成 24 个 `.translation` / `.csv.import` 垃圾文件。新建空 `docs/.gdignore` 让编辑器跳过整个 `docs/`（设计文档与数值源不参与引擎资源扫描），清理这 24 个可再生生成物，并在 `.gitignore` 加两行兜底。**不影响任何资源加载**：`res://assets/...` 与 `res://scenes/...` 不在 `docs/` 下。
- **全量自检**：新增 `tools/final_selfcheck.py`（静态断言）+ `docs/final-selfcheck.json`，覆盖 JSON 解析 / CSV 列数 / Python 编译 / 冻结清单 / 回执 / 伤害红线 / 72 卡 / 两套报告 / 质检 / 产物齐备 / `project.godot` 关键值 / 场景帧路径 / 机器绝对路径 / 过期状态 / `.gdignore`。动态侧另跑 `verify_damage_ceiling.py`、`check_traceability.py`、`check_godot_project.py` 与 4.7.2 headless 加载，四路复验。
- **诚实边界**：以上全是**离线 / 静态验证**。像素是否硬边不糊、镜像是否穿帮、480×270×4 对齐、R22 阴兵对比度仍必须用户 F5 目检；`docs/final-selfcheck.json` 的 PASS 不等于「游戏能玩」。""",
    ),
    (
        "§8 表格前加状态口径说明",
        "## 8. 风险与验收（接手别漏）\n\n| 编号 | 风险 | 对策 |",
        """## 8. 风险与验收（接手别漏）

> **状态口径（第 15 轮）**：下表 R27–R30 的「未处置 / 待用户确认」是**当时诊断快照**，已于第 15 轮随 `01` v0.2 合并全部处置；R32/R38 ✅ 已处置；R36 的覆盖率口径在第 15 轮已升级为「只认 `@trace`，权威清单 22 条」。新增 **R39**（`docs/.gdignore`）。未处置项只有 R9 字体授权、R22 实机对比度、R33/R34/R35 卡牌实测、R37 的 GUI 目检。

| 编号 | 风险 | 对策 |""",
    ),
    (
        "R27 状态列",
        "见 `09` §3。**未处置** |",
        "见 `09` §3。**✅ 第 15 轮已处置**：`01` v0.2 的 M3 按效果类型分口径并新增 `legacy_effects` 字典 |",
    ),
    (
        "R28 状态列",
        "已产 8 件 `icon_gear_*` 按品类命名**无需改名**；见 `09` §4。**待用户确认** |",
        "已产 8 件 `icon_gear_*` 按品类命名**无需改名**；见 `09` §4。**✅ 第 15 轮已处置**：`01` v0.2 统一为 3 个 `slot_*` + 8 个 `gear_type_*` |",
    ),
    (
        "R29 状态列",
        "属**已明确假设修订，待用户确认** |",
        "✅ **第 15 轮已处置**：`01` §4 改为「不联网不上传、本地埋点可关闭」 |",
    ),
    (
        "R30 状态列",
        "**第 12 轮已给结论**：`10` §3 第 2 行（等合并时写入） |",
        "✅ **第 15 轮已处置**：`01` §15 已补 M6 / M6-f / M10 |",
    ),
    (
        "§8 新增 R39",
        "| **R38** | 工程自检误把 `docs/asset-manifest.json`（**v1 水墨 256px / 105 帧归档基线**）当成生效规格，报 4 条错误 | ✅ **第 15 轮已修**：不抑制检查，改为新建 `docs/asset-manifest-godot.json`（v2 像素 64×64 生效规格）并在 `project-spec.json` 指定；复跑错误 0 |",
        """| **R38** | 工程自检误把 `docs/asset-manifest.json`（**v1 水墨 256px / 105 帧归档基线**）当成生效规格，报 4 条错误 | ✅ **第 15 轮已修**：不抑制检查，改为新建 `docs/asset-manifest-godot.json`（v2 像素 64×64 生效规格）并在 `project-spec.json` 指定；复跑错误 0 |
| **R39** | Godot 4.7 编辑器把 `docs/` 下两份设计 CSV 误判为翻译表，生成 24 个 `.translation` / `.csv.import` 垃圾文件，污染交接目录 | ✅ **第 15 轮收口已处置**：新建空 `docs/.gdignore` 让引擎跳过 `docs/`，清理 24 个可再生生成物，`.gitignore` 加 `docs/*.translation` / `docs/*.csv.import` 兜底；headless 复验资源加载不受影响 |""",
    ),
    (
        "验收段 R30 已并入",
        "在 `02` §5，**尚未并入 `01` §15（R30）**；",
        "在 `02` §5，**✅ 第 15 轮已随 v0.2 并入 `01` §15（R30 处置完毕），并补 M6-f / M10**；",
    ),
    (
        "§9 删重复编号与过期条目",
        """9. **仍可推进但不依赖 Q1 的活**：Q21 已定 128 → 开 B3 两个 Boss；Q24 已定程序化 + pixelfx → 开 B4 剩余 4 技能 / 命中 / 5 组 overlay（**这两项需先确认是否现在投入出图积分**）；R22 阴兵对比度、`hitboxOffsetX=16px`、剑魂 8fps、R9 字体最终核验、4× 实机排版、Godot 编辑器验证。
10. 工程侧用 `DF-xx` 回指编号，`check_traceability.py` 统计覆盖率；阶段一覆盖率 **0 为预期**（R36 已修口径）。""",
        """11. **工程侧追溯**：用 `@trace DF-xx` 回指编号，两套脚本口径统一为**只认 `@trace` 后编号**；当前权威清单 22 条，最小验证工程覆盖 **4/22 = 18.18%**（DF-04 / DF-12 / DF-13 / DF-15），是真实进度，**不得塞标记凑数**。正式战斗工程按 `01` §12 另建时逐条补回指。
12. **仍需用户拍板/实测**：R9 字体授权、R33 层间 6 s 读卡窗口、R34 `combo_hash` 区分度、R35 夺主改 `k` 后重算 `B`、R22 阴兵对比度、`hitboxOffsetX=16px`、剑魂 8fps、4× 实机排版；72 张卡权重与概率仍 PROPOSAL。
13. **全量自检可复跑**：`python3 tools/final_selfcheck.py` → `docs/final-selfcheck.json`；动态四路复验命令见 `docs/13` §12 与 `docs/08` §8.5。换账号后先跑这两项再动手，别只看文档结论。""",
    ),
    (
        "第16轮 抬头状态",
        "> 最后更新：**2026-11-08 10:55**（第 15 轮收口：用户「**策划案整体确认**」",
        "> 最后更新：**2026-11-08 11:15**（第 16 轮：用户**首次在 GUI 打开工程**并反馈编辑器状态 → 处置 **R41**（`Player` 缺 `CollisionShape2D` 的黄色警告，已补碰撞体与真实地面 `GroundBody`）、**R42**（三个 miora 预览画板落在工程根目录被引擎扫描，已移入 `previews/` 并加 `.gdignore`）；`docs/13` §12.4 步骤改为 4 步（新增「切 2D 视图」）。headless 复验 `VERIFY|PASS`、结构自检错误 0、全量静态自检 20/20 PASS。**画面目检仍待用户按 F5**）",
    ),
    (
        "第16轮 §0 待办句",
        "**当前唯一待办在用户侧**：按 `docs/13` §12 打开工程按 F5 做画面目检；助手**从未跑过 GUI**，不得标「已通过」。",
        "**当前唯一待办在用户侧**：按 `docs/13` §12 打开工程按 F5 做画面目检；助手**从未跑过 GUI**，不得标「已通过」。\n> **第 16 轮（用户首次打开 GUI）**：工程已在编辑器里成功打开，场景树 `MinimalRun` 正常加载。当时看到的 `Player` 黄色三角警告是**真实缺陷**（`CharacterBody2D` 缺 `CollisionShape2D`），已处置为 R41；顺带处置 R42（预览画板归位）。用户下一步见 `docs/13` §12.4 的 4 步。",
    ),
    (
        "第16轮 §6 追加小节",
        "- **诚实边界**：以上全是**离线 / 静态验证**。像素是否硬边不糊、镜像是否穿帮、480×270×4 对齐、R22 阴兵对比度仍必须用户 F5 目检；`docs/final-selfcheck.json` 的 PASS 不等于「游戏能玩」。",
        """- **诚实边界**：以上全是**离线 / 静态验证**。像素是否硬边不糊、镜像是否穿帮、480×270×4 对齐、R22 阴兵对比度仍必须用户 F5 目检；`docs/final-selfcheck.json` 的 PASS 不等于「游戏能玩」。

### 第 16 轮（用户首次在 GUI 打开工程 → R41 / R42 处置）

- **R41：`Player` 缺碰撞形状（编辑器黄色三角警告，真实缺陷）**：`Player` 是 `CharacterBody2D` 却只有 `AnimatedSprite2D` 子节点，没有 `CollisionShape2D`；编辑器节点面板因此挂黄色警告，且 `move_and_slide()` 不会与任何物体产生碰撞。处置：`scenes/MinimalRun.tscn` 的 `Player` 下新增 `Body(CollisionShape2D)`（`RectangleShape2D` 32×56），并把地面从「只有视觉的 `ColorRect`」补成**真实物理地面** `GroundBody(StaticBody2D)` + `Shape(CollisionShape2D)` 480×54（顶部 y=216）；另加 `Feet(Marker2D)` 标出脚底参考点。headless 断言 `player_bottom=216.0` 与 `ground_top=216.0` **严格对齐**，不陷地不悬空。`tools/verify_minimal_run.gd` 增补碰撞体存在性断言，防止回归。
- **R42：miora 预览画板落在 Godot 工程根目录**：三个 `*.miora` 画板及其 `*_assets` 素材副本直接放在工程根，会被引擎当资源扫描（用户文件面板里能看到，还生成了 `.import`）。处置：整体移入 `previews/`，加空 `previews/.gdignore` 让引擎跳过（`previews/.gdignore` **别删**）；同时给 `assets/_preview/` 也加 `.gdignore`，把 31 个预览拼图的 `.import` 清理掉（拼图是浏览器/系统看图用，不参与运行时），`assets/` 其余 181 项游戏资源导入不受影响。画板文件与素材同级关系保持不变，仍可正常打开。
- **给用户的指引更新**：`docs/13` §12.4 从 3 步改 4 步，新增「首次打开默认停在 **3D 视图**（看到网格 + 坐标轴是正常的），按 `2` 键或点 `2D` 标签切到 2D 视图」；§12.1 文件表补 `previews/`；§12.2 的 VERIFY 输出更新为含碰撞断言的新版。
- **诚实边界不变**：以上仍是**离线 / headless** 验证。碰撞体对齐是数值对齐，**画面上脚底与地面线是否贴合、像素硬边、镜像穿不穿帮，仍要用户 F5 看**。""",
    ),
    (
        "第16轮 §8 状态口径",
        "新增 **R39**（`docs/.gdignore`）与 **R40**（冻结清单占位符编号）。未处置项只有 R9 字体授权、R22 实机对比度、R33/R34/R35 卡牌实测、R37 的 GUI 目检。",
        "新增 **R39**（`docs/.gdignore`）、**R40**（冻结清单占位符编号）、**R41**（`Player` 缺碰撞形状）、**R42**（预览画板落在工程根目录）。未处置项只有 R9 字体授权、R22 实机对比度、R33/R34/R35 卡牌实测、R37 的 GUI 目检。",
    ),
    (
        "第16轮 §8 新增 R41 / R42",
        "| **R39** | Godot 4.7 编辑器把 `docs/` 下两份设计 CSV 误判为翻译表，生成 24 个 `.translation` / `.csv.import` 垃圾文件，污染交接目录 | ✅ **第 15 轮收口已处置**：新建空 `docs/.gdignore` 让引擎跳过 `docs/`，清理 24 个可再生生成物，`.gitignore` 加 `docs/*.translation` / `docs/*.csv.import` 兜底；headless 复验资源加载不受影响 |",
        """| **R39** | Godot 4.7 编辑器把 `docs/` 下两份设计 CSV 误判为翻译表，生成 24 个 `.translation` / `.csv.import` 垃圾文件，污染交接目录 | ✅ **第 15 轮收口已处置**：新建空 `docs/.gdignore` 让引擎跳过 `docs/`，清理 24 个可再生生成物，`.gitignore` 加 `docs/*.translation` / `docs/*.csv.import` 兜底；headless 复验资源加载不受影响 |
| **R40** | 结构自检把 `design-freeze-draft.json` 里两处占位符编号当成「不在冻结清单中的需求编号」，报 1 条错误 | ✅ **第 15 轮已处置**：改成描述性文字，不删条目、不改列表结构、不抑制检查；错误 1 → 0 |
| **R41** | `Player(CharacterBody2D)` 没有 `CollisionShape2D` 子节点 → 编辑器节点面板挂**黄色三角警告**，且 `move_and_slide()` 不与任何物体碰撞 | ✅ **第 16 轮已处置**：`Player` 下新增 `Body(CollisionShape2D)` 32×56；新增 `GroundBody(StaticBody2D)` 作真实地面（顶 y=216）+ `Feet(Marker2D)`；headless 断言 `player_bottom == ground_top == 216.0`，`verify_minimal_run.gd` 增补回归断言 |
| **R42** | 三个 `*.miora` 预览画板与 `*_assets` 素材副本直接放在 Godot 工程根目录，被引擎当资源扫描（污染文件面板、生成多余 `.import`） | ✅ **第 16 轮已处置**：整体移入 `previews/` + 空 `previews/.gdignore`；`assets/_preview/` 亦加 `.gdignore` 并清理 31 个拼图 `.import`；游戏资源导入不受影响 |
| **R43** | `AnimatedSprite2D` 的 `SpriteFrames` 原本由脚本在 `_ready()` 里动态构造 → 编辑器节点面板挂**「必须先设置 SpriteFrames 资源」黄色警告**，且编辑器里预览不到任何帧 | ✅ **第 16 轮已处置**：新增 `tools/build_sprite_frames.gd`，**由引擎自己** `ResourceSaver.save()` 写出 `assets/char/player_frames.tres`（idle3/run4、6/8fps，含 7 张帧引用），场景直接挂该资源；脚本保留「资源缺失才动态构建」的兜底分支。headless 复验 `frames_before=true`（不再依赖脚本构造） |""",
    ),
    (
        "第16轮 §6 追加 R43 小节",
        "- **诚实边界不变**：以上仍是**离线 / headless** 验证。碰撞体对齐是数值对齐，**画面上脚底与地面线是否贴合、像素硬边、镜像穿不穿帮，仍要用户 F5 看**。",
        """- **诚实边界不变**：以上仍是**离线 / headless** 验证。碰撞体对齐是数值对齐，**画面上脚底与地面线是否贴合、像素硬边、镜像穿不穿帮，仍要用户 F5 看**。

### 第 16 轮（续）· R43：帧资源化

- **现象**：场景重载后 `Sprite` 节点报「必须先在『Sprite Frames』属性中新建或设置 SpriteFrames 资源，才能让 AnimatedSprite2D 显示动画帧」。
- **原因**：原实现的 `SpriteFrames` 是 `PlayerProbe.gd` 在 `_ready()` 里用 `SpriteFrames.new()` + `add_frame()` 动态拼的，**运行时才有，编辑器静态视图拿不到**，于是既报警告又预览不到帧。
- **处置**：新增 `tools/build_sprite_frames.gd`，由 **4.7.2 引擎自己** `ResourceSaver.save()` 写出 `assets/char/player_frames.tres`（不手写引擎资源格式；生成后回读校验 `idle=3 / run=4`）；`scenes/MinimalRun.tscn` 的 `AnimatedSprite2D` 直接挂这个资源并设 `animation = &"idle"`。脚本改为「资源缺失才动态构建」的兜底分支，行为不倒退。headless 复验 `frames_before=true`，即**帧来自资源而非脚本**，编辑器里现在能直接看到帧与动画列表。
- **收益**：零经验用户不用「运行一次才知道帧对不对」，在 Inspector 里就能核对 `idle`/`run` 两组动画与 6/8fps 节奏；正式工程所有角色都应走这条「帧资源化」的路子，不在脚本里动态拼帧。""",
    ),
    (
        "第16轮 §8 状态口径补 R43",
        "**R42**（预览画板落在工程根目录）。未处置项只有",
        "**R42**（预览画板落在工程根目录）、**R43**（帧未资源化）。未处置项只有",
    ),
]

GUIDE_APPEND = """

### 12.6 交付后收口（R39 / 全量自检）

- **`docs/.gdignore` 是空文件，别删**：它让 Godot 编辑器**跳过整个 `docs/` 目录**扫描。原因：4.7 把 `docs/卡牌库.csv` / `docs/数值框架.csv` 当成 CSV 翻译表导入，生成了 24 个 `.translation` / `.csv.import` 垃圾文件。这两份是设计数值源、不参与运行时，已清理并在 `.gitignore` 加了兜底规则。`res://assets/` 与 `res://scenes/` 不在 `docs/` 下，资源导入与加载不受影响，headless 复验仍 PASS。
- `tools/final_selfcheck.py` / `docs/final-selfcheck.json` 是交付前的全量静态自检（JSON / CSV / 脚本编译 / 冻结 / 红线 / 产物 / 绝对路径 / 过期状态 / `.gdignore`），动态侧另跑伤害验算、两套追溯、工程结构检查与 4.7.2 headless 加载。**全部 PASS 仍不等于 GUI 画面通过**，§12.5 边界不变。
"""

NUMBERS_ROWS = [
    ["round15", "round15_final_selfcheck_checks", "20", "项", "0", "30", "15批次 2026-11-08", "yes", "final_selfcheck.py静态断言;全PASS"],
    ["round15", "round15_r39_gdignore", "1", "个", "0", "1", "15批次 2026-11-08", "yes", "docs/.gdignore让引擎跳过docs扫描;设计CSV不再被当翻译表"],
    ["round15", "round15_r39_junk_removed", "24", "个", "0", "30", "15批次 2026-11-08", "yes", "24个.translation/.csv.import引擎生成物已清理;可再生非设计资产"],
    ["round15", "round15_stale_handover_fixed", "12", "处", "0", "20", "15批次 2026-11-08", "yes", "00交接文档过期门禁/重复编号/R27-R30状态/R39/验收段共12处修正"],
    ["round15", "round15_credits_total", "0", "积分", "0", "50", "15批次 2026-11-08", "yes", "第15轮含收口全程0积分;无出图"],
    ["round15", "round15_r40_placeholders_fixed", "2", "处", "0", "5", "15批次 2026-11-08", "yes", "draft两处占位符编号改描述性文字;结构自检错误1→0"],
    ["round15", "round15_final_selfcheck_passed", "20", "项", "0", "20", "15批次 2026-11-08", "yes", "静态自检20/20 PASS;动态四路复验全PASS"],
    ["round16", "round16_r41_collision_shapes", "2", "个", "0", "5", "16批次 2026-11-08", "yes", "Player/Body CollisionShape2D 32x56 + GroundBody/Shape 480x54;消除编辑器黄色警告;并新增真实地面"],
    ["round16", "round16_r41_feet_align", "216", "px", "0", "270", "16批次 2026-11-08", "yes", "headless断言 player_bottom=216.0 == ground_top=216.0;脚底与地面顶严格对齐"],
    ["round16", "round16_r42_previews_moved", "6", "个", "0", "10", "16批次 2026-11-08", "yes", "3个miora画板+3个_assets目录移入previews/并加.gdignore;引擎不再扫描"],
    ["round16", "round16_preview_imports_removed", "31", "个", "0", "40", "16批次 2026-11-08", "yes", "assets/_preview加.gdignore后清理31个拼图.import;游戏资源181项导入不受影响"],
    ["round16", "round16_credits_total", "0", "积分", "0", "50", "16批次 2026-11-08", "yes", "第16轮全程0积分;无出图"],
    ["round16", "round16_godot_imports_now", "196", "项", "0", "300", "16批次 2026-11-08", "yes", "R42清理预览目录与画板后当前实际导入数;round15的229项为历史值保留"],
    ["round16", "round16_r43_frames_tres", "7", "帧", "0", "15", "16批次 2026-11-08", "yes", "player_frames.tres由引擎生成含idle3+run4共7帧;场景直接挂资源;编辑器可预览无黄色警告"],
]

ROUND16_GUIDE_APPEND = """
### 12.7 第 16 轮：首次打开后修的两处（R41 / R42）

**你在编辑器里看到的两个现象，来源如下：**

| 现象 | 真实原因 | 处置 |
|---|---|---|
| `Player` 节点上的**黄色三角警告**「该节点没有描述其形状的子节点」 | `Player` 是 `CharacterBody2D`，却只有 `AnimatedSprite2D` 子节点，**没有 `CollisionShape2D`**。Godot 因此挂警告，且 `move_and_slide()` 不会与任何物体碰撞 | 场景改为 `Player` → `AnimatedSprite2D` + **`Body(CollisionShape2D)`**（32×56），并新增 **`GroundBody(StaticBody2D)`** 作为真实地面（480×54，顶 y=216）+ `Feet(Marker2D)` 标脚底。headless 断言 `player_bottom == ground_top == 216.0` |
| 文件面板里出现 `首批/第二批/第三批像素素材_assets` | 三个 miora 预览画板连同素材副本被直接放在**工程根目录**，引擎会当资源扫描并生成多余 `.import` | 整体移入 **`previews/`** 并加空 `previews/.gdignore`（**别删**）；`assets/_preview/` 同样加 `.gdignore` 并清理 31 个拼图 `.import`。画板仍可正常打开，游戏资源 181 项导入不受影响 |

**另外**：首次打开默认停在 **3D 视图**（网格地面 + 红绿蓝坐标轴），这是正常的。按 **`2`** 键或点视口左上角 **`2D`** 标签切到 2D 视图再 F5。

**改完文件后编辑器不会自动重载场景**：右键场景标签 → **重载**，或关掉 `MinimalRun` 标签页重新打开。
"""

ROUND16B_GUIDE_APPEND = """
### 12.8 第 16 轮（续）· R43：帧改成真正的 SpriteFrames 资源

**你在编辑器里看到的第三个现象**：`Sprite` 节点报「必须先在『Sprite Frames』属性中新建或设置 SpriteFrames 资源，才能让 AnimatedSprite2D 显示动画帧」。

- **原因**：原实现的 `SpriteFrames` 是 `PlayerProbe.gd` 在 `_ready()` 里用 `SpriteFrames.new()` + `add_frame()` **动态拼**出来的，运行时才有，编辑器静态视图拿不到 → 既报警告又预览不到帧。
- **处置**：新增 `tools/build_sprite_frames.gd`，由 **4.7.2 引擎自己** `ResourceSaver.save()` 写出 `assets/char/player_frames.tres`（**不手写引擎资源格式**；生成后回读校验 `idle=3 / run=4`）。`scenes/MinimalRun.tscn` 的 `AnimatedSprite2D` 直接挂这个资源并设 `animation = &"idle"`；脚本保留「资源缺失才动态构建」的兜底分支。
- **现在应该看到**：选中 `Sprite` 节点，Inspector 的 **Sprite Frames** 处不再是空，而是一个含 `idle`（3 帧 / 6fps）与 `run`（4 帧 / 8fps）两组动画的资源；视口里能直接看到角色贴图（切 2D 视图后）。**节点面板不再有黄色警告。**
- **headless 复验**：`VERIFY|sprite_node=AnimatedSprite2D|frames_before=true`（帧来自资源而非脚本）。

> **正式工程沿用这条规矩**：所有角色的帧都要做成 `SpriteFrames` 资源并挂到场景，**不要在脚本里动态拼帧**——否则编辑器无法预览、也无法在 Inspector 里核对帧表。
"""

MEMORY_APPEND = """

## 10:45 · 第 15 轮收口（全量自检 / 交接一致性 / R39）

- 承接上一轮「策划案整体确认」的 Task #26：此前已完成 v0.2 合并、冻结、最小验证工程、headless 实测与结构自检，本轮把**全量回填、自检、交接文档更新**做完，0 积分 / 0 张源图 / 未做 GUI F5。
- **发现并处置 R39**：Godot 4.7 编辑器把 `docs/卡牌库.csv` / `docs/数值框架.csv` 当 CSV 翻译表导入，生成 24 个 `.translation` / `.csv.import` 垃圾文件污染交接目录。用官方机制新建空 `docs/.gdignore` 让引擎跳过整个 `docs/`，清理这 24 个可再生生成物，`.gitignore` 加两行兜底；`res://assets/` / `res://scenes/` 不受影响，headless 复验加载仍 PASS。换账号别删这个空文件。
- **交接文档去自相矛盾（重要）**：`docs/00` §0 还留着「当前唯一阻塞已换成用户整体确认策划案……不合并 / 不冻结 / 不建工程」，与第 15 轮已落地状态直接冲突；§8 R27–R30 状态列仍写「未处置 / 待用户确认」；§9 尾部有重复编号 9/10 与「阶段一覆盖率 0 为预期」；验收段仍写 M6 未并入 §15。全部改为「历史快照 + 当前状态」双层口径，共 12 处精确替换（每个锚点断言唯一命中），脚本 `tools/finalize_handover.py` 可复跑、已收口的锚点自动跳过。
- 新增 `tools/final_selfcheck.py` + `docs/final-selfcheck.json`：全量静态断言（JSON 解析 / CSV 列数 / Python 编译 / 冻结清单 / 回执 / 伤害红线 / 72 卡 / 两套报告 / 质检 / 产物齐备 / project.godot 关键值 / 场景帧路径 / 机器绝对路径 / 过期状态 / .gdignore）+ 4 条已知例外（检查器报告自指绝对路径、覆盖率 4/22 真实进度、draft 历史字段、receipt 的 received-not-applied 是脚本语义）。动态四路另跑 verify_damage_ceiling / check_traceability / check_godot_project / 4.7.2 headless。
- 回填：`docs/00`（抬头 / §0 / §6 新增收口小节 / §8 / §9）、`docs/13` §12.6、`design-freeze-draft.json` 的 `round15Freeze` 两段说明（原位「清单尚不存在」字段按基线不覆盖原则保留，仅加注失效说明）、`docs/数值框架.csv`（+5 行，永远追加）、`docs/asset-content-manifest.json`（round15Final）、本日志。
- **诚实边界不变**：所有验证都是离线 / 静态；像素硬边、镜像穿帮、480×270×4 对齐、R22 阴兵对比度仍要用户按 `13` §12 按 F5 目检。PASS ≠ 游戏能玩。
- **下一步**：用户侧导入 + F5 目检（唯一待办）；之后才谈 B3 两个 Boss / B4 剩余技能（要花出图积分，等点头）、R33–R35 卡牌实测、R9 字体授权、正式战斗工程。
"""

ROUND16_MEMORY_APPEND = """
## 11:15 · 第 16 轮（用户首次在 GUI 打开工程 → R41 / R42）

- 用户把编辑器打开后的状态截图发来，问「接下来做什么」。**GUI 是用户自己开的，我仍未跑过 F5**。
- **R41（真实缺陷）**：`Player(CharacterBody2D)` 只有 `AnimatedSprite2D` 子节点、**没有 `CollisionShape2D`** → 编辑器节点面板挂黄色三角警告，`move_and_slide()` 不与任何物体碰撞。处置：场景加 `Body(CollisionShape2D)` 32×56；把「只有视觉的 ColorRect 地面」补成**真实地面** `GroundBody(StaticBody2D)` + `Shape` 480×54（顶 y=216）；加 `Feet(Marker2D)` 标脚底。`tools/verify_minimal_run.gd` 增补碰撞存在性断言防回归。headless 断言 `player_bottom=216.0 == ground_top=216.0`。
- **R42**：三个 `*.miora` 预览画板 + `*_assets` 素材副本落在 Godot 工程根目录，被引擎当资源扫描（用户文件面板可见、生成多余 `.import`）。处置：整体移入 `previews/` + 空 `previews/.gdignore`；`assets/_preview/` 也加 `.gdignore` 并清理 31 个拼图 `.import`（拼图是给浏览器/看图器看的，不参与运行时），`assets/` 其余 181 项游戏资源导入不受影响。画板与素材同级关系不变，仍可打开。
- **指引更新**：`docs/13` §12.4 由 3 步改 4 步，补「首次打开默认是 3D 视图（网格 + 坐标轴属正常），按 `2` 键或点 `2D` 标签切换」；§12.1 文件表补 `previews/`；§12.2 VERIFY 输出更新为含碰撞断言的新版；新增 §12.7 专讲这两处。
- 复验：4.7.2 headless `VERIFY|PASS`、结构自检**错误 0 / 警告 2 通过**、追溯 PASS、伤害红线 PASS、全量静态自检 **20/20 PASS**。0 积分 / 0 张源图。
- **边界**：碰撞体对齐是**数值对齐**，画面上脚底与地面线是否贴合、像素硬边、镜像穿不穿帮，仍要用户 F5 看。
"""

ROUND16B_MEMORY_APPEND = """
## 11:25 · 第 16 轮（续）· R43：帧资源化

- 用户重载场景后截图：`GroundBody / Body / Feet` 已就位（R41 生效），但 `Sprite` 节点出现新警告「必须先在『Sprite Frames』属性中新建或设置 SpriteFrames 资源」。
- **根因**：原实现的 `SpriteFrames` 是 `PlayerProbe.gd` 在 `_ready()` 里 `SpriteFrames.new()` + `add_frame()` **动态拼**的，运行时才有，编辑器静态视图拿不到 → 既报警告又预览不到帧。
- **处置（原则：不手写引擎资源格式）**：新增 `tools/build_sprite_frames.gd`，由 4.7.2 引擎自己 `ResourceSaver.save()` 写出 `assets/char/player_frames.tres`（idle3/run4、6/8fps、7 张帧引用），生成后回读校验 `idle=3 run=4`；`scenes/MinimalRun.tscn` 的 `AnimatedSprite2D` 直接挂该资源并设 `animation=&"idle"`；脚本改为「资源缺失才动态构建」的兜底分支。headless 复验 `frames_before=true`，帧来自资源而非脚本。
- **收益与规矩**：零经验用户不用运行一次才知道帧对不对，Inspector 里可直接核对 idle/run 两组动画与帧率；**正式工程所有角色都走「帧资源化」，不在脚本里动态拼帧**。
- 自检扩充：`tools/final_selfcheck.py` 从 20 项加到 23 项（新增 `collision_r41` / `previews_r42` / `frames_tres_r43`），全部 PASS；导入资源现 196 项（第 15 轮的 229 为历史值保留）；`docs/13` 新增 §12.8。
"""


# 追加型替换的「完成标记」：文档后续又在这些段落里补了内容时，
# 新文本不再是完整子串，靠标记判定已收口，保证脚本可重复运行。
SKIP_MARKERS = {
    # 抬头在第 16 轮被再次改写，两个标记任一命中即视为已收口。
    "抬头状态改为第 15 轮收口": ["第 15 轮收口：用户", "第 16 轮：用户**首次在 GUI 打开工程**"],
    "§0 接续提示：过期门禁改标历史快照 + 加当前状态": "下面三条「第 12 / 14 轮接续提示」与「当时唯一阻塞」都是**历史快照**",
    "§0 本机探测段补第 15 轮引擎实测边界": "清理预览目录与画板后**现为 196 项**",
    "§6 追加第 15 轮收口小节": "### 第 15 轮收口（全量自检",
    "§8 表格前加状态口径说明": "**状态口径（第 15 轮）**",
    "§8 新增 R39": "| **R39** |",
    "第16轮 抬头状态": "第 16 轮：用户**首次在 GUI 打开工程**",
    "第16轮 §0 待办句": "> **第 16 轮（用户首次打开 GUI）**",
    "第16轮 §6 追加小节": "### 第 16 轮（用户首次在 GUI 打开工程",
    "第16轮 §8 状态口径": "**R42**（预览画板落在工程根目录）",
    "第16轮 §8 新增 R41 / R42": "| **R41** |",
    "第16轮 §6 追加 R43 小节": "### 第 16 轮（续）· R43：帧资源化",
    "第16轮 §8 状态口径补 R43": "**R43**（帧未资源化）",
}


def _marker_hit(text: str, label: str) -> bool:
    """完成标记判定：值可为 str 或 list[str]，任一命中即视为该段已收口。"""
    marks = SKIP_MARKERS.get(label)
    if not marks:
        return False
    if isinstance(marks, str):
        marks = [marks]
    return any(x in text for x in marks)


def apply_replaces(path: Path, replaces: list[tuple[str, str, str]]) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    # 先全量校验锚点，避免写半成品。
    # 幂等判定：新文本已在 → 视为已收口（追加型替换的 new 含 old，更要靠这条拦住重复追加）。
    for label, old, new in replaces:
        if _marker_hit(text, label):
            continue  # 段落已存在（可能又被后续轮次扩写过）
        n_old, n_new = text.count(old), text.count(new)
        if n_new >= 1:
            continue
        if n_old != 1:
            raise SystemExit(f"锚点「{label}」命中 {n_old} 次（应为 1），且新文本命中 {n_new} 次 → 中止：{path.name}")
    done = skipped = 0
    for label, old, new in replaces:
        if _marker_hit(text, label) or new in text or old not in text:
            skipped += 1
            print(f"  SKIP  {label}")
            continue
        text = text.replace(old, new, 1)
        done += 1
        print(f"  OK    {label}")
    path.write_text(text, encoding="utf-8")
    return done, skipped


def main() -> None:
    print("[1/8] 交接文档去自相矛盾")
    d, s = apply_replaces(HANDOVER, HANDOVER_REPLACES)
    print(f"  → 替换 {d} 处 / 跳过 {s} 处")

    print("[2/8] 导入指南追加 §12.6")
    g = GUIDE.read_text(encoding="utf-8")
    if "### 12.6 交付后收口" in g:
        print("  SKIP  已存在")
    else:
        GUIDE.write_text(g.rstrip("\n") + GUIDE_APPEND, encoding="utf-8")
        print("  OK    §12.6 已追加")

    print("[3/8] design-freeze-draft.json 补历史字段失效说明（不覆盖正文）")
    draft = json.loads(DRAFT.read_text(encoding="utf-8"))
    r15 = draft.setdefault("round15Freeze", {})
    r15["notTheRealFreezeIsHistorical"] = (
        "notTheRealFreeze 字段中「设计冻结清单尚不存在」是第 10 轮的历史描述；"
        "第 15 轮起 docs/design-freeze.json 已存在且 status=frozen，以本段 note 为准。"
        "原字段按「基线正文不覆盖」原则保留不改。"
    )
    r15["finalSelfCheck"] = "docs/final-selfcheck.json（tools/final_selfcheck.py），含 R39 与交接文档过期状态检查"
    DRAFT.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("  OK    round15Freeze 补 2 键；frozen=false / status=draft 不变")

    print("[4/8] 数值源追加 round15Final（永远追加不覆盖）")
    raw = NUMBERS.read_text(encoding="utf-8-sig")
    existing = {r[1] for r in csv.reader(raw.splitlines()) if len(r) > 1}
    added = 0
    with NUMBERS.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        for row in NUMBERS_ROWS:
            if row[1] in existing:
                print(f"  SKIP  {row[1]}")
                continue
            w.writerow(row)
            added += 1
    print(f"  OK    追加 {added} 行")

    print("[5/8] asset-content-manifest.json 追加 round15Final")
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    m["round15Final"] = {
        "trigger": "第 15 轮收口：全量回填、自检与交接文档更新",
        "finalSelfCheck": "tools/final_selfcheck.py → docs/final-selfcheck.json",
        "handoverFixed": "docs/00 §0 过期门禁改历史快照 / §6 收口小节 / §8 R27–R30 状态 / §9 重复编号 / 验收段，共 12 处",
        "riskR39": "Godot 把 docs 下 CSV 误判为翻译表 → 新建空 docs/.gdignore、清理 24 个生成物、.gitignore 兜底",
        "riskR40": "结构自检复跑报 1 错误：design-freeze-draft.json 两处占位符编号被当未知需求编号；改为描述性文字，错误 1→0，未删条目、未改列表结构",
        "dynamicRecheck": "verify_damage_ceiling PASS / check_traceability PASS / check_godot_project 错误0警告2通过 / Godot 4.7.2 headless VERIFY|PASS",
        "selfCheckVerdict": "20/20 PASS",
        "guideAppendix": "docs/13 §12.6",
        "credits": 0,
        "sourceImages": 0,
        "guiF5": "未做；仍需用户按 docs/13 §12 目检",
        "verdict": "静态/离线全量自检 PASS；GUI 画面未验证",
    }
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("  OK    round15Final 已写入")

    print("[6/8] 工作区日志追加第 15 轮收口")
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    old = MEMORY.read_text(encoding="utf-8") if MEMORY.exists() else ""
    if "第 15 轮收口（全量自检" in old:
        print("  SKIP  已存在")
    else:
        with MEMORY.open("a", encoding="utf-8") as f:
            f.write(MEMORY_APPEND if old else MEMORY_APPEND.lstrip("\n"))
        print("  OK    已追加")

    print("[7/8] 第 16 轮：导入指南追加 §12.7")
    g = GUIDE.read_text(encoding="utf-8")
    if "### 12.7 第 16 轮" in g:
        print("  SKIP  已存在")
    else:
        GUIDE.write_text(g.rstrip("\n") + ROUND16_GUIDE_APPEND, encoding="utf-8")
        print("  OK    §12.7 已追加")

    print("[8/8] 第 16 轮：台账 round16Final + 工作区日志")
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    m["round16Final"] = {
        "trigger": "第 16 轮：用户首次在 GUI 打开工程并反馈编辑器状态",
        "riskR41": "Player(CharacterBody2D) 缺 CollisionShape2D → 编辑器黄色警告 + 无碰撞；已补 Body(32x56) 与 GroundBody(StaticBody2D, 480x54, 顶 216) + Feet(Marker2D)",
        "riskR42": "三个 miora 预览画板落在工程根目录被引擎扫描 → 移入 previews/ 并加 .gdignore；assets/_preview/ 加 .gdignore 并清理 31 个拼图 .import",
        "feetAlign": "headless 断言 player_bottom=216.0 == ground_top=216.0（数值对齐；画面贴合仍待目检）",
        "importsNow": 196,
        "importsHistory": "第 15 轮导入 229 项为历史值；第 16 轮清理 assets/_preview 与 previews/ 后现 196 项",
        "riskR43": "AnimatedSprite2D 的 SpriteFrames 原由脚本动态构造 → 编辑器报「必须先设置 SpriteFrames 资源」黄色警告且预览不到帧；已新增 tools/build_sprite_frames.gd 由引擎 ResourceSaver.save 写出 assets/char/player_frames.tres（idle3/run4，6/8fps，7 帧引用）并挂到场景，脚本保留兜底分支",
        "guideSteps": "docs/13 §12.4 由 3 步改 4 步（新增「切 2D 视图」）；§12.1 文件表补 previews/；§12.2 VERIFY 输出更新",
        "dynamicRecheck": "Godot 4.7.2 headless VERIFY|PASS / check_godot_project 错误0警告2通过 / check_traceability PASS / verify_damage_ceiling PASS",
        "selfCheckVerdict": "20/20 PASS",
        "credits": 0,
        "sourceImages": 0,
        "guiF5": "仍需用户按 F5 目检；助手未跑过 GUI",
        "verdict": "离线/headless 全绿；画面未验证",
    }
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("  OK    round16Final 已写入")

    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    old = MEMORY.read_text(encoding="utf-8") if MEMORY.exists() else ""
    if "第 16 轮（用户首次在 GUI 打开工程" in old:
        print("  SKIP  日志已存在")
    else:
        with MEMORY.open("a", encoding="utf-8") as f:
            f.write(ROUND16_MEMORY_APPEND if old else ROUND16_MEMORY_APPEND.lstrip("\n"))
        print("  OK    已追加")

    print("[9/9] 第 16 轮续：导入指南追加 §12.8（R43 帧资源化）")
    g = GUIDE.read_text(encoding="utf-8")
    if "### 12.8 第 16 轮（续）· R43" in g:
        print("  SKIP  已存在")
    else:
        GUIDE.write_text(g.rstrip("\n") + ROUND16B_GUIDE_APPEND, encoding="utf-8")
        print("  OK    §12.8 已追加")

    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    old = MEMORY.read_text(encoding="utf-8") if MEMORY.exists() else ""
    if "R43：帧资源化" in old:
        print("  SKIP  R43 日志已存在")
    else:
        with MEMORY.open("a", encoding="utf-8") as f:
            f.write(ROUND16B_MEMORY_APPEND if old else ROUND16B_MEMORY_APPEND.lstrip("\n"))
        print("  OK    R43 日志已追加")

    print("DONE|handover_replaced=%d|handover_skipped=%d|csv_added=%d" % (d, s, added))


if __name__ == "__main__":
    main()
