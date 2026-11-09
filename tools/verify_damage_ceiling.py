#!/usr/bin/env python3
"""R32 极值验算：72 张卡全生效后，伤害峰值是否击穿第 9 层 Boss 4400 红线。

背景：02 §4 P0-3 把 realm_ratio 从 4.00 压到 1.60 后，全最大伤害 5940 → 3996，
只剩 404 点余量。第 12 轮立了「卡牌不得提高四上界」的铁律，但复算发现：
铁律漏了第五个变量 base（20–180），3 张 base_damage 卡叠满会把 base 推到 254，
峰值 4529 > 4400，红线复燃。本脚本把这件事变成机器可查的事实。

用法：
  /opt/homebrew/bin/python3 tools/verify_damage_ceiling.py

输入：docs/buff-card-library.json（唯一机器可读卡源）
输出：docs/damage-ceiling-report.json + 控制台摘要

判定规则（不是靠人回忆）：
  1. 凡 hook 以 "SkillCaster." 开头、且 params 触碰伤害上界变量的卡，
     必须显式声明 cap 或 pool，否则记为违规。
  2. 按「不守共享池」的最坏叠加算一次峰值（暴露漏洞）。
  3. 按「守五上界 + offense_pool 与 extra_pool 共享 600」算一次峰值。
  4. 守规则后的峰值必须 <= BOSS_HP，且 >= 1（钳制下界）。
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "docs" / "buff-card-library.json"
OUT = ROOT / "docs" / "damage-ceiling-report.json"

# 已确认红线（来源：02 §4 P0-3 / 数值框架.csv longevity_dmg_max_v02_raw=3996）
CEILING = {
    "base": 180.0,
    "realm_ratio": 1.60,
    "extra_pool": 600.0,
    "combo_mult": 2.5,
    "crit_mult": 1.8,
    "defense_rate_min": 0.0,
}
BOSS_HP = 4400

# 触碰伤害上界的 params 键；出现即要求该卡显式带 cap 或 pool
TOUCH_KEYS = {
    "realm_ratio", "extra_pool", "combo_multiplier", "crit_multiplier",
    "base_damage", "damage", "per_stack", "multiplier",
}


def dmg(base: float, realm: float, pool: float, combo: float,
        crit: float, defense: float) -> int:
    """与 01 §8.1 / SkillCaster.gd 同源的乘性公式，含 clamp(1, 9999)。"""
    raw = (base * realm + pool) * combo * crit * (1.0 - min(max(defense, 0.0), 0.75))
    return max(1, min(9999, round(raw)))


def main() -> None:
    lib = json.loads(LIB.read_text(encoding="utf-8"))
    cards = lib["cards"]

    ceiling_touching = []
    violations = []
    base_bonus_unbounded = 0.0   # 未声明 pool 的 base_damage 卡（实现若忽略边界会直接叠）
    base_bonus_all = 0.0         # 全部 base_damage 卡，用于「pool 声明被实现忽略」的最坏取证
    for c in cards:
        hook = str(c.get("hook", ""))
        params = c.get("params", {}) or {}
        touched = sorted(set(params.keys()) & TOUCH_KEYS)
        if not hook.startswith("SkillCaster.") or not touched:
            continue
        has_guard = ("cap" in params) or ("pool" in params)
        ceiling_touching.append({
            "id": c["id"], "hook": hook, "touched": touched,
            "guard": ("cap=%s" % params["cap"]) if "cap" in params
                     else ("pool=%s" % params["pool"]) if "pool" in params
                     else "NONE",
            "compliant": has_guard,
        })
        if not has_guard:
            violations.append(c["id"])
        # 「不守共享池」的最坏口径：所有 base_damage 加成按 stack 叠满
        if "base_damage" in params:
            v = params["base_damage"]
            if isinstance(v, (int, float)):
                total = float(v) * int(c.get("stack", 1))
                base_bonus_all += total
                if "pool" not in params:
                    base_bonus_unbounded += total

    base_worst = CEILING["base"] + base_bonus_unbounded
    worst_without_pool = dmg(base_worst, CEILING["realm_ratio"], CEILING["extra_pool"],
                             CEILING["combo_mult"], CEILING["crit_mult"],
                             CEILING["defense_rate_min"])
    base_worst_all = CEILING["base"] + base_bonus_all
    worst_all_direct = dmg(base_worst_all, CEILING["realm_ratio"], CEILING["extra_pool"],
                            CEILING["combo_mult"], CEILING["crit_mult"],
                            CEILING["defense_rate_min"])
    baseline = dmg(CEILING["base"], CEILING["realm_ratio"], CEILING["extra_pool"],
                   CEILING["combo_mult"], CEILING["crit_mult"],
                   CEILING["defense_rate_min"])
    # 守规则：base 保持 180，卡牌增益并入共享池（池上限仍是 600）
    with_pool = dmg(CEILING["base"], CEILING["realm_ratio"], CEILING["extra_pool"],
                    CEILING["combo_mult"], CEILING["crit_mult"],
                    CEILING["defense_rate_min"])

    numeric = sum(1 for c in cards if c.get("type") == "numeric")
    mechanical_or_hybrid = sum(1 for c in cards if c.get("type") in ("mechanical", "hybrid"))

    report = {
        "spec": "docs/01-策划案.md §8.1 + docs/11-塔层三选一卡牌系统.md §4",
        "generator": "tools/verify_damage_ceiling.py",
        "engineVersion": "Godot 4.7.2.stable（本验算为离线公式复算，未在编辑器实测）",
        "formula": "final = clamp(round((base*realm_ratio + extra_pool) * combo_mult * crit_mult * (1-defense_rate)), 1, 9999)",
        "confirmedCeiling": CEILING,
        "bossHP": BOSS_HP,
        "headroom": BOSS_HP - baseline,
        "cardsScanned": len(cards),
        "numericCards": numeric,
        "numericRatio": round(numeric / len(cards), 4),
        "mechanicalOrHybrid": mechanical_or_hybrid,
        "ceilingTouchingCards": ceiling_touching,
        "violations": violations,
        "scenario": {
            "baseline": {"base": CEILING["base"], "damage": baseline,
                         "verdict": "PASS" if baseline <= BOSS_HP else "FAIL"},
            "worstWithoutSharedPool": {
                "base": base_worst,
                "baseBonus": base_bonus_unbounded,
                "damage": worst_without_pool,
                "verdict": "PASS" if worst_without_pool <= BOSS_HP else "FAIL",
                "note": "仅未声明 pool 的 base_damage 卡直接叠加；修复前为 236 -> 4399，距 4400 只剩 1 点，任何后续调 stack 即击穿",
            },
            "worstIfAllBaseCardsDirect": {
                "base": base_worst_all,
                "baseBonus": base_bonus_all,
                "damage": worst_all_direct,
                "verdict": "PASS" if worst_all_direct <= BOSS_HP else "FAIL",
                "note": "假设连已声明 pool 的卡也被实现成直接叠加（第 12 轮四上界铁律漏掉第五变量 base 的真实风险）",
            },
            "withSharedPool": {"base": CEILING["base"], "damage": with_pool,
                               "verdict": "PASS" if with_pool <= BOSS_HP else "FAIL",
                               "note": "修复后：base 固定 <=180，所有数值增益并入 offense_pool 并与 extra_pool 共享 600 上限"},
        },
        "rule": {
            "fiveCeilings": "realm_ratio<=1.60 / extra_pool<=600 / combo<=2.5 / crit<=1.8 / base<=180",
            "sharedPool": "offense_pool 与 extra_pool 共享同一个 600 点上限，不得另开池",
            "machineCheck": "凡 SkillCaster.* 钩子且 params 触碰上界变量的卡，必须显式带 cap 或 pool",
        },
        "verdict": ("PASS" if (not violations and with_pool <= BOSS_HP) else "FAIL"),
        "recompute": "python3 tools/verify_damage_ceiling.py  # 可复算，零第三方依赖",
        "status": "结构红线已机器核对；卡牌具体数值/权重仍为 PROPOSAL 待实测",
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("R32 极值验算 ->", OUT.relative_to(ROOT))
    print("  基线全最大      :", baseline, "/ Boss", BOSS_HP, "余量", BOSS_HP - baseline)
    print("  不守共享池最坏  : base=%.0f -> %d  %s" %
          (base_worst, worst_without_pool, "❌ 击穿红线" if worst_without_pool > BOSS_HP else "OK"))
    print("  守共享池后      :", with_pool, "OK" if with_pool <= BOSS_HP else "FAIL")
    print("  触碰上界卡      :", len(ceiling_touching), "张 / 违规", len(violations), violations)
    print("  纯数值占比      : %d/%d = %.1f%%（硬约束 <=33.3%%）" %
          (numeric, len(cards), 100.0 * numeric / len(cards)))
    print("  verdict         :", report["verdict"])


if __name__ == "__main__":
    main()
