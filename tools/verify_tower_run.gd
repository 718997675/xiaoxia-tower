extends SceneTree
# 第 41 轮 · Godot 可玩原型的 headless 结构与状态机证据。
# 用法：Godot --headless --path <工程根> --script res://tools/verify_tower_run.gd
#
# 只证明：场景能加载 / 脚本能编译 / 节点树齐 / 资源齐 / 卡库 72 张 /
#         抽取确定性 / 9 层状态机能从菜单走到结算 / 伤害红线未破。
# 不证明：GUI 画面、中文是否成字、像素是否糊、手感、平衡 —— 那些仍需用户按 F5 目检。
# 结果写 docs/tower-run-verify-report.json，供 tools/final_selfcheck.py 第 39 项复算。

const BattleFormula = preload("res://scripts/BattleFormula.gd")
const REPORT_PATH := "res://docs/tower-run-verify-report.json"

var checks: Array = []
var passed: int = 0
var failed: int = 0
var ended_count: int = 0


func _ck(name: String, ok: bool, detail: String = "") -> void:
	checks.append({"name": name, "ok": ok, "detail": detail})
	if ok:
		passed += 1
	else:
		failed += 1
	print("VERIFY|", "PASS" if ok else "FAIL", "|", name, "|", detail)


func _on_ended(_result: String, _layer: int) -> void:
	ended_count += 1


func _count_png(dir_path: String) -> int:
	var d := DirAccess.open(dir_path)
	if d == null:
		return 0
	var n: int = 0
	for f in d.get_files():
		if f.ends_with(".png"):
			n += 1
	return n


func _init() -> void:
	var packed := load("res://scenes/TowerRun.tscn") as PackedScene
	if packed == null:
		_ck("scene_load", false, "TowerRun.tscn 打不开")
		_finish({})
		return
	_ck("scene_load", true, "TowerRun.tscn")
	var inst := packed.instantiate()
	root.add_child(inst)
	# --script 模式不会自动触发子节点 _ready()（见 tools/verify_minimal_run.gd 注释），
	# 按依赖顺序显式补一次；用「已初始化标记」判重，避免重复建 UI。
	var stage_node := inst.get_node("Stage") as Node
	var hud_node := inst.get_node("HUD") as Node
	var picker_node := inst.get_node("RewardPicker") as Node
	if stage_node.get("player") == null:
		stage_node.call("_ready")
	if hud_node.get("root") == null:
		hud_node.call("_ready")
	if picker_node.get("root") == null:
		picker_node.call("_ready")
	if inst.menu_root == null:
		inst.call("_ready")
	inst.run_ended.connect(_on_ended)

	# ---- 节点树（docs/01 §12） ----
	var node_names: Array = ["Stage", "HUD", "RewardPicker", "MenuLayer", "ResultLayer"]
	var missing: Array = []
	for n in node_names:
		if inst.get_node_or_null(NodePath(n)) == null:
			missing.append(n)
	_ck("node_tree", missing.is_empty(), "缺节点=" + str(missing))
	_ck("main_scene", String(ProjectSettings.get_setting("application/run/main_scene")) \
		== "res://scenes/TowerRun.tscn", String(ProjectSettings.get_setting("application/run/main_scene")))
	_ck("minimal_run_retained", ResourceLoader.exists("res://scenes/MinimalRun.tscn"),
		"门禁验证场景保留")

	# ---- 数据与资源 ----
	_ck("cards_loaded", inst.deck.card_count() == 72 and inst.library.size() == 72,
		"deck=%d library=%d" % [inst.deck.card_count(), inst.library.size()])
	_ck("card_art_72", _count_png("res://assets/ui/card_art/") == 72,
		"png=%d" % _count_png("res://assets/ui/card_art/"))
	_ck("frozen_frames", _count_png("res://assets/ui/cards/") == 10,
		"png=%d（4 卡框 + 6 纹样）" % _count_png("res://assets/ui/cards/"))
	var stages: Array = BattleFormula.stages()
	_ck("nine_stages", stages.size() == 9, "count=%d" % stages.size())
	var max_hit: int = BattleFormula.max_hit()
	_ck("damage_ceiling", max_hit < int(BattleFormula.BOSS_HP_REFERENCE),
		"maxHit=%d / 4400" % max_hit)
	var bg_ok: bool = true
	for key in ["bg_normal", "bg_rest", "bg_high", "bg_boss"]:
		if not ResourceLoader.exists("res://assets/bg/%s/%s_composite.png" % [key, key]):
			bg_ok = false
	_ck("bg_composites", bg_ok, "4 张 480x270 背景合成图")
	var vfx_ok: bool = true
	for s in RunConfig.SKILLS:
		if not ResourceLoader.exists("res://assets/vfx/frames/%s_00.png" % String(s["vfx"])):
			vfx_ok = false
	_ck("skill_vfx", vfx_ok, "4 技能首帧")

	# ---- 抽取确定性（R47 xorshift32） ----
	var probe := CardDeck.new()
	probe.new_run("verify-r41")
	var a: Array = probe.offer(1)
	var b: Array = probe.offer(1)
	_ck("offer_deterministic", a == b and a.size() == 3,
		"offer(1)=" + str(a))

	# ---- 完整闭环：菜单 → 9 层战斗 → 8 次选卡 → 结算 ----
	inst.start_run("verify-r41")
	var s0: Dictionary = inst.debug_state()
	_ck("start_battle", int(s0["state"]) == 1 and int(s0["stage_index"]) == 0,
		"state=%d stage=%d" % [int(s0["state"]), int(s0["stage_index"])])

	inst.debug_clear_current_stage()
	var s1: Dictionary = inst.debug_state()
	_ck("stage1_to_draft", int(s1["state"]) == 2, "state=%d" % int(s1["state"]))
	_ck("draft_three_distinct", inst.picker.offered.size() == 3 \
		and inst.picker.offered[0] != inst.picker.offered[1] \
		and inst.picker.offered[1] != inst.picker.offered[2],
		"offered=" + str(inst.picker.offered))
	inst.debug_pick_first()
	var s2: Dictionary = inst.debug_state()
	_ck("pick_to_stage2", int(s2["state"]) == 1 and int(s2["stage_index"]) == 1 \
		and inst.picks.size() == 1,
		"state=%d stage=%d picks=%d" % [int(s2["state"]), int(s2["stage_index"]),
		inst.picks.size()])

	var guard: int = 0
	while String(inst.debug_state()["result"]) == "" and guard < 40:
		var st: int = int(inst.debug_state()["state"])
		if st == 1:
			inst.debug_clear_current_stage()
		elif st == 2:
			inst.debug_pick_first()
		else:
			break
		guard += 1
	var final: Dictionary = inst.debug_state()
	_ck("run_finished_win", String(final["result"]) == "win" and ended_count == 1,
		"result=%s runEnded=%d loopSteps=%d" % [String(final["result"]), ended_count, guard])
	_ck("reached_last_stage", int(final["stage_index"]) == 8,
		"stage_index=%d" % int(final["stage_index"]))
	_ck("picks_within_cap", inst.picks.size() <= 8,
		"picks=%d（R49 封牌可少于 8）" % inst.picks.size())
	_ck("ceiling_not_violated", bool(final["damage_ceiling_ok"]),
		"peak<4400 且违规 0")

	_finish({
		"round": 41,
		"engine": "4.7.2.stable",
		"mainScene": String(ProjectSettings.get_setting("application/run/main_scene")),
		"cardsLoaded": inst.deck.card_count(),
		"stages": stages.size(),
		"maxHit": max_hit,
		"finalResult": String(final["result"]),
		"reachedStage": int(final["stage_index"]) + 1,
		"picks": inst.picks.size(),
		"runEndedSignals": ended_count,
		"boundary": "headless 结构与状态机证据；GUI 画面 / 中文字形 / 手感 / 平衡均未目检",
	})


func _finish(extra: Dictionary) -> void:
	var report: Dictionary = extra.duplicate()
	report["checks"] = checks
	report["passed"] = passed
	report["failed"] = failed
	report["status"] = "PASS" if failed == 0 else "FAIL"
	var f := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(report, "\t"))
		f.close()
	print("VERIFY|SUMMARY|passed=%d failed=%d|%s" % [passed, failed, report["status"]])
	quit(0 if failed == 0 else 1)
