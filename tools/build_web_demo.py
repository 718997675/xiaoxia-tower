#!/usr/bin/env python3
"""生成单文件、零依赖的网页验证 Demo：previews/web-demo.html

第 19 轮（用户要求）：「不借助 Godot 就能看到效果，测试没问题再导入 Godot，这样可控」。
第 20 轮（用户要求）：「先做主菜单和战斗横版界面，不然 demo 只能看到选卡」→ 新增
 ⓪ 主菜单 / ① 横版战斗两个视图，并把「清层 → 选卡 → 下一层伤害变化」做成闭环。

本生成器把以下东西全部内嵌进一个 HTML，file:// 双击即可运行，不需要服务器 / Godot / 网络：

  - docs/buff-card-library.json 的设计源副本（data/ 运行时副本）
  - tools/card_rules.js + tools/battle_sim.js 的**全文**（网页 / Node 共用同一份规则实现）
  - 已产 91 帧像素素材（主角 15 / 4 种怪 60 / 4 套 VFX 16）+ 47 图标 + 4 挂件 + 10 卡面（base64）
  - Godot headless / 全量自检 / 跨端比对 / 战斗内核的报告摘要（进度看板数据源）

用法：
  python3 tools/build_web_demo.py           生成
  python3 tools/build_web_demo.py --check   只校验产物完整性（生成到内存比对，不写盘）

边界：这是**网页验证层**，不是游戏本体；网页 CSS 的 image-rendering 只模拟 Nearest，
      不等于 Godot 实机渲染；字体为系统预览字体，不等于实机点阵字（R9 未结案）。
      主菜单/战斗 UI 是职责原型，不是 03 §7 的可编辑设计稿；Q17 仍未拍板。
第 32 轮：Boss / 技能 / overlay / 四深度层背景已由 gpt-image2 回稿转录产出
      （tools/build_from_reference_art.py），本页默认直接用 assets/boss/ 的
      boss_judge / boss_tower_lord 真帧与 assets/bg/*_composite.png 原稿背景；
      ?art=placeholder 或页面按钮可切回第 20 轮的怪物帧放大占位做对照。
      仍只是网页验证层：未接 Godot 场景、未改任何冻结数值，Q17 / GUI F5 未过。
第 33 轮：9 张 gpt-image2 UI 设计稿（assets/ui/reference/ui_*_panel.png，
      16:9 归一 960x540）作为**按视图联动的对照层**内嵌进 nav 下：切视图自动切稿、
      可下拉查看全部 9 张、?ui=off 或按钮可收起。这些稿含示例文字与写死数值
      （血条 276/300、结算 +180、完整卡牌文案），只作设计稿对照，**不贴进任何
      section、不替换交互组件、不参与规则复算**，否则会出现「显示值与规则值不一致」
      的假数值。44 组件 / 48 逐格图标仍是候选资产，未替换 47 个冻结图标与 10 张卡面。
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "previews" / "web-demo.html"
LIB_PATH = ROOT / "data" / "buff-card-library.json"
RULES_PATH = ROOT / "tools" / "card_rules.js"
BATTLE_PATH = ROOT / "tools" / "battle_sim.js"
EFFECTS_PATH = ROOT / "tools" / "card_effects.js"


def b64(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def load_images() -> dict:
    cards = ROOT / "assets" / "ui" / "cards"
    char = ROOT / "assets" / "char"
    out: dict[str, str] = {}
    for p in sorted(cards.glob("frame_*.png")):
        out[p.stem] = b64(p)
    for p in sorted(cards.glob("sigil_*.png")):
        out[p.stem] = b64(p)
    for i in range(3):
        out[f"idle_{i}"] = b64(char / f"char_player_idle_r_0{i}.png")
    for i in range(4):
        out[f"run_{i}"] = b64(char / f"char_player_run_r_0{i}.png")
    needed = {f"frame_{r}" for r in ("common", "rare", "legend", "curse")}
    needed |= {f"sigil_{c}" for c in ("dmg", "attr", "mech", "res", "surv", "syn")}
    needed |= {f"idle_{i}" for i in range(3)} | {f"run_{i}" for i in range(4)}

    # 第 20 轮：战斗视图需要全套序列帧；key 一律用文件名 stem，JS 直接按动画名拼 key。
    char_dir = ROOT / "assets" / "char"
    enemy_dir = ROOT / "assets" / "enemy"
    vfx_dir = ROOT / "assets" / "vfx" / "frames"
    icon_dir = ROOT / "assets" / "ui" / "icons"
    for directory in (char_dir, enemy_dir, vfx_dir, icon_dir, char_dir / "acc"):
        for p in sorted(directory.glob("*.png")):
            out[p.stem] = b64(p)

    n_char = sum(1 for k in out if k.startswith("char_player_") and "_r_" in k)
    n_enemy = sum(1 for k in out if k.startswith("mob_") and "_r_" in k)
    n_vfx = sum(1 for k in out if k.startswith("vfx_") and k[-2:].isdigit())

    # 第 29 轮：B4 补齐后 vfx 从 16 帧涨到 36 帧，写死 (15, 60, 16) 会让
    # 网页产物校验无谓失败。改为「PNG 实际数 == 引擎 JSON 帧数之和」的动态自洽，
    # 并保留旧基线作下界，防止误删素材被当成通过。
    def engine_frame_total(directory: Path, prefix: str) -> int:
        total = 0
        for p in sorted(directory.glob("*.json")):
            if p.name.endswith("_report.json"):
                continue
            meta = json.loads(p.read_text(encoding="utf-8"))
            if (str(meta.get("id", "")).startswith(prefix)
                    and isinstance(meta.get("frameCount"), int)):
                total += meta["frameCount"]
        return total

    expected = (engine_frame_total(char_dir, "char_"),
                engine_frame_total(enemy_dir, "mob_"),
                engine_frame_total(vfx_dir, "vfx_"))
    lower_bounds = (15, 60, 16)
    if ((n_char, n_enemy, n_vfx) != expected
            or any(a < b for a, b in zip(expected, lower_bounds))):
        raise RuntimeError(
            f"战斗素材帧数不符：char={n_char} enemy={n_enemy} vfx={n_vfx}"
            f"（引擎 JSON 合计 {expected}，下界 {lower_bounds}）")
    # 第 32 轮：把 gpt-image2 回稿转录的资源接进验证层（默认原稿模式）。
    # key 一律用文件名 stem（背景四张给语义别名），不与上面的 char/mob/vfx 冲突。
    boss_dir = ROOT / "assets" / "boss"
    overlay_dir = ROOT / "assets" / "vfx" / "overlay"
    bg_dir = ROOT / "assets" / "bg"
    for p in sorted(boss_dir.glob("*.png")):
        out[p.stem] = b64(p)
    for p in sorted(overlay_dir.glob("*.png")):
        out[p.stem] = b64(p)
    bg_scenes = ("normal", "rest", "high", "boss")
    for scene in bg_scenes:
        p = bg_dir / f"bg_{scene}" / f"bg_{scene}_composite.png"
        if not p.is_file():
            raise RuntimeError(f"缺第 31 轮背景合成图：{p}")
        out[f"bg_{scene}"] = b64(p)

    # 动态自洽：Boss 帧数取引擎 JSON 之和，不写死 42；overlay / 背景各有下界防误删。
    n_boss = sum(1 for k in out if k.startswith("boss_") and "_r_" in k)
    boss_expected = engine_frame_total(boss_dir, "boss_")
    n_ovl = sum(1 for k in out if k.startswith("ovl_") and k[-2:].isdigit())
    if n_boss != boss_expected or boss_expected < 42:
        raise RuntimeError(
            f"Boss 帧数不符：PNG={n_boss} 引擎 JSON 合计={boss_expected}（下界 42）")
    if n_ovl != 10 or any(f"bg_{s}" not in out for s in bg_scenes):
        raise RuntimeError(f"状态层/背景不全：overlay={n_ovl}，背景={[s for s in bg_scenes if f'bg_{s}' in out]}")

    # 第 33 轮：9 张 gpt-image2 UI 设计稿（16:9 归一版）作为「按视图联动的对照层」。
    # 只取 manifest 登记的 panel16x9（不用 glob：ui_04-result_result_panel.png 之类
    # 组件名也会匹配 ui_*_panel.png）。这些稿含示例文字与写死数值（血条 276/300、
    # 结算 +180），只作设计稿对照，绝不贴进可交互界面冒充真实组件/显示假数值。
    ui_ref_dir = ROOT / "assets" / "ui" / "reference"
    ui_manifest = json.loads((ui_ref_dir / "ui_reference_manifest.json").read_text(encoding="utf-8"))
    panel_files = [e["file"] for e in ui_manifest["files"]
                   if e.get("kind") == "panel16x9"]
    if len(panel_files) != 9:
        raise RuntimeError(f"UI 设计稿 16:9 底板不是 9 张：{len(panel_files)}")
    for name in panel_files:
        p = ui_ref_dir / name
        if not p.is_file():
            raise RuntimeError(f"缺 UI 设计稿底板：{p}")
        out[Path(name).stem] = b64(p)

    missing = sorted(needed - set(out))
    if missing:
        raise RuntimeError(f"缺素材：{missing}")
    return out


def read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_meta() -> dict:
    rules = read_json(ROOT / "docs" / "card-rules-report.json")
    selfcheck = read_json(ROOT / "docs" / "final-selfcheck.json")
    cross = read_json(ROOT / "docs" / "cross-platform-report.json")
    battle = read_json(ROOT / "docs" / "battle-sim-report.json")
    effects = read_json(ROOT / "docs" / "card-effects-report.json")
    battle_cross = read_json(ROOT / "docs" / "battle-cross-report.json")
    golden = read_json(ROOT / "docs" / "card-golden-samples.json")
    run_a = next((c for c in golden.get("cases", []) if c["runId"] == "runA"), {})
    golden_stages = [
        {
            "stage": s["stage"],
            "offered": s["offered"],
            "picked": s.get("picked", ""),
            "seed": s["seed"],
            "peakAfter": s["peakAfter"],
        }
        for s in run_a.get("stages", [])
    ]
    return {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "round": 22,
        "engine": "Godot 4.7.2.stable (headless)",
        "rules": {
            "verdict": rules.get("verdict", "N/A"),
            "total": rules.get("summary", {}).get("total", 0),
            "passed": rules.get("summary", {}).get("passed", 0),
            "peak": rules.get("summary", {}).get("peakDamage", 0),
            "guardEvents": rules.get("summary", {}).get("guardEvents", 0),
        },
        "selfcheck": {
            "verdict": selfcheck.get("verdict", "N/A"),
            "checks": selfcheck.get("summary", {}).get("checks", 0),
            "passed": selfcheck.get("summary", {}).get("passed", 0),
        },
        "cross": {
            "verdict": cross.get("verdict", "N/A"),
            "total": cross.get("summary", {}).get("total", 0),
            "passed": cross.get("summary", {}).get("passed", 0),
            "algorithm": cross.get("algorithm", ""),
        },
        "battle": {
            "verdict": battle.get("verdict", "N/A"),
            "total": battle.get("summary", {}).get("total", 0),
            "passed": battle.get("summary", {}).get("passed", 0),
            "scope": battle.get("scope", ""),
        },
        "cardEffects": {
            "verdict": effects.get("verdict", "N/A"),
            "total": effects.get("summary", {}).get("total", 0),
            "passed": effects.get("summary", {}).get("passed", 0),
            "battleBoundCards": effects.get("summary", {}).get("battleBoundCards", 0),
            "boundEntries": effects.get("summary", {}).get("boundEntries", 0),
            "deckBound": effects.get("summary", {}).get("deckBound", 0),
            "unbound": effects.get("summary", {}).get("unbound", 0),
            "specConflicts": effects.get("summary", {}).get("specConflicts", 0),
        },
        "battleCross": {
            "verdict": battle_cross.get("verdict", "N/A"),
            "total": battle_cross.get("summary", {}).get("total", 0),
            "passed": battle_cross.get("summary", {}).get("passed", 0),
            "scope": battle_cross.get("scope", ""),
        },
        "goldenRunA": golden_stages,
        "goldenPeak": golden.get("mega", {}).get("peak", 0),
        "timeline": [
            ["第 12 轮", "72 张卡 / 6 类 / 4 档 / UI 规格 / 10 张程序化卡面（PROPOSAL）"],
            ["第 15 轮", "策划案整体确认 → 01 v0.2 合并、design-freeze.json 置 frozen、最小验证工程交付"],
            ["第 16 轮", "用户首次在 GUI 打开工程 → 处置 R41 碰撞体 / R42 预览画板归位"],
            ["第 17 轮", "工作空间迁至 ~/Documents/ai-game/xianxia-tower/（1103 文件 SHA-256 零缺失）"],
            ["第 18 轮", "R44 接手指南引用层级、R45 运行时数据副本；CardDeck.gd 规则层 headless 23/23 PASS"],
            ["第 19 轮", "按用户要求先做网页验证层：R47 统一跨端随机源、黄金样本 25/25、初版网页 Demo"],
            ["第 20 轮", "用户「先做主菜单和战斗界面」→ ⓪ 主菜单 / ① 横版战斗可玩原型、battle_sim.js 44/44、选卡→战斗闭环"],
            ["第 21 轮", "机制型卡不再只是记录：card_effects.js 只读冻结卡库编译效果集，26/72 张在战斗里可观测，其余如实标注归属；R54 卡面/参数不自洽已记录"],
            ["第 22 轮 ← 当前", "UI 设计外发：docs/19 给出 18 段中英提示词（⓪ 风格锚点板 + 6 界面 + 图鉴 + 图标）+ tools/check_ui_art.py 回稿体检；同时补齐战斗「公式层」跨端：scripts/BattleFormula.gd 与 battle_sim.js 逐条复算 8/8 一致（52 条黄金样本）"],
        ],
        "risks": [
            ["R9", "字体授权（凤凰点阵体 CC0 候选未最终核验）", "待拍板"],
            ["R22", "阴兵在墨底对比度（实机目检）", "待实测"],
            ["R33", "层间 6 s / 首见 12 s 阅读窗口", "待实测"],
            ["R34", "combo_hash 区分度 / 卡组不重复率", "待内测"],
            ["R35", "夺主改 k 后重算 B", "待确认"],
            ["R37", "用户侧 GUI 按 F5 画面目检", "待用户做"],
            ["R46", "Godot 内置默认字体不含 CJK（headless 中文 0/30）", "待 GUI 核实"],
            ["R47", "随机源改 xorshift32，网页/Node/Godot 逐层一致", "✅ 第 19 轮已处置"],
            ["R48", "12 §2「10px × 14 汉字/行」与 96px 卡宽不自洽", "待 4× 实机复核"],
            ["R49", "封牌卡 stop_draw 可令一局不足 8 次选择（8 次是上限）", "待设计确认"],
            ["R50", "第 32 轮已解除：assets/boss/ 42 帧与 assets/bg/ 四场景原稿背景已接入本页（默认原稿模式，?art=placeholder 可切回旧占位对照）", "✅ 第 32 轮已处置"],
            ["R51", "技能 CD / cost / HP / 敌人伤害 / 暴击率策划案未给值 → 本页一律 PROPOSAL 占位", "待设计确认"],
            ["R52", "03 §10 Q17「本轮先做哪一类」未拍板；主菜单 / 战斗 UI 仅为职责原型，非可编辑设计稿", "待用户拍板"],
            ["R54", "破云式卡面「总伤不变」与 params split:2 × per_hit:0.6 = 1.2 不自洽；网页按卡面 text 均分 0.5/0.5，待设计确认", "待设计确认"],
            ["R55", "外部模型出的 UI 图只能作参考稿：像素风需逐像素可控（1px 描边 / 整数放大 / 24 色不越界），入库仍走程序化像素链路", "已记录（docs/19 §0）"],
            ["R56", "战斗「公式层」已跨端一致（8/8），但**逐 tick 状态机尚未跨端对齐**，网页战斗结果不能直接当 Godot 实机结论", "待后续轮次"],
        ],
        "importChecklist": [
            "① 在本页 ⓪ 主菜单点「开始入塔」，① 看横版战斗：移动 / 4 技能特效 / 飘字 / 闪白 / 清层",
            "② 清层后点「去选一张卡」，在 ② 选卡再回战斗：① 右侧「本局生效卡牌效果」列出每张卡改变了什么，战斗日志会显示多段命中 / 破防 / 护盾 / 复活等实际触发；未映射条目也如实列出",
            "③ 跑完 ② 的 8 层三选一，确认候选数、峰值 3996、红线与已选卡都符合预期",
            "④ 打开 Godot 编辑器导入 project.godot，按 F5 看 MinimalRun（像素硬边 / 4× 对齐 / 镜像）",
            "⑤ 四步都确认后再按 01 §12 建正式战斗工程：先拍板 Q17、产出 6 界面设计稿、补 Boss 素材与技能数值",
            "⑥ UI 设计稿走外部模型路线：提示词在 docs/19 与 previews/ui-prompts-pack.md（⓪ 风格锚点板先出），回稿丢进 previews/ui/ 后跑 python3 tools/check_ui_art.py previews/ui/ 做调色板 / 尺寸 / 半透明体检",
            "注意：网页只验证规则与布局，不替代 Godot 实机渲染与像素目检；CSS 模拟 Nearest ≠ 实机",
        ],
    }


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>九重天梯 · 网页验证 Demo（第 22 轮 · 主菜单 / 横版战斗 / 卡牌效果 / 战斗跨端）</title>
<style>
:root{
  --bg:#12161F; --panel:#2A3140; --ink:#000000; --paper:#E8DFC8;
  --paper-dim:#C9BFA3; --jade:#5FA8A0; --gold:#D9A441; --gold-hi:#F2D089;
  --red:#C8453B; --red-hi:#E8806F; --purple:#8A6FC4; --curse:#7A2420;
  --text:#E8DFC8; --muted:#8A8268; --line:#4A5568;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--text);
  font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
  font-size:13px;line-height:1.6}
img{image-rendering:pixelated;image-rendering:crisp-edges}
button,input{font-family:inherit;font-size:inherit}
.wrap{max-width:1400px;margin:0 auto;padding:0 20px 48px}
header{border-bottom:1px solid var(--line);padding:18px 0 12px;margin-bottom:0}
.brand{font-size:20px;font-weight:700;letter-spacing:2px;color:var(--gold-hi)}
.brand small{font-size:12px;font-weight:400;letter-spacing:0;color:var(--muted);margin-left:10px}
.flags{margin-top:8px;color:var(--muted);font-size:12px}
.flags b{color:var(--jade);font-weight:600}
.flags .now{color:var(--gold);font-weight:700}
.badge{display:inline-block;border:1px solid var(--jade);color:var(--jade);
  padding:1px 8px;margin-left:8px;font-size:11px;vertical-align:middle}
nav{display:flex;gap:0;border-bottom:1px solid var(--line);margin:14px 0 20px;flex-wrap:wrap}
nav button{background:transparent;border:1px solid transparent;border-bottom:none;color:var(--muted);
  padding:9px 18px;cursor:pointer;border-radius:0}
nav button:hover{color:var(--text)}
nav button.active{color:var(--gold-hi);border:1px solid var(--line);border-bottom:2px solid var(--gold);
  background:var(--panel)}
/* 第 33 轮：UI 设计稿对照层。整屏稿含示例文字与写死数值，只作并排对照，
   不铺进任何 section，也不替换交互组件；设计稿是 LANCZOS 归一的 960x540，
   不能用全局 pixelated，否则缩略会被最近邻放大成锯齿。 */
.uiskinbar{border:1px solid var(--line);background:var(--panel);margin:0 0 18px;padding:10px 12px}
.uiskin-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:12px}
.uiskin-head b{color:var(--gold-hi);letter-spacing:1px}
.uiskin-tag{color:var(--jade);font-size:11px}
.uiskin-hint{color:var(--muted);font-size:11px;flex:1 1 200px;min-width:160px}
#uiSkinSelect{background:#1B2130;color:var(--text);border:1px solid var(--line);
  padding:3px 6px;font-family:inherit;font-size:11px;max-width:300px}
.uiskin-body{display:flex;gap:14px;align-items:flex-start;margin-top:10px;flex-wrap:wrap}
#uiSkinImg{width:480px;height:270px;object-fit:contain;image-rendering:auto;
  border:1px solid var(--line);background:#0E1118;flex:0 0 auto}
.uiskin-note{flex:1 1 300px;color:var(--muted);font-size:11px;line-height:1.75}
.uiskin-note b{color:var(--red-hi)}
.uiskinbar.off .uiskin-body{display:none}
section{display:none}
section.active{display:block}
h2{font-size:15px;margin:0 0 12px;color:var(--gold-hi);letter-spacing:1px}
h3{font-size:13px;margin:18px 0 8px;color:var(--jade)}
.note{color:var(--muted);font-size:12px;margin:6px 0 14px;border-left:2px solid var(--line);padding-left:10px}
.warn{border-left:2px solid var(--red);color:var(--red-hi);font-size:12px;padding-left:10px;margin:8px 0}
.grid2{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:20px;align-items:start}
.panel{background:var(--panel);border:1px solid var(--line);padding:14px}
.kv{display:flex;justify-content:space-between;border-bottom:1px dotted var(--line);padding:4px 0;gap:10px}
.kv span:first-child{color:var(--muted);flex:0 0 auto}
.kv span:last-child{text-align:right;word-break:break-all}
.ok{color:var(--jade)} .bad{color:var(--red-hi)} .gold{color:var(--gold)}
.bar{height:10px;background:var(--ink);border:1px solid var(--line);margin:6px 0 12px}
.bar i{display:block;height:100%;background:var(--jade)}
.bar i.over{background:var(--red)}
.btn{background:var(--panel);border:1px solid var(--line);color:var(--text);padding:6px 12px;
  cursor:pointer;border-radius:0;margin:0 6px 6px 0}
.btn:hover{border-color:var(--gold);color:var(--gold-hi)}
.btn.primary{border-color:var(--gold);color:var(--gold-hi)}
.btn.on{border-color:var(--jade);color:var(--jade)}
.controls{margin-top:12px}
.log{margin-top:10px;max-height:170px;overflow:auto;border:1px solid var(--line);
  background:#0D1119;padding:8px;font-size:11px;line-height:1.7;white-space:pre-wrap}
/* 480x270 逻辑画布 */
.stage-wrap{position:relative;background:#0D1119;border:1px solid var(--line);overflow:hidden}
#stage{position:relative;width:480px;height:270px;background:var(--bg);
  transform-origin:top left;overflow:hidden}
#stage .bg{position:absolute;inset:0;background:var(--bg)}
#stage .titleband{position:absolute;left:0;top:8px;width:480px;height:20px;background:#1B2130}
#stage .separator{position:absolute;left:0;top:28px;width:480px;height:1px;background:var(--line)}
#stage .t{position:absolute;left:8px;top:8px;width:300px;height:20px;line-height:20px;
  font-size:12px;color:var(--gold-hi);letter-spacing:1px}
#stage .p{position:absolute;left:292px;top:8px;width:180px;height:20px;line-height:20px;
  font-size:11px;color:var(--muted);text-align:right}
#stage .footer{position:absolute;left:0;top:214px;width:480px;height:32px;background:#1B2130;
  border-top:1px solid var(--line)}
#stage .hint{position:absolute;left:8px;top:218px;width:340px;height:24px;line-height:24px;
  font-size:10px;color:var(--muted)}
#stage .confirm{position:absolute;left:356px;top:218px;width:116px;height:24px;
  background:var(--panel);border:1px solid var(--line);color:var(--text);font-size:10px;
  cursor:pointer;border-radius:0}
#stage .confirm.ready{border-color:var(--gold);color:var(--gold-hi)}
#stage .goldline{position:absolute;left:0;top:246px;width:480px;height:1px;background:var(--line)}
#stage .goldline.on{background:var(--gold)}
#stage .stateline{position:absolute;left:8px;top:198px;width:464px;height:14px;
  line-height:14px;font-size:10px;color:var(--jade)}
.card{position:absolute;width:96px;height:144px;top:52px;cursor:pointer;display:none}
/* docs/12 §2：三卡 x = 80 / 192 / 304，y = 52，卡 96×144，间距 16 */
.card[data-i="0"]{left:80px}
.card[data-i="1"]{left:192px}
.card[data-i="2"]{left:304px}
.card.show{display:block}
.card .paper{position:absolute;inset:0;background:var(--paper)}
.card .frame{position:absolute;inset:0;width:96px;height:144px}
.card .catbar{position:absolute;left:5px;top:4px;width:8px;height:8px;background:var(--line)}
.card .sigil{position:absolute;left:24px;top:24px;width:48px;height:48px}
.card .cname{position:absolute;left:4px;top:79px;width:88px;height:15px;line-height:15px;
  font-size:12px;text-align:center;color:#1B2130;overflow:hidden;white-space:nowrap}
.card .cdesc{position:absolute;left:5px;top:96px;width:86px;height:30px;font-size:10px;
  line-height:10px;color:#2A3140;overflow:hidden;white-space:pre-line}
.card .cinfo{position:absolute;left:5px;top:130px;width:86px;height:11px;font-size:9px;
  line-height:11px;color:#4A5568}
.card .pips{position:absolute;left:84px;top:3px;width:9px;height:9px}
.card .pips i{position:absolute;width:2px;height:2px;background:var(--gold)}
.card .unread{position:absolute;left:91px;top:12px;width:3px;height:3px;background:var(--red-hi);display:none}
.card .unread.on{display:block}
.card .goldframe{position:absolute;inset:0;border:1px solid var(--gold);display:none;pointer-events:none}
.card .goldframe:after{content:"";position:absolute;inset:3px;border:1px solid var(--gold)}
.card.selected{transform:translateY(-4px)}
.card.selected .goldframe{display:block}
.card.curse .cname,.card.curse .cdesc,.card.curse .cinfo{color:var(--paper)}
.goldbase{position:absolute;top:192px;width:96px;height:4px;background:var(--gold);display:none}
.goldbase.on{display:block}
#resultOverlay{position:absolute;inset:0;background:#0D1119;border:1px solid var(--gold);
  padding:12px;display:none;z-index:5;font-size:11px;overflow:auto}
#resultOverlay h3{margin:0 0 6px;color:var(--gold-hi);font-size:14px}
/* 像素跑动 */
#spriteWrap{position:relative;background:#0D1119;border:1px solid var(--line);overflow:hidden}
#spriteStage{position:relative;width:480px;height:270px;background:var(--bg);transform-origin:top left}
#spriteStage .ground{position:absolute;left:0;top:216px;width:480px;height:54px;background:#212A2E}
#spriteStage .gline{position:absolute;left:0;top:216px;width:480px;height:1px;background:#3A4A48}
#spriteImg{position:absolute;width:64px;height:64px}
#spriteHud{position:absolute;left:8px;top:8px;font-size:11px;color:var(--jade);
  background:#0D1119;padding:2px 6px;white-space:pre}
/* 图鉴 */
.filters{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:12px}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--muted);padding:3px 9px;
  cursor:pointer;font-size:11px;border-radius:0}
.chip.on{border-color:var(--gold);color:var(--gold-hi)}
#search{background:#0D1119;border:1px solid var(--line);color:var(--text);padding:4px 8px;width:180px}
.codex-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:8px}
.codex-card{background:var(--panel);border:1px solid var(--line);padding:6px;cursor:pointer;min-height:74px}
.codex-card:hover{border-color:var(--gold)}
.codex-card .cn{font-size:12px;color:var(--text)}
.codex-card .cm{font-size:10px;color:var(--muted);margin-top:3px}
.codex-card .dot{display:inline-block;width:7px;height:7px;margin-right:4px;vertical-align:middle}
#codexDetail{position:fixed;right:20px;top:80px;width:320px;max-height:70vh;overflow:auto;
  background:#0D1119;border:1px solid var(--gold);padding:14px;z-index:20;display:none}
#codexDetail pre{white-space:pre-wrap;word-break:break-all;font-size:11px;color:var(--jade)}
/* 看板 */
.cards4{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-bottom:18px}
.metric{background:var(--panel);border:1px solid var(--line);padding:12px}
.fxpanel{font-size:11px;line-height:1.55;max-height:236px;overflow:auto;border:1px solid var(--line);background:#0D1119;padding:6px}
.fxpanel .fxcard{border-bottom:1px dashed var(--line);padding:4px 0}
.fxpanel .fxcard:last-child{border-bottom:none}
.fxpanel .fxhead{color:var(--gold-hi)}
.fxpanel .fx-b{color:#8FD3C8}
.fxpanel .fx-n{color:var(--muted);font-size:10px}
.fxpanel .fx-w{color:#E8A06F;font-size:10px}
.fxpanel .fxempty{color:var(--muted)}
.metric .n{font-size:24px;color:var(--gold-hi);line-height:1.2}
.metric .l{font-size:11px;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--jade);font-weight:600}
ul{margin:6px 0;padding-left:20px} li{margin:3px 0}
.tag{display:inline-block;border:1px solid var(--line);padding:0 6px;margin-right:4px;font-size:11px}
.tag.done{border-color:var(--jade);color:var(--jade)}
.tag.todo{border-color:var(--red);color:var(--red-hi)}
footer{margin-top:26px;border-top:1px solid var(--line);padding-top:12px;color:var(--muted);font-size:11px}
/* ⓪ 主菜单（480×270 逻辑画布，按 01 §11 MainMenu 四职责） */
#menuWrap{position:relative;background:#0D1119;border:1px solid var(--line);overflow:hidden}
#menuScreen{position:relative;width:480px;height:270px;transform-origin:top left;overflow:hidden}
#menuScreen .sky{position:absolute;inset:0;background:linear-gradient(#12161F 0%,#1B2130 58%,#2A3140 100%)}
#menuScreen .stars{position:absolute;inset:0;background-image:radial-gradient(#F2D089 1px,transparent 1px);
  background-size:37px 29px;background-position:6px 3px;opacity:.30}
#menuScreen .moon{position:absolute;right:54px;top:20px;width:30px;height:30px;border-radius:50%;
  background:#E8DFC8;box-shadow:0 0 0 7px rgba(232,223,200,.07)}
#menuScreen .mfar{position:absolute;left:0;bottom:44px;width:480px;height:88px;background:#2A3140;
  clip-path:polygon(0 100%,0 62%,12% 38%,24% 66%,38% 24%,52% 60%,66% 32%,80% 64%,92% 42%,100% 70%,100% 100%)}
#menuScreen .mnear{position:absolute;left:0;bottom:44px;width:480px;height:58px;background:#212A2E;
  clip-path:polygon(0 100%,0 66%,18% 40%,34% 72%,52% 44%,70% 70%,86% 48%,100% 74%,100% 100%)}
#menuScreen .tower{position:absolute;right:88px;bottom:44px;width:22px;height:112px;background:#1B2130;
  border:1px solid #4A5568;border-bottom:none}
#menuScreen .tower:before,#menuScreen .tower:after{content:"";position:absolute;left:-6px;width:32px;height:7px;
  background:#1B2130;border:1px solid #4A5568}
#menuScreen .tower:before{top:22px}#menuScreen .tower:after{top:58px}
#menuScreen .mg{position:absolute;left:0;bottom:0;width:480px;height:44px;background:#1B2130;border-top:1px solid #3A4A48}
#menuHero{position:absolute;left:52px;bottom:38px;width:96px;height:96px;image-rendering:pixelated}
#menuScreen .mtitle{position:absolute;left:22px;top:20px;font-size:25px;letter-spacing:7px;
  color:var(--gold-hi);text-shadow:2px 2px 0 #000;line-height:1.2}
#menuScreen .msub{position:absolute;left:24px;top:58px;font-size:10px;color:var(--paper-dim);letter-spacing:2px}
#menuScreen .mver{position:absolute;left:24px;top:76px;font-size:9px;color:var(--muted)}
.menu-btns{position:absolute;left:196px;top:96px;width:214px;display:flex;flex-direction:column;gap:6px}
.menu-btns button{background:rgba(27,33,48,.92);border:1px solid var(--line);color:var(--text);
  padding:5px 10px;text-align:left;cursor:pointer;font-size:11px;letter-spacing:1px;border-radius:0}
.menu-btns button:hover,.menu-btns button.on{border-color:var(--gold);color:var(--gold-hi)}
.menu-btns button b{display:inline-block;width:16px;color:var(--gold)}
/* ① 横版战斗 */
#battleWrap{position:relative;background:#0D1119;border:1px solid var(--line);overflow:hidden}
#battleStage{position:relative;width:480px;height:270px;background:var(--bg);transform-origin:top left;overflow:hidden}
#battleWorld{position:absolute;inset:0}
/* 第 32 轮：原稿模式。bbgart 是 480x270 的 gpt-image2 四层合成图，1:1 铺底；
   art-ref 下隐藏第 20 轮的 CSS 山影/地面色块，避免不透明图层挡住原稿。
   HUD 的半透明底衬只是验证层可读性兜底，不是 UI 设计定稿。 */
.arttoggle{float:right;font-size:11px;padding:3px 10px;background:#1B2130;color:var(--paper);
  border:1px solid var(--gold);border-radius:2px;cursor:pointer;font-family:inherit}
.arttoggle:hover{background:#2A3140}
.bbgart{position:absolute;inset:0;width:480px;height:270px;image-rendering:pixelated;
  display:none;z-index:0;pointer-events:none}
#battleStage.art-ref .bbgart{display:block}
#battleStage.art-ref .bsky,#battleStage.art-ref .bfar,#battleStage.art-ref .bground{display:none}
#battleStage.art-ref .bgline{background:rgba(232,223,200,.35)}
#battleStage.art-ref .bhud,#battleStage.art-ref .bstage{background:rgba(18,22,31,.80);
  padding:3px;border-radius:2px;border:1px solid rgba(232,223,200,.18)}
#battleStage.art-ref #bossBar{background:rgba(18,22,31,.82);padding:2px}
.bsky{position:absolute;inset:0;background:linear-gradient(#12161F 0%,#1B2130 66%,#2A3140 100%)}
.bfar{position:absolute;left:0;top:150px;width:480px;height:66px;background:#222A38;opacity:.75;
  clip-path:polygon(0 100%,0 60%,10% 34%,22% 68%,36% 28%,50% 62%,64% 30%,78% 66%,90% 38%,100% 64%,100% 100%)}
.bground{position:absolute;left:0;top:216px;width:480px;height:54px;background:#212A2E}
.bgline{position:absolute;left:0;top:216px;width:480px;height:1px;background:#3A4A48}
.bhud{position:absolute;left:6px;top:5px;width:214px}
.barrow{display:flex;align-items:center;gap:4px;height:10px}
.barrow .lab{width:16px;font-size:8px;color:var(--paper-dim)}
.barrow .track{width:132px;height:6px;background:#000;border:1px solid var(--line)}
.barrow .track i{display:block;height:100%}
.barrow .num{font-size:8px;color:var(--muted);width:46px;text-align:right}
.bstage{position:absolute;right:6px;top:5px;font-size:10px;color:var(--gold-hi);text-align:right;line-height:1.5}
.bstage .br{font-size:8px;color:var(--muted)}
.realm-pips{display:inline-flex;gap:2px;margin-left:3px;vertical-align:middle}
.realm-pips i{width:4px;height:7px;background:var(--jade);display:inline-block}
/* top 44px：避开 .bhud 三条（到 35px）与 .bstage 第二行，防止 Boss 血条压住层数文字 */
#bossBar{position:absolute;left:118px;top:44px;width:244px;height:8px;background:#000;
  border:1px solid var(--gold);display:none}
#bossBar i{display:block;height:100%;background:var(--red)}
.bslots{position:absolute;left:6px;bottom:5px;display:flex;gap:5px}
.bslot{position:relative;width:36px;height:36px;background:#1B2130;border:1px solid var(--line)}
.bslot img{position:absolute;left:1px;top:1px;width:32px;height:32px;image-rendering:pixelated}
.bslot .key{position:absolute;left:2px;top:-2px;font-size:8px;color:var(--gold-hi);z-index:2;text-shadow:1px 1px 0 #000}
.bslot .cdmask{position:absolute;inset:0;background:rgba(18,22,31,.80);color:var(--gold-hi);
  font-size:12px;display:flex;align-items:center;justify-content:center;z-index:1}
.bslot .cdmask.hide{display:none}
.bhint{position:absolute;right:6px;bottom:5px;font-size:8px;color:var(--muted);text-align:right;line-height:1.5}
.bsprite,.benemy{position:absolute;width:64px;height:64px;image-rendering:pixelated}
.benemy.flash,.bsprite.flash{filter:brightness(3) saturate(0)}
.bvfx{position:absolute;width:64px;height:64px;image-rendering:pixelated;pointer-events:none}
.benemyHp{position:absolute;height:4px;background:#000;border:1px solid var(--line);pointer-events:none}
.benemyHp i{display:block;height:100%;background:var(--red)}
.float{position:absolute;font-size:12px;font-weight:700;color:var(--gold-hi);
  text-shadow:1px 1px 0 #000;pointer-events:none;white-space:nowrap;z-index:4}
.float.crit{font-size:15px;color:#FFFFFF}
.float.hurt{color:var(--red-hi)}.float.heal{color:#9BD4CC}
#edgeTint{position:absolute;inset:0;box-shadow:inset 0 0 26px 8px rgba(200,69,59,.85);
  opacity:0;pointer-events:none;z-index:5}
#battleOverlay{position:absolute;inset:0;background:rgba(13,17,25,.93);z-index:7;
  padding:16px;display:none;font-size:11px;color:var(--text);overflow:auto}
#battleOverlay h3{margin:0 0 8px;color:var(--gold-hi);font-size:14px}
#battleOverlay .obtns{margin-top:10px}
#battleOverlay button{background:var(--panel);border:1px solid var(--line);color:var(--text);
  padding:5px 10px;margin:0 6px 6px 0;cursor:pointer;font-size:10px}
#battleOverlay button.primary{border-color:var(--gold);color:var(--gold-hi)}
.battle-log{max-height:190px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="brand">九重天梯 · 网页验证 Demo <small>第 22 轮 · 单文件 / 零依赖 / 不需要 Godot</small><span class="badge">file:// 直接运行</span></div>
  <div class="flags">进度：<b>阶段一 规格</b> ✅ → <b>阶段二 最小验证工程</b> ✅ → <b>卡牌规则层</b> ✅ → <span class="now">网页验证层（主菜单 / 横版战斗）← 你在这里</span> → 正式战斗工程（未开工）</div>
</header>

<nav>
  <button class="active" data-tab="menu">⓪ 主菜单 · 入口</button>
  <button data-tab="battle">① 横版战斗 · 可玩</button>
  <button data-tab="draft">② 层间三选一 · 可玩</button>
  <button data-tab="sprite">③ 像素跑动预览</button>
  <button data-tab="codex">④ 72 卡图鉴</button>
  <button data-tab="status">⑤ 进度与自检看板</button>
</nav>

<!-- 第 33 轮：UI 设计稿对照层（gpt-image2 回稿，按视图自动联动） -->
<div id="uiSkinBar" class="uiskinbar">
  <div class="uiskin-head">
    <b>UI 设计稿对照</b>
    <span class="uiskin-tag">gpt-image2 回稿 · 9 张 · 960×540 归一</span>
    <select id="uiSkinSelect" aria-label="选择 UI 设计稿"></select>
    <button id="uiSkinToggle" class="arttoggle" type="button"></button>
    <span id="uiSkinHint" class="uiskin-hint"></span>
  </div>
  <div id="uiSkinBody" class="uiskin-body">
    <img id="uiSkinImg" alt="UI 设计稿对照">
    <div class="uiskin-note">
      <b>⚠️ 这是设计稿对照层，不是界面贴图，也不是 UI 定稿。</b><br>
      稿中含<b>示例文字与写死数值</b>（血条 <code>276/300</code>、结算 <code>+180</code>、完整卡牌文案、
      「开始入塔」按钮），一律<b>不作实机数值、不参与任何规则复算</b>；下方六个视图仍是
      第 20 轮起的手写 CSS 职责原型，展示的是<b>可交互的规则与布局</b>。
      之所以不把切出的 44 个组件直接贴进界面：它们大多自带示例文案，贴上去会出现
      「显示值与 <code>battle_sim.js</code> 规则值不一致」的假数值，违反项目「数值必须可复算」纪律。<br>
      口径：<code>R55</code> 外部模型出图只算参考稿、不算入库资源；<b>Q17 未拍板</b>，稿中坐标为
      <b>PROPOSAL</b>；<code>assets/ui/reference/</code> 的 44 组件 / 48 逐格图标仍是<b>候选资产</b>，
      未替换 47 个冻结图标 ID 与 10 张卡面；本层<b>不接 Godot 场景、不改任何冻结数值</b>。
      切换视图会自动联动到对应稿，<code>?ui=off</code> 可默认收起。
    </div>
  </div>
</div>

<!-- ⓪ 主菜单 -->
<section id="menu" class="active">
  <h2>主菜单 · 按 01 §11 MainMenu 职责表（开始 / 境界总览 / 传承灵韵栏 / 设置）</h2>
  <div class="warn">⚠️ 这是<b>界面职责原型</b>，不是 <code>03</code> §7 的「6 个界面可编辑设计稿」：<code>03</code> §10 的 <b>Q17「本轮先做哪一类」至今未拍板</b>。山影 / 塔 / 月均为 CSS 程序化绘制（0 出图积分），角色用已产 idle 帧；字体为系统预览字体（R9 未结案）。</div>
  <div class="grid2">
    <div>
      <div id="menuWrap"><div id="menuScreen">
        <div class="sky"></div><div class="stars"></div><div class="moon"></div>
        <div class="mfar"></div><div class="tower"></div><div class="mnear"></div><div class="mg"></div>
        <img id="menuHero" alt="player idle">
        <div class="mtitle">九重天梯</div>
        <div class="msub">一层一境 · 择一机缘</div>
        <div class="mver">网页验证层 v20 · 480×270 逻辑画布</div>
        <div class="menu-btns">
          <button data-menu="start" class="on"><b>▸</b>开始入塔 → 横版战斗</button>
          <button data-menu="realm"><b>·</b>境界总览（9 境 / 4 段色）</button>
          <button data-menu="legacy"><b>·</b>传承灵韵栏（6 条）</button>
          <button data-menu="settings"><b>·</b>设置（验证层说明 / 占位）</button>
        </div>
      </div></div>
      <div class="controls">
        <button class="btn primary" id="btnMenuStart">▶ 开始入塔（进入 ① 横版战斗）</button>
        <button class="btn" id="btnMenuBoss">⚡ 直接看第 9 层 Boss（占位素材）</button>
      </div>
    </div>
    <aside class="panel">
      <h2 style="margin-top:0" id="menuPanelTitle">开始入塔</h2>
      <div id="menuPanel"></div>
      <h3>首启流程（01 §11）</h3>
      <div class="note" style="margin-top:0">MainMenu → 创建 <code>user://meta_save.json</code> → 教学层 1 → 首次结算展示「传承」引导 → MainMenu。本页<b>没有存档 / 没有音频 / 没有 Godot 场景</b>，只演示入口与跳转。</div>
    </aside>
  </div>
</section>

<!-- ① 横版战斗 -->
<section id="battle">
  <h2>横版战斗 · 可玩原型（移动 / 4 技能特效 / 命中飘字 / 闪白 / 清层）
    <button id="artToggle" class="arttoggle" type="button"></button></h2>
  <div class="note">规则跑的是 <code>tools/battle_sim.js</code>（与 Node 断言同一份）：伤害公式照抄 <code>01</code> §8.1、层波形照抄 §8.3、怪物映射照抄 <code>06</code> §7、状态机照抄 §6 M1。<b>第 32 轮起素材默认走 gpt-image2 回稿转录版</b>：第 5 / 9 层用 <code>assets/boss/</code> 的判官 / 塔主真帧，战斗底图按层型用 <code>assets/bg/</code> 四场景原稿合成图，技能与状态层是 <code>C1 / C2</code> 派生帧；点右上「切换素材」或加 <code>?art=placeholder</code> 可回到第 20 轮的 CSS 山影 + 剑魂帧放大占位做对照。<b>只换像素源，不改任何冻结数值、不接 Godot 场景</b>；Q17 与 GUI F5 仍未过。</div>
  <div class="warn">⚠️ 技能 CD / 灵力消耗 / HP / 敌人伤害 / 暴击率等策划案未给值，全部是 <b>PROPOSAL 占位</b>（R51），只为让你看到节奏，<b>不是冻结数值、不是平衡结论</b>。CSS 模拟 Nearest ≠ Godot 实机渲染；本页不是游戏本体，<code>project.godot</code> 与 <code>MinimalRun.tscn</code> 一个字节未改。</div>
  <div class="note">关于「选卡后战斗会变强多少」：按冻结规格<b>卡牌不得提高五上界</b>，卡库里只有 5 张数值型卡，共享池增量仅 10–30 点；<b>第 21 轮起机制型卡也会生效</b>——<code>tools/card_effects.js</code> 只读冻结卡库，把卡面与参数对得上的键编译成战斗效果（26/72 张：多段命中 / 破防 / 护盾 / CD / 灵力 / 减伤 / 复活等），在右侧「本局生效卡牌效果」与战斗日志里逐条可查；<b>归抽卡层、条件未满足、语义需确认的条目一律如实列为未映射，不猜数值、不伪造效果</b>（<code>docs/18</code>）。想直观看「共享池 → 伤害」因果点 <b>🧪 共享池 +150</b>；想直接看机制卡效果点 <b>🧪 预置机制卡组</b>。两者都是<b>明确标注的人造演示输入</b>，不经过抽卡规则、不改卡库与冻结数值，点「重置本层」即复原。</div>
  <div class="grid2">
    <div>
      <div id="battleWrap"><div id="battleStage"><div id="battleWorld">
        <img id="bBgArt" class="bbgart" alt="gpt-image2 回稿转录的塔层四深度合成背景">
        <div class="bsky"></div><div class="bfar"></div>
        <div class="bground"></div><div class="bgline"></div>
        <div id="bossBar"><i></i></div>
        <div class="bhud" id="bHud"></div>
        <div class="bstage" id="bStage"></div>
        <div id="bActors"></div>
        <div id="bVfx"></div>
        <div id="bFloats"></div>
        <div class="bslots" id="bSlots"></div>
        <div class="bhint">A/D 移动 · J/K/L/I 技能 · Space 闪避 · Esc 暂停<br>只镜像角色与特效，不镜像整个场景（DF-04）</div>
        <div id="edgeTint"></div>
        <div id="battleOverlay"></div>
      </div></div></div>
      <div class="controls">
        <button class="btn primary" id="btnBattleAuto">▶ 自动演示战斗（打到清层）</button>
        <button class="btn" id="btnBattleReset">重置本层</button>
        <button class="btn" id="btnBattlePause">暂停 / 继续 (Esc)</button>
        <button class="btn" id="btnBattleBoss">⚡ 跳到第 9 层 Boss</button>
        <button class="btn" id="btnBattleDraft">🎴 去选一张卡（联动）</button>
        <button class="btn" id="btnPoolDemo">🧪 共享池 +150（演示注入，非卡牌）</button>
        <button class="btn" id="btnFxDemo">🧪 预置机制卡组（演示注入，非抽卡）</button>
      </div>
      <div class="log battle-log" id="battleLog"></div>
    </div>
    <aside class="panel">
      <h2 style="margin-top:0">战斗实时状态</h2>
      <div id="battlePanel"></div>
      <h3>本局生效卡牌效果 <span style="font-size:10px;color:var(--muted);font-weight:normal">（第 21 轮）</span></h3>
      <div id="fxPanel" class="fxpanel"></div>
      <div class="note" style="margin-top:6px;font-size:10px">⚠️ 这是<b>网页验证层的可视化口径</b>，不是冻结规格、不是平衡结论、不迁移到 Godot 实机。只映射卡面 text 与 params 对得上的键；归抽卡层 / 条件未满足 / 需设计确认的键一律如实列出，<b>不猜数值、不伪造效果</b>。详见 <code>docs/18</code>。</div>
      <h3>伤害公式（01 §8.1）</h3>
      <div class="note" style="margin-top:0;font-size:11px">final = clamp(round((base × realm_ratio + extra_pool) × combo_mult × crit_mult × (1 − defense_rate)), 1, 9999)<br>五上界：base≤180 / realm≤1.60 / pool≤600 / combo≤2.5 / crit≤1.8。<b>选卡后共享池变化 → 这里和飘字同步变大</b>。</div>
    </aside>
  </div>
</section>

<!-- ② 三选一 -->
<section id="draft">
  <h2>层间三选一 · 8 层完整流程（跑的是与 Godot 同一份规则）</h2>
  <div class="note">候选卡、种子、峰值、守卫事件全部来自 <code>tools/card_rules.js</code>，与 <code>scripts/CardDeck.gd</code> 逐层一致（跨端比对见 ⑤）。卡面 PNG 不含文字；此处文字为系统预览字体，<b>不等于实机点阵字</b>（R9 未结案）。<br>与 ① 战斗联动时，<b>数值型卡</b>改共享池让飘字变大；<b>机制型卡从第 21 轮起也会生效</b>（26/72 张，见 <code>tools/card_effects.js</code>）：多段命中 / 破防 / 护盾 / CD / 灵力 / 减伤 / 复活等在 ① 的日志与本局效果面板里可观测；归抽卡层、条件未满足、语义需确认的条目<b>如实列为未映射，不伪造</b>（<code>docs/18</code>）。面板上的「峰值 3996」是五上界最坏口径，<b>不是当前实战单次伤害</b>。</div>
  <div class="grid2">
    <div>
      <div class="stage-wrap" id="stageWrap"><div id="stage">
        <div class="bg"></div>
        <div class="titleband"></div><div class="separator"></div>
        <div class="t" id="stageTitle"></div><div class="p" id="stageProgress"></div>
        <div class="goldbase" id="goldBase"></div>
        <div class="card" data-i="0"><div class="paper"></div><img class="frame"><div class="catbar"></div><img class="sigil"><div class="cname"></div><div class="cdesc"></div><div class="cinfo"></div><div class="pips"></div><div class="unread"></div><div class="goldframe"></div></div>
        <div class="card" data-i="1"><div class="paper"></div><img class="frame"><div class="catbar"></div><img class="sigil"><div class="cname"></div><div class="cdesc"></div><div class="cinfo"></div><div class="pips"></div><div class="unread"></div><div class="goldframe"></div></div>
        <div class="card" data-i="2"><div class="paper"></div><img class="frame"><div class="catbar"></div><img class="sigil"><div class="cname"></div><div class="cdesc"></div><div class="cinfo"></div><div class="pips"></div><div class="unread"></div><div class="goldframe"></div></div>
        <div class="stateline" id="stageState"></div>
        <div class="footer"></div>
        <div class="hint" id="stageHint"></div>
        <button class="confirm" id="confirmBtn">确认 (Enter)</button>
        <div class="goldline" id="goldLine"></div>
        <div id="resultOverlay"></div>
      </div></div>
      <div class="controls">
        <button class="btn primary" id="btnConfirm">确认选卡 (Enter)</button>
        <button class="btn" id="btnRestart">重开一局 (R)</button>
        <button class="btn" id="btnWuxiang">切「无相」词缀 (W)</button>
        <button class="btn" id="btnReplay">确定性复核</button>
        <button class="btn" id="btnCodex">已选卡 (Esc)</button>
        <button class="btn primary" id="btnAutoRun">▶ 自动演示整局（8 层）</button>
      </div>
      <div class="log" id="draftLog"></div>
    </div>
    <aside class="panel">
      <h2 style="margin-top:0">实时状态</h2>
      <div id="statePanel"></div>
      <h3>本局已选</h3>
      <div class="log" id="pickedList" style="max-height:150px"></div>
    </aside>
  </div>
</section>

<!-- ③ 像素跑动 -->
<section id="sprite">
  <h2>主角像素跑动 · 把 F5 目检项先搬到网页</h2>
  <div class="note">素材：64×64 / idle 3 帧 @6fps / run 4 帧 @8fps / 锚点 (32,62) / 逻辑画布 480×270，与 <code>PlayerProbe.gd</code> 同口径。按 <b>A / D</b> 或下面按钮左右跑；亦默认开启「自动来回跑」。</div>
  <div class="warn">⚠️ 网页用 CSS <code>image-rendering: pixelated</code> 模拟 Nearest 与整数倍缩放，<b>不等于 Godot 实机渲染</b>。像素是否硬边、4× 对齐、朝右镜像是否穿帮，仍需你在编辑器按 F5 目检（R37）；本页只能让你先看到效果大概长什么样。</div>
  <div class="grid2">
    <div>
      <div id="spriteWrap"><div id="spriteStage">
        <div class="ground"></div><div class="gline"></div>
        <img id="spriteImg" alt="player">
        <div id="spriteHud"></div>
      </div></div>
      <div class="controls">
        <button class="btn" id="btnLeft">← 向左 (A)</button>
        <button class="btn" id="btnRight">向右 (D) →</button>
        <button class="btn on" id="btnAuto">自动来回跑：开</button>
        <button class="btn" id="btnScale">缩放 ×2 / ×3 / ×4</button>
      </div>
    </div>
    <aside class="panel">
      <h2 style="margin-top:0">目检对照项</h2>
      <div id="spritePanel"></div>
      <h3>说明</h3>
      <div class="note" style="margin-top:0">朝右素材，向左时只镜像 <code>img</code> 本身（<code>scaleX(-1)</code>），不镜像整个场景——对应 DF-04「不镜像 UI/文字」的同一纪律。</div>
    </aside>
  </div>
</section>

<!-- ④ 图鉴 -->
<section id="codex">
  <h2>72 张卡图鉴 · 类别 / 稀有度 / 搜索 / 详情</h2>
  <div class="note">数据直接来自冻结卡库 <code>docs/buff-card-library.json</code>；权重、概率、层数曲线均标 <b>PROPOSAL / 待实测</b>，不是已验证的平衡结论。</div>
  <div class="filters" id="codexFilters"></div>
  <div class="note" id="codexCount"></div>
  <div class="codex-grid" id="codexGrid"></div>
</section>

<!-- ⑤ 看板 -->
<section id="status">
  <h2>项目进度与自检看板 · 具体到哪一步了</h2>
  <div class="cards4" id="metricCards"></div>
  <div class="grid2">
    <div>
      <h3>浏览器内实跑自检（本页加载时计算）</h3>
      <div id="browserChecks" class="panel"></div>
      <h3>轮次时间线</h3>
      <div class="panel" id="timeline"></div>
    </div>
    <div>
      <h3>待处置风险 / 边界</h3>
      <div class="panel"><table id="riskTable"></table></div>
      <h3>导入 Godot 前的检查清单</h3>
      <div class="panel" id="checklist"></div>
    </div>
  </div>
  <div class="warn" style="margin-top:16px">网页是<b>验证层</b>，不是游戏本体：① 的横版战斗是<b>规则原型</b>（PROPOSAL 数值 / Boss 占位素材），没有存档、没有音频、没有 Godot 渲染。所有数值仍标「待实测」；Godot 工程（<code>project.godot</code>）仍是正式载体，主场景与 <code>MinimalRun.tscn</code> 未改。</div>
</section>

<footer>生成时间 <span id="genAt"></span> · 规则实现 <code>tools/card_rules.js</code> + <code>tools/battle_sim.js</code> + <code>tools/card_effects.js</code> · 数据源 <code>docs/buff-card-library.json</code> / <code>docs/01-策划案.md</code> · 单文件自包含，无网络请求</footer>
</div>

<div id="codexDetail"></div>

<script>__RULES_JS__
__BATTLE_JS__
__EFFECTS_JS__</script>
<script>
"use strict";
const LIB = __LIB_JSON__;
const IMG = __IMG_JSON__;
const META = __META_JSON__;

/* ---------------- 第 33 轮：UI 设计稿对照层（按视图联动） ---------------- */
/* 9 张 16:9 归一底板，key 与 assets/ui/reference/ui_reference_manifest.json
   里 kind=panel16x9 的 stem 一一对应；顺序沿用 docs/19 的 ⓪~⑧ 界面编号。
   声明放在脚本前部，避免 renderStatus() 调 browserSelfcheck() 时踩 TDZ。 */
const UI_SKINS = [
  ['ui_00-anchor_panel', '⓪ 风格锚点板 · 色板 / 纹样 / 边框'],
  ['ui_01-mainmenu_panel', '① 主菜单'],
  ['ui_02-towerhud_panel', '② 战斗 HUD'],
  ['ui_03-draft_panel', '③ 层间三选一'],
  ['ui_04-result_panel', '④ 结算'],
  ['ui_05-pause_panel', '⑤ 暂停'],
  ['ui_06-affix_panel', '⑥ 词缀自选'],
  ['ui_07-codex_panel', '⑦ 图鉴'],
  ['ui_08-icons_panel', '⑧ 图标系统样式表'],
];
/* 六视图 -> 对应设计稿；04/05/06 三张暂无独立视图，只能下拉查看。 */
const SKIN_BY_TAB = {
  menu: 'ui_01-mainmenu_panel',
  battle: 'ui_02-towerhud_panel',
  draft: 'ui_03-draft_panel',
  sprite: 'ui_00-anchor_panel',
  codex: 'ui_07-codex_panel',
  status: 'ui_08-icons_panel',
};
let uiSkinOn = !/[?&]ui=off/.test(location.search);
let uiSkinKey = UI_SKINS[0][0];

function setUiSkin(on) {
  uiSkinOn = !!on;
  const bar = $('uiSkinBar');
  if (bar) bar.classList.toggle('off', !uiSkinOn);
  const btn = $('uiSkinToggle');
  if (btn) btn.textContent = uiSkinOn ? '对照：开（点此收起）' : '对照：关（点此展开）';
  applyUiSkin();
}
function applyUiSkin() {
  if (!uiSkinOn) return;
  const sel = $('uiSkinSelect');
  if (sel) sel.value = uiSkinKey;
  const img = $('uiSkinImg');
  if (img) img.src = IMG[uiSkinKey] || '';
  const hint = $('uiSkinHint');
  if (hint) {
    const hit = UI_SKINS.find(s => s[0] === uiSkinKey);
    const linked = SKIN_BY_TAB[currentTab] === uiSkinKey;
    hint.textContent = '当前：' + (hit ? hit[1] : uiSkinKey) +
      (linked ? ' · 随视图自动联动' : ' · 手动选择（切视图恢复联动）');
  }
}
function applyUiSkinForTab(tab) {
  uiSkinKey = SKIN_BY_TAB[tab] || UI_SKINS[0][0];
  applyUiSkin();
}

const R = window.CardRules;
const B = window.BattleSim;
const E = window.CardEffects;
let activeFx = null;   // 本局已选卡 → 战斗效果集（每次开局按 pickedLog 重编译）
const byId = Object.create(null);
for (const c of LIB.cards) byId[c.id] = c;
const catMap = Object.create(null), rarMap = Object.create(null);
for (const c of LIB.categories) catMap[c.key] = c;
for (const c of LIB.rarities) rarMap[c.key] = c;
const RAR_ORDER = LIB.rarities.map(r => r.key);
const BOSS = R.BOSS_HP_REFERENCE;

function $(id) { return document.getElementById(id); }
function esc(s) { return String(s).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }
function kv(k, v, cls) { return '<div class="kv"><span>' + esc(k) + '</span><span class="' + (cls||'') + '">' + v + '</span></div>'; }
/* 卡面描述按真实像素容量截断。注意：docs/12 §2 写「最多 3 行 × 每行 ≤14 汉字（10px）」，
   但 96px 卡面 / 86px 文本区放不下 14 个 10px 汉字（需 140px），规格内部不自洽。
   网页验证层按 8 字/行 × 3 行截断，全文在图鉴详情可见；该矛盾记为待 4× 实机复核。 */
function wrapText(s, perLine, maxLines) {
  const chars = Array.from(String(s));
  const lines = [];
  for (let i = 0; i < chars.length && lines.length < maxLines; i += perLine) {
    lines.push(chars.slice(i, i + perLine).join(''));
  }
  if (chars.length > perLine * maxLines) {
    lines[maxLines - 1] = Array.from(lines[maxLines - 1]).slice(0, perLine - 1).join('') + '…';
  }
  return lines.join('\n');
}

/* ---------------- Tab 切换 ---------------- */
let currentTab = 'menu';
document.querySelectorAll('nav button').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('nav button').forEach(x => x.classList.remove('active'));
  document.querySelectorAll('section').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  currentTab = b.dataset.tab;
  $(currentTab).classList.add('active');
  applyUiSkinForTab(currentTab);   // 第 33 轮：设计稿随视图联动
  fitStage();
}));
function switchTab(id) {
  const b = document.querySelector('nav button[data-tab="' + id + '"]');
  if (b) b.click();
}

/* ---------------- 画布整数倍缩放（4 个 480×270 逻辑舞台） ---------------- */
let scaleFactor = 2;
function fitStage() {
  const pairs = [
    ['stageWrap', 'stage'], ['spriteWrap', 'spriteStage'],
    ['battleWrap', 'battleStage'], ['menuWrap', 'menuScreen'],
  ];
  for (const [wid, nid] of pairs) {
    const w = $(wid), n = $(nid);
    if (!w || !n) continue;
    const avail = w.parentElement ? w.parentElement.clientWidth : 480;
    let s = Math.max(1, Math.min(scaleFactor, Math.floor(avail / 480)));
    if (s < 1) s = 1;
    n.style.transform = 'scale(' + s + ')';
    w.style.width = (480 * s) + 'px';
    w.style.height = (270 * s) + 'px';
  }
}
window.addEventListener('resize', fitStage);

/* ================= ⓪ 主菜单（01 §11 MainMenu 四职责） ================= */
const MENU_PAGES = {
  start: {
    title: '开始入塔',
    html: kv('入口', 'TowerRun / 横版战斗') + kv('目标', '9 层 · 第 9 层塔主 4400 HP') +
      kv('本页状态', '<b class="gold">规则原型可玩</b>') + kv('素材', '已产 91 帧中的主角 / 4 怪 / 4 VFX') +
      '<div class="note" style="margin-top:10px">点左侧「开始入塔」进入 ① 横版战斗：A/D 移动、J/K/L/I 放技能、Space 闪避。清层后可去 ② 选一张卡，回来伤害数字会随共享池变化。</div>',
  },
  realm: {
    title: '境界总览 · 9 境 / 4 段色',
    html: kv('realm_ratio', '1.00 → 1.60（等距线性，Q11 已压缩）') +
      kv('作用', '只提升上限与解锁，不直接加局内伤害基数（M2）') +
      kv('色阶', '9 境压成 4 段色 + 1–9 道刻痕（DF-14）') +
      '<div class="note" style="margin-top:10px"><span class="realm-pips"><i></i><i style="background:#5FA8A0"></i><i style="background:#8A6FC4"></i><i style="background:#D9A441"></i></span> 本页只演示职责与信息层级，<b>不是可编辑设计稿</b>（Q17 未拍板）。</div>',
  },
  legacy: {
    title: '传承灵韵栏 · 6 条',
    html: kv('上限', '6 条，超出按「最旧优先」替换（M3）') +
      kv('产出', '每局结算从本局装备抽 1 条固化；败了也带走一条') +
      kv('塔内口径', '数值型按 50% 计入 extra_pool；机制型按 50% 效果强度') +
      '<pre style="white-space:pre-wrap;font-size:10px;color:#9BD4CC;margin:8px 0">legacy_jianhen / fuyin / danxi\ntiegu / jiying / lingquan</pre>' +
      '<div class="note" style="margin-top:6px">按 09 §3 定稿；本页<b>没有存档</b>，仅展示栏目职责。</div>',
  },
  settings: {
    title: '设置 · 网页验证层说明',
    html: kv('渲染', 'CSS image-rendering: pixelated（模拟 Nearest）') +
      kv('字体', '系统预览字体，R9 授权未结案') +
      kv('音频', '<b class="bad">无</b>（网页不实现 01 §10 音频）') +
      kv('随机源', 'xorshift32 + FNV-1a（与 Godot 同口径）') +
      '<div class="warn" style="margin-top:10px">这里是<b>占位</b>：正式设置项（音量 / 键位 / 画质）属于 6 界面设计稿范围，等 Q17 拍板后才有定稿；本页不假装已实现。</div>',
  },
};
function renderMenuPage(key) {
  const p = MENU_PAGES[key] || MENU_PAGES.start;
  $('menuPanelTitle').textContent = p.title;
  $('menuPanel').innerHTML = p.html;
  document.querySelectorAll('.menu-btns button').forEach(b => b.classList.toggle('on', b.dataset.menu === key));
}
document.querySelectorAll('.menu-btns button').forEach(b =>
  b.addEventListener('click', () => renderMenuPage(b.dataset.menu)));
// 主菜单立绘：主角 idle 3 帧 @~5fps（素材只出朝右一套，这里不镜像）
let menuFrame = 0;
$('menuHero').src = IMG.char_player_idle_r_00 || '';
setInterval(() => {
  if (currentTab !== 'menu') return;
  menuFrame = (menuFrame + 1) % 3;
  $('menuHero').src = IMG['char_player_idle_r_0' + menuFrame] || '';
}, 200);

/* ================= ① 横版战斗 ================= */
let battle = null, battleRunning = false, battleAuto = false, battlePaused = false;
let linkedDraft = false, battleLogLines = [];
let vfxNodes = [], floatNodes = [], enemyNodes = Object.create(null);
let edgeAlpha = 0, shakeMs = 0, playerHitMs = 0, battleLastTs = 0;
const held = { axis: 0, skills: [false, false, false, false], dodge: false };
const ANIM_FRAMES = { idle: 3, run: 4, cast: 4, atk: 4, hit: 1, death: 3 };
const ANIM_FPS = { idle: 6, run: 8, cast: 10, atk: 8, hit: 8, death: 8 };

/* ===== 第 32 轮：gpt-image2 回稿转录素材模式 =====
   默认开启；?art=placeholder 或右上按钮切回第 20 轮的 CSS 山影 + 剑魂帧占位。
   只换像素源：STAGES / SKILLS / PROPOSAL / 伤害公式 / 状态机一律不动。 */
let refArt = !/[?&]art=placeholder/.test(location.search);
let lastBgStage = -1;
const BG_BY_TYPE = { '教学': 'normal', '常规': 'normal', '喘息': 'rest',
                     '精英': 'high', '挑战': 'boss', '塔主 Boss': 'boss' };

function setArtMode(on) {
  refArt = !!on;
  const stage = $('battleStage');
  if (stage) stage.classList.toggle('art-ref', refArt);
  const btn = $('artToggle');
  if (btn) btn.textContent = refArt ? '素材：原稿转录（点此切旧占位）'
                                    : '素材：旧占位（点此切原稿）';
  applyStageBg();
}

function applyStageBg() {
  const el = $('bBgArt');
  if (!el) return;
  if (!refArt) { el.removeAttribute('src'); return; }
  const snap = battle ? battle.snapshot() : null;
  const type = snap && snap.stage ? (B.STAGES[snap.stage - 1] || {}).type : '常规';
  el.src = IMG['bg_' + (BG_BY_TYPE[type] || 'normal')] || IMG.bg_normal || '';
}

/* Boss 帧表由转录产物实际文件数决定（判官 18 / 塔主 24），不写死帧数；
   当前动画该 Boss 没有对应帧时回落到 idle，避免 src 为空。 */
function bossFrameKey(id, anim, t) {
  function count(a) {
    let n = 0;
    while (n < 24 && IMG[id + '_' + a + '_r_0' + n]) n++;
    return n;
  }
  let n = count(anim);
  if (!n) { anim = 'idle'; n = count(anim); }
  if (!n) return '';
  const i = n === 1 ? 0 : Math.floor(t * (ANIM_FPS[anim] || 6)) % n;
  return id + '_' + anim + '_r_0' + i;
}

function blog(line) {
  battleLogLines.push(line);
  if (battleLogLines.length > 70) battleLogLines.shift();
  $('battleLog').textContent = battleLogLines.join('\n');
  $('battleLog').scrollTop = $('battleLog').scrollHeight;
}
function frameKey(prefix, anim, t) {
  const n = ANIM_FRAMES[anim] || 1;
  const i = n === 1 ? 0 : Math.floor(t * (ANIM_FPS[anim] || 8)) % n;
  return prefix + '_' + anim + '_r_0' + i;
}
function buildSlots() {
  $('bSlots').innerHTML = B.SKILLS.map((s, i) =>
    '<div class="bslot" data-i="' + i + '"><span class="key">' + s.key + '</span>' +
    '<img src="' + (IMG[s.vfx + '_00'] || '') + '" alt="' + esc(s.name) + '" title="' + esc(s.name) + '">' +
    '<div class="cdmask hide" id="cd' + i + '"></div></div>').join('');
}
function clearBattleNodes() {
  vfxNodes = []; floatNodes = []; enemyNodes = Object.create(null);
  $('bVfx').innerHTML = ''; $('bFloats').innerHTML = ''; $('bActors').innerHTML = '';
  const p = document.createElement('img');
  p.id = 'bPlayer'; p.className = 'bsprite';
  $('bActors').appendChild(p);
  edgeAlpha = 0; shakeMs = 0; playerHitMs = 0;
}
function startBattle(n, opt) {
  const o = opt || {};
  const deckState = deck ? deck.offenseState() : {};
  battle = new B.BattleSim({ runId: runId || 'web-demo', stage: n, deckState: deckState });
  // 第 21 轮：本局已选卡（数值 + 机制）统一编译后接进战斗；pickedLog 是唯一真源，
  // 重开一局自动清空，不会残留上一局的卡。空效果时与第 20 轮行为一致。
  activeFx = E.compileCardEffects(LIB, pickedLog.map(p => p.id));
  battle.applyCardEffects(activeFx);
  if (o.carryHp !== undefined) battle.hp = Math.min(o.carryHp, battle.maxHp);
  battleRunning = !!o.auto; battleAuto = !!o.auto; battlePaused = false;
  battleLogLines = [];
  clearBattleNodes(); buildSlots(); renderFxPanel();
  $('battleOverlay').style.display = 'none';
  $('btnBattleAuto').classList.toggle('on', battleAuto);
  blog('── 第 ' + battle.stage + ' 层 / ' + battle.stageDef.type + ' · HP_total ' + battle.stageDef.hp +
       ' · 共享池 ' + battle.pool + ' ──');
  blog('  🎴 本局已选 ' + activeFx.counts.cards + ' 张 / 战斗生效 ' + activeFx.counts.battle +
       ' 条 · 归抽卡层 ' + activeFx.counts.deck + ' 条 · 未映射 ' + activeFx.counts.none + ' 条' +
       '（详见右侧「本局生效卡牌效果」）');
  for (const e of battle.enemies) {
    // 第 32 轮：snapshot 的 placeholder 是 battle_sim.js 的旧占位标记（冻结规则不改），
    // 但页面实际像素源由 refArt 决定；日志必须跟画面一致，不能一边用真帧一边写「未产」。
    const bossNote = e.placeholder
      ? (refArt ? ' · Boss 用 gpt-image2 转录真帧（assets/boss/）'
                : ' · ⚠️ 旧占位模式，用 ' + e.sprite + ' 放大')
      : '';
    blog('  出场 ' + e.name + ' (' + e.type + ') HP ' + e.hp + bossNote);
  }
  if (!battleRunning) blog('  静态待机中：点「▶ 自动演示战斗」或直接按 A/D、J/K/L/I 开始');
}
let floatSeq = 0;
function addFloat(text, x, y, cls) {
  // 确定性错位：同帧多次命中时飘字不叠成一团（不用 Math.random，保证画面可复现）
  const n = floatSeq++;
  const jx = ((n * 13) % 7 - 3) * 10;
  const jy = ((n * 7) % 5 - 2) * 8;
  // 同屏最多 5 个飘字：避免连续命中 / 冻结截图时堆成一团
  while (floatNodes.length >= 5) { const old = floatNodes.shift(); old.el.remove(); }
  const el = document.createElement('div');
  el.className = 'float ' + (cls || '');
  el.textContent = text;
  el.style.left = Math.round(x + jx) + 'px'; el.style.top = Math.round(y + jy) + 'px';
  $('bFloats').appendChild(el);
  floatNodes.push({ el: el, x: x + jx, y: y + jy, life: 0.85 });
}
function addVfx(v) {
  const el = document.createElement('img');
  el.className = 'bvfx';
  $('bVfx').appendChild(el);
  vfxNodes.push({ el: el, vfx: v.vfx, x: v.x, y: v.y, facing: v.facing,
                  life: v.ttl || 0.42, max: v.ttl || 0.42 });
}
function onStageCleared(e) {
  blog('✅ 第 ' + e.stage + ' 层清层 · 命中 ' + battle.hits + ' / 累计伤害 ' + e.damage);
  battleRunning = false; battleAuto = false;
  const ov = $('battleOverlay');
  ov.innerHTML = '<h3>' + (e.stage >= 9 ? '🏆 通关 · 天梯之主已败' : '第 ' + e.stage + ' 层已清') + '</h3>' +
    '<div>本层命中 <b>' + battle.hits + '</b> 次 · 累计伤害 <b>' + e.damage + '</b> · 承受 <b>' +
    battle.damageTaken + '</b> · 用时 ' + battle.time.toFixed(1) + ' s</div>' +
    '<div style="margin-top:6px;color:#8A8268">共享池（来自已选卡）' + battle.pool + ' / 600；下一层伤害会按 01 §8.1 公式实时变化。</div>' +
    (e.stage >= 9 ? '' : '<div class="obtns"><button class="primary" data-act="draft">🎴 去选一张卡（联动）</button>' +
      '<button data-act="next">直接进第 ' + (e.stage + 1) + ' 层</button>' +
      '<button data-act="replay">重打本层</button></div>');
  ov.style.display = 'block';
  const act = (name, fn) => { const b = ov.querySelector('[data-act="' + name + '"]'); if (b) b.addEventListener('click', fn); };
  act('draft', () => prepareLinkedDraft(e.stage));
  act('next', () => { const hp = battle.hp; startBattle(e.stage + 1, { auto: true, carryHp: hp }); switchTab('battle'); });
  act('replay', () => startBattle(e.stage, { auto: true }));
  // ?autolink=1：无头浏览器自动跑「清层 → 选一张卡 → 回下一层战斗」闭环，供机器验证联动
  if (window.__autoLink && e.stage < 9) {
    prepareLinkedDraft(e.stage);
    setTimeout(() => {
      if (currentTab === 'draft' && !finished && offered.length > 0) {
        // 演示时优先选「有战斗层效果」的卡（第 21 轮起含机制卡），让「选卡 → 战斗变化」肉眼可见；
        // 这只是演示选法，抽卡规则与候选序列一个字节未改。
        const fxIdx = offered.findIndex(id => E.compileCardEffects(LIB, [id]).counts.battle > 0);
        const nIdx = fxIdx >= 0 ? fxIdx : offered.findIndex(id => {
          const p = byId[id].params || {};
          return p.extra_pool || p.base_damage || p.pool || p.combo_multiplier;
        });
        if (nIdx >= 0) selectIndex(nIdx);
        confirmPick();
      }
    }, 120);
  }
}
function handleBattleEvents(events) {
  for (const e of events) {
    if (e.type === 'vfx_requested') addVfx(e);
    else if (e.type === 'damage_applied') {
      const seg = e.segments ? ' 第' + e.segment + '/' + e.segments + '段' : '';
      addFloat((e.crit ? '✦ ' : '') + e.damage + (e.segments ? '·' + e.segment : ''),
               e.x, e.y, e.crit ? 'crit' : '');
      blog('  ' + (e.skill || '') + ' → ' + e.target + ' ' + e.damage + (e.crit ? ' 暴击' : '') +
           seg + ' [pool=' + e.pool + ' combo=' + e.combo + ']');
    } else if (e.type === 'card_effect') blog('  🎴 ' + (e.text || e.kind));
    else if (e.type === 'shield_absorb') blog('  🛡 护盾吸收 ' + e.amount + '（护盾剩余 ' + e.shieldLeft + '）');
    else if (e.type === 'revive') blog('  ✨ 复活：HP ' + e.hp);
    else if (e.type === 'player_hurt') {
      if (e.damage > 0) {
        addFloat('-' + e.damage, e.x, e.y, 'hurt'); edgeAlpha = 1; playerHitMs = 220;
        blog('  ⚠ 受伤 -' + e.damage + '（HP ' + battle.hp + '）');
      } else {
        blog('  🛡 本次伤害被护盾完全吸收（HP 未损失）');
      }
    } else if (e.type === 'heal') {
      addFloat('+' + e.amount, e.x, e.y, 'heal'); blog('  回春诀 +' + e.amount + ' HP');
    } else if (e.type === 'shake') shakeMs = 130;
    else if (e.type === 'enemy_death') blog('  ✕ ' + (e.name || e.target) + ' 倒下');
    else if (e.type === 'boss_phase') blog('  ◆ Boss 进入第 ' + e.phase + ' 阶段（3 段色，轮廓不变）');
    else if (e.type === 'stage_cleared') onStageCleared(e);
    else if (e.type === 'run_ended') blog((e.win ? '🏆 通关' : '☠ 本局结束') + ' · 第 ' + e.stage + ' 层');
    else if (e.type === 'dodge_ignore') blog('  ◇ 闪避无敌帧，忽略本次伤害');
    else if (e.type === 'cast_unavailable') blog('  · 技能不可用：' + e.reason);
  }
}
/* 第 21 轮：把「本局已选卡 → 战斗里到底改变了什么」逐条列出来。
   生效 / 归抽卡层 / 未映射三层如实分列，不把估算写成结论。 */
function renderFxPanel() {
  const el = $('fxPanel'); if (!el || !E) return;
  const fx = activeFx || E.compileCardEffects(LIB, []);
  if (!fx.counts.cards) {
    el.innerHTML = '<div class="fxempty">本局还没选卡。清层 → ② 选一张 → 回 ①，这里会逐条列出它改变了什么。</div>';
    return;
  }
  let h = '<div class="fxhead">已选 ' + fx.counts.cards + ' 张 · <span class="fx-b">战斗生效 ' +
          fx.counts.battle + '</span> / <span class="fx-n">归抽卡层 ' + fx.counts.deck +
          ' · 未映射 ' + fx.counts.none + '</span></div>';
  for (const c of fx.cards) {
    const b = c.effects.filter(e => e.layer === 'battle');
    const rest = c.effects.length - b.length;
    h += '<div class="fxcard"><b>' + esc(c.name) + '</b>' + (c.stacks > 1 ? ' ×' + c.stacks : '') +
         ' <span class="fx-n">[' + esc(c.type) + ']</span><br>';
    h += b.length
      ? b.map(e => '<span class="fx-b">▸ ' + esc(e.label) + '</span> <span class="fx-n">' + esc(e.detail) + '</span>').join('<br>')
      : '<span class="fx-n">（本卡无战斗层效果）</span>';
    if (rest > 0) h += '<br><span class="fx-n">另有 ' + rest + ' 条归抽卡层 / 未映射（见下方）</span>';
    h += '</div>';
  }
  if (fx.notes.length) {
    h += '<div class="fxcard fx-w">⚠️ 口径提示：<br>' +
         fx.notes.map(n => esc(n.name + '：' + n.note)).join('<br>') + '</div>';
  }
  if (fx.unboundKeys.length) {
    h += '<div class="fxcard fx-n">未映射键 ' + fx.unboundKeys.length + ' 类（不伪造）：<br>' +
         fx.unboundKeys.map(k => esc(k.key) + ' — ' + esc(k.reason)).join('<br>') + '</div>';
  }
  el.innerHTML = h;
}
function bar(label, val, max, color) {
  const pct = Math.max(0, Math.min(100, val / max * 100));
  return '<div class="barrow"><span class="lab">' + label + '</span><span class="track"><i style="width:' +
    pct + '%;background:' + color + '"></i></span><span class="num">' + Math.round(val) + '/' + max + '</span></div>';
}
function renderBattleUi(dt) {
  if (!battle) return;
  const s = battle.snapshot();
  if (s.stage !== lastBgStage) { lastBgStage = s.stage; applyStageBg(); }
  $('bHud').innerHTML = bar('血', s.hp, s.maxHp, '#C8453B') +
    bar('灵', s.spirit, B.PROPOSAL.playerMaxSpirit, '#5FA8A0') +
    bar('体', s.stamina, B.PROPOSAL.playerMaxStamina, '#D9A441');
  const def = B.STAGES[s.stage - 1];
  $('bStage').innerHTML = '第 ' + s.stage + ' / 9 层 · ' + def.type +
    '<br><span class="br">HP_total ' + def.hp + ' · T(n) ' + def.t + 's · D(n) ' + def.d.toFixed(2) +
    ' · 境界 1/9</span> <span class="realm-pips"><i></i><i style="background:#5FA8A0;opacity:.35"></i>' +
    '<i style="background:#8A6FC4;opacity:.25"></i><i style="background:#D9A441;opacity:.2"></i></span>';
  for (let i = 0; i < B.SKILLS.length; i++) {
    const m = $('cd' + i);
    if (!m) continue;
    const cd = s.cd[i];
    m.classList.toggle('hide', cd <= 0.001);
    m.textContent = cd > 0.001 ? cd.toFixed(1) : '';
  }
  // 主角帧
  let panim = 'idle';
  if (s.state === 'DEAD') panim = 'death';
  else if (playerHitMs > 0) panim = 'hit';
  else if (s.state === 'CASTING') panim = 'cast';
  else if (s.state === 'DODGING' || held.axis !== 0) panim = 'run';
  const pEl = $('bPlayer');
  if (pEl) {
    const key = frameKey('char_player', panim, (panim === 'run' || panim === 'idle') ? s.time : s.time);
    pEl.src = IMG[key] || IMG.char_player_idle_r_00 || '';
    pEl.style.left = (s.x - 32) + 'px';
    pEl.style.top = (B.GROUND_Y - 64) + 'px';
    pEl.style.transform = s.facing === 1 ? 'none' : 'scaleX(-1)';
  }
  // 敌人帧池
  for (const e of s.enemies) {
    let node = enemyNodes[e.id];
    if (!node) {
      const img = document.createElement('img');
      img.className = 'benemy'; $('bActors').appendChild(img);
      const hp = document.createElement('div');
      hp.className = 'benemyHp'; hp.innerHTML = '<i></i>'; $('bActors').appendChild(hp);
      node = enemyNodes[e.id] = { img: img, hp: hp };
    }
    // 第 32 轮：原稿 Boss 帧是 Q21 冻结的 128×128，1:1 显示才不丢甲胄纹样；
    // 旧占位模式仍沿用第 20 轮的 96px 放大，保证对照可复现。
    const size = e.boss ? (refArt ? 128 : 96) : 64;
    let anim = e.anim;
    if (e.dead) anim = 'death';
    // 第 32 轮：原稿模式下 Boss 用 assets/boss/ 的真帧（e.type 是 boss_judge /
    // boss_tower_lord，e.sprite 是第 20 轮的 mob_jian_hun 占位映射）。
    const useRefBoss = refArt && e.boss && e.type && IMG[e.type + '_idle_r_00'];
    const key = useRefBoss
      ? bossFrameKey(e.type, anim, e.dead ? Math.min(e.animTime, 0.36) : e.animTime)
      : frameKey(e.sprite, anim, e.dead ? Math.min(e.animTime, 0.36) : e.animTime);
    node.img.src = IMG[key] ||
      (useRefBoss ? IMG[e.type + '_idle_r_00'] : IMG[e.sprite + '_idle_r_00']) || '';
    node.img.style.width = size + 'px'; node.img.style.height = size + 'px';
    node.img.style.left = (e.x - size / 2) + 'px';
    node.img.style.top = (B.GROUND_Y - size) + 'px';
    const faceLeft = e.x > s.x;
    node.img.style.transform = 'scaleX(' + (faceLeft ? -1 : 1) + ')';
    node.img.classList.toggle('flash', e.flash > 0.001);
    if (e.boss) node.img.style.filter = e.phase === 3 ? 'hue-rotate(-30deg) brightness(1.2)' :
      (e.phase === 2 ? 'hue-rotate(35deg)' : 'none');
    node.hp.style.left = (e.x - 22) + 'px';
    node.hp.style.top = (B.GROUND_Y - size - 7) + 'px';
    node.hp.style.width = '44px';
    node.hp.firstChild.style.width = Math.max(0, e.hp / e.maxHp * 100) + '%';
    node.hp.style.display = e.boss ? 'none' : 'block';
  }
  const boss = s.enemies.find(e => e.boss && !e.dead);
  const bb = $('bossBar');
  bb.style.display = boss ? 'block' : 'none';
  if (boss) bb.firstChild.style.width = Math.max(0, boss.hp / boss.maxHp * 100) + '%';
  // 特效 / 飘字 / 反馈
  for (const v of vfxNodes) {
    const elapsed = v.max - v.life;
    const i = Math.min(3, Math.floor(elapsed * 12));
    v.el.src = IMG[v.vfx + '_0' + i] || '';
    v.el.style.left = (v.x - 32) + 'px'; v.el.style.top = (v.y - 32) + 'px';
    v.el.style.transform = 'scaleX(' + (v.facing === 1 ? 1 : -1) + ')';
  }
  for (const f of floatNodes) {
    f.el.style.top = Math.round(f.y) + 'px';
    f.el.style.opacity = Math.max(0, Math.min(1, f.life / 0.5));
  }
  edgeAlpha = Math.max(0, edgeAlpha - dt * 3.2);
  $('edgeTint').style.opacity = edgeAlpha.toFixed(2);
  playerHitMs = Math.max(0, playerHitMs - dt * 1000);
  shakeMs = Math.max(0, shakeMs - dt * 1000);
  // 镜头微震用确定性抖动（不引入 Math.random，保持「同输入同画面」的可复现性）
  const shakePx = (Math.floor(shakeMs / 22) % 3) - 1;
  $('battleWorld').style.transform = shakeMs > 0 ? 'translate(' + shakePx + 'px,0)' : 'none';
  // 右侧面板
  let h = kv('当前层', s.stage + ' / 9 · ' + def.type) + kv('状态', s.state) +
    kv('共享池 extra_pool', '<b>' + s.pool + ' / 600</b>', 'gold') +
    kv('combo_mult', s.combo + ' / 2.5') + kv('上次伤害', s.lastDamage) +
    kv('本局累计伤害', s.damageDealt) + kv('承受伤害', s.damageTaken) +
    kv('命中 / 击杀', s.hits + ' / ' + s.kills) +
    kv('护盾 / HP 上限', s.shield + ' / ' + s.maxHp) +
    kv('灵力上限 / 命中分段', s.maxSpirit + ' / ' + s.cardEffects.segments) +
    kv('复活机会 / 已生效卡', s.cardEffects.reviveLeft + ' / ' + s.cardEffects.bound) +
    kv('五上界峰值', '<b>3996 / 4400</b>', 'ok') +
    kv('tick / 时间', s.tick + ' / ' + s.time + ' s') +
    kv('规则实现', 'tools/battle_sim.js') +
    kv('Node 断言', META.battle.passed + '/' + META.battle.total + ' (' + META.battle.verdict + ')');
  // 用纯函数展示「共享池 → 伤害」的因果，不改 sim 状态、不伪造数值
  const cmp = p => B.damageFormula(60, 1.0, p, s.combo, 1.0, 0, null);
  h += kv('同技能伤害（池 0 / 当前 / 600）',
          '<span style="white-space:nowrap">' + cmp(0) + ' / <b>' + cmp(s.pool) +
          '</b> / ' + cmp(600) + '</span>', 'gold');
  $('battlePanel').innerHTML = h;
}
function autoInput(s) {
  const alive = s.enemies.filter(e => !e.dead);
  const inp = { axis: 0, skills: [false, false, false, false], dodge: false };
  if (!alive.length) return inp;
  const t = alive[0], dist = t.x - s.x;
  if (Math.abs(dist) > 76) inp.axis = dist > 0 ? 1 : -1;
  // 攻击优先；只有「没有可释放的攻击技能」且血量偏低时才治疗，
  // 否则会陷入「治疗→挨打→再治疗」而永远不出手的死循环（第 20 轮实测）。
  let attacked = false;
  for (let i = 2; i >= 0; i--) {
    const sk = B.SKILLS[i];
    if (s.cd[i] <= 0 && s.spirit >= sk.spirit && Math.abs(dist) <= sk.reach) {
      inp.skills[i] = true; attacked = true; break;
    }
  }
  if (!attacked && s.hp < s.maxHp * 0.4 && s.cd[3] <= 0 && s.spirit >= B.SKILLS[3].spirit) {
    inp.skills[3] = true;
  }
  return inp;
}
/* 自动演示的规则推进交给定时器：无头浏览器虚拟时间下 rAF 只跑一帧，
   setTimeout/setInterval 仍可靠触发（第 19 轮自动演示已验证）。rAF 只负责渲染，
   手动操作仍走 rAF，两条路径互斥（battleAuto 为唯一开关），不会重复推进。 */
function autoPlayStep() {
  if (!battle || !battleRunning || !battleAuto || battlePaused || battle.finished) return;
  // ?freeze=N：跑到指定 tick 就冻结，供无头浏览器稳定截取「战斗中」画面（不影响正常玩法）
  if (window.__freezeTick > 0 && battle.tickCount >= window.__freezeTick) return;
  handleBattleEvents(battle.step(B.TICK * 3, autoInput(battle.snapshot())));
}
function renderBattle(ts) {
  const dt = battleLastTs ? Math.min(0.05, (ts - battleLastTs) / 1000) : 0;
  battleLastTs = ts;
  if (battle) {
    if (battleRunning && !battlePaused && !battle.finished && !battleAuto) {
      const inp = { axis: held.axis, skills: held.skills.slice(), dodge: held.dodge };
      handleBattleEvents(battle.step(dt, inp));
      held.skills = [false, false, false, false]; held.dodge = false;
    }
    const frozen = window.__freezeTick > 0 && battle.tickCount >= window.__freezeTick;
    if (!frozen) {
      for (const v of vfxNodes) v.life -= dt;
      for (const f of floatNodes) { f.life -= dt; f.y -= 30 * dt; }
    }
    vfxNodes = vfxNodes.filter(v => { if (v.life > 0) return true; v.el.remove(); return false; });
    floatNodes = floatNodes.filter(f => { if (f.life > 0) return true; f.el.remove(); return false; });
    renderBattleUi(dt);
  }
  requestAnimationFrame(renderBattle);
}
function toggleBattlePause() {
  battlePaused = !battlePaused;
  blog(battlePaused ? '⏸ 已暂停' : '▶ 继续');
  $('btnBattlePause').classList.toggle('on', battlePaused);
}
$('btnMenuStart').addEventListener('click', () => { startBattle(1, { auto: true }); switchTab('battle'); });
$('btnMenuBoss').addEventListener('click', () => { startBattle(9, { auto: true }); switchTab('battle'); });
$('btnBattleAuto').addEventListener('click', () => {
  if (!battle || battle.finished) { startBattle(battle ? battle.stage : 1, { auto: true }); return; }
  battleRunning = true; battleAuto = true;
  battlePaused = false;
  $('btnBattleAuto').classList.add('on');
  blog('▶ 自动演示战斗：AI 自动走位 + 按 CD 放技能，打到清层');
});
$('btnBattleReset').addEventListener('click', () => startBattle(battle ? battle.stage : 1, { auto: false }));
$('btnBattlePause').addEventListener('click', toggleBattlePause);
$('btnBattleBoss').addEventListener('click', () => { startBattle(9, { auto: true }); switchTab('battle'); });
$('btnBattleDraft').addEventListener('click', () => prepareLinkedDraft(battle ? battle.stage : 1));
function injectPool(amount) {
  if (!battle) return;
  const before = battle.pool;
  const after = Math.min(B.CAP_EXTRA_POOL, before + amount);
  battle.syncDeck({ extra_pool: after, offense_pool_used: 0,
                    combo_multiplier: battle.comboBonus });
  blog('🧪 演示注入：共享池 ' + before + ' → ' + battle.pool + ' / 600（人造输入，不是抽到的卡；' +
       '不改卡库 / 冻结数值，点「重置本层」即复原）→ 下一击飘字按 01 §8.1 变大');
}
$('btnPoolDemo').addEventListener('click', () => injectPool(150));

/* 第 21 轮：一键预置一组代表性机制卡，让用户不输 URL 也能看到「选卡 → 战斗变化」。
   ⚠️ 明确是演示注入：不经过 CardDeck 抽卡规则、不改候选 / 种子 / 共享池，
   只用于观察 card_effects.js → battle_sim.js 的效果链路，不得当作抽卡结果。 */
const FX_DEMO_IDS = ['card_poyun', 'card_huti', 'card_sheli', 'card_tiepi', 'card_qingling'];
function presetFxCards(ids) {
  const by = Object.create(null); for (const c of LIB.cards) by[c.id] = c;
  const valid = ids.filter(id => by[id]);
  pickedLog = valid.map((id, i) => ({ stage: i + 1, id: id, name: by[id].name,
                                      offered: [], preset: true }));
  const stageNow = battle ? battle.stage : 1;
  startBattle(stageNow, { auto: true });
  blog('🧪 演示注入 ' + valid.length + ' 张机制卡（' + valid.map(id => by[id].name).join('、') +
       '）· 不经过抽卡规则 / 共享池仍为 ' + battle.pool + ' · 只验证效果链路');
  log('🧪 演示预置卡 ' + valid.length + ' 张（非抽卡结果）：' + valid.map(id => by[id].name).join('、'));
  switchTab('battle');
}
$('btnFxDemo').addEventListener('click', () => presetFxCards(FX_DEMO_IDS));

/* 清层 → 三选一选卡 → 回到下一层战斗（让用户看到选卡真的改变战斗伤害） */
function prepareLinkedDraft(n) {
  linkedDraft = true;
  if (!deck || finished || deck.isSealed()) newRun('battle-linked-' + n);
  stage = Math.min(Math.max(n, 1), 8);
  finished = false;
  $('resultOverlay').style.display = 'none';
  log('── 层间选卡（来自战斗第 ' + n + ' 层清层）· 选完自动回到战斗 ──');
  refresh();
  switchTab('draft');
}
function syncBattleFromDeck() {
  const carryHp = battle ? battle.hp : B.PROPOSAL.playerMaxHp;
  const poolBefore = battle ? battle.pool : 0;
  const next = Math.min(stage, 9);
  startBattle(next, { auto: true, carryHp: carryHp });
  const poolAfter = battle.pool;
  const last = activeFx && activeFx.cards.length ? activeFx.cards[activeFx.cards.length - 1] : null;
  const b = last ? last.effects.filter(e => e.layer === 'battle') : [];
  blog('🎴 卡牌联动：共享池 ' + poolBefore + ' → ' + poolAfter + ' / 600 → 进第 ' + next + ' 层');
  blog('   ' + (last ? last.name : '—') + ' → 战斗生效 ' + b.length + ' 条' +
       (b.length ? '：' + b.map(e => e.label).join(' / ') : '（本卡归抽卡层 / 未映射，右侧面板逐条列明原因）'));
  switchTab('battle');
}

/* ================= ② 三选一 ================= */
let deck, runId = 'web-demo', runSeq = 0, stage = 1, selected = 0;
let offered = [], pickedLog = [], seen = new Set(), wuxiang = false, finished = false;
let draftLog = [];

function curContext() { return { realm: 9, affix: wuxiang ? ['affix_wuxiang'] : [] }; }

function log(line) { draftLog.push(line); if (draftLog.length > 60) draftLog.shift(); $('draftLog').textContent = draftLog.join('\n'); }

function newRun(id) {
  runId = id;
  deck = new R.CardDeck(LIB);
  deck.newRun(runId, curContext());
  stage = 1; selected = 0; finished = false;
  pickedLog = []; seen = new Set();
  $('resultOverlay').style.display = 'none';
  log('── 新局 ' + runId + ' / realm=9 / affix=' + JSON.stringify(curContext().affix) + ' ──');
  refresh();
}

function refresh() {
  if (finished) { renderResult(); return; }
  offered = deck.offer(stage);
  if (offered.length === 0 && deck.isSealed()) { finished = true; renderResult(); return; }
  if (stage > 8) { finished = true; renderResult(); return; }
  if (selected >= offered.length) selected = Math.max(0, offered.length - 1);
  for (const id of offered) seen.add(id);
  renderCards(); renderPanel();
  $('stageTitle').textContent = '第 ' + stage + ' 层 · 择一机缘';
  $('stageProgress').textContent = '已选 ' + pickedLog.length + '/8 · seed ' + deck.runSeed(stage);
  $('stageHint').textContent = '1/2/3 直选 · ←/→ 切换 · Enter 确认 · W 无相 · R 重开 · Esc 已选';
  $('confirmBtn').classList.toggle('ready', offered.length > 0);
  $('goldLine').classList.toggle('on', offered.length > 0);
}

function renderCards() {
  const nodes = document.querySelectorAll('#stage .card');
  const goldBase = $('goldBase');
  goldBase.classList.remove('on');
  nodes.forEach((el, i) => {
    el.classList.remove('show', 'selected', 'curse');
    if (i >= offered.length) return;
    const c = byId[offered[i]];
    el.classList.add('show');
    if (c.rarity === 'curse') el.classList.add('curse');
    if (i === selected) el.classList.add('selected');
    el.querySelector('.paper').style.background = c.rarity === 'curse' ? '#7A2420' : '#E8DFC8';
    el.querySelector('.frame').src = IMG['frame_' + c.rarity] || IMG.frame_common;
    el.querySelector('.sigil').src = IMG['sigil_' + c.cat] || IMG.sigil_dmg;
    el.querySelector('.catbar').style.background = (catMap[c.cat] || {}).color || '#4A5568';
    el.querySelector('.cname').textContent = c.name;
    el.querySelector('.cdesc').textContent = wrapText(c.text, 8, 3);
    el.querySelector('.cinfo').textContent = (rarMap[c.rarity] || {}).name + ' ×' + (c.stack || 1) + ' · ' + c.cat;
    const pips = el.querySelector('.pips'); pips.innerHTML = '';
    const n = RAR_ORDER.indexOf(c.rarity) + 1;
    for (let k = 0; k < n; k++) {
      const d = document.createElement('i');
      d.style.left = (k % 2) * 3 + 'px'; d.style.top = Math.floor(k / 2) * 3 + 'px';
      pips.appendChild(d);
    }
    el.querySelector('.unread').classList.toggle('on', !seen.has(c.id));
    if (i === selected) {
      goldBase.classList.add('on');
      goldBase.style.left = [80, 192, 304][i] + 'px';
    }
  });
  $('stageState').textContent = '峰值 ' + deck.peakDamage() + ' / ' + BOSS +
    ' · 守卫事件 ' + deck.clampEvents.length + ' · 违规 ' + deck.violations.length +
    ' · 候选 ' + offered.length + ' 张';
}

function renderPanel() {
  const peak = deck.peakDamage();
  const over = peak >= BOSS;
  const pct = Math.min(100, peak / BOSS * 100);
  let h = '';
  h += kv('局号 run_id', esc(runId));
  h += kv('当前层', stage + ' / 8');
  h += kv('确定性种子 seed', deck.runSeed(stage));
  h += kv('候选张数', offered.length + (offered.length === 2 ? '（无相压 2 选 1）' : ''));
  h += kv('无相词缀', wuxiang ? '开' : '关');
  h += kv('本局已选', pickedLog.length + ' / 8');
  h += kv('封牌', deck.isSealed() ? '是' : '否');
  h += kv('五上界峰值', '<b>' + peak + ' / ' + BOSS + '</b>', over ? 'bad' : 'ok');
  h += '<div class="bar"><i class="' + (over ? 'over' : '') + '" style="width:' + pct + '%"></i></div>';
  h += kv('守卫事件 / 违规', deck.clampEvents.length + ' / ' + deck.violations.length,
          deck.violations.length ? 'bad' : 'ok');
  h += kv('红线状态', deck.damageCeilingOk() ? 'PASS（未击穿）' : 'FAIL',
          deck.damageCeilingOk() ? 'ok' : 'bad');
  h += kv('规则实现', 'tools/card_rules.js');
  $('statePanel').innerHTML = h;
  $('pickedList').textContent = pickedLog.length
    ? pickedLog.map(p => 's' + p.stage + '  ' + p.name + '  [' + p.id + ']').join('\n')
    : '（尚未选卡）';
}

function selectIndex(i) {
  if (finished || i < 0 || i >= offered.length) return;
  selected = i; renderCards();
}

function confirmPick() {
  if (finished || offered.length === 0) return;
  const chosen = offered[selected];
  const ev = deck.pickEvent(stage, offered, chosen);
  const good = deck.pick(chosen, stage);
  pickedLog.push({ stage, id: chosen, name: byId[chosen].name, offered: offered.slice() });
  log('s' + stage + ' seed=' + ev.seed + ' 候选=[' + offered.join(', ') + '] → 选 ' + chosen +
      ' (' + byId[chosen].name + ') · 峰值 ' + deck.peakDamage() + (good ? '' : ' [pick FAILED]'));
  stage += 1;
  if (stage > 8 || deck.isSealed()) { finished = true; }
  refresh();
  // 来自战斗清层的联动选卡：同步共享池后自动回到下一层战斗
  if (linkedDraft) { linkedDraft = false; syncBattleFromDeck(); }
}

function renderResult() {
  document.querySelectorAll('#stage .card').forEach(e => e.classList.remove('show'));
  $('goldBase').classList.remove('on');
  $('stageTitle').textContent = deck.isSealed() ? '本局已封牌 · 传承结算' : '九重天梯 · 传承结算';
  $('stageProgress').textContent = '共 ' + pickedLog.length + ' 次选择';
  $('stageHint').textContent = '按 R 重开一局，或切到 ⑤ 看自检结果';
  $('confirmBtn').classList.remove('ready');
  const peak = deck.peakDamage();
  let h = '<h3>' + (deck.isSealed() ? '本局已封牌（card_sheli / card_wuxin）' : '8 层流程跑完') + '</h3>';
  h += '<div style="color:#E8DFC8">共 <b>' + pickedLog.length + '</b> 次选择 · 单局峰值 <b>' + peak +
       '</b> / Boss ' + BOSS + ' · 守卫事件 ' + deck.clampEvents.length + ' · 违规 ' + deck.violations.length + '</div>';
  h += '<div style="margin-top:6px;color:' + (deck.damageCeilingOk() ? '#5FA8A0' : '#E8806F') + '">红线：' +
       (deck.damageCeilingOk() ? 'PASS，未击穿' : 'FAIL') + '</div>';
  h += '<pre style="font-size:10px;color:#9BD4CC;white-space:pre-wrap;margin:8px 0">' +
       esc(pickedLog.map(p => 's' + p.stage + ' ' + p.name).join('\n') || '（无选择）') + '</pre>';
  h += '<div style="color:#8A8268;font-size:10px">同一 run_id 重放可得到完全相同的候选序列（点「确定性复核」验证）。<br>本页规则与 Godot 逐层一致，见 ④ 跨端比对。</div>';
  $('resultOverlay').innerHTML = h;
  $('resultOverlay').style.display = 'block';
  renderPanel();
}

function replay() {
  if (pickedLog.length === 0) { log('（本局还没有选择，先选一张卡）'); return; }
  const d2 = new R.CardDeck(LIB);
  d2.newRun(runId, curContext());
  let all = true;
  const rows = [];
  for (const p of pickedLog) {
    const off = d2.offer(p.stage);
    const same = JSON.stringify(off) === JSON.stringify(p.offered);
    if (!same) all = false;
    rows.push('s' + p.stage + ' ' + (same ? 'OK' : 'MISMATCH') + ' ' + off.join(','));
    d2.pick(p.id, p.stage);
  }
  log('── 确定性复核 ' + (all ? 'PASS' : 'FAIL') + ' ──\n' + rows.join('\n'));
  $('replayResult') && ($('replayResult').textContent = all ? 'PASS' : 'FAIL');
}

function toggleCodex() {
  const el = $('pickedList');
  el.style.maxHeight = el.style.maxHeight === '420px' ? '150px' : '420px';
  el.scrollTop = el.scrollHeight;
  log('已选卡清单：' + pickedLog.length + ' 条（面板高度已展开）');
}

/* 自动演示：逐层推进，日志实时刷新，方便一眼看到「跑到第几步 / 数值怎么变」。
   避开 stop_draw 封牌卡以跑满 8 层；URL 带 ?autorun=1 时自动启动，供无头浏览器自测。 */
function autoRunDemo() {
  if (finished) { runSeq++; newRun('web-demo-auto-' + (runSeq + 1)); }
  log('── 自动演示开始：每层 350ms，日志逐层刷新 ──');
  let guard = 0;
  const step = () => {
    guard++;
    if (finished || guard > 9) {
      log('── 自动演示结束：共 ' + pickedLog.length + ' 次选择 / 峰值 ' + deck.peakDamage() + ' ──');
      return;
    }
    const idx = offered.findIndex(id => !(byId[id].params || {}).stop_draw);
    if (idx >= 0) selectIndex(idx);
    confirmPick();
    setTimeout(step, 350);
  };
  step();
}

/* ================= ② 像素跑动 ================= */
const IDLE = ['idle_0','idle_1','idle_2'], RUNF = ['run_0','run_1','run_2','run_3'];
let sx = 240, facing = 1, axis = 0, autoRun = true, autoT = 0, frame = 0, acc = 0, lastT = 0;
function spriteTick(t) {
  if (!lastT) lastT = t;
  const dt = Math.min((t - lastT) / 1000, 0.1); lastT = t;
  if (autoRun && axis === 0) {
    autoT += dt;
    if (autoT > 2.2) { autoT = 0; facing = -facing; }
    axis = facing;
  }
  if (axis !== 0) {
    sx = Math.max(16, Math.min(464, sx + axis * 60 * dt));
    const nf = axis > 0 ? 1 : -1;
    if (nf !== facing) facing = nf;
  }
  const anim = axis === 0 ? 'idle' : 'run';
  const fps = anim === 'idle' ? 6 : 8;
  acc += dt;
  const step = 1 / fps;
  if (acc >= step) { acc -= step; frame = (frame + 1) % (anim === 'idle' ? 3 : 4); }
  const key = anim === 'idle' ? IDLE[frame] : RUNF[frame];
  const img = $('spriteImg');
  img.src = IMG[key];
  img.style.left = (sx - 32) + 'px';
  img.style.top = (216 - 62) + 'px';
  img.style.transform = facing === 1 ? 'none' : 'scaleX(-1)';
  const mirror = facing === -1 ? 'scaleX(-1)' : '不镜像（素材朝右）';
  $('spriteHud').textContent =
    'anim=' + anim + '  frame=' + key + '  fps=' + fps + '\n' +
    'x=' + sx.toFixed(1) + '  facing=' + (facing > 0 ? '右 →' : '左 ←') + '  ' + mirror + '\n' +
    'ground_top=216  anchor=(32,62)  frame=64×64';
  $('spritePanel').innerHTML =
    kv('逻辑画布', '480 × 270') + kv('帧尺寸', '64 × 64') +
    kv('缩放', '×' + scaleFactor + '（整数倍，CSS 模拟）') +
    kv('纹理过滤', 'image-rendering: pixelated（模拟 Nearest）') +
    kv('当前动画', anim + ' @ ' + fps + ' fps') +
    kv('当前帧', key) + kv('朝向', facing > 0 ? '右（原帧）' : '左（scaleX(-1) 镜像）') +
    kv('坐标 x', sx.toFixed(1) + '（clamp 16…464）') +
    '<div class="warn" style="margin-top:10px">以上为网页侧对照数据；Godot 实机像素表现仍需 F5 目检。</div>';
  if (autoRun && axis !== 0) axis = 0;
  requestAnimationFrame(spriteTick);
}

/* ================= ③ 图鉴 ================= */
let fCat = '', fRar = '', fQuery = '';
function buildFilters() {
  const box = $('codexFilters');
  let h = '<span class="chip' + (fCat === '' ? ' on' : '') + '" data-k="cat" data-v="">全类别</span>';
  for (const c of LIB.categories) h += '<span class="chip' + (fCat === c.key ? ' on' : '') + '" data-k="cat" data-v="' + c.key + '">' + esc(c.name) + '</span>';
  h += '<span style="width:12px"></span>';
  h += '<span class="chip' + (fRar === '' ? ' on' : '') + '" data-k="rar" data-v="">全稀有度</span>';
  for (const r of LIB.rarities) h += '<span class="chip' + (fRar === r.key ? ' on' : '') + '" data-k="rar" data-v="' + r.key + '">' + esc(r.name) + '</span>';
  h += '<span style="width:12px"></span><input id="search" placeholder="搜卡名 / ID / 效果" value="' + esc(fQuery) + '">';
  box.innerHTML = h;
  box.querySelectorAll('.chip').forEach(ch => ch.addEventListener('click', () => {
    if (ch.dataset.k === 'cat') fCat = ch.dataset.v; else fRar = ch.dataset.v;
    buildFilters(); renderCodex();
  }));
  $('search').addEventListener('input', e => { fQuery = e.target.value; renderCodex(); });
}
function renderCodex() {
  const list = LIB.cards.filter(c => {
    if (fCat && c.cat !== fCat) return false;
    if (fRar && c.rarity !== fRar) return false;
    if (fQuery && !(c.name + c.id + c.text).toLowerCase().includes(fQuery.toLowerCase())) return false;
    return true;
  });
  $('codexCount').textContent = '显示 ' + list.length + ' / ' + LIB.cards.length + ' 张 · 点击任一张看完整 params / hook / 前置 / 互斥';
  $('codexGrid').innerHTML = list.map(c => {
    const col = (catMap[c.cat] || {}).color || '#4A5568';
    return '<div class="codex-card" data-id="' + c.id + '"><span class="dot" style="background:' + col + '"></span><span class="cn">' +
      esc(c.name) + '</span><div class="cm">' + esc((rarMap[c.rarity] || {}).name) + ' · ' +
      esc((catMap[c.cat] || {}).name) + ' · ×' + (c.stack || 1) + '</div><div class="cm">' + esc(c.id) + '</div></div>';
  }).join('');
  $('codexGrid').querySelectorAll('.codex-card').forEach(el => el.addEventListener('click', () => showDetail(el.dataset.id)));
}
function showDetail(id) {
  const c = byId[id];
  if (!c) return;
  const d = $('codexDetail');
  let h = '<h3 style="color:#F2D089;margin-top:0">' + esc(c.name) + ' <span style="float:right;cursor:pointer" id="closeDetail">✕</span></h3>';
  h += kv('ID', esc(c.id)) + kv('类别', esc((catMap[c.cat] || {}).name)) +
       kv('稀有度', esc((rarMap[c.rarity] || {}).name)) + kv('效果类型', esc(c.type)) +
       kv('权重（PROPOSAL）', c.weight) + kv('堆叠上限', c.stack || 1) +
       kv('解锁', esc(c.unlock || 'none')) + kv('实现钩子', esc(c.hook || ''));
  h += '<div style="margin:8px 0;color:#E8DFC8">' + esc(c.text) + '</div>';
  h += '<pre>' + esc(JSON.stringify(c, null, 2)) + '</pre>';
  h += '<div class="note" style="margin-bottom:0">数值均为 PROPOSAL / 待实测；hook 中只有触碰五上界变量的部分已在规则层实现。</div>';
  d.innerHTML = h; d.style.display = 'block';
  $('closeDetail').addEventListener('click', () => { d.style.display = 'none'; });
}

/* ================= ④ 看板 ================= */
function browserSelfcheck() {
  const checks = [];
  const add = (label, ok, detail) => checks.push({ label, ok, detail });
  const d0 = new R.CardDeck(LIB);
  add('卡库加载 72 张', d0.isLoaded() && d0.cardCount() === 72, 'count=' + d0.cardCount());
  const d1 = new R.CardDeck(LIB); d1.newRun('browser-check');
  const a1 = d1.offer(1), a2 = d1.offer(1);
  add('同 (run_id, stage) 确定性', JSON.stringify(a1) === JSON.stringify(a2), a1.join(', '));
  // 重要口径：card_sheli / card_wuxin 带 stop_draw，选到即封牌，后续层不再弹卡。
  // 因此「一局 8 次选择」是上限而非必然；为验满 8 层主流程，此处主动避开封牌卡，
  // 封牌分支另设独立断言。① 里玩家真的选到封牌卡时会看到提前结算，行为一致。
  const d2 = new R.CardDeck(LIB); d2.newRun('browser-check', { realm: 9 });
  let flow = true, stagesRun = 0;
  for (let s = 1; s <= 8; s++) {
    const off = d2.offer(s);
    if (off.length === 0 || off.length > 3) flow = false;
    const cats = new Set(off.map(id => byId[id].cat));
    if (cats.size !== off.length) flow = false;
    const choice = off.find(id => !(byId[id].params || {}).stop_draw) || off[0];
    if (choice) { d2.pick(choice, s); stagesRun++; }
  }
  add('8 层流程 / 同类同层最多 1 张', flow && stagesRun === 8 && d2.offer(9).length === 0,
      '跑满 8 层 · 第 9 层不弹卡（避开 stop_draw 封牌卡）');
  const d3 = new R.CardDeck(LIB); d3.newRun('seal-check');
  d3.sealed = true; // 与 verify_card_rules.gd 同口径的白盒注入
  add('封牌后本局不再弹卡', d3.offer(1).length === 0, 'card_sheli / card_wuxin · 8 次选择是上限');
  const mega = new R.CardDeck(LIB); mega.newRun('all');
  for (const c of LIB.cards) mega.applyParams(c.id);
  add('72 卡全叠加峰值 < Boss 4400', mega.damageCeilingOk() && mega.peakDamage() <= 3996,
      'peak=' + mega.peakDamage() + ' / 守卫=' + mega.clampEvents.length + ' / 违规=' + mega.violations.length);
  // 与 Godot 黄金样本逐层比对（本页实时复算）
  const g = new R.CardDeck(LIB); g.newRun('runA', {});
  let goldenOk = META.goldenRunA.length > 0;
  for (const s of META.goldenRunA) {
    const off = g.offer(s.stage);
    if (JSON.stringify(off) !== JSON.stringify(s.offered)) goldenOk = false;
    if (s.picked) g.pick(s.picked, s.stage);
    if (g.peakDamage() !== s.peakAfter) goldenOk = false;
  }
  add('网页复算 == Godot 黄金样本 runA', goldenOk,
      '9 步逐层比对 / 峰值 ' + g.peakDamage());
  const w = new R.CardDeck(LIB); w.newRun('runW', { affix: ['affix_wuxiang'], realm: 9 });
  add('无相词缀压成 2 选 1', w.choiceCount() === 2 && w.offer(1).length <= 2, 'choiceCount=' + w.choiceCount());
  // 第 20 轮：战斗内核在本页实时复算（与 tools/verify_battle_sim.js 同源，非抄报告数字）
  add('战斗伤害公式 == 01 §8.1',
      B.damageFormula(180, 1.60, 600, 2.5, 1.8, 0, null) === 3996 &&
      B.damageFormula(60, 1.60, 120, 1.0, 1.0, 0.30, null) === 151, '3996 / 151');
  add('Boss 4400 需 2 次峰值命中', B.maxHit() < 4400 && 2 * B.maxHit() >= 4400, '2×3996=7992');
  add('9 层波形 HP_total 合计 10330',
      B.STAGES.length === 9 && B.STAGES.reduce((a, s) => a + s.hp, 0) === 10330, 'sum=10330');
  const bs1 = new B.BattleSim({ runId: 'page-check', stage: 1 });
  const bs2 = new B.BattleSim({ runId: 'page-check', stage: 1 });
  for (let t = 0; t < 120; t++) {
    const inp = { axis: t % 40 < 20 ? 1 : -1, skills: [t % 18 === 0, false, false, false], dodge: false };
    bs1.step(B.TICK, inp); bs2.step(B.TICK, inp);
  }
  add('战斗同 seed 同输入逐字段一致',
      JSON.stringify(bs1.snapshot()) === JSON.stringify(bs2.snapshot()), '120 tick / 4 s');
  const bs3 = new B.BattleSim({ runId: 'page-link', stage: 1 });
  const dmgBefore = bs3.computeDamage(60, false, 0);
  bs3.syncDeck({ extra_pool: 200, offense_pool_used: 50, combo_multiplier: 0.3 });
  const dmgAfter = bs3.computeDamage(60, false, 0);
  add('选卡共享池提高实战伤害且不越 600',
      dmgAfter > dmgBefore && bs3.pool <= 600,
      dmgBefore + ' → ' + dmgAfter + ' / pool=' + bs3.pool);
  // 第 21 轮：卡牌效果编译 / 联动在本页实时复算（不是抄报告数字）
  const fxAll = E.compileCardEffects(LIB, LIB.cards.map(c => c.id));
  const paramTotal = LIB.cards.reduce((a, c) => a + Object.keys(c.params || {}).length, 0);
  add('72 卡效果编译不抛异常且三层计数自洽',
      fxAll.counts.cards === 72 &&
      fxAll.counts.battle + fxAll.counts.deck + fxAll.counts.none === paramTotal,
      'battle=' + fxAll.counts.battle + ' / deck=' + fxAll.counts.deck +
      ' / none=' + fxAll.counts.none + ' / params=' + paramTotal);
  const fxEmpty = E.compileCardEffects(LIB, []);
  const bsBase = new B.BattleSim({ runId: 'fx-check', stage: 1 });
  const bsFxEmpty = new B.BattleSim({ runId: 'fx-check', stage: 1 });
  bsFxEmpty.applyCardEffects(fxEmpty);
  for (let t = 0; t < 90; t++) {
    const inp = { axis: t % 30 < 15 ? 1 : -1, skills: [t % 15 === 0, false, false, false], dodge: false };
    bsBase.step(B.TICK, inp); bsFxEmpty.step(B.TICK, inp);
  }
  add('空效果与未接效果逐字段一致（不扰动第 20 轮）',
      JSON.stringify(bsBase.snapshot()) === JSON.stringify(bsFxEmpty.snapshot()) &&
      JSON.stringify(Object.keys(fxEmpty.mods).sort()) === JSON.stringify(Object.keys(B.emptyCardMods()).sort()),
      '90 tick / schema 一致');
  const fxPoyun = E.compileCardEffects(LIB, ['card_poyun']);
  add('破云式 → 2 段且总伤不变（R54 以卡面 text 为准）',
      fxPoyun.mods.segmentRatios.length === 2 &&
      Math.abs(fxPoyun.mods.segmentRatios.reduce((a, b) => a + b, 0) - 1) < 1e-6 &&
      fxPoyun.notes.some(n => n.card === 'card_poyun'), '0.5 + 0.5 = 1.0');
  const bsHp = new B.BattleSim({ runId: 'fx-hp', stage: 1 });
  const hp0 = bsHp.maxHp;
  bsHp.applyCardEffects(E.compileCardEffects(LIB, ['card_ningdan']));
  add('凝丹 → HP 上限 300 → 324（战斗状态真的变了）',
      hp0 === 300 && bsHp.maxHp === 324, hp0 + ' → ' + bsHp.maxHp);
  const keys = Object.keys(IMG);
  // 第 32 轮：vfx 已从 16 帧涨到 36 帧，写死 16 会让本页自检无谓 FAIL。
  // 改为「不低于旧基线 + 新增资源齐备」，帧数按内嵌资源实时统计。
  const nVfx = keys.filter(k => /^vfx_.*_\d\d$/.test(k)).length;
  const nBoss = keys.filter(k => /^boss_.*_r_\d\d$/.test(k)).length;
  const nOvl = keys.filter(k => /^ovl_.*_\d\d$/.test(k)).length;
  add('内嵌像素素材齐备（含第 31 轮回稿转录资源）',
      keys.filter(k => k.startsWith('char_player_') && k.includes('_r_')).length === 15 &&
      keys.filter(k => k.startsWith('mob_') && k.includes('_r_')).length === 60 &&
      nVfx >= 16 && nBoss >= 42 && nOvl === 10 &&
      ['bg_normal', 'bg_rest', 'bg_high', 'bg_boss'].every(k => !!IMG[k]),
      'char 15 / mob 60 / vfx ' + nVfx + ' / boss ' + nBoss +
      ' / overlay ' + nOvl + ' / bg 4');
  const artExpected = !/[?&]art=placeholder/.test(location.search);
  add('原稿素材模式与旧占位模式可切换（第 32 轮）',
      refArt === artExpected && typeof setArtMode === 'function' &&
      !!document.getElementById('bBgArt') && !!document.getElementById('artToggle'),
      'refArt=' + refArt + '（默认原稿；?art=placeholder 切旧占位）');
  // 第 22 轮：战斗公式层与网页内核逐条复算（不抄报告数字）
  const fxCases = [[20, 1, 0, 1, 1, 0], [180, 1.6, 600, 2.5, 1.8, 0],
                   [180, 1.6, 600, 2.5, 1.8, 0.75], [0, 0, 0, 0, 0, 0],
                   [-1, -1, -1, -1, 0, -1], [999, 9, 9999, 9, 9, 9],
                   [1, 1, 0, 1, 1, 0.5], [3, 1, 0, 1, 1, 0.5]];
  const fxExpect = [20, 3996, 999, 1, 1, 999, 1, 2];
  const fxGot = fxCases.map(c => B.damageFormula(c[0], c[1], c[2], c[3], c[4], c[5], []));
  add('伤害公式边界用例复算一致（含钳制与 .5 舍入）',
      JSON.stringify(fxGot) === JSON.stringify(fxExpect), fxGot.join(' / '));
  add('五上界最坏伤害 = 3996 < Boss 4400',
      B.maxHit() === 3996 && B.maxHit() < 4400, 'maxHit=' + B.maxHit());
  // 第 33 轮：UI 设计稿对照层（内嵌真图 + 六视图联动映射），防止只改文案不接真图
  add('UI 设计稿对照 9 张内嵌齐备',
      UI_SKINS.length === 9 && UI_SKINS.every(s => typeof IMG[s[0]] === 'string' &&
        IMG[s[0]].startsWith('data:image/png;base64,')),
      UI_SKINS.filter(s => !!IMG[s[0]]).length + '/9');
  add('设计稿按六视图联动映射完整',
      Object.keys(SKIN_BY_TAB).length === 6 &&
      Object.values(SKIN_BY_TAB).every(k => UI_SKINS.some(s => s[0] === k)),
      '6 视图 / 9 稿 · 04/05/06 可下拉查看');
  return checks;
}

function renderStatus() {
  const bc = browserSelfcheck();
  const passed = bc.filter(c => c.ok).length;
  const m = META;
  $('metricCards').innerHTML =
    '<div class="metric"><div class="n">' + m.rules.passed + '/' + m.rules.total + '</div><div class="l">Godot 规则层 headless 断言（' + m.rules.verdict + '）· 峰值 ' + m.rules.peak + '</div></div>' +
    '<div class="metric"><div class="n">' + m.selfcheck.passed + '/' + m.selfcheck.checks + '</div><div class="l">工程全量静态自检（' + m.selfcheck.verdict + '）</div></div>' +
    '<div class="metric"><div class="n">' + m.cross.passed + '/' + m.cross.total + '</div><div class="l">网页/Node ↔ Godot 跨端一致性（' + m.cross.verdict + '）</div></div>' +
    '<div class="metric"><div class="n">' + m.battle.passed + '/' + m.battle.total + '</div><div class="l">横版战斗规则内核 Node 断言（' + m.battle.verdict + '）</div></div>' +
    '<div class="metric"><div class="n">' + m.battleCross.passed + '/' + m.battleCross.total + '</div><div class="l">战斗公式层 Godot ↔ 网页跨端（' + m.battleCross.verdict + '）</div></div>' +
    '<div class="metric"><div class="n">' + passed + '/' + bc.length + '</div><div class="l">本页浏览器内实跑自检（实时计算）</div></div>';
  $('browserChecks').innerHTML = bc.map(c =>
    '<div class="kv"><span>' + (c.ok ? '<span class="ok">PASS</span>' : '<span class="bad">FAIL</span>') + ' ' + esc(c.label) + '</span><span>' + esc(c.detail) + '</span></div>'
  ).join('') + '<div class="note" style="margin-bottom:0">这些断言在<b>你打开本页时实时计算</b>，不是抄报告数字。算法：' + esc(m.cross.algorithm) + '</div>';
  $('timeline').innerHTML = '<table><tr><th>轮次</th><th>落地内容</th></tr>' +
    m.timeline.map(r => '<tr><td>' + esc(r[0]) + '</td><td>' + esc(r[1]) + '</td></tr>').join('') + '</table>';
  $('riskTable').innerHTML = '<tr><th>编号</th><th>内容</th><th>状态</th></tr>' +
    m.risks.map(r => '<tr><td>' + esc(r[0]) + '</td><td>' + esc(r[1]) + '</td><td>' +
      (r[2].startsWith('✅') ? '<span class="tag done">' + esc(r[2]) + '</span>' : '<span class="tag todo">' + esc(r[2]) + '</span>') +
      '</td></tr>').join('');
  $('checklist').innerHTML = '<ul>' + m.importChecklist.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul>';
  $('genAt').textContent = META.generatedAt + ' · ' + META.engine;
}

/* ================= 事件绑定 ================= */
$('btnConfirm').addEventListener('click', confirmPick);
$('confirmBtn').addEventListener('click', confirmPick);
$('btnRestart').addEventListener('click', () => { runSeq++; newRun(runSeq === 1 ? 'web-demo-2' : 'web-demo-' + (runSeq + 1)); });
$('btnWuxiang').addEventListener('click', () => {
  wuxiang = !wuxiang;
  $('btnWuxiang').classList.toggle('on', wuxiang);
  log('无相词缀 → ' + (wuxiang ? '开（2 选 1）' : '关（3 选 1）'));
  newRun(runId);
});
$('btnReplay').addEventListener('click', replay);
$('btnCodex').addEventListener('click', toggleCodex);
$('btnAutoRun').addEventListener('click', autoRunDemo);
document.querySelectorAll('#stage .card').forEach(el =>
  el.addEventListener('click', () => { selectIndex(Number(el.dataset.i)); confirmPick(); }));
document.addEventListener('keydown', e => {
  const tag = document.activeElement ? document.activeElement.tagName : '';
  if (tag === 'INPUT' || tag === 'TEXTAREA') { if (e.key === 'Escape') $('codexDetail').style.display = 'none'; return; }
  const k = e.key;
  // ① 横版战斗：A/D 移动 · J/K/L/I 技能 · Space 闪避 · Esc 暂停（01 §6 输入映射表）
  if (currentTab === 'battle') {
    const bk = k.toLowerCase();
    let used = true;
    if (bk === 'a' || k === 'ArrowLeft') held.axis = -1;
    else if (bk === 'd' || k === 'ArrowRight') held.axis = 1;
    else if (bk === 'j') held.skills[0] = true;
    else if (bk === 'k') held.skills[1] = true;
    else if (bk === 'l') held.skills[2] = true;
    else if (bk === 'i') held.skills[3] = true;
    else if (k === ' ') held.dodge = true;
    else if (k === 'Escape') { toggleBattlePause(); return; }
    else used = false;
    if (used) {
      e.preventDefault();
      battleRunning = true; battlePaused = false; battleAuto = false;
      $('btnBattleAuto').classList.remove('on');
    }
    return;
  }
  if (k === '1' || k === '2' || k === '3') { selectIndex(Number(k) - 1); }
  else if (k === 'ArrowLeft') { selectIndex(selected - 1); }
  else if (k === 'ArrowRight') { selectIndex(selected + 1); }
  else if (k === 'Enter') { confirmPick(); }
  else if (k === 'Escape') { toggleCodex(); $('codexDetail').style.display = 'none'; }
  else if (k === 'r' || k === 'R') { runSeq++; newRun('web-demo-' + (runSeq + 1)); }
  else if (k === 'w' || k === 'W') { $('btnWuxiang').click(); }
  else if (k === 'a' || k === 'A') { autoRun = false; $('btnAuto').classList.remove('on'); $('btnAuto').textContent = '自动来回跑：关'; axis = -1; }
  else if (k === 'd' || k === 'D') { autoRun = false; $('btnAuto').classList.remove('on'); $('btnAuto').textContent = '自动来回跑：关'; axis = 1; }
});
document.addEventListener('keyup', e => {
  if (currentTab === 'battle' && ['a','A','d','D','ArrowLeft','ArrowRight'].includes(e.key)) {
    held.axis = 0; return;
  }
  if (['a','A','d','D'].includes(e.key)) axis = 0;
});
function hold(btn, v) {
  const set = () => { autoRun = false; $('btnAuto').classList.remove('on'); $('btnAuto').textContent = '自动来回跑：关'; axis = v; };
  btn.addEventListener('pointerdown', set);
  btn.addEventListener('pointerup', () => { axis = 0; });
  btn.addEventListener('pointerleave', () => { axis = 0; });
}
hold($('btnLeft'), -1); hold($('btnRight'), 1);
$('btnAuto').addEventListener('click', () => {
  autoRun = !autoRun; axis = 0;
  $('btnAuto').classList.toggle('on', autoRun);
  $('btnAuto').textContent = '自动来回跑：' + (autoRun ? '开' : '关');
});
$('btnScale').addEventListener('click', () => {
  scaleFactor = scaleFactor >= 4 ? 2 : scaleFactor + 1;
  $('btnScale').textContent = '缩放 ×' + scaleFactor + '（点击切换）';
  fitStage();
});

/* ================= 启动 ================= */
buildFilters(); renderCodex(); renderStatus(); newRun('web-demo');
renderMenuPage('start');
startBattle(1, { auto: false });
fitStage(); requestAnimationFrame(spriteTick); requestAnimationFrame(renderBattle);
setInterval(autoPlayStep, 32);
const QS = new URLSearchParams(location.search);
// 第 32 轮：素材模式开关（?art=placeholder 由 refArt 初始化时读取）
const artBtn = $('artToggle');
if (artBtn) artBtn.addEventListener('click', () => setArtMode(!refArt));
setArtMode(refArt);
window.__setArtMode = setArtMode;   // 供 Node/浏览器自动化复验两种模式
window.__getArtMode = () => refArt;
// 第 33 轮：UI 设计稿对照层初始化（?ui=off 默认收起）
const uiSel = $('uiSkinSelect');
if (uiSel) {
  uiSel.innerHTML = UI_SKINS.map(s =>
    '<option value="' + s[0] + '">' + esc(s[1]) + '</option>').join('');
  uiSel.addEventListener('change', () => { uiSkinKey = uiSel.value; applyUiSkin(); });
}
const uiToggle = $('uiSkinToggle');
if (uiToggle) uiToggle.addEventListener('click', () => setUiSkin(!uiSkinOn));
applyUiSkinForTab(currentTab);
setUiSkin(uiSkinOn);
window.__setUiSkin = setUiSkin;   // 供无头浏览器复验开 / 关两种模式
window.__getUiSkin = () => ({ on: uiSkinOn, key: uiSkinKey });
window.__freezeTick = QS.has('freeze') ? (Number(QS.get('freeze')) || 0) : 0;
window.__autoLink = QS.has('autolink');
if (QS.has('autorun')) setTimeout(autoRunDemo, 120);
// 联动自测用固定局号：其第 1 层候选含数值卡 card_danbao，可机器验证真实卡牌联动
if (QS.has('autolink')) newRun('linked-seed-2');
// ?battle=N 供无头浏览器直接进战斗第 N 层并自动演示（不依赖点击）
if (QS.has('battle')) {
  const n = Math.max(1, Math.min(9, Number(QS.get('battle')) || 1));
  startBattle(n, { auto: true });
  switchTab('battle');
}
// ?pool=N 等价于点「🧪 共享池 +N」：供无头浏览器验证伤害公式对共享池的敏感度
if (QS.has('pool')) injectPool(Number(QS.get('pool')) || 150);
// ?cards=id1,id2 调试预置（同样不经过抽卡规则），便于直接观察指定卡的战斗效果
if (QS.has('cards')) presetFxCards(QS.get('cards').split(','));
</script>
</body>
</html>
"""


# 产物一致性判定要忽略「来自外部报告 / 时钟」的易变数字。
# 否则 final_selfcheck.py 每次重写自己的报告（检查项数变化）→ 网页 META 变化 → --check FAIL，
# 形成自检与网页互相判过期的循环。模板 / JS / 图片 / 卡库 / 风险 / 时间线仍逐字节严格比对。
VOLATILE = [
    (re.compile(r'"generatedAt":"[^"]*"'), '"generatedAt":"<TS>"'),
    (re.compile(r'"verdict":"[A-Z]+"'), '"verdict":"<V>"'),
    (re.compile(r'"total":\d+'), '"total":<N>'),
    (re.compile(r'"passed":\d+'), '"passed":<N>'),
    (re.compile(r'"checks":\d+'), '"checks":<N>'),
    (re.compile(r'"peak":[\d.]+'), '"peak":<N>'),
    (re.compile(r'"guardEvents":\d+'), '"guardEvents":<N>'),
    (re.compile(r'"goldenPeak":[\d.]+'), '"goldenPeak":<N>'),
]


def canonicalize(s: str) -> str:
    for pattern, replacement in VOLATILE:
        s = pattern.sub(replacement, s)
    return s


def build() -> str:
    lib = json.loads(LIB_PATH.read_text(encoding="utf-8"))
    rules_js = RULES_PATH.read_text(encoding="utf-8")
    battle_js = BATTLE_PATH.read_text(encoding="utf-8")
    effects_js = EFFECTS_PATH.read_text(encoding="utf-8")
    images = load_images()
    meta = load_meta()
    html = TEMPLATE
    html = html.replace("__RULES_JS__", rules_js)
    html = html.replace("__BATTLE_JS__", battle_js)
    html = html.replace("__EFFECTS_JS__", effects_js)
    html = html.replace("__LIB_JSON__", json.dumps(lib, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("__IMG_JSON__", json.dumps(images, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("__META_JSON__", json.dumps(meta, ensure_ascii=False, separators=(",", ":")))
    return html


def structural_checks(html: str) -> list[str]:
    problems = []
    for token in ("__RULES_JS__", "__BATTLE_JS__", "__EFFECTS_JS__", "__LIB_JSON__",
                  "__IMG_JSON__", "__META_JSON__"):
        if token in html:
            problems.append(f"占位符未替换：{token}")
    for needle in ("window.CardRules", "window.BattleSim", "window.CardEffects", "xorshift32",
                  "const LIB =", "function browserSelfcheck", "function renderBattle(",
                  "applyCardEffects", "compileCardEffects", 'id="fxPanel"',
                  "data:image/png;base64,", "id=\"menu\"", "id=\"battle\"", "id=\"draft\"",
                  "id=\"sprite\"", "id=\"codex\"", "id=\"status\"", "id=\"battleStage\"",
                  "id=\"menuScreen\"", "id=\"uiSkinBar\"", "id=\"uiSkinImg\"",
                  "function setUiSkin", "function applyUiSkinForTab",
                  "const UI_SKINS", "const SKIN_BY_TAB", "ui=off"):
        if needle not in html:
            problems.append(f"关键片段缺失：{needle}")
    if html.count("<script>") != 2 or html.count("</script>") != 2:
        problems.append("script 标签数量异常")
    # 三份规则实现必须与工程内文件字节级同源
    for path in (RULES_PATH, BATTLE_PATH, EFFECTS_PATH):
        if path.read_text(encoding="utf-8") not in html:
            problems.append(f"内嵌规则实现与 {path.name} 不是同一份")
    return problems


def main() -> int:
    check_only = "--check" in sys.argv
    try:
        html = build()
    except Exception as exc:  # noqa: BLE001
        print(f"WEBDEMO|FAIL|生成失败：{exc}")
        return 1
    problems = structural_checks(html)
    if problems:
        for p in problems:
            print(f"WEBDEMO|FAIL|{p}")
        return 1
    canonical = canonicalize(html)
    sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    if check_only:
        if not OUT.is_file():
            print("WEBDEMO|FAIL|产物不存在：" + str(OUT.relative_to(ROOT)))
            return 1
        disk = OUT.read_text(encoding="utf-8")
        # 时间戳与外部报告数字会变，比对实质内容时统一抹掉；其余字节必须完全一致。
        if canonicalize(disk) != canonical:
            print("WEBDEMO|FAIL|产物与当前源不一致，请重跑 python3 tools/build_web_demo.py")
            return 1
        print(f"WEBDEMO|PASS|--check 产物一致 | bytes={len(disk.encode('utf-8'))} | sha={sha}")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"WEBDEMO|PASS|{OUT.relative_to(ROOT)} | bytes={len(html.encode('utf-8'))} | sha={sha}")
    print("WEBDEMO|内嵌卡库 " + str(len(json.loads(LIB_PATH.read_text(encoding='utf-8'))['cards'])) +
          " 张 / 图片 " + str(len(load_images())) + " 张 / 规则实现 " +
          str(len(RULES_PATH.read_text(encoding='utf-8'))) + " 字节")
    return 0


if __name__ == "__main__":
    sys.exit(main())
