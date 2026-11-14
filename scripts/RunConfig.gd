class_name RunConfig
extends RefCounted

## 第 41 轮 · Godot 可玩原型的「数值边界」集中地。
##
## 纪律（与 tools/battle_sim.js 头注释一致）：
##   - 冻结数值一律不在这里重定义，只读引用 BattleFormula.stages() / damage_formula()。
##   - 本文件所有 PLAYER_* / SKILLS / MOBS / ENEMY_* 常量都是 PROPOSAL 占位，
##     与 tools/battle_sim.js 的 PROPOSAL / SKILLS / MOBS 同源，仅供原型跑得起来，
##     **不是冻结规格、不是平衡结论、不得写进任何设计文档当作已定值**（R51 / docs/17 §4）。
##   - 第 40 轮 07 风格卡框是「候选 / 不得直接入库」，本原型一律用 assets/ui/cards/
##     的冻结卡框 + assets/ui/card_art/ 的 72 张插画，不引用 previews/card_frames_codex/。
##   - 逐 tick 状态机仍未跨端对齐（R56）；本原型只保证 Godot 侧自洽，不宣称与网页同帧。
## 缩进：本工程统一 4 空格，禁用 Tab。

const BattleFormula = preload("res://scripts/BattleFormula.gd")

const LOGICAL_W: int = 480
const LOGICAL_H: int = 270
const GROUND_Y: float = 216.0

# 24 色锁定板（tools/snap_ui_palette.py）中的取用色；只用于 UI 绘制，不生成新色。
const C_INK := Color(0.070588, 0.086275, 0.121569)        # #12161F
const C_SLATE := Color(0.164706, 0.192157, 0.250980)      # #2A3140
const C_BLUEGRAY := Color(0.290196, 0.333333, 0.407843)   # #4A5568
const C_STONE := Color(0.541176, 0.509804, 0.407843)      # #8A8268
const C_PAPER := Color(0.909804, 0.874510, 0.784314)      # #E8DFC8
const C_PAPER_DIM := Color(0.788235, 0.749020, 0.639216)  # #C9BFA3
const C_JADE := Color(0.372549, 0.658824, 0.627451)       # #5FA8A0
const C_JADE_LIGHT := Color(0.607843, 0.831373, 0.800000) # #9BD4CC
const C_GOLD := Color(0.850980, 0.643137, 0.254902)       # #D9A441
const C_GOLD_LIGHT := Color(0.949020, 0.815686, 0.537255) # #F2D089
const C_CINNABAR := Color(0.784314, 0.270588, 0.231373)   # #C8453B
const C_CINNABAR_DARK := Color(0.478431, 0.141176, 0.125490) # #7A2420
const C_VIOLET := Color(0.541176, 0.435294, 0.768627)     # #8A6FC4
const C_BLACK := Color(0.0, 0.0, 0.0)
const C_WHITE := Color(1.0, 1.0, 1.0)

# ---------- PROPOSAL 占位（策划案未给值，待设计确认） ----------
const PLAYER_MAX_HP: float = 300.0
const PLAYER_MAX_SPIRIT: float = 100.0
const PLAYER_MAX_STAMINA: float = 100.0
const SPIRIT_REGEN: float = 9.0
const STAMINA_REGEN: float = 12.0
const MOVE_SPEED: float = 96.0
const CAST_LOCK: float = 0.18
const CRIT_CHANCE: float = 0.10
const COMBO_GAIN_PER_HIT: float = 0.08
const COMBO_DECAY: float = 0.12
const DODGE_COST: float = 25.0
const DODGE_INVULN: float = 0.42
const DODGE_SPEED: float = 190.0
const ENEMY_ATTACK_BASE: float = 9.0
const ENEMY_ATTACK_PER_STAGE: float = 3.2
const ENEMY_ATTACK_INTERVAL: float = 1.9
const ENEMY_MOVE_SPEED: float = 42.0
const ENEMY_ATTACK_RANGE: float = 88.0
const VFX_LIFETIME: float = 0.28

# 4 技能槽：id / name / key / vfx / direction 来自 docs/06 §4 冻结字段；
# cd / spirit / base / reach / hits / heal 全部 PROPOSAL（battle_sim.js 同源）。
const SKILLS: Array = [
    {"id": "sword_qi", "name": "剑气斩", "key": "J", "action": "skill_1", "kind": "attack",
     "vfx": "vfx_sword_qi", "cd": 0.8, "spirit": 6.0, "base": 20.0, "reach": 104.0, "hits": 1},
    {"id": "thunder_talisman", "name": "引雷符", "key": "K", "action": "skill_2", "kind": "attack",
     "vfx": "vfx_thunder_talisman", "cd": 2.4, "spirit": 16.0, "base": 46.0, "reach": 168.0, "hits": 2},
    {"id": "dan_fire", "name": "三昧丹火", "key": "L", "action": "skill_3", "kind": "attack",
     "vfx": "vfx_dan_fire", "cd": 1.6, "spirit": 12.0, "base": 34.0, "reach": 132.0, "hits": 2},
    {"id": "rejuvenation", "name": "回春诀", "key": "I", "action": "skill_4", "kind": "heal",
     "vfx": "vfx_rejuvenation", "cd": 6.0, "spirit": 20.0, "base": 0.0, "reach": 0.0, "hits": 0,
     "heal": 60.0},
]

# 怪物行为（docs/06 §5），defense / speed 是网页演示用的 PROPOSAL 占位。
const MOBS: Dictionary = {
    "mob_shanxiao": {"name": "山魈", "defense": 0.10, "speed": 0.85},
    "mob_zhi_kui": {"name": "纸傀", "defense": 0.05, "speed": 0.75},
    "mob_yin_bing": {"name": "阴兵", "defense": 0.20, "speed": 0.95},
    "mob_jian_hun": {"name": "剑魂", "defense": 0.15, "speed": 1.45},
    "boss_judge": {"name": "锁血判官", "defense": 0.30, "speed": 0.80, "boss": true},
    "boss_tower_lord": {"name": "天梯之主", "defense": 0.30, "speed": 1.00, "boss": true},
}


## 输入映射按 docs/01 §6：A/D 或 ←/→ 移动、J/K/L/I 四技能、Space 闪避、Esc 暂停。
## 不写进 project.godot（避免改动门禁工程配置），运行时补齐缺失的 action。
static func ensure_actions() -> void:
    var defs: Dictionary = {
        "skill_1": [KEY_J], "skill_2": [KEY_K], "skill_3": [KEY_L], "skill_4": [KEY_I],
        "dodge": [KEY_SPACE], "pause": [KEY_ESCAPE],
    }
    for action in defs.keys():
        if InputMap.has_action(action):
            continue
        InputMap.add_action(action)
        for code in defs[action]:
            var ev := InputEventKey.new()
            ev.physical_keycode = int(code)
            InputMap.action_add_event(action, ev)


## R46 / R9：引擎内置字体不含 CJK，headless 取不到系统字体。
## 这里只用 SystemFont 运行时调用本机系统字体（**不打包任何字体资产、不碰 R9 授权**），
## GUI 下用于中文可读；导出跨端时仍需另解，明确标注为待核实项。
static func make_cjk_theme() -> Theme:
    var t := Theme.new()
    t.default_font_size = 10
    # R46：SystemFont 在 headless 取不到系统字体，会刷一屏 FreeType 空字体报错。
    # 无头校验只需结构与状态，不需要字形，因此这里直接返回默认主题。
    if DisplayServer.get_name() == "headless":
        return t
    var f := SystemFont.new()
    f.font_names = PackedStringArray([
        "PingFang SC", "Heiti SC", "Songti SC", "Noto Sans CJK SC",
        "Microsoft YaHei", "WenQuanYi Micro Hei", "sans-serif",
    ])
    t.default_font = f
    return t


## 层型 → 已转录的 gpt-image2 背景合成图（docs/25，480×270）。
static func bg_path(stage_type: String) -> String:
    var key: String = "bg_normal"
    if stage_type == "喘息":
        key = "bg_rest"
    elif stage_type == "挑战":
        key = "bg_high"
    elif stage_type.find("Boss") >= 0:
        key = "bg_boss"
    return "res://assets/bg/" + key + "/" + key + "_composite.png"


## 怪物真帧目录：Boss 在 assets/boss/，其余在 assets/enemy/（docs/22 / docs/24）。
static func mob_prefix(mob_id: String) -> String:
    if mob_id.begins_with("boss_"):
        return "res://assets/boss/" + mob_id
    return "res://assets/enemy/" + mob_id


static func stage_data(index: int) -> Dictionary:
    var all: Array = BattleFormula.stages()
    return all[clampi(index, 0, all.size() - 1)]


static func stage_count() -> int:
    return BattleFormula.stages().size()
