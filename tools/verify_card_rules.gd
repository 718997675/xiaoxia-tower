extends SceneTree
# 卡牌规则层 headless 断言：让 Godot 4.7.2 自己编译 CardDeck.gd、读运行时卡库、跑完所有规则。
# 用法：Godot --headless --path <工程根> --script res://tools/verify_card_rules.gd
# 输出：docs/card-rules-report.json（机器可读证据）+ stdout 的 VERIFY|... 行。
# 边界：这是「规则/数值」验证，不是画面验证，也不是 GUI F5 目检；权重与概率仍为待实测。
# 部分断言直接读写 CardDeck 的下划线成员做白盒检查（GDScript 无强制私有），仅为可复算取证。

const CardDeckScript = preload("res://scripts/CardDeck.gd")
const SOURCE_PATH := "res://docs/buff-card-library.json"
const RUNTIME_PATH := "res://data/buff-card-library.json"
const REPORT_PATH := "res://docs/card-rules-report.json"

var checks: Array = []
var failures: Array = []


func ok(cond: bool, label: String, detail: String = "") -> void:
    checks.append({"label": label, "ok": cond, "detail": detail})
    if cond:
        print("VERIFY|ok|", label, "|", detail)
    else:
        failures.append(label)
        print("VERIFY|FAIL|", label, "|", detail)


func _init() -> void:
    var deck = CardDeckScript.new()
    ok(deck.is_loaded() and deck.card_count() == 72,
       "卡库加载 72 张", "count=%d err=%s" % [deck.card_count(), deck.last_error()])

    # ---- 数据链路（R45）----
    var src_text := FileAccess.get_file_as_string(SOURCE_PATH)
    var run_text := FileAccess.get_file_as_string(RUNTIME_PATH)
    var src: Variant = JSON.parse_string(src_text)
    var run: Variant = JSON.parse_string(run_text)
    ok(src is Dictionary and run is Dictionary and JSON.stringify(src) == JSON.stringify(run),
       "docs 设计源与 data 运行时副本语义一致", "bytes %d/%d" % [src_text.length(), run_text.length()])
    ok(FileAccess.file_exists(SOURCE_PATH),
       ".gdignore 只挡编辑器扫描，工程内 docs/ 仍可读", "导出后该目录不进包，故运行时只读 data/")

    var lib: Dictionary = run if run is Dictionary else {}
    var ids: Array = []
    for c in lib.get("cards", []):
        ids.append(String(c["id"]))
    ok(ids.size() == 72, "运行时卡库 ID 数 = 72", "ids=%d" % ids.size())

    # ---- 确定性种子 ----
    deck.new_run("runA")
    ok(deck.run_seed(1) == 4264777024, "FNV-1a(runA:1) 跨实现可复算", "seed=%d" % deck.run_seed(1))
    var o1: Array = deck.offer(3)
    var o2: Array = deck.offer(3)
    ok(o1 == o2 and not o1.is_empty(), "同 (run_id, stage) 候选确定性一致", "offered=%s" % str(o1))
    deck.new_run("runB")
    var differs := false
    for s in range(1, 9):
        var a: Array = deck.offer(s)
        var b: Array = (func(st: int) -> Array:
            var d = CardDeckScript.new()
            d.new_run("runA")
            return d.offer(st)).call(s)
        if a != b:
            differs = true
    ok(differs, "不同 run_id 的抽卡序列确实不同", "8 层逐一比对")

    # ---- 8 次弹卡 / 第 9 层不弹 / 同类最多 1 张 ----
    deck.new_run("runA", {"realm": 9, "school": "jian", "slots": 3})
    var flow_ok := true
    var flow_log: Array = []
    for stage in range(1, 10):
        var offered: Array = deck.offer(stage)
        flow_log.append("s%d:%d" % [stage, offered.size()])
        if stage > 8:
            if not offered.is_empty():
                flow_ok = false
            continue
        if offered.is_empty() or offered.size() > 3:
            flow_ok = false
        var cats: Dictionary = {}
        for cid in offered:
            var cat := String(deck._by_id[cid]["cat"])
            if cats.has(cat):
                flow_ok = false
            cats[cat] = true
        if not offered.is_empty():
            if not deck.pick(String(offered[0]), stage):
                flow_ok = false
    ok(flow_ok, "1–8 层各弹一次 / 第 9 层不弹 / 同类最多 1 张", " ".join(flow_log))
    var total_picks := 0
    for key in deck.picked_counts().keys():
        total_picks += int(deck.picked_counts()[key])
    # 堆叠允许同一张卡被重复选中，故按「总次数」而非「不同 ID 数」断言。
    # 第 19 轮口径修正：card_sheli / card_wuxin 带 stop_draw，玩家选到即封牌，
    # 后续层不再弹卡（网页流程实测 browser-check 第 2 层即触发）。故 8 次是上限而非必然；
    # 本断言只针对「该样例局未触发封牌」的确定性序列，不得读成「每局必然 8 次」。
    ok(total_picks == 8, "本样例局 8 次选择（堆叠可重复；封牌卡未触发，8 次是上限）",
       "total=%d unique=%d" % [total_picks, deck.picked_counts().size()])

    # ---- 词缀联动 / 无相破 ----
    deck.new_run("runW", {"affix": ["affix_wuxiang"], "realm": 9})
    ok(deck.choice_count() == 2 and deck.offer(1).size() <= 2,
       "无相词缀把 3 选 1 压成 2 选 1", "count=%d" % deck.choice_count())
    deck._picked["card_wuxiangpo"] = 1
    ok(deck.choice_count() == 3, "无相破把候选恢复为 3 张", "count=%d" % deck.choice_count())

    # ---- 互斥双向 / 堆叠 / 前置 / 解锁 / 封牌 ----
    deck.new_run("runE", {"realm": 9})
    deck._picked["card_nianzhuan"] = 1
    ok(deck._excluded("card_juling"), "excl 正向：已选 A 则 B 不进池", "nianzhuan→juling")
    deck.new_run("runE2", {"realm": 9})
    deck._picked["card_juling"] = 1
    ok(deck._excluded("card_nianzhuan"), "excl 反向同样生效", "juling→nianzhuan")

    deck.new_run("runS", {"realm": 9})
    deck._picked["card_jianfeng"] = 3
    ok(not deck.eligible(1).has("card_jianfeng"), "堆满 stack=3 后移出池", "picked=3")
    deck._picked["card_jianfeng"] = 1
    ok(deck.eligible(1).has("card_jianfeng"), "未堆满仍可再选（堆叠语义）", "picked=1")

    deck.new_run("runR", {"realm": 1})
    ok(not deck.eligible(1).has("card_duozhu"), "realm=1 时 realm:6 解锁卡不进池", "unlock")
    deck.new_run("runR2", {"realm": 9})
    ok(not deck.eligible(1).has("card_duozhu"), "stage=1 不满足 stage>=5 前置", "req")
    ok(deck.eligible(5).has("card_duozhu"), "realm>=6 且 stage>=5 才进池", "req+unlock")

    deck.new_run("runF")
    deck._sealed = true
    ok(deck.offer(1).is_empty(), "封牌后本局不再弹卡", "card_sheli / card_wuxin")

    # ---- 五上界（DF-21 / R32）：逐卡扫 + 全卡叠加 ----
    var per_card_ok := true
    var touched := 0
    for cid in ids:
        var d = CardDeckScript.new()
        d.new_run("scan")
        d.apply_params(cid)
        if not d.damage_ceiling_ok():
            per_card_ok = false
        if d.peak_damage() > 3996.0 or d.peak_damage() >= 4400.0:
            per_card_ok = false
        if not d.violations().is_empty():
            per_card_ok = false
        if not d.clamp_events().is_empty():
            touched += 1
    ok(per_card_ok, "72 张卡逐张生效都不破五上界 / 无 pool+cap 声明违规", "guard_hits=%d" % touched)

    var mega = CardDeckScript.new()
    mega.new_run("all")
    for cid in ids:
        mega.apply_params(cid)
    ok(mega.damage_ceiling_ok() and mega.peak_damage() <= 3996.0,
       "72 卡全生效峰值仍 3996 < Boss 4400", "peak=%d" % int(mega.peak_damage()))
    ok(not mega.clamp_events().is_empty(),
       "上界守卫确实拦下过卡牌增量（非空跑）", "events=%d" % mega.clamp_events().size())

    # ---- 埋点字段 ----
    deck.new_run("runT")
    var ev: Dictionary = deck.pick_event(1, ["card_jianfeng"], "card_jianfeng")
    var keys_ok := true
    for k in ["stage", "offered", "picked", "card_id", "card_rarity", "card_category", "seen_before", "run_id", "seed"]:
        if not ev.has(k):
            keys_ok = false
    ok(keys_ok, "pick_event 含 11 §5 增补字段", "keys=%d" % ev.size())

    # ---- 落报告 ----
    var report := {
        "version": 1,
        "generatedAt": Time.get_date_string_from_system(),
        "generator": "tools/verify_card_rules.gd",
        "engine": "Godot 4.7.2.stable（headless）",
        "scope": "层间三选一卡牌规则层 · 离线断言（非 GUI 目检）",
        "verdict": "PASS" if failures.is_empty() else "FAIL",
        "checks": checks,
        "summary": {
            "total": checks.size(),
            "passed": checks.size() - failures.size(),
            "failed": failures.size(),
            "cards": ids.size(),
            "peakDamage": mega.peak_damage(),
            "guardEvents": mega.clamp_events().size(),
        },
        "note": "权重/概率/层数曲线均为 PROPOSAL / 待实测；本报告只证明规则与上界守卫可复算，不证明平衡性或画面。",
    }
    var out := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
    if out != null:
        out.store_string(JSON.stringify(report, "\t") + "\n")
        out.close()
        print("VERIFY|report=", REPORT_PATH)
    else:
        failures.append("报告写入失败")
        print("VERIFY|FAIL|报告写入失败")

    if failures.is_empty():
        print("VERIFY|PASS|checks=", checks.size(), "|cards=72|peak=3996")
        quit(0)
    else:
        print("VERIFY|FAIL|", failures.size(), " 项：", str(failures))
        quit(1)
