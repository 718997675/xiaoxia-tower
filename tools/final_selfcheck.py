#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 15 轮交付前全量静态自检（可复跑、零第三方依赖）。

只做离线/静态断言：JSON 解析、CSV 格式、Python 编译、冻结清单、回执、
伤害红线、卡牌库、两套报告、质检、产物齐备、project.godot 配置、
场景帧路径、机器绝对路径、交接文档过期状态、R39 的 .gdignore。

动态侧（另行复跑，不由本脚本代跑）：
  python3 tools/verify_damage_ceiling.py
  python3 tools/check_traceability.py
  check_godot_project.py . --spec docs/project-spec.json --freeze docs/design-freeze.json --json docs/godot-project-check.json
  Godot --headless --script tools/verify_minimal_run.gd（须先用编辑器导入过资源）

用法：python3 tools/final_selfcheck.py   →   docs/final-selfcheck.json
退出码：0=PASS，1=FAIL
"""
from __future__ import annotations

import csv
import json
import py_compile
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs"
REPORT = DOC / "final-selfcheck.json"

CHECKS: list[dict] = []


def check(cid: str, desc: str, fn) -> None:
    try:
        detail = fn()
        CHECKS.append({"id": cid, "desc": desc, "status": "PASS", "detail": str(detail)})
    except Exception as exc:  # 任何断言失败都如实落盘，不静默吞掉
        CHECKS.append({"id": cid, "desc": desc, "status": "FAIL", "detail": f"{type(exc).__name__}: {exc}"})


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def load(name: str):
    return json.loads((DOC / name).read_text(encoding="utf-8"))


def read_csv(name: str, cols: int) -> list[list[str]]:
    p = DOC / name
    need(not p.read_bytes().startswith(b"\xef\xbb\xbf"), f"{name} 含 UTF-8 BOM")
    text = p.read_text(encoding="utf-8")
    need(not any(line.strip() == "" for line in text.splitlines()), f"{name} 含空行")
    rows = list(csv.reader(text.splitlines()))
    bad = [i + 1 for i, r in enumerate(rows) if len(r) != cols]
    need(not bad, f"{name} 列数异常的行：{bad[:8]}")
    return rows


# ---------------------------------------------------------------- 1 JSON
def c_json():
    files = sorted(DOC.glob("*.json"))
    need(len(files) >= 15, f"docs 下 JSON 太少：{len(files)}")
    for p in files:
        json.loads(p.read_text(encoding="utf-8"))
    return f"{len(files)} 份 JSON 全部可解析"


# ---------------------------------------------------------------- 2/3 CSV
def c_nums():
    rows = read_csv("数值框架.csv", 9)
    need(len(rows) >= 240, f"数值源行数 {len(rows)} < 240（怀疑被覆盖而非追加）")
    keys = [r[1] for r in rows[1:]]
    need(any(k.startswith("round15") for k in keys), "缺第 15 轮数值行")
    need(any(k == "round15_final_selfcheck_checks" for k in keys), "缺收口自检行")
    need(len(keys) == len(set(keys)), "数值源 key 有重复")
    return f"{len(rows)} 行（含表头）× 9 列，无 BOM / 无空行，含 round15 行"


def c_cards():
    rows = read_csv("卡牌库.csv", 15)
    need(len(rows) == 73, f"卡牌 CSV 应为 1 表头 + 72 卡 = 73 行，实为 {len(rows)}")
    return f"{len(rows)} 行（含表头）× 15 列，无 BOM / 无空行"


# ---------------------------------------------------------------- 4 脚本编译
def c_py():
    files = sorted((ROOT / "tools").glob("*.py"))
    need(len(files) >= 12, f"tools 下 Python 脚本太少：{len(files)}")
    for p in files:
        py_compile.compile(str(p), doraise=True)
    return f"{len(files)} 个 tools/*.py 全部编译通过"


# ---------------------------------------------------------------- 5/6 冻结
def c_freeze():
    d = load("design-freeze.json")
    need(d.get("status") == "frozen", "权威清单未 frozen")
    need(d.get("version") == 1, "version 不是 1")
    need(d.get("traceMarker") == "@trace", "traceMarker 不是 @trace")
    items = d.get("items", [])
    ids = [x.get("id") for x in items]
    expect = [f"DF-{i:02d}" for i in range(1, 23)]
    need(ids == expect, f"DF 编号不是 DF-01..DF-22 连续唯一：{ids}")
    bad = [x["id"] for x in items if x.get("confirmed") is not True]
    need(not bad, f"存在未确认条目：{bad}")
    return "status=frozen / version=1 / 22 条 DF-01..DF-22 连续唯一且全部 confirmed"


def c_draft():
    d = load("design-freeze-draft.json")
    need(d.get("status") == "draft" and d.get("frozen") is False, "历史快照被误置 frozen")
    r15 = d.get("round15Freeze", {})
    need("notTheRealFreezeIsHistorical" in r15, "缺历史字段失效说明")
    need("finalSelfCheck" in r15, "缺最终自检引用")
    # R40：冻结清单里不能出现占位符编号，工程结构检查会把它当「未知需求编号」报错
    placeholder = "DF-" + "xx"
    for name in ("design-freeze-draft.json", "design-freeze.json"):
        raw = (DOC / name).read_text(encoding="utf-8")
        need("@trace " + placeholder not in raw, f"{name} 含追溯标记占位符（R40）")
    need(placeholder not in (DOC / "design-freeze-draft.json").read_text(encoding="utf-8"),
         "draft 仍含占位符编号（R40）")
    return "仍 draft / frozen=false；历史字段失效说明齐备，且已清除占位符编号（R40）"


# ---------------------------------------------------------------- 7 回执
def c_receipt():
    d = load("decision-receipt.json")
    s = d["validation"]["stats"]
    need(s["knownItems"] == 16 and s["answered"] == 16, "回执不是 16/16")
    need(s["hardGatesResolved"] == 4 and s["hardGatesUnresolved"] == [], "硬门禁不是 4/4")
    need(d["validation"]["errors"] == [], "回执校验有错误")
    need(d.get("frozenTouched") is False and d.get("baselineDocsTouched") is False, "回执脚本碰了冻结或基线")
    return "16/16 已答 / 硬门禁 4/4 / 错误 0 / 告警 1（Q28 正文修订，已随 v0.2 处置）"


# ---------------------------------------------------------------- 8 伤害红线
def c_damage():
    d = load("damage-ceiling-report.json")
    need(d.get("verdict") == "PASS", "R32 极值验算非 PASS")
    need(d.get("violations") == [], "仍有违规卡")
    ceiling = d["confirmedCeiling"]
    for k, v in {"base": 180.0, "realm_ratio": 1.6, "extra_pool": 600.0,
                 "combo_mult": 2.5, "crit_mult": 1.8}.items():
        need(ceiling.get(k) == v, f"五上界 {k} 被改动：{ceiling.get(k)}")
    worst = d["scenario"]["withSharedPool"]["damage"]
    need(worst == 3996 and worst < d["bossHP"], f"峰值 {worst} 未守住 Boss {d['bossHP']}")
    need(d.get("cardsScanned") == 72, "验算未覆盖 72 张卡")
    return "五上界齐全 / 违规 0 / 峰值 3996 < Boss 4400 / 72 卡全扫"


# ---------------------------------------------------------------- 9 卡库
def c_cards_lib():
    d = load("buff-card-library.json")
    need(len(d["cards"]) == 72, f"卡数 {len(d['cards'])} ≠ 72")
    need(len(d["categories"]) == 6 and len(d["rarities"]) == 4, "类别/稀有度档数不对")
    rule = d["offenseCeiling"]["rule"]
    for token in ["realm_ratio<=1.60", "extra_pool<=600", "base<=180"]:
        need(token in rule, f"五上界铁律缺 {token}")
    fixed = d["offenseCeiling"]["fixedCards"]
    need(len(fixed) == 3, "R32 修复卡清单不是 3 张")
    by_id = {c["id"]: c for c in d["cards"]}
    for cid in fixed:
        params = by_id[cid]["params"]
        need(params.get("pool") == "offense_pool" and params.get("cap") == 600,
             f"{cid} 缺 pool/cap 声明")
    return "72 张 / 6 类 / 4 档；3 张 R32 修复卡均带 pool:offense_pool + cap:600"


# ---------------------------------------------------------------- 10/11 报告
def c_project_check():
    d = load("godot-project-check.json")
    need(d.get("errorCount") == 0, f"工程结构自检有 {d.get('errorCount')} 错误")
    return f"错误 0 / 警告 {d.get('warningCount')}（覆盖率缺口 + 报告自指绝对路径，已知例外）"


def c_trace():
    d = load("traceability-report.json")
    need(d.get("verdict") == "PASS", "追溯核对非 PASS")
    a = d["authoritative"]
    need(a.get("status") == "frozen" and a.get("items") == 22, "权威清单状态/条数不对")
    cov = a["coverage"]
    # 第 18 轮：不再写死 4/22。新增真实回指（DF-19 / DF-21）时覆盖率会自然上升，
    # 这里只校验「covered / total / rate 三者自洽」+「不低于最小验证工程的 4 条」，
    # 避免把真实进度误判成回归，也避免有人手工塞标记凑数却被放行。
    need(cov["total"] == 22 and 4 <= cov["covered"] <= 22, "追溯覆盖率 covered 越界")
    need(abs(cov["rate"] - round(cov["covered"] / cov["total"], 4)) < 1e-6,
         "覆盖率数值与 covered/total 不自洽")
    need(d.get("issues") == [], "追溯报告有 issues")
    return (f"verdict=PASS / 权威清单 frozen 22 条 / 覆盖 "
            f"{cov['covered']}/22 = {cov['rate'] * 100:.2f}%（真实进度）")


# ---------------------------------------------------------------- 12/13 质检
def c_qc():
    d = load("qc-report.json")
    s = d["summary"]
    n = s["frames"]
    groups = d.get("groups", [])
    # 第 29 轮：B3/B4 落地后质检从 142 帧涨到 214 帧。按第 18 轮 traceability
    # 的同一口径改成动态自洽，不再写死帧数；仍逐项守住硬指标与旧基线不退化。
    need(n > 0 and s["verdicts"] == {"SHIP": n}, f"质检不是 {n} 项全 SHIP")
    need(sum(len(g["frames"]) for g in groups) == n, "各组帧数与汇总帧数不一致")
    need(all(g["verdict"] == "SHIP" for g in groups), "存在非 SHIP 的素材组")
    need(n >= 142, f"帧数 {n} 低于旧基线 142，疑似误删素材")
    need(s["outOfPaletteTotal"] == 0 and s["semiAlphaFrames"] == 0, "越界色/半透明不为 0")
    need(s["sizeMismatchFrames"] == 0, "存在尺寸不符帧")
    return (f"{len(groups)} 组 / {n} 项全 SHIP，越界色 0 / 半透明帧 0 / "
            "尺寸不符 0（帧数动态自洽，>=142 基线）")


def c_icons():
    d = load("icon-catalog.json")
    need(len(d["items"]) == 47 and len(d["accessories"]) == 4, "图标/挂件数量不对")
    need(d["pending"] == [], "图标工单仍有 pending")
    return "图标 47/47、挂件 4/4、pending 归零（R31 返修后）"


# ---------------------------------------------------------------- 14/15/16 工程
def c_project_cfg():
    t = (ROOT / "project.godot").read_text(encoding="utf-8")
    for token in ['window_width_override=1920', 'window_height_override=1080',
                  'viewport_width=480', 'viewport_height=270',
                  'default_texture_filter=0', 'stretch/mode="viewport"',
                  'run/main_scene="res://scenes/MinimalRun.tscn"',
                  '[input]', 'move_left={', 'move_right={']:
        need(token in t, f"project.godot 缺 {token}")
    return "480×270×4 / Nearest(0) / stretch=viewport / 主场景 / 左右输入映射齐全"


def c_scene():
    t = (ROOT / "scenes" / "MinimalRun.tscn").read_text(encoding="utf-8")
    for token in ['type="Node2D"', 'name="Player"', 'type="CharacterBody2D"',
                  'name="Sprite"', 'type="AnimatedSprite2D"',
                  'res://scripts/PlayerProbe.gd']:
        need(token in t, f"MinimalRun.tscn 缺 {token}")
    return "节点树 MinimalRun → Player(CharacterBody2D) → Sprite(AnimatedSprite2D)，脚本已挂"


def c_collision_r41():
    """R41：Player 必须带 CollisionShape2D，地面必须是真实 StaticBody2D，且脚底与地面顶对齐。"""
    t = (ROOT / "scenes" / "MinimalRun.tscn").read_text(encoding="utf-8")
    need('type="StaticBody2D"' in t, "场景缺 StaticBody2D 地面碰撞体")
    need('type="CollisionShape2D"' in t, "场景缺 CollisionShape2D")
    need('name="GroundBody"' in t and 'name="Body"' in t, "场景缺 GroundBody / Body 节点")
    need('size = Vector2(32, 56)' in t, "主角碰撞形状应为 32×56")
    need('size = Vector2(480, 54)' in t, "地面碰撞形状应为 480×54")
    # 主角原点 y=188 + 半高 28 = 216；地面 StaticBody2D 原点 y=216
    need("position = Vector2(240, 188)" in t, "主角原点应仍为 (240, 188)")
    need("position = Vector2(0, 216)" in t, "地面碰撞体原点应仍为 (0, 216)")
    need(188 + 56 / 2 == 216, "主角碰撞底边与地面顶未对齐")
    # verify 脚本必须带回归断言，防止 R41 再退化
    v = (ROOT / "tools" / "verify_minimal_run.gd").read_text(encoding="utf-8")
    need("GroundBody StaticBody2D missing" in v, "verify_minimal_run.gd 缺碰撞回归断言")
    need("Player/Body CollisionShape2D missing" in v, "verify_minimal_run.gd 缺主角碰撞回归断言")
    return "Player/Body 32×56 + GroundBody/Shape 480×54，脚底 216 == 地面顶 216；verify 脚本带回归断言"


def c_frames_tres():
    """R43：帧必须是真正的 SpriteFrames 资源并挂在场景上，编辑器才能预览、不报黄色警告。"""
    tres = ROOT / "assets" / "char" / "player_frames.tres"
    need(tres.is_file(), "缺 assets/char/player_frames.tres")
    t = tres.read_text(encoding="utf-8")
    need(t.count("ExtResource(") == 7, f"SpriteFrames 应引用 7 张帧，实为 {t.count('ExtResource(')}")
    need('"name": &"idle"' in t and '"name": &"run"' in t, "SpriteFrames 缺 idle / run 动画")
    need('"speed": 6.0' in t and '"speed": 8.0' in t, "SpriteFrames 帧率应为 idle6 / run8")
    sc = (ROOT / "scenes" / "MinimalRun.tscn").read_text(encoding="utf-8")
    need("player_frames.tres" in sc, "场景未引用 SpriteFrames 资源")
    need("sprite_frames = ExtResource" in sc, "AnimatedSprite2D 未挂 sprite_frames")
    probe = (ROOT / "scripts" / "PlayerProbe.gd").read_text(encoding="utf-8")
    need("if sprite.sprite_frames == null:" in probe, "脚本缺资源缺失兜底分支")
    builder = (ROOT / "tools" / "build_sprite_frames.gd").read_text(encoding="utf-8")
    need("ResourceSaver.save" in builder, "生成器未用引擎写出资源")
    return "player_frames.tres 由引擎生成（idle3/run4，6/8fps）并已挂场景；脚本保留兜底分支"


def c_previews_r42():
    """R42：预览画板不得留在工程根目录；previews/ 与 assets/_preview/ 都应有 .gdignore。"""
    stray = [p.name for p in ROOT.glob("*.miora")]
    need(not stray, f"工程根目录仍有 miora 画板：{stray}")
    stray_assets = [p.name for p in ROOT.glob("*_assets")]
    need(not stray_assets, f"工程根目录仍有画板素材目录：{stray_assets}")
    pre = ROOT / "previews"
    need(pre.is_dir(), "缺 previews/ 目录")
    need((pre / ".gdignore").is_file(), "previews/.gdignore 不存在")
    need((pre / ".gdignore").stat().st_size == 0, "previews/.gdignore 不是空文件")
    need(len(list(pre.glob("*.miora"))) == 3, "previews/ 应含 3 个 miora 画板")
    need((ROOT / "assets" / "_preview" / ".gdignore").is_file(), "assets/_preview/.gdignore 不存在")
    imports = list((ROOT / "assets" / "_preview").glob("*.import"))
    need(not imports, f"assets/_preview 仍有 {len(imports)} 个 .import，应由 .gdignore 排除")
    return "3 个画板已入 previews/（含空 .gdignore）；根目录无 miora / *_assets；assets/_preview 预览图 0 个 .import"


def c_probe():
    t = (ROOT / "scripts" / "PlayerProbe.gd").read_text(encoding="utf-8")
    paths = re.findall(r'"(res://assets/[^"]+\.png)"', t)
    need(len(paths) == 7, f"主角帧路径应为 idle3+run4=7，实为 {len(paths)}")
    for p in paths:
        need((ROOT / p.removeprefix("res://")).is_file(), f"缺帧：{p}")
    traces = re.findall(r"@trace[ \t]+([^\r\n#]+)", t)
    ids = sorted({tok for chunk in traces for tok in re.split(r"[\s,;]+", chunk.strip()) if tok})
    need(ids == ["DF-04", "DF-12", "DF-13", "DF-15"], f"@trace 回指不符：{ids}")
    need("sprite.scale.x" in t, "缺朝右镜像实现")
    return f"7 帧全部存在 / @trace = {','.join(ids)} / 只镜像 Sprite.scale.x"


# ---------------------------------------------------------------- 17 产物
REQUIRED = [
    "project.godot", ".gitignore", "docs/.gdignore",
    "scenes/MinimalRun.tscn", "scripts/PlayerProbe.gd",
    "tools/bootstrap_project.gd", "tools/verify_minimal_run.gd",
    "tools/build_sprite_frames.gd", "assets/char/player_frames.tres",
    "tools/build_gdd_v02.py", "tools/verify_damage_ceiling.py",
    "tools/check_traceability.py", "tools/finalize_handover.py", "tools/final_selfcheck.py",
    "docs/00-项目交接与进度.md", "docs/01-策划案.md",
    "docs/01-策划案-v0.1-baseline.md", "docs/13-Godot导入与本机配置指南.md",
    "docs/14-v0.2合并差异记录.md", "docs/15-卡牌规则层实现说明.md",
    "docs/16-网页验证层与跨端口径说明.md",
    "docs/design-freeze.json",
    "docs/damage-ceiling-report.json", "docs/traceability-report.json",
    "data/buff-card-library.json", "docs/card-runtime-data-report.json",
    "docs/card-rules-report.json", "scripts/CardDeck.gd",
    "tools/build_card_runtime_data.py", "tools/verify_card_rules.gd",
    "tools/card_rules.js", "tools/build_web_demo.py",
    "tools/verify_cross_platform.py", "tools/cross_platform_check.js",
    "tools/export_card_golden.gd", "docs/card-golden-samples.json",
    "docs/cross-platform-report.json", "previews/web-demo.html",
    "previews/web-demo-首屏截图.png", "previews/web-demo-战斗截图.png",
    "previews/web-demo-Boss战截图.png",
    "docs/17-主菜单与横版战斗网页原型.md",
    "tools/battle_sim.js", "tools/verify_battle_sim.js",
    "tools/verify_battle_sim.py", "docs/battle-sim-report.json",
    "tools/card_effects.js", "tools/verify_card_effects.js",
    "tools/verify_card_effects.py", "docs/card-effects-report.json",
    "docs/18-卡牌效果在网页战斗中的映射说明.md",
    "previews/web-demo-卡牌效果截图.png",
    "docs/godot-project-check.json", "docs/project-spec.json",
    "docs/asset-manifest-godot.json", "docs/数值框架.csv", "docs/卡牌库.csv",
    "assets/_preview/vfx-preview.html", "assets/_preview/buff-card-preview.html",
    "assets/_preview/decision-card.html", "assets/_preview/icons_final_contact_sheet.png",
    "assets/_preview/buff_cards_contact_sheet.png",
    "docs/19-UI界面设计规格与外发提示词.md",
    "previews/ui-prompts-pack.md",
    "tools/check_ui_art.py", "tools/build_ui_prompt_pack.py",
    "docs/ui-art-check-report.json",
    "scripts/BattleFormula.gd",
    "tools/export_battle_golden.gd", "docs/battle-golden-samples.json",
    "tools/cross_platform_battle_check.js", "tools/verify_battle_cross.py",
    "docs/battle-cross-report.json",
]


def c_artifacts():
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    need(not missing, f"缺产物：{missing}")
    return (f"{len(REQUIRED)} 项关键产物齐备（交接文档 / 冻结 / 工程 / 报告 / "
            f"3 个预览页 / 2 张拼图 / 卡牌规则层 / 网页验证层 / 主菜单与战斗原型）")


# ---------------------------------------------------------------- 18 绝对路径
def c_abs_paths():
    targets: list[Path] = []
    for pat in ["*.md", "*.json", "*.csv"]:
        # 两份「报告自身」排除：godot-project-check.json 写入 projectDir，
        # final-selfcheck.json 是上一轮的自检输出，避免报告自指被当成工程残留。
        targets += [p for p in DOC.glob(pat)
                    if p.name not in ("godot-project-check.json", "final-selfcheck.json")]
    targets += list((ROOT / "scripts").glob("*.gd"))
    targets += list((ROOT / "tools").glob("*.gd"))
    targets += list((ROOT / "scenes").glob("*.tscn"))
    targets += [ROOT / "project.godot", ROOT / ".gitignore"]
    needle = "/" + "Users" + "/"  # 字面量拆开，避免本脚本被自己扫成命中
    hits = []
    for p in targets:
        if not p.is_file():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if needle in line:
                hits.append(f"{p.relative_to(ROOT).as_posix()}:{i}")
    need(not hits, f"文档/工程文件残留机器绝对路径：{hits[:8]}")
    return f"扫描 {len(targets)} 个文档与工程文件，机器绝对路径命中 0（两份报告自指已排除）"


# ---------------------------------------------------------------- 19 交接状态
# ---------------------------------------------------------------- 24 工作空间迁移
def c_workspace_moved():
    """第 17 轮：工作空间迁至 ~/Documents/ai-game/ 的一致性断言。

    检查三件事：① 工程确实位于 ai-game 稳定目录下（不再在带时间戳的会话目录）；
    ② 接手指南在**工程根** `xianxia-tower/` 内且指向唯一交接入口（第 18 轮 R44：
       用户明确「不该放到 ai-game 下，那是根目录；正确要放在 ai-game/xianxia-tower 下」，
       故工作空间根 `ai-game/` 不得再有同名副本）；
    ③ 交接文档已记录第 17 轮迁移事实。
    """
    # ① 目录位置：必须在 ai-game 下，且必须是用户指定的 ~/Documents/ai-game
    need("ai-game" in ROOT.parts,
         f"工程不在 ai-game 工作空间目录下（当前：{ROOT}）")
    need(ROOT.parent.parent.name == "Documents",
         f"工作空间根目录应为 ~/Documents/ai-game（当前：{ROOT.parent}）")
    need(ROOT.parent.name == "ai-game",
         f"工作空间根目录名应为 ai-game（当前：{ROOT.parent.name}）")
    # ② 接手指南：按用户第 18 轮口径，归工程根所有，不放在工作空间根
    guide = ROOT / "README-从这里开始.md"
    need(guide.is_file(), "缺 xianxia-tower/README-从这里开始.md（换账号后的第一入口）")
    need(not (ROOT.parent / "README-从这里开始.md").is_file(),
         "工作空间根 ai-game/ 下多出同名接手指南；用户明确要求只放工程根（R44 回归）")
    g = guide.read_text(encoding="utf-8")
    for s in ["docs/00-项目交接与进度.md", "开场白", "xianxia-tower/project.godot",
              "~/Documents/ai-game/"]:
        need(s in g, f"接手指南缺关键指引：{s}")
    # ③ 交接文档记录
    t = (DOC / "00-项目交接与进度.md").read_text(encoding="utf-8")
    for s in ["第 17 轮", "~/Documents/ai-game/"]:
        need(s in t, f"交接文档缺迁移记录：{s}")
    # ④ 不得把工程指向误建的中间路径。
    #    注意：文档里「曾误建 ~/WorkBuddy/ai-game，已清理」属于如实记录历史，允许存在；
    #    只禁止把当前实际位置写成那个路径。
    stale_path = "WorkBuddy/" + "ai-game"
    for p in [guide, DOC / "00-项目交接与进度.md",
              DOC / "asset-content-manifest.json"]:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if stale_path not in line:
                continue
            # 允许：明确标注为「曾误建 / 已清理 / 已移除」的历史陈述
            if any(k in line for k in ["误建", "已清理", "曾误建", "已移除"]):
                continue
            need(False, f"{p.name}:{i} 把当前路径误写为 {stale_path}")
    return (f"工程位于 ~/Documents/ai-game/ ；接手指南在工程根 xianxia-tower/ 内（R44 用户口径），"
            f"工作空间根无重复副本，交接文档已记录第 17 轮迁移，无误建路径残留")


# ---------------------------------------------------------------- 25/26 卡牌规则层（第 18 轮）
def c_card_runtime_data():
    """R45：docs/.gdignore 让 docs/ 导出后不进包，运行时卡库必须有独立副本且与设计源一致。"""
    d = load("card-runtime-data-report.json")
    need(d.get("verdict") == "PASS", "运行时数据报告非 PASS")
    need(d.get("cards") == 72, "运行时卡库不是 72 张")
    src = json.loads((DOC / "buff-card-library.json").read_text(encoding="utf-8"))
    tgt = json.loads((ROOT / "data" / "buff-card-library.json").read_text(encoding="utf-8"))
    norm = lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    need(norm(src) == norm(tgt),
         "运行时副本与设计源语义不一致，请重跑 tools/build_card_runtime_data.py")
    need((DOC / ".gdignore").is_file(), "docs/.gdignore 缺失（R39 前提）")
    need(d.get("canonicalSha256") == __import__("hashlib").sha256(
        norm(src).encode("utf-8")).hexdigest(), "一致性报告指纹与当前设计源不符")
    return "72 张设计源 → data/ 运行时副本语义一致；docs/.gdignore 仍在（R45 链路完整）"


def c_card_rules():
    d = load("card-rules-report.json")
    need(d.get("verdict") == "PASS", "卡牌规则 headless 报告非 PASS")
    s = d.get("summary", {})
    need(s.get("failed") == 0 and s.get("total", 0) >= 20, "headless 断言未全绿")
    need(s.get("cards") == 72, "验证覆盖卡数不是 72")
    peak = float(s.get("peakDamage", 99999.0))
    need(peak <= 3996.0 and peak < 4400.0, f"全卡叠加峰值破红线：{peak}")
    need(s.get("guardEvents", 0) > 0, "上界守卫未触发，疑为空跑恒等式")
    code = (ROOT / "scripts" / "CardDeck.gd").read_text(encoding="utf-8")
    need("@trace DF-19, DF-21" in code, "CardDeck.gd 缺 DF-19/DF-21 真实回指")
    for literal in ["CAP_BASE: float = 180.0", "CAP_EXTRA_POOL: float = 600.0",
                    "CAP_REALM_RATIO: float = 1.60", "CAP_COMBO: float = 2.5",
                    "CAP_CRIT: float = 1.8"]:
        need(literal in code, f"CardDeck.gd 缺五上界常量：{literal}")
    return (f"headless {s['passed']}/{s['total']} PASS / 72 卡 / 峰值 {int(peak)} < 4400 / "
            f"守卫事件 {s['guardEvents']} 条 / @trace DF-19,DF-21")


def c_web_demo_r19():
    """第 19 轮：网页验证层 + 跨端同口径（R47）。"""
    page = ROOT / "previews" / "web-demo.html"
    need(page.is_file(), "缺 previews/web-demo.html")
    t = page.read_text(encoding="utf-8")
    for token in ("__RULES_JS__", "__BATTLE_JS__", "__EFFECTS_JS__",
                  "__LIB_JSON__", "__IMG_JSON__", "__META_JSON__"):
        need(token not in t, f"网页占位符未替换：{token}")
    need(t.count("<script>") == 2 and t.count("</script>") == 2, "网页 script 标签数异常")
    # 第 29 轮：B4 补齐后内嵌图从 159 涨到 179。精确一致性由下方
    # build_web_demo.py --check 的字节级比对保证，这里只守「不低于旧基线」，
    # 不再写死张数（与 c_qc / c_trace 的动态自洽同口径）。
    n_img = t.count("data:image/png;base64,")
    need(n_img >= 159, f"网页内嵌像素素材 {n_img} 张，低于第 20 轮基线 159")
    need(all(f'id="{k}"' in t for k in ("menu", "battle", "draft", "sprite", "codex", "status")),
         "网页缺六视图")
    # 网页内嵌的规则实现必须与 tools/card_rules.js 字节级同源（不是「照着写一份」）
    rules_js = (ROOT / "tools" / "card_rules.js").read_text(encoding="utf-8")
    need(rules_js in t, "网页内嵌规则实现与 tools/card_rules.js 不是同一份")
    need("xorshift32" in rules_js and "Math.imul" in rules_js,
         "JS 规则实现缺可跨端复刻的 R47 随机源")
    lib = json.loads((ROOT / "data" / "buff-card-library.json").read_text(encoding="utf-8"))
    need(len(lib["cards"]) == 72, "运行时卡库不是 72 张")
    ids_ok = True
    for c in lib["cards"]:
        cid = c["id"]
        if f'"id":"{cid}"' not in t:
            ids_ok = False
            break
    need(ids_ok, "网页内嵌卡库不完整")
    deck = (ROOT / "scripts" / "CardDeck.gd").read_text(encoding="utf-8")
    # 注释里会提到改前的 RandomNumberGenerator（说明性文字），故不能按「不出现该词」判定；
    # 只检查代码不再实例化引擎 PRNG，且自实现 RNG 三件套都在。
    need("xorshift32" in deck and "RandomNumberGenerator.new()" not in deck
         and "_rng_reset" in deck and "_rng_next" in deck and "_rng_randf" in deck,
         "CardDeck.gd 未换成可跨端复刻的随机源（R47）")
    cross = load("cross-platform-report.json")
    need(cross.get("verdict") == "PASS", "跨端一致性报告不是 PASS")
    s = cross.get("summary", {})
    need(s.get("total", 0) >= 25 and s.get("passed") == s.get("total") and s.get("failed") == 0,
         "跨端断言数或结果异常")
    golden = load("card-golden-samples.json")
    need(len(golden.get("cases", [])) == 5 and len(golden.get("rngSequence", [])) == 12,
         "黄金样本结构异常")
    need(golden.get("mega", {}).get("peak") == 3996.0, "黄金样本全卡叠加峰值不是 3996")
    need((ROOT / "previews" / ".gdignore").is_file(),
         "previews/ 缺 .gdignore（网页产物会被 Godot 当资源扫描，R42）")
    need((ROOT / "docs" / "16-网页验证层与跨端口径说明.md").is_file(), "缺 docs/16 增量文档")
    # 防回归：生成器与产物必须一致（改了生成器没重建会在这里 FAIL）
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_web_demo.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True)
    need(proc.returncode == 0, f"网页产物与当前源不一致：{proc.stdout.strip()[:160]}")
    return (f"网页 Demo 六视图 / {n_img} 图 / 72 卡齐备；内嵌 JS 与 R47 随机源同源；"
            f"跨端 {s['passed']}/{s['total']} PASS；黄金样本 5 局 + 12 randf")


def c_battle_demo_r20():
    """第 20 轮：主菜单 + 横版战斗网页原型（R50–R53），且不得动冻结数值 / Godot 主场景。"""
    page = ROOT / "previews" / "web-demo.html"
    t = page.read_text(encoding="utf-8")
    kernel = (ROOT / "tools" / "battle_sim.js").read_text(encoding="utf-8")
    need(kernel in t, "网页内嵌战斗内核与 tools/battle_sim.js 不是同一份")
    need("window.BattleSim" in t, "网页未挂载共享战斗内核")
    # 五上界 / Boss 红线：防止有人拿 PROPOSAL 顺手改了冻结数值
    for token in ("CAP_BASE = 180.0", "CAP_REALM_RATIO = 1.60", "CAP_EXTRA_POOL = 600.0",
                  "CAP_COMBO = 2.5", "CAP_CRIT = 1.8", "CAP_DEFENSE = 0.75",
                  "BOSS_HP_REFERENCE = 4400.0"):
        need(token in kernel, f"战斗内核冻结数值被改：{token}")
    need("n: 9, hp: 4400" in kernel and "n: 1, hp: 300" in kernel,
         "9 层波形与 docs/01 §8.3 不一致")
    need("skills 全 false 时仍执行 move" in (ROOT / "tools" / "verify_battle_sim.js").read_text(encoding="utf-8"),
         "缺 R53 输入吞 move 的防回归断言")
    report = load("battle-sim-report.json")
    need(report.get("verdict") == "PASS", "战斗内核报告不是 PASS")
    s = report.get("summary", {})
    need(s.get("total", 0) >= 44 and s.get("passed") == s.get("total") and s.get("failed") == 0,
         "战斗内核断言未全绿或数量不足 44")
    # 边界必须如实标注，不能把原型说成定稿设计 / 正式素材。
    # 第 32 轮：Boss 真帧已接入，「素材未产」不再是事实；边界改为「素材来源如实标注
    # + 未接 Godot 场景」，避免为了过断言保留一句假话。
    for token in ("Q17", "PROPOSAL", "assets/boss/", "不接 Godot 场景", "不是游戏本体"):
        need(token in t, f"网页缺边界标记：{token}")
    need("Boss 素材未产" not in t, "网页仍声称 Boss 素材未产，与实际像素源矛盾")
    need(all(x.is_file() for x in (
        ROOT / "docs" / "17-主菜单与横版战斗网页原型.md",
        ROOT / "previews" / "web-demo-战斗截图.png",
        ROOT / "previews" / "web-demo-Boss战截图.png",
        ROOT / "tools" / "verify_battle_sim.py",
    )), "第 20 轮关键产物不齐")
    cfg = (ROOT / "project.godot").read_text(encoding="utf-8")
    need('run/main_scene="res://scenes/MinimalRun.tscn"' in cfg,
         "Godot 主场景被改（第 20 轮禁止动工程）")
    scene = (ROOT / "scenes" / "MinimalRun.tscn").read_text(encoding="utf-8")
    need("CardDraftDemo" not in scene and "BattleSim" not in scene,
         "MinimalRun.tscn 被挂了网页原型节点")
    return (f"六视图含主菜单 / 横版战斗；战斗内核 {s['passed']}/{s['total']} PASS；"
            f"冻结数值与 Godot 主场景未改；R50–R52 边界如实标注")


def c_card_effects_r21():
    """第 21 轮：机制型卡在网页战斗生效（R54），不得改冻结数值 / 抽卡规则 / Godot 主场景。"""
    page = ROOT / "previews" / "web-demo.html"
    t = page.read_text(encoding="utf-8")
    effects_js = (ROOT / "tools" / "card_effects.js").read_text(encoding="utf-8")
    kernel = (ROOT / "tools" / "battle_sim.js").read_text(encoding="utf-8")
    need(effects_js in t, "网页内嵌效果编译器与 tools/card_effects.js 不是同一份")
    need(kernel in t, "网页内嵌战斗内核与 tools/battle_sim.js 不是同一份")
    for token in ("window.CardEffects", 'id="fxPanel"', "applyCardEffects",
                  "compileCardEffects", "预置机制卡组"):
        need(token in t, f"网页缺第 21 轮效果链路片段：{token}")
    need("applyCardEffects" in kernel and "emptyCardMods" in kernel,
         "战斗内核未接 EffectSet / 缺默认空效果")
    report = load("card-effects-report.json")
    need(report.get("verdict") == "PASS", "卡牌效果报告不是 PASS")
    s = report.get("summary", {})
    need(s.get("total", 0) >= 40 and s.get("passed") == s.get("total") and s.get("failed") == 0,
         "卡牌效果断言未全绿或数量不足 40")
    need(s.get("battleBoundCards") == 26, "有战斗效果的卡不是 26 张（不得凑数）")
    need(s.get("boundEntries") == 28 and s.get("deckBound") == 42 and s.get("unbound") == 59,
         "三层计数异常（battle/deck/none 应为 28/42/59）")
    need(s.get("unbound", 0) > 0 and s.get("unboundKeys", 0) >= 60,
         "未映射条目 / 理由被抹掉（不得伪称全覆盖）")
    need(s.get("specConflicts") == 1, "R54 卡面与 params 不自洽未记录")
    # 防回归：五上界 / 波形 / 抽卡随机源 / Godot 主场景一个字节都不能动
    for token in ("CAP_BASE = 180.0", "CAP_REALM_RATIO = 1.60", "CAP_EXTRA_POOL = 600.0",
                  "CAP_COMBO = 2.5", "CAP_CRIT = 1.8", "CAP_DEFENSE = 0.75",
                  "BOSS_HP_REFERENCE = 4400.0"):
        need(token in kernel, f"第 21 轮误改冻结数值：{token}")
    deck = (ROOT / "scripts" / "CardDeck.gd").read_text(encoding="utf-8")
    need("xorshift32" in deck and "RandomNumberGenerator.new()" not in deck,
         "抽卡随机源被改（R47 黄金样本会失效）")
    lib = json.loads((ROOT / "data" / "buff-card-library.json").read_text(encoding="utf-8"))
    # 注意：卡库 status 一直是「PROPOSAL · 数值待实测」说明文字，不是 frozen；
    # 冻结的是结构红线（五上界 / 共享池），本轮只读卡库，不得改 72 张卡或状态口径。
    need(len(lib["cards"]) == 72 and "PROPOSAL" in lib.get("status", ""),
         "卡库被改（本轮只读，不得改 72 张卡或 PROPOSAL 状态口径）")
    cfg = (ROOT / "project.godot").read_text(encoding="utf-8")
    need('run/main_scene="res://scenes/MinimalRun.tscn"' in cfg, "Godot 主场景被改")
    doc = (ROOT / "docs" / "18-卡牌效果在网页战斗中的映射说明.md").read_text(encoding="utf-8")
    for token in ("不是平衡结论", "不迁移到 Godot 实机", "R54", "26 / 72",
                  "不猜数值", "不可迁移到实机"):
        need(token in doc, f"docs/18 缺边界标记：{token}")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_web_demo.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True)
    need(proc.returncode == 0, f"网页产物与当前源不一致：{proc.stdout.strip()[:160]}")
    return (f"卡牌效果 {s['passed']}/{s['total']} PASS；26/72 张生效 / 三层 28-42-59 如实分列；"
            f"R54 已记录；冻结数值 / 抽卡规则 / Godot 主场景未改")


def c_ui_prompt_r22():
    """第 22 轮：UI 设计外发提示词包 + 回稿体检脚本；不得改冻结文档 / Godot 工程。"""
    doc_path = DOC / "19-UI界面设计规格与外发提示词.md"
    need(doc_path.is_file(), "缺 docs/19-UI界面设计规格与外发提示词.md")
    doc = doc_path.read_text(encoding="utf-8")
    blocks = re.findall(r"<!--PROMPT:([a-z]+):(zh|en)-->", doc)
    need(len(blocks) == 18, f"docs/19 提示词区块应为 18 段，实际 {len(blocks)}")
    need(len({b[0] for b in blocks}) == 9, "docs/19 提示词覆盖的界面数不是 9 个")
    for token in ("24 色锁定板", "#12161F", "#E8DFC8", "#5FA8A0", "#C8453B", "#D9A441",
                  "禁止", "回稿验收", "PROPOSAL", "Q17", "R9", "R50", "R51",
                  "参考稿", "冻结", "提案"):
        need(token in doc, f"docs/19 缺关键口径：{token}")
    # 提示词包必须与源文档严格一致（由生成器搬运，不手改）
    pack = ROOT / "previews" / "ui-prompts-pack.md"
    need(pack.is_file(), "缺 previews/ui-prompts-pack.md")
    need(pack.read_text(encoding="utf-8").count("```text") == 18,
         "提示词包代码块数量不是 18")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_ui_prompt_pack.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True)
    need(proc.returncode == 0, f"提示词包与 docs/19 不一致：{proc.stdout.strip()[:160]}")
    # 体检脚本必须从冻结色板源取色，不得写死色值
    chk = (ROOT / "tools" / "check_ui_art.py").read_text(encoding="utf-8")
    need("asset-manifest-pixel.json" in chk, "体检脚本未从冻结色板源取色")
    need("#12161F" not in chk and "#E8DFC8" not in chk, "体检脚本写死了色值（应读冻结色板）")
    need("OUT_OF_PALETTE_DIST" in chk and "semi_transparent" in chk,
         "体检脚本缺少越界色 / 半透明检查项")
    # 冻结文档与 Godot 工程一个字节都不能动
    cfg = (ROOT / "project.godot").read_text(encoding="utf-8")
    need('run/main_scene="res://scenes/MinimalRun.tscn"' in cfg, "Godot 主场景被改")
    scene = (ROOT / "scenes" / "MinimalRun.tscn").read_text(encoding="utf-8")
    need("BattleFormula" not in scene and "CardDraftDemo" not in scene,
         "第 22 轮禁止把新脚本挂进 MinimalRun.tscn")
    return "docs/19 18 段中英提示词 + 提示词包一致 + 回稿体检脚本就绪；冻结文档 / Godot 工程未改"


def c_battle_cross_r22():
    """第 22 轮：战斗「公式层」Godot ↔ 网页跨端一致；不得改冻结数值 / 抽卡规则。"""
    gd = (ROOT / "scripts" / "BattleFormula.gd")
    need(gd.is_file(), "缺 scripts/BattleFormula.gd")
    gdt = gd.read_text(encoding="utf-8")
    for token in ("CAP_BASE := 180.0", "CAP_REALM_RATIO := 1.60", "CAP_EXTRA_POOL := 600.0",
                  "CAP_COMBO := 2.5", "CAP_CRIT := 1.8", "CAP_DEFENSE := 0.75",
                  "BOSS_HP_REFERENCE := 4400.0"):
        need(token in gdt, f"Godot 公式镜像缺冻结常量：{token}")
    need("damage_formula" in gdt and "max_hit" in gdt, "Godot 公式镜像接口缺失")
    golden = load("battle-golden-samples.json")
    need(len(golden.get("cases", [])) >= 52, "战斗黄金样本用例不足 52 条")
    need(golden.get("maxHit") == 3996, "黄金样本 maxHit 不是 3996")
    need(len(golden.get("stages", [])) == 9 and len(golden.get("skillsFrozen", [])) == 4,
         "黄金样本缺 9 层波形 / 4 技能冻结字段")
    rep = load("battle-cross-report.json")
    need(rep.get("verdict") == "PASS", "战斗跨端报告不是 PASS")
    s = rep.get("summary", {})
    need(s.get("total", 0) >= 8 and s.get("passed") == s.get("total") and s.get("failed") == 0,
         "战斗跨端断言未全绿或数量不足 8")
    need("逐 tick 状态机" in rep.get("scope", ""),
         "跨端报告未如实标注「不含逐 tick 状态机」")
    # 冻结数值 / 抽卡随机源 / Godot 主场景一个字节都不能动
    kernel = (ROOT / "tools" / "battle_sim.js").read_text(encoding="utf-8")
    for token in ("CAP_BASE = 180.0", "CAP_REALM_RATIO = 1.60", "CAP_EXTRA_POOL = 600.0",
                  "CAP_COMBO = 2.5", "CAP_CRIT = 1.8", "CAP_DEFENSE = 0.75",
                  "BOSS_HP_REFERENCE = 4400.0"):
        need(token in kernel, f"第 22 轮误改冻结数值：{token}")
    deck = (ROOT / "scripts" / "CardDeck.gd").read_text(encoding="utf-8")
    need("xorshift32" in deck and "RandomNumberGenerator.new()" not in deck,
         "抽卡随机源被改（R47 黄金样本会失效）")
    cfg = (ROOT / "project.godot").read_text(encoding="utf-8")
    need('run/main_scene="res://scenes/MinimalRun.tscn"' in cfg, "Godot 主场景被改")
    return (f"战斗公式层跨端 {s['passed']}/{s['total']} PASS；52 条黄金样本逐条一致；"
            f"maxHit 3996 < Boss 4400；不含逐 tick 状态机已如实标注；冻结数值未改")


def c_handover():
    t = (DOC / "00-项目交接与进度.md").read_text(encoding="utf-8")
    stale = [
        "当前唯一阻塞已换成「用户整体确认策划案」",
        "阶段一覆盖率 **0 为预期**",
        "尚未并入 `01` §15（R30）",
        "9. **仍可推进但不依赖 Q1 的活**",
    ]
    for s in stale:
        need(s not in t, f"仍残留过期状态：{s}")
    required = [
        "第 15 轮当前状态（换账号先看这一段）",
        "GUI 按 F5 目检仍需用户做",
        "docs/final-selfcheck.json",
        "R39",
        "R41",
        "R42",
        "第 15 轮收口（全量自检",
        "第 16 轮（用户首次在 GUI 打开工程",
        "状态口径（第 15 轮）",
    ]
    for s in required:
        need(s in t, f"缺当前状态标记：{s}")
    need(t.count("✅ 第 15 轮已处置") >= 4, "R27–R30 的已处置标记不足 4 处")
    need("13. **全量自检可复跑**" in t, "§9 缺自检复跑条目")
    return "4 类过期状态已清除；当前状态 / R39 / R41 / R42 / 收口段 / 状态口径 / 17 处修正全部就位"


# ---------------------------------------------------------------- 20 R39
def c_gdignore():
    p = DOC / ".gdignore"
    need(p.is_file() and p.stat().st_size == 0, "docs/.gdignore 不存在或不是空文件")
    junk = [f.name for f in DOC.iterdir()
            if f.is_file() and (f.suffix == ".translation" or f.name.endswith(".csv.import"))]
    need(not junk, f"仍有引擎误生成文件：{junk}")
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    need("docs/*.translation" in gi and "docs/*.csv.import" in gi, ".gitignore 缺 R39 兜底规则")
    return "空 .gdignore 就位 / 24 个生成物已清理 / .gitignore 双行兜底"


# ---------------------------------------------------------------- 32 第 29 轮素材
def c_assets_r29():
    """第 29 轮三块素材四方一致：报告 ↔ 磁盘 ↔ 引擎 JSON ↔ 生成器 / 目检页。

    第 30 轮补：本自检保持「零第三方依赖」，像素级层带检查由
    tools/build_bg_layers.py（带 Pillow）复算并写进报告，这里只核对报告与 --check。
    """
    b = load("b3b4-build-report.json")
    g = load("bg-layers-report.json")
    q = load("qc-report.json")
    bt, gt = b["totals"], g["totals"]
    vfx_total = sum(x["frameCount"] for x in q["groups"]
                    if str(x["id"]).startswith("vfx_"))

    need(bt["outOfPaletteTotal"] == 0 and bt["semiAlphaTotal"] == 0,
         "B3/B4 报告存在越界色或半透明")
    need(gt["outOfPaletteTotal"] == 0 and gt["semiAlphaTotal"] == 0,
         "背景层报告存在越界色或半透明")
    need(gt["bandStrayTotal"] == 0,
         f"背景层带外不透明像素 {gt['bandStrayTotal']}，四层不能独立切图")
    need(gt["l4Under10PercentAll"], "背景 L4 前景占比 >=10%")
    # 第 31 轮口径修正：R22 是「回稿文件亮度代理」，不是实机对比度实测。
    # 默认入库改为原稿保真（不替用户改配色）后，代理值可能如实超过 30%。
    # 这里不再把它当硬门禁，改为核对「报告如实复算 + 未达标项显式登记」：
    # 既不伪造 PASS，也不因高保真原稿误判整条资产链失败。
    disc = g.get("r22Disclosure") or {}
    need(disc.get("shippedMode") in ("faithful", "tuned"),
         "背景报告缺 r22Disclosure.shippedMode，无法确认入库色阶模式")
    for s in g["scenes"]:
        measured = s["combatZone"]["darkPixelRatio"]
        need(abs(s["combatDarkRatioShipped"] - measured) < 0.02,
             f"{s['scene']} 报告的入库 R22 值与复算不一致")
        need(s["combatDarkUnder30Percent"] == (measured < 0.30),
             f"{s['scene']} 的 R22 达标标记与复算不一致（疑似伪造 PASS）")
    need(gt["combatDarkUnder30PercentAll"] == all(
        s["combatDarkUnder30Percent"] for s in g["scenes"]),
        "背景 R22 汇总标记与各场景不一致")
    if not gt["combatDarkUnder30PercentAll"]:
        need(bool(disc.get("knownExceptions")),
             "背景存在 R22 未达标场景，但报告未登记 knownExceptions")
        need(set(disc["knownExceptions"]) == {
            s["scene"] for s in g["scenes"] if not s["combatDarkUnder30Percent"]},
             "R22 knownExceptions 与实际未达标场景不一致")
    need(gt["layers"] == 16 and gt["scenes"] == 4, "背景层不是 4 场景 x 4 层")

    def count(d, pattern, expected, label):
        n = len(list((ROOT / d).glob(pattern)))
        need(n == expected, f"{label} 实际 {n} 张 != 期望 {expected}")

    count("assets/boss", "boss_*_r_*.png", bt["bossFrames"], "Boss 帧")
    count("assets/vfx/frames", "vfx_*_[0-9][0-9].png", vfx_total, "技能特效帧")
    count("assets/vfx/overlay", "ovl_*_[0-9][0-9].png", bt["overlayFrames"], "overlay 帧")
    count("assets/bg", "**/*.png", gt["layers"] + gt["composites"], "背景图")

    for d in ("assets/boss", "assets/vfx/frames", "assets/vfx/overlay"):
        for jp in sorted((ROOT / d).glob("*.json")):
            if jp.name.endswith("_report.json"):
                continue
            e = json.loads(jp.read_text(encoding="utf-8"))
            need(e["frameCount"] == len(e["frames"]), f"{jp.name} frameCount 与 frames 不一致")
            need(all((jp.parent / n).is_file() for n in e["frames"]), f"{jp.name} 有缺失帧")
            need(e.get("status") == "待目检与合规确认；不得直接入库",
                 f"{jp.name} 的待目检状态被改写")

    for s in g["scenes"]:
        sid = s["scene"]
        folder = ROOT / "assets/bg" / sid
        ej = folder / f"{sid}.json"
        need(ej.is_file(), f"{sid} 缺层清单")
        e = json.loads(ej.read_text(encoding="utf-8"))
        need(e["layerSize"] == [480, 270] and len(e["layers"]) == 4,
             f"{sid} 层尺寸 / 层数不符")
        need(e.get("status") == "待目检与合规确认；不得直接入库", f"{sid} 状态被改写")
        for lv in ("L1", "L2", "L3", "L4"):
            need((folder / f"{sid}_{lv}.png").is_file(), f"{sid}_{lv} 缺失")
        need((folder / f"{sid}_composite.png").is_file(), f"{sid} 缺合成图")

    page = ROOT / "previews/asset-overview.html"
    need(page.is_file(), "缺 previews/asset-overview.html")
    t = page.read_text(encoding="utf-8")
    need(t.count("<script>") == 1 and t.count("</script>") == 1, "目检页 script 标签异常")
    need("__IMG_JSON__" not in t and "__META_JSON__" not in t, "目检页占位符未替换")
    n_img = t.count("data:image/png;base64,")
    expect_imgs = (bt["bossFrames"] + vfx_total + bt["overlayFrames"]
                   + gt["layers"] + gt["composites"])
    need(n_img == expect_imgs, f"目检页内嵌 {n_img} 图，与素材合计 {expect_imgs} 不符")
    for token in ("/Users/", "/home/", "C:\\"):
        need(token not in t, "目检页含机器绝对路径")

    for tool in ("build_b3b4_assets.py", "build_bg_layers.py",
                 "build_asset_overview.py"):
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / tool), "--check"],
                              cwd=ROOT, capture_output=True, text=True)
        need(proc.returncode == 0,
             f"{tool} --check 失败：{(proc.stdout + proc.stderr).strip()[:160]}")

    return (f"B3 {bt['bossFrames']} 帧 / B4 {bt['vfxFrames'] + bt['overlayFrames']} 帧 / "
            f"背景 {gt['layers']} 层（带外像素 0 / 越界色 0）；目检页 {n_img} 图；"
            "三个生成器 --check 全 PASS")


def c_ui_reference_r31():
    """第 31 轮：gpt-image2 回稿是否真的被当像素源用掉（防「全部丢掉重画」复发）。

    第 29/30 轮把 docs/03 §4「AI 直出整图不算入库」错误扩大成几何重绘，一张
    回稿都没读；本项把「源稿覆盖率」变成机器可复算的硬断言。
    """
    r = load("ui-reference-assets-report.json")
    t = load("reference-transcription-report.json")
    cov = r["sourceCoverage"]
    all_pal = sorted((ROOT / "previews/ui").glob("*_palette24.png"))
    need(len(all_pal) == cov["palette24Total"],
         f"palette24 回稿实际 {len(all_pal)} 张 != 报告 {cov['palette24Total']}")
    need(cov["usedByRound31"] == len(all_pal) - 1 and len(cov["unusedSources"]) == 1,
         "本轮取用数 / 未取用数不自洽")
    need(cov["unusedSources"][0].endswith("A2-bgrest-gpt-image2_palette24.png")
         and cov.get("unusedReason"),
         "唯一未取用源稿不是已登记理由的 A2 旧版")
    for s in r["sourceFiles"] + t["sourceFiles"]:
        need((ROOT / s).is_file(), f"转录报告引用的源稿缺失：{s}")
    need(len(r["sourceFiles"]) == 9 and r["counts"]["sources"] == 9,
         "UI 九张源稿未被全部纳入")
    need(r["counts"]["outOfPaletteTotal"] == 0, "UI 派生资产存在越界色")

    mf = json.loads((ROOT / "assets/ui/reference/ui_reference_manifest.json")
                    .read_text(encoding="utf-8"))
    need(len(mf["files"]) == r["counts"]["files"], "UI 清单条目数与报告不一致")
    for e in mf["files"]:
        need((ROOT / "assets/ui/reference" / e["file"]).is_file(),
             f"UI 派生文件缺失：{e['file']}")
        need(e.get("status") == "待目检与合规确认；不得直接入库",
             f"{e['file']} 的待目检状态被改写")

    # 新目录不得反客为主：冻结的 47 图标 / 10 卡面契约保持不变
    need(len(list((ROOT / "assets/ui/icons").glob("*.png"))) == 47,
         "assets/ui/icons 的 47 个冻结图标被改动")
    need(len(list((ROOT / "assets/ui/cards").glob("*.png"))) == 10,
         "assets/ui/cards 的 10 张卡面被改动")

    # 主转录脚本必须真的读回稿，而不是又写一遍几何绘制
    src = (ROOT / "tools/build_from_reference_art.py").read_text(encoding="utf-8")
    need("def load_ref(" in src and "previews" in src,
         "主转录脚本未读取 previews/ui 回稿（疑似退回几何重绘）")
    b = load("b3b4-build-report.json")
    g = load("bg-layers-report.json")
    need("gpt-image2" in b["pipeline"], "B3/B4 报告未声明回稿来源")
    need("gpt-image2" in g["pipeline"], "背景报告未声明回稿来源")

    page = ROOT / "previews/ui-reference-overview.html"
    need(page.is_file(), "缺 UI 参考稿目检页")
    txt = page.read_text(encoding="utf-8")
    need(txt.count("data:image/png;base64,") == r["counts"]["files"],
         "UI 目检页内嵌图数与派生资产数不一致")
    for token in ("/Users/", "/home/", "C:\\"):
        need(token not in txt, "UI 目检页含机器绝对路径")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools/build_ui_reference_assets.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True)
    need(proc.returncode == 0,
         f"UI 资产生成器 --check 失败：{(proc.stdout + proc.stderr).strip()[:160]}")

    return (f"17 张 palette24 回稿取用 16 张（A2 旧版被 A2R 取代且已登记）；"
            f"UI 派生 {r['counts']['files']} 张 / 越界色 0；"
            "冻结 47 图标 + 10 卡面未替换")


def c_web_reference_art_r32():
    """第 32 轮：gpt-image2 回稿转录资源是否真的进了网页验证层的战斗画面。

    第 31 轮的资源只躺在 assets/ 与静态目检页里；本项同时防两种回归：
    ① 网页仍用第 20 轮的 CSS 山影 + 剑魂帧占位；② 只改文案、不接真实像素字节。
    """
    import base64

    page = ROOT / "previews" / "web-demo.html"
    need(page.is_file(), "缺 previews/web-demo.html")
    t = page.read_text(encoding="utf-8")

    for token in ('id="bBgArt"', 'id="artToggle"', "function setArtMode",
                  "function applyStageBg", "function bossFrameKey",
                  "art=placeholder", "art-ref", "bg_normal"):
        need(token in t, f"网页缺原稿素材模式标记：{token}")
    need("assets/boss/ 为空" not in t, "网页仍写 Boss 素材缺失（R50 未解除）")
    need("第 32 轮已解除" in t, "R50 未标注已处置")
    need("Boss 素材未产，用 " not in t, "战斗日志仍写「Boss 素材未产」，与画面矛盾")

    boss = sorted((ROOT / "assets/boss").glob("*.png"))
    ovl = sorted((ROOT / "assets/vfx/overlay").glob("*.png"))
    bg = [ROOT / f"assets/bg/bg_{s}/bg_{s}_composite.png"
          for s in ("normal", "rest", "high", "boss")]
    need(len(boss) >= 42 and len(ovl) == 10 and all(p.is_file() for p in bg),
         "回稿转录资源本身不齐")

    def b64(p: Path) -> str:
        return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")

    # 逐字节核对：内嵌的必须是磁盘上的真实转录 PNG，不是几何重绘或占位图
    for p in bg + [boss[0], boss[-1], ovl[0], ovl[-1]]:
        need(b64(p) in t, f"网页未内嵌真实字节：{p.relative_to(ROOT)}")
    n_img = t.count("data:image/png;base64,")
    need(n_img >= 159 + len(boss) + len(ovl) + 4,
         f"网页内嵌图 {n_img} 张，未覆盖第 20 轮基线 + 全部转录资源")

    # 浏览器内实时自检不得再写死 vfx=16（第 29 轮起已是 36 帧）
    need("nVfx >= 16" in t and "length === 16, 'char 15 / mob 60 / vfx 16'" not in t,
         "浏览器内实时自检仍写死 vfx 16 帧")
    need("原稿素材模式与旧占位模式可切换" in t, "浏览器内实时自检缺第 32 轮模式断言")

    res = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_web_demo.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True)
    need(res.returncode == 0, f"build_web_demo.py --check 失败：{res.stdout[-200:]}")

    return (f"网页默认原稿模式 / 内嵌 {n_img} 图（Boss {len(boss)} + overlay {len(ovl)} + bg 4 "
            "+ 第 33 轮 UI 设计稿对照 9 张）；R50 已解除、实时自检动态化、--check 一致")


def c_ui_skin_r33():
    """第 33 轮：9 张 gpt-image2 UI 设计稿是否真的进了网页验证层（按视图联动对照）。

    同时防两种回归：① 只改文案、不接真图；② 把含写死示例数值的设计稿贴进
    可交互界面冒充真实组件（会出现「显示值与规则值不一致」的假数值）。
    """
    import base64

    page = ROOT / "previews" / "web-demo.html"
    need(page.is_file(), "缺 previews/web-demo.html")
    t = page.read_text(encoding="utf-8")

    for token in ('id="uiSkinBar"', 'id="uiSkinImg"', 'id="uiSkinSelect"',
                  'id="uiSkinToggle"', "function setUiSkin",
                  "function applyUiSkinForTab", "const UI_SKINS",
                  "const SKIN_BY_TAB", "ui=off",
                  "applyUiSkinForTab(currentTab)"):
        need(token in t, f"网页缺 UI 设计稿对照层标记：{token}")

    # 边界必须如实标注：设计稿含示例数值，只作对照，不得冒充入库组件 / 实机数值
    for token in ("示例文字与写死数值", "不作实机数值", "Q17 未拍板",
                  "候选资产", "不接 Godot 场景", "R55"):
        need(token in t, f"网页缺设计稿对照边界标注：{token}")
    need("UI 设计稿对照 9 张内嵌齐备" in t and "设计稿按六视图联动映射完整" in t,
         "浏览器内实时自检缺第 33 轮两条断言")

    ui_dir = ROOT / "assets" / "ui" / "reference"
    manifest = json.loads((ui_dir / "ui_reference_manifest.json").read_text(encoding="utf-8"))
    panels = [e["file"] for e in manifest["files"] if e.get("kind") == "panel16x9"]
    need(len(panels) == 9, f"UI 设计稿 16:9 底板不是 9 张：{len(panels)}")

    def b64(p: Path) -> str:
        return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")

    for name in panels:
        p = ui_dir / name
        stem = p.stem
        need(p.is_file() and b64(p) in t, f"网页未内嵌 UI 设计稿真实字节：{name}")
        need(f"'{stem}'" in t, f"UI_SKINS 缺条目：{stem}")

    # 六视图 -> 设计稿的对位是规格，逐项核对；04/05/06 三张稿只在下拉里出现
    expected_map = {
        "menu": "ui_01-mainmenu_panel", "battle": "ui_02-towerhud_panel",
        "draft": "ui_03-draft_panel", "sprite": "ui_00-anchor_panel",
        "codex": "ui_07-codex_panel", "status": "ui_08-icons_panel",
    }
    for tab, key in expected_map.items():
        need(f"{tab}: '{key}'" in t, f"设计稿按视图联动映射不符：{tab} -> {key}")

    for script, label in (("build_web_demo.py", "网页产物"),
                          ("build_ui_reference_assets.py", "UI 派生资产")):
        res = subprocess.run(
            [sys.executable, str(ROOT / "tools" / script), "--check"],
            cwd=ROOT, capture_output=True, text=True)
        need(res.returncode == 0, f"{label} --check 失败：{res.stdout[-200:]}")

    return (f"9 张 UI 设计稿逐字节内嵌 / 六视图联动 / 开关与边界齐备；"
            "浏览器实时自检 +2 条；网页与 UI 派生资产 --check 一致")


# ---------------------------------------------------------------- 36 第 34–35 轮 / R57 + R58
def c_card_art_r34():
    plan = load("card-art-plan.json")
    cards = plan.get("cards", [])
    need(len(cards) == 72, f"独立插画映射不是 72 张：{len(cards)}")

    rows = read_csv("卡牌库.csv", 15)[1:]
    csv_ids = [r[0] for r in rows]
    need([c["id"] for c in cards] == csv_ids, "映射表 ID / 顺序与冻结卡库不一致")

    for key in ("motif", "motifEn", "silhouette", "signature", "outputName"):
        vals = [c[key] for c in cards]
        need(len(set(vals)) == 72, f"一卡一母题被破坏：{key} 不是 72 个唯一值")
    need(all(c["signature"] == "|".join(
        (c["motif"], c["silhouette"], c["composition"], c["focalBand"])) for c in cards),
        "signature 不是由母题/剪影/构图/主色段复算得出")

    by_cat: dict[str, list[dict]] = {}
    for c in cards:
        by_cat.setdefault(c["category"], []).append(c)
    need(sorted(by_cat) == ["attr", "dmg", "mech", "res", "surv", "syn"],
         "类别分组不是 6 类")
    for cat, group in by_cat.items():
        need(len(group) == 12, f"{cat} 不是 12 张：{len(group)}")
        need(len({g["silhouette"] for g in group}) == 12,
             f"{cat} 类内剪影重复，三选一会撞脸")
        need(all(len(g["excludes"]) == 2 for g in group),
             f"{cat} 有卡缺「不得画成」排除项")

    stats = plan["stats"]
    need(stats["artReceived"] + stats["artPending"] == 72,
         "回稿计数不自洽（不得伪造 72/72）")
    art_dir = ROOT / "previews" / "card_art"
    received = sorted(p.name for p in art_dir.glob(
        "*-cardart-original.png")) if art_dir.is_dir() else []
    need(stats["artReceived"] == len(received), "单卡原稿计数与磁盘不一致")
    need(stats["sheetsReceived"] + stats["sheetsPending"] == 6,
         "拼版回稿计数不自洽（不得伪造 6/6）")
    sheet_dir = ROOT / "previews" / "card_art_sheets"
    sheets_on_disk = sorted(p.name for p in sheet_dir.glob("sheet-*.png")) if sheet_dir.is_dir() else []
    need(stats["sheetsReceived"] == len(sheets_on_disk), "拼版回稿计数与磁盘不一致")
    need(all(c["status"] == "待外发 · 未回稿 · 候选资产；不得直接入库" for c in cards),
         "有卡被标成已入库")

    anchors = plan["styleAnchors"]
    need(len(anchors) == 4 and all("gpt-image2" in a for a in anchors),
         "风格锚点不是 4 张用户 gpt-image2 回稿")
    need(anchors[0] == "previews/ui/07-codex-gpt-image2_original.png",
         "07-codex 图鉴原稿不是第一风格基准（用户审美基准）")
    for a in anchors:
        need((ROOT / a).is_file(), f"风格锚点原稿缺失：{a}")
    need(stats["codexSampleCoverage"] == 16
         and len({c["codexRef"] for c in cards}) == 16,
         "07-codex 16 个画法样板未 16/16 全覆盖")
    need(all(c["codexRefTechnique"] and c["codexRefTechniqueEn"]
             and c["codexRefSample"] for c in cards),
         "有卡缺 07-codex 画法样板描述")

    spec = plan["sheetSpec"]
    need(spec["sheetCount"] == 6 and spec["cellsPerSheet"] == 12
         and spec["generations"] == 6, "拼版规格不是 6 张 × 12 格 / 6 次生成")
    need(spec["sheetSize"] == [1536, 1024] and spec["grid"] == [3, 4]
         and spec["cellSize"] == [512, 256] and spec["cropSize"] == [384, 256]
         and spec["cropPadX"] == 64, "拼版尺寸 / 裁切框不符合第 35 轮规格")
    need(len(plan["sheets"]) == 6
         and [s["cellCount"] for s in plan["sheets"]] == [12] * 6,
         "6 张 sheet 不是各 12 格")
    need(len({(c["sheetIndex"], c["cellLabel"]) for c in cards}) == 72,
         "72 个拼版格位不唯一")
    need(all(c["sheetFile"] == f"sheet-{c['sheetIndex']:02d}.png" for c in cards),
         "卡与 sheet 文件名不一致")
    need(all(c["cropBox"][2] - c["cropBox"][0] == 384
             and c["cropBox"][3] - c["cropBox"][1] == 256 for c in cards),
         "裁切框尺寸不是 384×256")

    pack = (ROOT / "previews" / "card-art-prompts-pack.md").read_text(encoding="utf-8")
    need(pack.count(":zh -->") == 6 and pack.count(":en -->") == 6,
         "外发提示词包不是 6 组中文 + 6 组英文")
    for token in ("禁止出现任何文字", "24 色锁定板", "不得直接入库", "Q17",
                  "【12 格逐格清单", "不得画成", "【命名】", "6 次生成", "3 列 × 4 行"):
        need(token in pack, f"提示词包缺规格/边界：{token}")

    # ---- 第 36 轮：风格基准改回 07-codex 克制画法（R59） ----
    for token in ("第 36 轮风格更正", "做减法", "SUBTRACT, DO NOT ADD", "#12161F",
                  "45–60%", "45-60%", "安静、克制", "每格最多 2–4 枚",
                  "16 张里只有「聚灵阵」「太虚咒」", "不要沿用旧版提示词",
                  "【参考图使用边界 · 严禁照抄示意卡主体】", "唯一的内容依据"):
        need(token in pack, f"提示词包缺第 36 轮克制风格规格：{token}")
    for bad in ("多数格用一个圆形或双层圆环法阵", "每格四角与四周散布 4–8 枚菱形小星点",
                "most cells wrap the subject", "Circular arrays and corner star points ARE"):
        need(bad not in pack, f"提示词包仍残留旧华丽徽章口径：{bad}")

    # ---- 第 37 轮：参考图不得压过母题清单（R60） ----
    for token in ("第 37 轮内容更正", "严禁照抄示意卡主体",
                  "REFERENCE USAGE BOUNDARY - DO NOT COPY THE SAMPLE CARD SUBJECTS",
                  "本拼版唯一的内容依据", "12-CELL LIST - THE ONLY CONTENT SPEC",
                  "NEVER COPY THE REFERENCE", "只借鉴该张的线条密度、留白比例与色阶节奏",
                  "16 张示意卡的任何一张搬进本拼版"):
        need(token in pack, f"提示词包缺第 37 轮参考图边界规格：{token}")
    for bad in ("原稿 16 张插画绝大多数是「一个符号直接放在墨底上」——螺旋气旋",
                "In the reference, most of the 16 cards are simply one emblem placed directly "
                "on the ink ground - spiral",
                "画法样板只取主体形态与线条密度", "STYLE SAMPLES BORROW ONLY THE SUBJECT SHAPE"):
        need(bad not in pack, f"提示词包仍残留会被照抄的主体名列举/样板描述：{bad}")
    need(pack.count("【参考图使用边界 · 严禁照抄示意卡主体】") == 7
         and pack.count("REFERENCE USAGE BOUNDARY - DO NOT COPY THE SAMPLE CARD SUBJECTS") == 7,
         "第 37 轮参考图边界不是 §0 + 6 组各内嵌一次")
    # 12 组代码块内不得出现任何参考稿示意卡的具体主体描述
    import importlib.util
    spec_mod = importlib.util.spec_from_file_location("cap", ROOT / "tools" / "build_card_art_plan.py")
    cap = importlib.util.module_from_spec(spec_mod); spec_mod.loader.exec_module(cap)
    parts = pack.split("<!-- sheet-")[1:]
    for _pos, _sample, tech, tech_en in cap.CODEX_SAMPLES.values():
        need(all(tech not in q and tech_en not in q for q in parts),
             "逐格清单代码块仍含参考稿示意卡主体描述，会被 AI 照抄")
    # 7 = §0 单列的通用规格 1 次 + 6 组各自内嵌 1 次
    need(pack.count("【风格第一基准 · 必须照此画】") == 7
         and pack.count("SUBTRACT, DO NOT ADD") == 7
         and pack.count("【最重要 · 做减法】") == 7,
         "6 组提示词不是每组都内嵌克制风格基准（含 §0 单列应为 7 次）")

    overview = (ROOT / "previews" / "card-art-plan-overview.html").read_text(encoding="utf-8")
    need(overview.count("data-search=") == 72 and overview.count('class="group"') == 6,
         "72 母题核对页不是 6 组 / 72 行")
    need("不得直接入库" in overview and "Q17" in overview,
         "母题核对页缺边界标注")
    need("07-codex 画法样板（第一基准）" in overview
         and all(f">{k}<" in overview for k in ("r1c1", "r2c1", "r3c1", "r4c1")),
         "母题核对页缺 07-codex 画法样板列")
    need("sheet-01.png" in overview and "sheet-06.png" in overview
         and "裁 64,0" in overview,
         "母题核对页缺拼版格位 / 裁切框列")

    # 冻结文档与 10 张卡面必须原样不动 —— 本轮只是提案，不是替换。
    spec12 = (DOC / "12-卡牌UI规格.md").read_text(encoding="utf-8")
    need("72 张卡只需要 4 张卡框 + 6 张纹样共" in spec12,
         "docs/12 §5 冻结口径被改写（Q17 前不得改）")
    frozen = sorted(p.name for p in (ROOT / "assets" / "ui" / "cards").glob("*.png"))
    need(len(frozen) == 10, f"冻结 10 张卡面被替换或增删：{len(frozen)}")

    doc27 = (DOC / "27-72卡独立插画设计决议与外发规格.md").read_text(encoding="utf-8")
    for token in ("R57", "R58", "R59", "Q17", "不得直接入库", "不替换", "24 色", "不产图",
                  "第一基准", "16/16", "07-codex", "6 次生成", "拼版", "克制", "留白",
                  "--adaptive", "289/534/779", "R60", "第 37 轮"):
        need(token in doc27, f"决议文档缺边界：{token}")

    split_tool = ROOT / "tools" / "split_card_art_sheets.py"
    need(split_tool.is_file(), "缺拼版裁剪脚本 tools/split_card_art_sheets.py")
    split_src = split_tool.read_text(encoding="utf-8")
    need("--adaptive" in split_src and "def detect_boundaries" in split_src
         and "def adaptive_boxes" in split_src and "def crop_with_pad" in split_src,
         "裁剪脚本缺第 36 轮自适应格位探测能力")
    for extra in (["--check"], ["--adaptive", "--check"]):
        res = subprocess.run([sys.executable, str(split_tool), *extra],
                             cwd=ROOT, capture_output=True, text=True)
        need(res.returncode == 0,
             f"裁剪脚本 {' '.join(extra)} 失败：{res.stdout[-200:]} {res.stderr[-200:]}")
    report = load("card-art-split-report.json")
    need(report["outputsTotal"] == 72 and len(report["outputs"]) == 72,
         "裁剪报告不是 72 条格位→输出名映射")
    need(report["sheetSpec"] == spec, "裁剪报告与映射表 sheetSpec 不一致")
    need(report["status"] == "待目检与合规确认；不得直接入库",
         "裁剪报告状态被标成已入库")
    need("adaptive" in report and all("usedBox" in o for o in report["outputs"]),
         "裁剪报告缺 adaptive 模式标记 / usedBox 实际使用框")

    res = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_card_art_plan.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True)
    need(res.returncode == 0,
         f"提示词生成器 --check 失败：{res.stdout[-200:]} {res.stderr[-200:]}")

    return (f"6 张拼版 / 6 次生成 / 72 格位与裁切框一一对应 / 72 卡母题·签名·剪影唯一 / "
            f"6 组中英提示词（第 36 轮克制风格 + 第 37 轮参考图边界/唯一内容依据）+ 72 行核对页 / "
            f"07-codex 原稿第一基准且 16/16 画法样板全覆盖 / "
            f"裁剪器 fixed + --adaptive 双 --check 通过 / 回稿 {stats['sheetsReceived']}/6 与 "
            f"{stats['artReceived']}/72 如实披露 / docs/12 与 10 张冻结卡面原样未动")


def c_card_art_integration_r39() -> str:
    """第 39 轮：6 组回稿 → 72 张 84×56 → 网页验证层 / Godot 卡面组件接入。"""
    import struct

    def png_size(p: Path) -> tuple[int, int]:
        with p.open("rb") as fh:
            head = fh.read(24)
        need(head[:8] == b"\x89PNG\r\n\x1a\n", f"{p.name} 不是 PNG")
        return struct.unpack(">II", head[16:24])

    imp = load("card-art-integration-report.json")
    need(imp["sheetsReceived"] == 6 and len(imp["outputs"]) == 6,
         "导入报告不是 6/6 拼版")
    need(imp["groupToSheet"] == {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6},
         "A–F → sheet-01..06 映射被改动")
    need(any(e["sheet"] == 2 and "1024" in e["reason"] for e in imp["knownExceptions"]),
         "B 组 1024×1024 尺寸例外未如实记录")
    for o in imp["outputs"]:
        p = ROOT / o["file"]
        need(p.is_file() and png_size(p) == (1536, 1024),
             f"{o['file']} 缺失或不是 1536×1024")

    tr = load("card-art-transcript-report.json")
    need(tr["cardsTotal"] == 72 and tr["cardsOnDisk"] == 72
         and tr["offPaletteTotal"] == 0 and tr["artSize"] == [84, 56],
         "转录报告不是 72/72 张 84×56 且色板外颜色 0")
    art_dir = ROOT / "assets" / "ui" / "card_art"
    lib = json.loads((ROOT / "data" / "buff-card-library.json").read_text(encoding="utf-8"))
    ids = [c["id"] for c in lib["cards"]]
    need(len(ids) == 72 and len(set(ids)) == 72, "运行时卡库不是 72 张唯一 id")
    files = sorted(p.name for p in art_dir.glob("*.png"))
    need(files == sorted(f"{i}.png" for i in ids),
         "assets/ui/card_art/ 的 72 个文件名与卡库 id 不逐一对位")
    for name in files:
        need(png_size(art_dir / name) == (84, 56), f"{name} 不是 84×56")

    html = (ROOT / "previews" / "web-demo.html").read_text(encoding="utf-8")
    need(html.count('class="cardart"') == 3 and "IMG[c.id]" in html,
         "web-demo 缺一卡一插画的 cardart 图层或按 id 取值")
    need(all(f'"{cid}":"data:image/png;base64,' in html for cid in ids),
         "web-demo 未内嵌全部 72 张插画")
    need(".card .cardart{position:absolute;left:6px;top:19px;width:84px;height:56px" in html,
         "web-demo 插画区定位不是 docs/12 §2 的 x6/y19/84×56")
    for extra in (["--check"],):
        res = subprocess.run([sys.executable, str(ROOT / "tools" / "build_web_demo.py"), *extra],
                             cwd=ROOT, capture_output=True, text=True)
        need(res.returncode == 0,
             f"build_web_demo.py --check 失败：{res.stdout[-200:]} {res.stderr[-200:]}")

    gd = (ROOT / "scripts" / "CardArtView.gd").read_text(encoding="utf-8")
    need("class_name CardArtView" in gd and "assets/ui/card_art/" in gd
         and "func show_card(" in gd and "TEXTURE_FILTER_NEAREST" in gd,
         "Godot 卡面组件缺动态按 card_id 载入 / 最近邻过滤")
    tscn = (ROOT / "scenes" / "CardArtView.tscn").read_text(encoding="utf-8")
    need("CardArtView.gd" in tscn and 'card_id = "card_jianfeng"' in tscn,
         "CardArtView.tscn 未挂脚本或缺示例卡 id")
    godot = (ROOT / "project.godot").read_text(encoding="utf-8")
    need('run/main_scene="res://scenes/MinimalRun.tscn"' in godot,
         "主场景被改动（第 39 轮只新增示例场景，不接管 F5）")
    frozen = sorted(p.name for p in (ROOT / "assets" / "ui" / "cards").glob("*.png"))
    need(len(frozen) == 10, f"冻结 10 张卡面被替换或增删：{len(frozen)}")
    need(imp["status"] == tr["status"] == "待目检与合规确认；不得直接入库",
         "集成报告状态被标成已入库")

    return ("6 组回稿按母题核对落盘 sheet-01..06（B 组 1:1 无损重排）/ "
            "72 张 384×256 原稿 → 24 色吸附 → 72 张 84×56 插画且色板外颜色 0 / "
            "web-demo 三选一卡面按 card_id 内嵌并绘制 / Godot CardArtView 组件与示例场景就位 / "
            "主场景、冻结 10 张卡面、数值与规则均未动")


def c_codex_frame_r40() -> str:
    """第 40 轮：07-codex 风格卡框候选 + 文字排版修复，冻结基线不许动。"""
    import hashlib
    import struct

    sys.path.insert(0, str(ROOT / "tools"))
    from snap_ui_palette import load_palette

    def png_size(p: Path) -> tuple[int, int]:
        with p.open("rb") as fh:
            head = fh.read(24)
        need(head[:8] == b"\x89PNG\r\n\x1a\n", f"{p.name} 不是 PNG")
        return struct.unpack(">II", head[16:24])

    rep = load("codex-card-frames-report.json")
    need(rep["round"] == 40 and rep["size"] == [96, 144]
         and rep["paletteSize"] == len(load_palette()),
         "候选卡框报告轮次 / 尺寸 / 色板数不对")
    need(rep["status"] == "待目检与合规确认；不得直接入库"
         and rep["noTextInPng"] is True,
         "候选卡框状态被标成已入库，或 PNG 内被写入文字")
    need(len(rep["frames"]) == 4 and rep["cardsCombo"] == 72,
         "候选卡框不是 4 档 / 整卡预览不是 72 张")
    for f in rep["frames"]:
        p = ROOT / f["file"]
        need(p.is_file() and png_size(p) == (96, 144), f"{f['file']} 缺失或不是 96×144")
        need(hashlib.sha256(p.read_bytes()).hexdigest() == f["sha256"],
             f"{f['file']} 与报告 sha256 不一致")

    # 冻结基线：10 张卡面 sha256 逐张比对，候选不得覆盖
    frozen_dir = ROOT / "assets" / "ui" / "cards"
    now = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(frozen_dir.glob("*.png"))}
    need(now == rep["frozenCardAssetsSha256"] and len(now) == 10,
         "冻结 10 张卡面被候选卡框覆盖或增删")
    spec = (ROOT / "docs" / "12-卡牌UI规格.md").read_text(encoding="utf-8")
    need("72 张卡只需要 4 张卡框 + 6 张纹样共 **10 张小图**" in spec,
         "docs/12 §2 冻结口径被改写（第 40 轮只允许出候选，不许改规格）")

    html = (ROOT / "previews" / "web-demo.html").read_text(encoding="utf-8")
    for token in ("frame=frozen", "codex_frame_", "applyFrameModeLabel",
                  "btnFrameMode", "wrapMeasure", "card.codex .cname",
                  "冻结卡面 10 张与规格一个字节未改"):
        need(token in html, f"web-demo 缺第 40 轮片段：{token}")
    for r in ("common", "rare", "legend", "curse"):
        need(f'"codex_frame_{r}":"data:image/png;base64,' in html,
             f"web-demo 未内嵌候选卡框 {r}")
    need("white-space:pre" in html and "measureText" in html,
         "折行修复（像素测量 + 禁止二次折行）未落地")

    for name in ("codex-frames-4tiers.png", "card-art-full-cards-codex.png",
                 "card-frame-frozen-vs-codex.png",
                 "web-demo-frame-codex-zoom.png", "web-demo-frame-frozen-zoom.png"):
        need((ROOT / "assets" / "_preview" / name).is_file(), f"缺目检预览 {name}")
    need((ROOT / "assets" / "_preview" / "card-art-full-cards.png").is_file(),
         "第 39 轮旧整卡预览被覆盖（基线不覆盖纪律）")

    for script in ("build_codex_card_frames.py", "build_web_demo.py"):
        res = subprocess.run([sys.executable, str(ROOT / "tools" / script), "--check"],
                             cwd=ROOT, capture_output=True, text=True)
        need(res.returncode == 0,
             f"{script} --check 失败：{res.stdout[-200:]} {res.stderr[-200:]}")

    return ("4 档 07-codex 候选卡框 96×144 / 色板外颜色 0 / PNG 无文字 / "
            "冻结 10 张卡面与 docs/12 §2 逐字节未动 / "
            "网页 ?frame=codex|frozen 双模式 + canvas 像素测量折行 / "
            "5 张目检预览齐备 / 两个生成器 --check 通过")


def main() -> None:
    check("json_parse", "docs/*.json 全部可解析", c_json)
    check("csv_numbers", "数值源 9 列、无 BOM、无空行、含 round15", c_nums)
    check("csv_cards", "卡牌 CSV 15 列 / 73 行", c_cards)
    check("python_compile", "tools/*.py 全部编译通过", c_py)
    check("freeze_authoritative", "权威冻结清单 frozen / 22 条 DF", c_freeze)
    check("freeze_draft", "draft 仍为历史快照且有失效说明", c_draft)
    check("receipt", "决策回执 16/16、硬门禁 4/4", c_receipt)
    check("damage_ceiling", "R32 五上界 / 3996 < 4400", c_damage)
    check("card_library", "72 张卡 + 3 张卡 pool/cap 声明", c_cards_lib)
    check("godot_project_check", "工程结构自检错误 0", c_project_check)
    check("traceability", "追溯核对 PASS / 覆盖率动态自洽", c_trace)
    check("qc_report", "全量素材 SHIP（帧数动态自洽）", c_qc)
    check("icon_catalog", "47 图标 + 4 挂件 / pending 0", c_icons)
    check("project_config", "project.godot 像素与输入配置", c_project_cfg)
    check("minimal_scene", "MinimalRun.tscn 节点树", c_scene)
    check("player_probe", "主角 7 帧路径 + @trace 回指", c_probe)
    check("artifacts", "关键产物齐备", c_artifacts)
    check("absolute_paths", "文档/工程无机器绝对路径", c_abs_paths)
    check("stale_handover", "交接文档过期状态已清除", c_handover)
    check("gdignore_r39", "R39 的 .gdignore 与兜底规则", c_gdignore)
    check("collision_r41", "R41 主角碰撞体与真实地面", c_collision_r41)
    check("previews_r42", "R42 预览画板归位与 .gdignore", c_previews_r42)
    check("frames_tres_r43", "R43 SpriteFrames 资源化并挂场景", c_frames_tres)
    check("workspace_moved_r17", "R17 工作空间已迁至 ai-game 且接手指南在工程根", c_workspace_moved)
    check("card_runtime_data_r45", "R45 运行时卡库副本与设计源一致", c_card_runtime_data)
    check("card_rules_r18", "卡牌规则层 headless 23 项 + 五上界守卫", c_card_rules)
    check("web_demo_r19", "R47 网页验证层 + 跨端同口径 25 项", c_web_demo_r19)
    check("battle_demo_r20", "第 20 轮主菜单 / 横版战斗原型 + 战斗内核 44 项", c_battle_demo_r20)
    check("card_effects_r21", "第 21 轮机制型卡映射 + R54 口径 + 40 项断言", c_card_effects_r21)
    check("ui_prompt_r22", "第 22 轮 UI 外发提示词包（18 段中英）+ 回稿体检脚本", c_ui_prompt_r22)
    check("battle_cross_r22", "第 22 轮战斗公式层 Godot ↔ 网页跨端（52 条黄金样本 / 8 项断言）", c_battle_cross_r22)
    check("assets_r29", "第 29 轮三块素材报告 / 磁盘 / 目检页四方一致（第 30 轮补）", c_assets_r29)
    check("ui_reference_r31", "第 31 轮 gpt-image2 回稿源覆盖率（17 取 16）+ UI 派生资产一致", c_ui_reference_r31)
    check("web_reference_art_r32", "第 32 轮回稿转录资源接入网页战斗画面（真实字节 / R50 解除 / 自检动态化）", c_web_reference_art_r32)
    check("ui_skin_r33", "第 33 轮 9 张 UI 设计稿按视图联动对照（逐字节 / 边界 / 六视图映射）", c_ui_skin_r33)
    check("card_art_r34", "第 34–37 轮 72 卡独立插画（6 组拼版 / 克制风格 / 参考图边界 / 自适应裁剪 / 冻结口径未动）", c_card_art_r34)
    check("card_art_integration_r39", "第 39 轮 6 组回稿集成（导入标准化 / 72 张 84×56 / 网页卡面 / Godot 组件 / 冻结口径未动）", c_card_art_integration_r39)
    check("codex_frame_r40", "第 40 轮 07 风格卡框候选 + 文字排版修复（4 档 96×144 / 双模式对照 / 冻结基线逐字节未动）", c_codex_frame_r40)

    passed = sum(1 for c in CHECKS if c["status"] == "PASS")
    failed = len(CHECKS) - passed
    report = {
        "version": 1,
        "generatedAt": date.today().isoformat(),
        "generator": "tools/final_selfcheck.py",
        "scope": "第 15 轮收口 · 交付前全量静态自检",
        "verdict": "PASS" if failed == 0 else "FAIL",
        "summary": {"checks": len(CHECKS), "passed": passed, "failed": failed},
        "checks": CHECKS,
        "knownExceptions": [
            "docs/godot-project-check.json 的 projectDir 由检查器写入机器绝对路径，属报告自指；不属工程文件残留，按纪律保留警告不抑制。",
            "docs/final-selfcheck.json 是本脚本的上一次输出，绝对路径扫描时排除自身以免自指；其 detail 文案也不写绝对路径字面量。",
            "冻结条目覆盖率由 check_traceability.py 动态给出（第 18/19 轮为 6/22 = 27.27%），是最小验证工程的真实进度，不塞 @trace 标记凑数。",
            "docs/design-freeze-draft.json 的 notTheRealFreeze 字段仍写「清单尚不存在」，是第 10 轮历史描述；按基线不覆盖原则保留，以 round15Freeze 的失效说明为准。",
            "docs/decision-receipt.json 的 status=received-not-applied 是脚本语义（回执本身不是执行结果）；实际落地证据见 docs/10 状态更新与 01 v0.2。",
        ],
        "dynamicRecheck": [
            "python3 tools/verify_damage_ceiling.py",
            "python3 tools/check_traceability.py",
            "check_godot_project.py . --spec docs/project-spec.json --freeze docs/design-freeze.json --json docs/godot-project-check.json",
            "Godot --headless --script tools/verify_minimal_run.gd（须先由编辑器导入资源）",
        ],
        "boundary": "本脚本只做离线/静态验证。像素硬边、朝右镜像、480×270×4 对齐、阴兵对比度等仍需用户按 docs/13 §12 在 GUI 按 F5 目检；PASS 不等于游戏可玩。",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for c in CHECKS:
        print(f"{c['status']:4} | {c['id']:22} | {c['detail']}")
    print(f"VERDICT|{report['verdict']}|checks={len(CHECKS)}|passed={passed}|failed={failed}")
    raise SystemExit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
