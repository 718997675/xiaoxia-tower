class_name CardDeck
extends RefCounted
# @trace DF-19, DF-21
# 层间三选一卡牌「规则层」——只管抽取规则与伤害红线守卫，不碰画面、不建 UI、不改冻结数值。
# 数据来源：res://data/buff-card-library.json（由 tools/build_card_runtime_data.py 从 docs 源生成，R45）。
# 规格依据：docs/11 §4/§6、docs/12、docs/buff-card-library.json（drawRule / hookWhitelist / offenseCeiling）。
# 边界：卡牌效果只落地「触碰五上界变量」的部分；其余 hook（RunState.* / VfxLayer.* / signal.* /
#       MetaSave.* / UI.pick_event）留给正式战斗工程按 01 §12 节点树接入，本脚本不假装已实现。
# 数值口径：一切权重、概率、层数曲线均为 PROPOSAL / 待实测，不得当作已验证的平衡结论。
# 跨端口径（R47 / 第 19 轮）：随机源不用引擎内置 RandomNumberGenerator（PCG32，网页与 Node 无法复刻），
#       改为自实现 xorshift32 + 24 位定点 randf，种子仍为 FNV-1a(run_id:stage)。
#       tools/card_rules.js 是同一算法的 JS 实现，逐 (run_id, stage) 结果由黄金样本比对保证一致，
#       这样「网页验证通过 → 再导入 Godot」才是可复算的，而不是口头承诺。
# 缩进：本工程统一 4 空格，禁用 Tab。

const LIB_PATH: String = "res://data/buff-card-library.json"

# 五上界铁律（DF-21 / R32，冻结规格，不得由卡牌提高）
const CAP_BASE: float = 180.0
const CAP_REALM_RATIO: float = 1.60
const CAP_EXTRA_POOL: float = 600.0
const CAP_COMBO: float = 2.5
const CAP_CRIT: float = 1.8
const CAP_DEFENSE: float = 0.75
const BOSS_HP_REFERENCE: float = 4400.0

const DEFAULT_CHOICES: int = 3
const WUXIANG_CHOICES: int = 2
const LAST_DRAW_STAGE: int = 8          # 第 9 层 Boss 后不弹卡
const UPPER_KEYS: Array = [
    "base_damage", "realm_ratio", "extra_pool", "combo_multiplier",
    "crit_multiplier", "defense_rate",
]
const FNV_OFFSET: int = 0x811c9dc5       # 自实现 FNV-1a 32 位，保证跨引擎版本可复算
const FNV_PRIME: int = 0x01000193
const MASK32: int = 0xffffffff

var _cards: Array = []
var _by_id: Dictionary = {}
var _picked: Dictionary = {}             # card_id -> 本局已选次数
var _context: Dictionary = {}            # school / skills / gear / affix / realm / slots
var _offense: Dictionary = {}            # 卡牌对五个上界变量贡献的增量
var _pool_used: float = 0.0              # offense_pool 与 extra_pool 共享的 600 点池
var _clamp_events: Array = []
var _violations: Array = []
var _sealed: bool = false               # card_sheli / card_wuxin 令本局后续不再弹卡
var _skipped: Array = []                # card_shouzhuo 主动放弃抽卡的层
var _run_id: String = ""
var _last_error: String = ""
var _rng_state: int = 0                  # xorshift32 状态，每次 offer() 由 run_seed(stage) 重置


func _init(lib_path: String = LIB_PATH) -> void:
    _reset_offense()
    var f := FileAccess.open(lib_path, FileAccess.READ)
    if f == null:
        _last_error = "打不开卡库：" + lib_path
        push_error(_last_error)
        return
    var parsed: Variant = JSON.parse_string(f.get_as_text())
    f.close()
    if not (parsed is Dictionary):
        _last_error = "卡库不是合法 JSON 对象"
        push_error(_last_error)
        return
    var lib: Dictionary = parsed
    if not lib.has("cards"):
        _last_error = "卡库缺 cards 字段"
        return
    for c in lib["cards"]:
        _cards.append(c)
        _by_id[String(c["id"])] = c


func _reset_offense() -> void:
    _offense = {}
    for key in UPPER_KEYS:
        _offense[key] = 0.0
    _pool_used = 0.0
    _clamp_events = []
    _violations = []


func is_loaded() -> bool:
    return _cards.size() == 72 and _last_error == ""


func last_error() -> String:
    return _last_error


func card_count() -> int:
    return _cards.size()


# ---------------------------------------------------------------- 局级状态
func new_run(run_id: String, context: Dictionary = {}) -> void:
    _run_id = run_id
    _picked = {}
    _sealed = false
    _skipped = []
    _reset_offense()
    _context = {
        "school": "jian",
        "skills": [],
        "gear": [],
        "affix": [],
        "realm": 1,
        "slots": 3,
    }
    for k in context.keys():
        _context[k] = context[k]


func set_context(key: String, value: Variant) -> void:
    _context[key] = value


func is_sealed() -> bool:
    return _sealed


func picked_counts() -> Dictionary:
    return _picked.duplicate()


func skipped_stages() -> Array:
    return _skipped.duplicate()


func offense_state() -> Dictionary:
    var out := _offense.duplicate()
    out["offense_pool_used"] = _pool_used
    return out


func clamp_events() -> Array:
    return _clamp_events.duplicate()


func violations() -> Array:
    return _violations.duplicate()


# ---------------------------------------------------------------- 确定性种子
func _fnv1a(s: String) -> int:
    var h: int = FNV_OFFSET
    for b in s.to_utf8_buffer():
        h = (h ^ int(b)) & MASK32
        h = (h * FNV_PRIME) & MASK32
    return h


func run_seed(stage: int) -> int:
    # hash(run_id, stage)：固定算法，便于埋点复现与存档回放；不依赖引擎内置 hash()
    return _fnv1a(_run_id + ":" + str(stage))


# ---- xorshift32（R47）：GDScript / JS / Python 三端逐位一致 -----------------
# 只用 32 位移位与异或，不依赖引擎 PRNG；randf 取高 24 位 / 2^24，避免浮点尾数差异。
func _rng_reset(seed: int) -> void:
    _rng_state = seed & MASK32
    if _rng_state == 0:
        _rng_state = 0x6d2b79f5       # xorshift 零态是死循环，固定非零替代


func _rng_next() -> int:
    var x: int = _rng_state
    x = (x ^ ((x << 13) & MASK32)) & MASK32
    x = (x ^ (x >> 17)) & MASK32
    x = (x ^ ((x << 5) & MASK32)) & MASK32
    _rng_state = x
    return x


func _rng_randf() -> float:
    return float((_rng_next() >> 8) & 0xffffff) / 16777216.0


# ---------------------------------------------------------------- 候选池过滤
func _req_ok(c: Dictionary, stage: int) -> bool:
    for raw in c.get("req", []):
        var r := String(raw)
        if r.begins_with("stage>="):
            if stage < int(r.substr(7)):
                return false
            continue
        var parts := r.split(":", true, 1)
        var key := parts[0]
        var val := parts[1] if parts.size() > 1 else ""
        match key:
            "school":
                if String(_context.get("school", "")) != val:
                    return false
            "skill":
                if not (_context.get("skills", []) as Array).has(val):
                    return false
            "gear":
                if val == "any":
                    if (_context.get("gear", []) as Array).is_empty():
                        return false
                elif val == "3slots":
                    if int(_context.get("slots", 3)) < 3:
                        return false
            "affix":
                if not (_context.get("affix", []) as Array).has(val):
                    return false
            _:
                return false   # 未知前置一律不放行，宁可少给卡也不静默破坏规则
    return true


func _unlock_ok(c: Dictionary) -> bool:
    var u := String(c.get("unlock", "none"))
    if u == "none":
        return true
    if u.begins_with("realm:"):
        return int(_context.get("realm", 1)) >= int(u.substr(6))
    return false


func _excluded(card_id: String) -> bool:
    # excl[] 双向生效：已选卡的 excl 含本卡，或本卡的 excl 含已选卡。
    for picked_id in _picked.keys():
        if int(_picked[picked_id]) <= 0:
            continue
        var pc: Dictionary = _by_id.get(picked_id, {})
        if (pc.get("excl", []) as Array).has(card_id):
            return true
    var c: Dictionary = _by_id.get(card_id, {})
    for other in c.get("excl", []):
        if int(_picked.get(other, 0)) > 0:
            return true
    return false


func eligible(stage: int) -> Array:
    var out: Array = []
    for c in _cards:
        var cid := String(c["id"])
        # §6 两行联合口径：已选且堆满 stack 上限才移出池；stack=1 等价于选过即移出。
        # 这是「去重」与「堆叠上限」并存时的实现解释，见 docs/15 §3。
        if int(_picked.get(cid, 0)) >= int(c.get("stack", 1)):
            continue
        if not _req_ok(c, stage):
            continue
        if not _unlock_ok(c):
            continue
        if _excluded(cid):
            continue
        out.append(cid)
    return out


# ---------------------------------------------------------------- 加权抽取
func _weight(c: Dictionary, stage: int) -> float:
    var w := float(c.get("weight", 10))
    if String(c.get("rarity", "")) == "legend":
        # 层数越高仙品权重线性 ×(1 + 0.1 × 层数)，待实测
        w *= 1.0 + 0.1 * float(stage)
    return maxf(w, 0.0)


func _weighted_pick(candidates: Array, weights: Array) -> String:
    var total := 0.0
    for w in weights:
        total += float(w)
    if total <= 0.0:
        return ""
    var r := _rng_randf() * total
    var acc := 0.0
    for i in range(candidates.size()):
        acc += float(weights[i])
        if r <= acc:
            return String(candidates[i])
    return String(candidates[candidates.size() - 1])


func choice_count() -> int:
    if int(_picked.get("card_wuxiangpo", 0)) > 0:
        return DEFAULT_CHOICES   # 无相破恢复 3 张
    if (_context.get("affix", []) as Array).has("affix_wuxiang"):
        return WUXIANG_CHOICES   # 无相词缀压成 2 选 1
    return DEFAULT_CHOICES


func offer(stage: int) -> Array:
    # 返回本层候选卡 ID；确定性：同一 (run_id, stage) 结果恒定。
    if _sealed or stage > LAST_DRAW_STAGE or stage < 1:
        return []
    var pool := eligible(stage)
    _rng_reset(run_seed(stage))
    var used_cat: Dictionary = {}
    var offered: Array = []
    for _i in range(choice_count()):
        var candidates: Array = []
        var weights: Array = []
        for cid in pool:
            var c: Dictionary = _by_id[cid]
            var cat := String(c["cat"])
            if used_cat.has(cat) or offered.has(cid):
                continue
            candidates.append(cid)
            weights.append(_weight(c, stage))
        if candidates.is_empty():
            break
        var chosen := _weighted_pick(candidates, weights)
        if chosen == "":
            break
        offered.append(chosen)
        used_cat[String(_by_id[chosen]["cat"])] = true
    return offered


func pick(card_id: String, stage: int) -> bool:
    if _sealed or not _by_id.has(card_id):
        return false
    if not offer(stage).has(card_id):
        return false   # 只允许从本层候选中选，防止绕过前置/互斥/去重
    _picked[card_id] = int(_picked.get(card_id, 0)) + 1
    apply_params(card_id)
    var p: Dictionary = _by_id[card_id].get("params", {})
    if bool(p.get("stop_draw", false)):
        _sealed = true
    if bool(p.get("skip_draw", false)):
        _skipped.append(stage)
    return true


func skip_draw(stage: int) -> bool:
    # 守拙：主动放弃本层抽卡。默认不开放舍牌，只有选中该卡后本层可舍。
    if int(_picked.get("card_shouzhuo", 0)) <= 0 or _skipped.has(stage):
        return false
    _skipped.append(stage)
    return true


# ---------------------------------------------------------------- 五上界守卫（DF-21）
func apply_params(card_id: String) -> Dictionary:
    # 落地「触碰上界变量」的效果；其余 hook 留给正式战斗工程。
    # 公开给验证脚本逐卡扫描，保证任何卡都不能把峰值推过 3996。
    if not _by_id.has(card_id):
        return {"ok": false}
    var c: Dictionary = _by_id[card_id]
    var p: Dictionary = c.get("params", {})
    var touches_upper := false
    for key in UPPER_KEYS:
        if p.has(key):
            touches_upper = true
            break
    if touches_upper and not (p.has("pool") or p.has("cap")):
        _violations.append({"card": card_id, "why": "触碰上界变量但未声明 pool/cap（R32 机器规则）"})

    if String(p.get("pool", "")) == "offense_pool":
        # 增益并入共享池，而不是直接叠 base（R32 的关键修复）
        _pool_used += float(p.get("base_damage", 0.0))
    for key in UPPER_KEYS:
        if not p.has(key):
            continue
        if key == "base_damage" and String(p.get("pool", "")) == "offense_pool":
            continue
        _offense[key] = float(_offense.get(key, 0.0)) + float(p[key])
    _clamp_offense()
    return {"ok": true, "offense": offense_state(), "peak": peak_damage()}


func _clamp_offense() -> void:
    var limits := {
        "base_damage": CAP_BASE,
        "realm_ratio": CAP_REALM_RATIO,
        "extra_pool": CAP_EXTRA_POOL,
        "combo_multiplier": CAP_COMBO,
        "crit_multiplier": CAP_CRIT,
        "defense_rate": CAP_DEFENSE,
    }
    for key in limits.keys():
        var before := float(_offense.get(key, 0.0))
        var after := clampf(before, 0.0, float(limits[key]))
        _offense[key] = after
        if absf(after - before) > 0.000001:
            _clamp_events.append({"var": key, "before": before, "after": after, "kind": "numeric_clamp"})
        elif before > 0.000001 and key != "defense_rate":
            # 基线已取全最大上界，卡牌的正增量一律不得提高上界：峰值计算时会被 clamp 忽略。
            # 记事件是为了能机器证明「守卫真的拦过东西」，而不是空跑一遍恒等式。
            _clamp_events.append({"var": key, "delta": before, "kind": "upper_bound_guard"})
    var pool_before := _pool_used
    _pool_used = clampf(pool_before, 0.0, CAP_EXTRA_POOL)
    if absf(_pool_used - pool_before) > 0.000001:
        _clamp_events.append({"var": "offense_pool", "before": pool_before, "after": _pool_used})


func peak_damage() -> float:
    # 语义：全最大基线 + 当前卡组增量，逐项钳回五上界后的「单次理论峰值」。
    # 用于机器断言 <= 3996 < Boss 4400；不是某一局的实际伤害。
    var base := clampf(CAP_BASE + float(_offense.get("base_damage", 0.0)), 0.0, CAP_BASE)
    var realm := clampf(CAP_REALM_RATIO + float(_offense.get("realm_ratio", 0.0)), 0.0, CAP_REALM_RATIO)
    var pool := clampf(CAP_EXTRA_POOL + float(_offense.get("extra_pool", 0.0)) + _pool_used, 0.0, CAP_EXTRA_POOL)
    var combo := clampf(CAP_COMBO + float(_offense.get("combo_multiplier", 0.0)), 0.0, CAP_COMBO)
    var crit := clampf(CAP_CRIT + float(_offense.get("crit_multiplier", 0.0)), 0.0, CAP_CRIT)
    # 最坏口径：目标不减伤。玩家侧 defense_rate 属生存维度，不是攻击方的伤害上界变量，
    # 混进峰值会把「玩家变肉」误算成「伤害变低」，掩盖红线是否被突破。
    var mitigation := 1.0
    return roundf((base * realm + pool) * combo * crit * mitigation)


func damage_ceiling_ok() -> bool:
    return peak_damage() < BOSS_HP_REFERENCE and _violations.is_empty()


# ---------------------------------------------------------------- 埋点（DF-22 字段增补）
func pick_event(stage: int, offered: Array, picked: String) -> Dictionary:
    var c: Dictionary = _by_id.get(picked, {})
    return {
        "stage": stage,
        "offered": offered.duplicate(),
        "picked": picked,
        "card_id": picked,
        "card_rarity": String(c.get("rarity", "")),
        "card_category": String(c.get("cat", "")),
        "seen_before": int(_picked.get(picked, 0)) > 1,
        "run_id": _run_id,
        "seed": run_seed(stage),
    }
