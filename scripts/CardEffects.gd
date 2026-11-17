class_name CardEffects
extends RefCounted

## 第 42 轮 · 卡牌「非五上界」机制效果编译器（Godot 实机侧）。
##
## 口径来源：tools/card_effects.js（网页验证层，第 21 轮，44/44 回归）。本脚本是它逐字段、
## 逐卡特例的 GDScript 移植，保证「网页验证通过 → Godot 实机一致」可复算（R47 / R56 的口径）。
##
## 严格边界（docs/18 / docs/30 / R54 / R64，不得省略）：
##   - 只读卡库 data/buff-card-library.json 的 cards[].params / hook / type；不改卡库、
##     不改冻结数值、不碰五上界（base_damage / realm_ratio / extra_pool / combo_multiplier /
##     crit_multiplier / defense_rate 归 CardDeck.gd + BattleFormula.gd，本脚本不重复实现）。
##   - 只映射语义明确的键；需设计确认 / 归局外系统 / 无对应系统的键一律不进 mods，不猜数值。
##   - CAPS 是网页验证层的安全上界（防飘字/数值失控），不是游戏平衡值；全部 PROPOSAL / 待实测。
##   - 本脚本产出的是「可玩原型的表现层口径」，不是 docs/01 冻结规格，不是平衡结论。
##   - 逐 tick 状态机仍未跨端对齐（R56）：本脚本只保证 mods 编译结果一致，不代表逐帧一致。
##
## 默认 mods 全 0 / 全 1，与 card_effects.js defaultMods() 逐字段一致；
## 不选任何卡时 StageView 行为与第 41 轮完全相同（20/20 基线不回退）。

const LIB_PATH: String = "res://data/buff-card-library.json"

# 与 card_effects.js CAPS 逐字段一致（网页验证层安全上界，非平衡值）。
const CAPS: Dictionary = {
    "segments": 4,
    "pierceDefense": 0.30,
    "shieldMax": 160.0,
    "cdScaleMin": 0.50,
    "spiritCostMin": 0.30,
    "spiritOnKill": 20.0,
    "spiritOnHit": 6.0,
    "spiritOnHurt": 8.0,
    "hpMaxDelta": 120.0,
    "spiritMaxDelta": 60.0,
    "moveSpeedBonus": 0.50,
    "hurtInvuln": 0.60,
    "critRateBonus": 0.30,
    "damageTakenMin": 0.50,
    "flatReduce": 20.0,
    "freeCastUses": 3,
    "reviveHp": 0.30,
}

# 20 个 fields，顺序与 card_effects.js defaultMods() 一致（黄金样本逐字段比对用）。
const MOD_KEYS: Array[String] = [
    "segmentRatios", "pierceDefense", "shieldMax", "cdScale", "spiritCostScale",
    "freeCastOnFull", "spiritOnKill", "spiritOnHit", "spiritOnHurt",
    "hpMaxFlat", "hpMaxRatio", "spiritMaxFlat", "spiritMaxRatio",
    "moveSpeedBonus", "hurtInvuln", "critRateBonus", "damageTakenScale",
    "flatReduce", "reviveHp", "reveal",
]

var _cards: Array = []
var _by_id: Dictionary = {}


func _init(lib_path: String = LIB_PATH) -> void:
    var f := FileAccess.open(lib_path, FileAccess.READ)
    if f == null:
        push_error("CardEffects 打不开卡库：" + lib_path)
        return
    var parsed: Variant = JSON.parse_string(f.get_as_text())
    if parsed is Dictionary:
        _cards = (parsed as Dictionary).get("cards", []) as Array
    for c in _cards:
        if c is Dictionary and (c as Dictionary).has("id"):
            _by_id[String((c as Dictionary)["id"])] = c


func is_loaded() -> bool:
    return not _by_id.is_empty()


func card_count() -> int:
    return _cards.size()


static func default_mods() -> Dictionary:
    return {
        "segmentRatios": [1.0],
        "pierceDefense": 0.0,
        "shieldMax": 0.0,
        "cdScale": 1.0,
        "spiritCostScale": 1.0,
        "freeCastOnFull": false,
        "spiritOnKill": 0.0,
        "spiritOnHit": 0.0,
        "spiritOnHurt": 0.0,
        "hpMaxFlat": 0.0,
        "hpMaxRatio": 0.0,
        "spiritMaxFlat": 0.0,
        "spiritMaxRatio": 0.0,
        "moveSpeedBonus": 0.0,
        "hurtInvuln": 0.0,
        "critRateBonus": 0.0,
        "damageTakenScale": 1.0,
        "flatReduce": 0.0,
        "reviveHp": 0.0,
        "reveal": false,
    }


## 按已选卡 id 序列（可重复=堆叠）编译 EffectSet；结果与 card_effects.js 逐字段一致。
func compile(picked_ids: Array) -> Dictionary:
    var mods := default_mods()
    var seen: Dictionary = {}
    for raw_id in picked_ids:
        var id := String(raw_id)
        if not _by_id.has(id):
            continue
        var c: Dictionary = _by_id[id]
        var p: Dictionary = c.get("params", {})
        for key in p.keys():
            _apply_battle_key(mods, String(key), p[key], c)
    return mods


## 单张卡的编译结果（验证脚本逐卡比对用）。
func compile_one(card_id: String) -> Dictionary:
    return compile([card_id])


## 返回该 id 的卡数据（只读），不存在返回空字典。
func card_data(card_id: String) -> Dictionary:
    return _by_id.get(card_id, {}) as Dictionary


# ---------------------------------------------------------------- 逐键映射（对齐 BATTLE_MAP）
func _apply_battle_key(m: Dictionary, key: String, raw: Variant, c: Dictionary) -> void:
    var id := String(c.get("id", ""))
    var p: Dictionary = c.get("params", {})
    match key:
        "split":
            var n: int = clampi(int(round(float(raw))), 1, int(CAPS["segments"]))
            m["segmentRatios"] = _equal_ratios(n)
        "hits":
            if not _truthy(p.get("split_total", false)):
                return
            var n: int = clampi(int(round(float(raw))), 1, int(CAPS["segments"]))
            m["segmentRatios"] = _equal_ratios(n)
        "extra_hit":
            var arr: Array = m["segmentRatios"]
            if arr.size() < int(CAPS["segments"]):
                arr.append(clampf(float(raw), 0.05, 1.0))
                m["segmentRatios"] = arr
        "pierce_defense":
            if _truthy(p.get("affix", false)):
                return  # 五行逆克只对「铁壁」词缀生效，词缀系统未建
            m["pierceDefense"] = clampf(float(m["pierceDefense"]) + float(raw),
                0.0, float(CAPS["pierceDefense"]))
        "shield_max":
            m["shieldMax"] = clampf(float(m["shieldMax"]) + float(raw), 0.0, float(CAPS["shieldMax"]))
        "skill_cd":
            m["cdScale"] = clampf(float(m["cdScale"]) + float(raw),
                float(CAPS["cdScaleMin"]), 1.5)
        "spirit_cost":
            if id == "card_danxiang":
                return  # 丹香卡面限定「回春诀灵耗减半」，4 技能槽不按技能区分，不全局套用
            m["spiritCostScale"] = clampf(float(m["spiritCostScale"]) + float(raw),
                float(CAPS["spiritCostMin"]), 1.5)
        "free_cast":
            if _truthy(raw):
                m["freeCastOnFull"] = true
        "on_kill":
            m["spiritOnKill"] = clampf(float(m["spiritOnKill"]) + float(raw),
                0.0, float(CAPS["spiritOnKill"]))
        "per_hit":
            if id != "card_nianzhuan":
                return  # 破云式里是分段倍率（由 split 处理），逆转回灵才是命中回灵
            m["spiritOnHit"] = clampf(float(m["spiritOnHit"]) + float(raw),
                0.0, float(CAPS["spiritOnHit"]))
        "on_hit":
            if id != "card_jieqi":
                return
            m["spiritOnHurt"] = clampf(float(m["spiritOnHurt"]) + float(raw),
                0.0, float(CAPS["spiritOnHurt"]))
        "hp_max":
            var v := float(raw)
            if absf(v) < 1.0:
                m["hpMaxRatio"] = clampf(float(m["hpMaxRatio"]) + v, -0.6, 0.6)
            else:
                m["hpMaxFlat"] = clampf(float(m["hpMaxFlat"]) + v,
                    -float(CAPS["hpMaxDelta"]), float(CAPS["hpMaxDelta"]))
        "spirit_max":
            var v: float = float(raw)
            if absf(v) < 1.0:
                m["spiritMaxRatio"] = clampf(float(m["spiritMaxRatio"]) + v, -0.6, 0.6)
            else:
                m["spiritMaxFlat"] = clampf(float(m["spiritMaxFlat"]) + v,
                    -float(CAPS["spiritMaxDelta"]), float(CAPS["spiritMaxDelta"]))
        "move_speed":
            m["moveSpeedBonus"] = clampf(float(m["moveSpeedBonus"]) + float(raw),
                -0.5, float(CAPS["moveSpeedBonus"]))
        "invuln":
            m["hurtInvuln"] = clampf(maxf(float(m["hurtInvuln"]), float(raw)),
                0.0, float(CAPS["hurtInvuln"]))
        "crit_rate":
            m["critRateBonus"] = clampf(float(m["critRateBonus"]) + float(raw),
                0.0, float(CAPS["critRateBonus"]))
        "defense_rate":
            m["damageTakenScale"] = clampf(float(m["damageTakenScale"]) - float(raw),
                float(CAPS["damageTakenMin"]), 1.0)
        "flat_reduce":
            m["flatReduce"] = clampf(float(m["flatReduce"]) + float(raw),
                0.0, float(CAPS["flatReduce"]))
        "revive_hp":
            m["reviveHp"] = clampf(maxf(float(m["reviveHp"]), float(raw)),
                0.0, float(CAPS["reviveHp"]))
        "reveal":
            if _truthy(raw):
                m["reveal"] = true
        # 其余键（pool/cap/stop_draw/hook 等）归抽卡层或局外系统，不在此实现。


static func _truthy(v: Variant) -> bool:
    # 对齐 JavaScript 的 truthy 语义（card_effects.js 用 if (p.affix) 等）：
    # 空字符串 / 0 / false 为假，其余（含 "affix_tiebi" 这类非空串）为真。
    if typeof(v) == TYPE_BOOL:
        return v as bool
    if v is String:
        return not (v as String).is_empty()
    return float(v) != 0.0


static func _equal_ratios(n: int) -> Array:
    var arr: Array = []
    var ratio := 1.0 / float(maxi(1, n))
    for _i in range(n):
        arr.append(ratio)
    return arr
