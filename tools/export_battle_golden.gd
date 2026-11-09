extends SceneTree
# Godot 侧「战斗公式层」黄金样本导出（第 22 轮）
#
# 把 scripts/BattleFormula.gd 的伤害公式与只读数据表写成机器可读证据，
# tools/cross_platform_battle_check.js（Node）必须逐条复算出完全相同的结果，
# 否则「网页战斗的伤害口径 == Godot 口径」这句话不成立。
#
# 用法：Godot --headless --path . --script res://tools/export_battle_golden.gd
#
# 边界：覆盖的是**公式 + 数据表**，不含逐 tick 状态机（见 scripts/BattleFormula.gd 文件头）。

const Formula = preload("res://scripts/BattleFormula.gd")
const OUT_PATH := "res://docs/battle-golden-samples.json"

# 手挑的边界用例：0 值 / 负值 / 越界值 / .5 舍入 / 满上界 / 带满减伤
const CASES: Array = [
    {"id": "base", "base": 20.0, "realm": 1.0, "pool": 0.0, "combo": 1.0, "crit": 1.0, "defense": 0.0},
    {"id": "pool_only", "base": 0.0, "realm": 1.0, "pool": 22.0, "combo": 1.0, "crit": 1.0, "defense": 0.0},
    {"id": "caps_max", "base": 180.0, "realm": 1.6, "pool": 600.0, "combo": 2.5, "crit": 1.8, "defense": 0.0},
    {"id": "caps_max_defense", "base": 180.0, "realm": 1.6, "pool": 600.0, "combo": 2.5, "crit": 1.8, "defense": 0.75},
    {"id": "all_zero", "base": 0.0, "realm": 0.0, "pool": 0.0, "combo": 0.0, "crit": 0.0, "defense": 0.0},
    {"id": "negative_all", "base": -1.0, "realm": -1.0, "pool": -1.0, "combo": -1.0, "crit": 0.0, "defense": -1.0},
    {"id": "over_caps", "base": 999.0, "realm": 9.0, "pool": 9999.0, "combo": 9.0, "crit": 9.0, "defense": 9.0},
    {"id": "round_half_up_1", "base": 1.0, "realm": 1.0, "pool": 0.0, "combo": 1.0, "crit": 1.0, "defense": 0.5},
    {"id": "round_half_up_2", "base": 3.0, "realm": 1.0, "pool": 0.0, "combo": 1.0, "crit": 1.0, "defense": 0.5},
    {"id": "crit_only", "base": 40.0, "realm": 1.0, "pool": 0.0, "combo": 1.0, "crit": 1.8, "defense": 0.0},
    {"id": "combo_only", "base": 40.0, "realm": 1.0, "pool": 0.0, "combo": 2.5, "crit": 1.0, "defense": 0.0},
    {"id": "defense_mid", "base": 40.0, "realm": 1.0, "pool": 0.0, "combo": 1.0, "crit": 1.0, "defense": 0.3},
]


func _init() -> void:
    var cases: Array = []
    for c in CASES:
        cases.append(_case(c["id"], c["base"], c["realm"], c["pool"], c["combo"], c["crit"], c["defense"]))

    # 系统扫描：40 组确定性输入，覆盖四舍五入与钳制边界
    for i in range(40):
        var base := float((i * 13) % 200)
        var realm := 1.0 + float(i % 7) * 0.1
        var pool := float((i * 29) % 650)
        var combo := 1.0 + float(i % 4) * 0.25
        var crit := 1.0 + float(i % 3) * 0.3
        var defense := float(i % 9) * 0.1
        cases.append(_case("sweep_%02d" % i, base, realm, pool, combo, crit, defense))

    var report := {
        "version": 1,
        "generatedAt": Time.get_date_string_from_system(),
        "generator": "tools/export_battle_golden.gd",
        "engine": "Godot 4.7.2.stable（headless）",
        "formulaSource": "res://scripts/BattleFormula.gd",
        "counterpart": "tools/battle_sim.js（浏览器 / Node 共用）",
        "scope": "伤害公式 + 只读数据表（9 层波形 / 4 技能冻结字段）；不含逐 tick 状态机",
        "caps": {
            "base": Formula.CAP_BASE,
            "realmRatio": Formula.CAP_REALM_RATIO,
            "extraPool": Formula.CAP_EXTRA_POOL,
            "comboMult": Formula.CAP_COMBO,
            "critMult": Formula.CAP_CRIT,
            "defenseRate": Formula.CAP_DEFENSE,
            "bossHpReference": Formula.BOSS_HP_REFERENCE,
            "dmgMin": Formula.DMG_MIN,
            "dmgMax": Formula.DMG_MAX,
        },
        "maxHit": Formula.max_hit(),
        "cases": cases,
        "stages": Formula.stages(),
        "skillsFrozen": Formula.skills_frozen(),
        "note": "黄金样本由 Godot 侧导出；Node/网页必须逐条复算一致。PROPOSAL 占位（技能 CD / 灵力 / 玩家 HP 等）刻意不镜像。",
    }

    var out := FileAccess.open(OUT_PATH, FileAccess.WRITE)
    if out == null:
        print("BGOLDEN|FAIL|写入失败")
        quit(1)
        return
    out.store_string(JSON.stringify(report, "\t") + "\n")
    out.close()
    print("BGOLDEN|cases=", cases.size(), "|max_hit=", Formula.max_hit(),
          "|stages=", report["stages"].size(), "|skills=", report["skillsFrozen"].size())
    print("BGOLDEN|PASS|", OUT_PATH)
    quit(0)


func _case(id: String, base: float, realm: float, pool: float,
        combo: float, crit: float, defense: float) -> Dictionary:
    var res := Formula.damage_formula(base, realm, pool, combo, crit, defense)
    return {
        "id": id,
        "input": {
            "base": base, "realm": realm, "pool": pool,
            "combo": combo, "crit": crit, "defense": defense,
        },
        "damage": int(res["damage"]),
        "negative": bool(res["negative"]),
        "clamped": bool(res["clamped"]),
    }
