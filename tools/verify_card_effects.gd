extends SceneTree

## 第 42 轮 · Godot 卡牌效果编译器跨端口径验证（headless --script）。
## 逐字段比对 scripts/CardEffects.gd 与网页 card_effects.js 生成的黄金样本
## （docs/card-effects-golden.json，76 样本 × 20 字段），并写证据报告。

const CardEffects = preload("res://scripts/CardEffects.gd")
const GOLDEN := "res://docs/card-effects-golden.json"
const REPORT := "res://docs/card-effects-verify-report.json"

var _passed := 0
var _failed := 0
var _fails: Array = []


func _ck(name: String, ok: bool, detail: String = "") -> void:
    if ok:
        _passed += 1
        print("VERIFY|PASS|", name, "|", detail)
    else:
        _failed += 1
        _fails.append(name + (" :: " + detail if detail != "" else ""))
        print("VERIFY|FAIL|", name, "|", detail)


func _mods_equal(a: Dictionary, b: Dictionary, mod_keys: Array) -> bool:
    if a.size() != mod_keys.size():
        return false
    for k in mod_keys:
        if not a.has(k) or not b.has(k):
            return false
        var av: Variant = a[k]
        var bv: Variant = b[k]
        if av is Array or bv is Array:
            if not (av is Array and bv is Array):
                return false
            var aa: Array = av
            var bb: Array = bv
            if aa.size() != bb.size():
                return false
            for i in range(aa.size()):
                if absf(float(aa[i]) - float(bb[i])) > 1e-6:
                    return false
        elif typeof(av) == TYPE_BOOL or typeof(bv) == TYPE_BOOL:
            if bool(av) != bool(bv):
                return false
        elif absf(float(av) - float(bv)) > 1e-6:
            return false
    return true


func _init() -> void:
    var ce := CardEffects.new()
    _ck("effects_loaded", ce.is_loaded() and ce.card_count() == 72,
        "cards=%d" % ce.card_count())

    var f := FileAccess.open(GOLDEN, FileAccess.READ)
    if f == null:
        _ck("golden_open", false, "打不开黄金样本")
        _finish()
        return
    var parsed: Variant = JSON.parse_string(f.get_as_text())
    if not (parsed is Dictionary):
        _ck("golden_parse", false)
        _finish()
        return
    var doc: Dictionary = parsed
    var mod_keys: Array = doc.get("modKeys", [])
    var samples: Dictionary = doc.get("samples", {})

    # 默认 mods 必须与 JS 逐字段一致
    var dm_js: Dictionary = samples.get("__default__", {})
    _ck("default_mods_20", CardEffects.default_mods().size() == 20 and mod_keys.size() == 20,
        "gd=%d js=%d" % [CardEffects.default_mods().size(), mod_keys.size()])
    _ck("default_mods_match", _mods_equal(CardEffects.default_mods(), dm_js, mod_keys))

    # 全部 72 张单卡 + 3 个堆叠组合逐字段比对
    var mismatch: Array = []
    for id in samples.keys():
        if id == "__default__":
            continue
        var expected: Dictionary = samples[id]
        var got: Dictionary
        if id.begins_with("__stack_") or id == "__mix__":
            var ids := _sample_ids(id)
            got = ce.compile(ids)
        else:
            got = ce.compile_one(id)
        if not _mods_equal(got, expected, mod_keys):
            mismatch.append(id)
    _ck("all_samples_match", mismatch.is_empty(),
        "samples=%d mismatch=%s" % [samples.size() - 1, str(mismatch)])

    # 关键特例断言（丹香不套全局灵耗 / 破云分段 / 接气受击回灵 / 复活 / 显示敌人HP）
    _ck("danxiang_no_global_cost", ce.compile_one("card_danxiang")["spiritCostScale"] == 1.0)
    _ck("poyun_split", _ratios(ce.compile_one("card_poyun")) == [0.5, 0.5])
    _ck("jieqi_on_hurt", ce.compile_one("card_jieqi")["spiritOnHurt"] == 4.0)
    _ck("sheli_revive", ce.compile_one("card_sheli")["reviveHp"] == 0.3)
    _ck("tianren_reveal", ce.compile_one("card_tianren")["reveal"] == true)
    _ck("wuxing_affix_none", ce.compile_one("card_wuxing")["pierceDefense"] == 0.0)

    _finish()


func _sample_ids(tag: String) -> Array:
    match tag:
        "__stack_cd__": return ["card_qingling", "card_wugen", "card_sheshi"]
        "__stack_hp__": return ["card_ningdan", "card_shouyuan", "card_sheshi"]
        "__mix__": return ["card_poyun", "card_huti", "card_tiegu", "card_juling", "card_tianren"]
    return []


func _ratios(mods: Dictionary) -> Array:
    var out: Array = []
    for v in (mods["segmentRatios"] as Array):
        out.append(snappedf(float(v), 0.0001))
    return out


func _finish() -> void:
    var total := _passed + _failed
    print("VERIFY|SUMMARY|passed=%d failed=%d|%s" % [_passed, _failed,
        "PASS" if _failed == 0 else "FAIL"])
    var report := {
        "status": "PASS" if _failed == 0 else "FAIL",
        "passed": _passed, "failed": _failed, "total": total,
        "failures": _fails,
        "golden_source": "tools/card_effects.js",
        "scope": "PROPOSAL / web-validation-mirrored / not frozen spec / not balance conclusion",
    }
    var rf := FileAccess.open(REPORT, FileAccess.WRITE)
    if rf != null:
        rf.store_string(JSON.stringify(report, "  "))
    quit(0 if _failed == 0 else 1)
