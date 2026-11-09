extends SceneTree
# Godot 侧「黄金样本」导出：把 CardDeck.gd 在若干局里的逐层抽取结果写成机器可读证据。
# tools/card_rules.js（Node）必须逐层复算出完全相同的结果，否则网页 Demo 的可信度不成立。
# 用法：Godot --headless --path . --script res://tools/export_card_golden.gd
# 边界：这是规则/数值复算，不是画面验证；权重与概率仍为 PROPOSAL / 待实测。

const CardDeckScript = preload("res://scripts/CardDeck.gd")
const LIB_PATH := "res://data/buff-card-library.json"
const OUT_PATH := "res://docs/card-golden-samples.json"


func _run_case(run_id: String, context: Dictionary, pick_index: int) -> Dictionary:
    var d = CardDeckScript.new()
    d.new_run(run_id, context)
    var stages: Array = []
    for stage in range(1, 10):
        var offered: Array = d.offer(stage)
        var entry := {
            "stage": stage,
            "seed": d.run_seed(stage),
            "choiceCount": d.choice_count(),
            "offered": offered.duplicate(),
            "eligibleCount": d.eligible(stage).size(),
        }
        if stage <= 8 and not offered.is_empty():
            var idx: int = pick_index % offered.size()
            var chosen := String(offered[idx])
            var ev: Dictionary = d.pick_event(stage, offered, chosen)
            var good: bool = d.pick(chosen, stage)
            entry["picked"] = chosen
            entry["pickOk"] = good
            entry["event"] = ev
        entry["peakAfter"] = d.peak_damage()
        entry["clampEvents"] = d.clamp_events().size()
        entry["violations"] = d.violations().size()
        stages.append(entry)
    return {
        "runId": run_id,
        "context": context,
        "pickIndex": pick_index,
        "stages": stages,
        "pickedCounts": d.picked_counts(),
        "peak": d.peak_damage(),
        "clampEvents": d.clamp_events().size(),
        "violations": d.violations().size(),
        "sealed": d.is_sealed(),
    }


func _init() -> void:
    var lib_text := FileAccess.get_file_as_string(LIB_PATH)
    var lib: Dictionary = JSON.parse_string(lib_text)
    var cases: Array = [
        _run_case("runA", {}, 0),
        _run_case("runW", {"affix": ["affix_wuxiang"], "realm": 9}, 1),
        _run_case("runB", {"realm": 9, "school": "jian", "slots": 3}, 2),
        _run_case("runDemo", {"realm": 9}, 1),
        _run_case("web-demo", {"realm": 9}, 0),
    ]

    # 全卡叠加的峰值 / 守卫事件（与 verify_card_rules.gd 同口径）
    var mega = CardDeckScript.new()
    mega.new_run("all")
    for c in lib["cards"]:
        mega.apply_params(String(c["id"]))

    # xorshift32 逐位样本：最强的一致性证据（浮点 randf 序列）
    var r = CardDeckScript.new()
    r.new_run("rng")
    r._rng_reset(4264777024)
    var rng_seq: Array = []
    for i in range(12):
        rng_seq.append(r._rng_randf())

    var report := {
        "version": 1,
        "generatedAt": Time.get_date_string_from_system(),
        "generator": "tools/export_card_golden.gd",
        "engine": "Godot 4.7.2.stable（headless）",
        "algorithm": "FNV-1a 32 位种子 + xorshift32 + 高 24 位定点 randf（R47）",
        "libPath": LIB_PATH,
        "cases": cases,
        "mega": {
            "peak": mega.peak_damage(),
            "clampEvents": mega.clamp_events().size(),
            "violations": mega.violations().size(),
            "offense": mega.offense_state(),
        },
        "rngSequence": rng_seq,
        "note": "黄金样本由 Godot 侧导出；Node/网页必须逐层复算一致。权重/概率仍为 PROPOSAL / 待实测。",
    }
    var out := FileAccess.open(OUT_PATH, FileAccess.WRITE)
    if out == null:
        print("GOLDEN|FAIL|写入失败")
        quit(1)
        return
    out.store_string(JSON.stringify(report, "\t") + "\n")
    out.close()
    print("GOLDEN|cases=", cases.size(), "|rng=", rng_seq.size(), "|mega_peak=", mega.peak_damage())
    print("GOLDEN|PASS|", OUT_PATH)
    quit(0)
