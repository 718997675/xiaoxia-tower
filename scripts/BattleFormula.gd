extends RefCounted
## 战斗「公式层」Godot 侧镜像（第 22 轮）
##
## 目的：让 Godot 侧也能给出与网页 / Node 完全一致的伤害结算证据。
## 本文件只镜像 **docs/01 §8.1 冻结口径** 与只读数据表，**不含任何新数值**。
##
## 对应实现：tools/battle_sim.js（浏览器 / Node 共用）
## 跨端证据：tools/export_battle_golden.gd → docs/battle-golden-samples.json
##            tools/cross_platform_battle_check.js 复算比对
##
## 边界：
##   - 本文件是「公式 + 数据表」镜像，**不是战斗状态机**；逐 tick 结算仍未跨端对齐。
##   - 技能 CD / 灵力消耗 / 玩家 HP / 敌人伤害等 PROPOSAL 占位**不镜像**，
##     因为它们是网页演示节奏用的未定值（docs/17 §4），镜像过去等于把占位伪装成规格。
##
## 工程纪律：4 空格缩进、禁用 Tab、全公开函数/变量标注类型。

# ---------- 冻结口径（docs/01 §8.1，不得改） ----------
const CAP_BASE := 180.0
const CAP_REALM_RATIO := 1.60
const CAP_EXTRA_POOL := 600.0
const CAP_COMBO := 2.5
const CAP_CRIT := 1.8
const CAP_DEFENSE := 0.75
const BOSS_HP_REFERENCE := 4400.0
const DMG_MIN := 1
const DMG_MAX := 9999

# ---------- 表现口径（docs/01 §9） ----------
const LOGICAL_W := 480
const LOGICAL_H := 270
const GROUND_Y := 216
const FRAME_SIZE := 64
const TICK := 1.0 / 30.0


## 与 battle_sim.js 的 clampf 同语义：先取上界再取下界。
static func clampf(v: float, lo: float, hi: float) -> float:
    return min(max(v, lo), hi)


## docs/01 §8.1 统一伤害公式（乘性结构）。
## 计算顺序与 battle_sim.js 逐字对应：raw = (b*r + p) * c * cr * (1 - d)
## 返回 {damage:int, negative:bool, clamped:bool}
static func damage_formula(base: float, realm: float, pool: float, combo: float,
        crit: float, defense: float) -> Dictionary:
    var negative: bool = (base < 0.0 or realm < 0.0 or pool < 0.0
            or combo < 0.0 or defense < 0.0)
    var b := clampf(base, 0.0, CAP_BASE)
    var r := clampf(realm, 0.0, CAP_REALM_RATIO)
    var p := clampf(pool, 0.0, CAP_EXTRA_POOL)
    var c := clampf(combo, 0.0, CAP_COMBO)
    var cr := clampf(crit, 0.0, CAP_CRIT)
    var d := clampf(defense, 0.0, CAP_DEFENSE)
    var raw: float = (b * r + p) * c * cr * (1.0 - d)
    var dmg := int(clampf(round(raw), float(DMG_MIN), float(DMG_MAX)))
    var clamped: bool = (b != base or r != realm or p != pool or c != combo
            or cr != crit or d != defense)
    return {"damage": dmg, "negative": negative, "clamped": clamped}


## 五上界最坏口径（目标不减伤）：Boss 4400 需 2 次命中。
static func max_hit() -> int:
    var res := damage_formula(CAP_BASE, CAP_REALM_RATIO, CAP_EXTRA_POOL,
            CAP_COMBO, CAP_CRIT, 0.0)
    return int(res["damage"])


## 9 层难度波形（docs/01 §8.3 逐行照抄）。
static func stages() -> Array:
    return [
        {"n": 1, "hp": 300, "dps": 10, "t": 39, "d": 1.00, "type": "教学", "mobs": ["mob_shanxiao"]},
        {"n": 2, "hp": 480, "dps": 14, "t": 45, "d": 1.15, "type": "常规", "mobs": ["mob_shanxiao", "mob_zhi_kui"]},
        {"n": 3, "hp": 440, "dps": 16, "t": 36, "d": 0.92, "type": "喘息", "mobs": ["mob_shanxiao", "mob_zhi_kui"]},
        {"n": 4, "hp": 700, "dps": 20, "t": 46, "d": 1.18, "type": "常规", "mobs": ["mob_yin_bing"]},
        {"n": 5, "hp": 920, "dps": 24, "t": 50, "d": 1.28, "type": "挑战", "mobs": ["boss_judge", "mob_shanxiao"]},
        {"n": 6, "hp": 780, "dps": 28, "t": 36, "d": 0.92, "type": "喘息", "mobs": ["mob_shanxiao", "mob_yin_bing"]},
        {"n": 7, "hp": 1150, "dps": 34, "t": 44, "d": 1.13, "type": "常规", "mobs": ["mob_shanxiao", "mob_zhi_kui", "mob_yin_bing", "mob_jian_hun"]},
        {"n": 8, "hp": 1160, "dps": 42, "t": 36, "d": 0.92, "type": "喘息", "mobs": ["mob_zhi_kui", "mob_jian_hun"]},
        {"n": 9, "hp": 4400, "dps": 55, "t": 104, "d": 2.67, "type": "塔主 Boss", "mobs": ["boss_tower_lord"]},
    ]


## 4 技能槽的**冻结字段**镜像（docs/06 §4 技能 ID / 名称 / VFX / 方向）。
## cd / spirit / base / reach / hits 是 PROPOSAL 占位，**不镜像**（见文件头边界说明）。
static func skills_frozen() -> Array:
    return [
        {"id": "sword_qi", "name": "剑气斩", "key": "J", "kind": "attack", "vfx": "vfx_sword_qi", "shape": "横向弯月弧"},
        {"id": "thunder_talisman", "name": "引雷符", "key": "K", "kind": "attack", "vfx": "vfx_thunder_talisman", "shape": "纵向落雷"},
        {"id": "dan_fire", "name": "三昧丹火", "key": "L", "kind": "attack", "vfx": "vfx_dan_fire", "shape": "圆形火团"},
        {"id": "rejuvenation", "name": "回春诀", "key": "I", "kind": "heal", "vfx": "vfx_rejuvenation", "shape": "环形青玉光晕"},
    ]
