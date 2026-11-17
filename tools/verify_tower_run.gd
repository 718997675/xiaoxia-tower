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
var milestone_count: int = 0
var last_milestone_tier: int = -1


func _on_combo_milestone(tier: int, _label: String) -> void:
	milestone_count += 1
	last_milestone_tier = tier


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
	# 第 46 轮：订阅连击里程碑信号，验证跨阈值确实发出。
	stage_node.connect("combo_milestone", Callable(self, "_on_combo_milestone"))
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

	# ---- 第 42 轮：机制卡效果落地到战斗层（可观测、可复算） ----
	var eff: CardEffects = inst.effects as CardEffects
	_ck("effects_compiler_loaded", eff != null and eff.is_loaded() and eff.card_count() == 72,
		"cards=%d" % (eff.card_count() if eff != null else -1))
	# 默认 mods：reset 后上限就是 RunConfig 常量、护盾 0、reveal=false。
	stage_node.call("apply_mods", eff.compile([]))
	stage_node.call("reset_player")
	var dflt: Dictionary = stage_node.call("snapshot")
	_ck("effects_default_baseline",
		absf(float(dflt["max_hp"]) - RunConfig.PLAYER_MAX_HP) < 0.001 \
		and absf(float(dflt["max_spirit"]) - RunConfig.PLAYER_MAX_SPIRIT) < 0.001 \
		and float(dflt["shield"]) == 0.0 and bool(dflt["reveal"]) == false,
		"maxHP=%d maxSP=%d shield=%d reveal=%s" % [int(dflt["max_hp"]),
			int(dflt["max_spirit"]), int(dflt["shield"]), str(dflt["reveal"])])
	# 寿元（hp_max +60）：注入后 max_hp=360，可观测。
	stage_node.call("apply_mods", eff.compile(["card_shouyuan"]))
	var hp_card: Dictionary = stage_node.call("snapshot")
	_ck("effects_hp_max_applied",
		absf(float(hp_card["max_hp"]) - (RunConfig.PLAYER_MAX_HP + 60.0)) < 0.001,
		"maxHP=%d（寿元 +60）" % int(hp_card["max_hp"]))
	# 卷甲（shield_max 20）+ 天人感应（reveal）：注入后 shield=20、reveal=true。
	stage_node.call("apply_mods", eff.compile(["card_huti", "card_tianren"]))
	var util_card: Dictionary = stage_node.call("snapshot")
	_ck("effects_shield_reveal_applied",
		float(util_card["shield"]) == 20.0 and bool(util_card["reveal"]) == true,
		"shield=%d reveal=%s" % [int(util_card["shield"]), str(util_card["reveal"])])
	# 还原默认，避免影响后续任何读取。
	stage_node.call("apply_mods", eff.compile([]))

	# ---- 第 43 轮：Boss 三阶段（表现层，划分对齐网页 0.66/0.33，R56 未跨端对齐） ----
	# Boss skill 真帧资源存在（判官 4 帧 / 塔主 10 帧）。
	var boss_skill_ok: bool = true
	for bid in ["boss_judge", "boss_tower_lord"]:
		var f0: String = "res://assets/boss/" + bid + "_skill_r_00.png"
		if not ResourceLoader.exists(f0):
			boss_skill_ok = false
	_ck("boss_skill_frames", boss_skill_ok, "判官/塔主 skill 真帧首帧存在")
	# 用冻结第 5 层（boss_judge）启一层，阶段应初始化为 1 且加载 skill 动画。
	stage_node.call("start_stage", 4, inst.deck)
	var bp0: Dictionary = stage_node.call("debug_boss_probe")
	_ck("boss_phase_init", int(bp0.get("phase", -1)) == 1 \
		and bool(bp0.get("has_skill_anim", false)) \
		and int(bp0.get("skill_frames", 0)) >= 4,
		"phase=%d skillFrames=%d" % [int(bp0.get("phase", -1)), int(bp0.get("skill_frames", 0))])
	# 血量比 0.5 → 阶段 2；snapshot 暴露 boss_phase=2。
	stage_node.call("debug_set_boss_hp_ratio", 0.5)
	var bp2: Dictionary = stage_node.call("debug_boss_probe")
	var snap2: Dictionary = stage_node.call("snapshot")
	_ck("boss_phase_2", int(bp2.get("phase", -1)) == 2 \
		and int(snap2.get("boss_phase", -1)) == 2,
		"probe=%d snapshot=%d" % [int(bp2.get("phase", -1)), int(snap2.get("boss_phase", -1))])
	# 血量比 0.2 → 阶段 3；阶段只升不降。
	stage_node.call("debug_set_boss_hp_ratio", 0.2)
	var bp3: Dictionary = stage_node.call("debug_boss_probe")
	_ck("boss_phase_3", int(bp3.get("phase", -1)) == 3,
		"phase=%d" % int(bp3.get("phase", -1)))
	stage_node.call("debug_set_boss_hp_ratio", 0.9)  # 回血也不应降阶段
	_ck("boss_phase_no_downgrade", int(stage_node.call("debug_boss_probe").get("phase", -1)) == 3,
		"回血到 0.9 仍为 3")
	# 阶段系数数组：长度 3、逐阶段伤害/攻速系数单调递增（非 Boss slot=0 恒为 1.0）。
	var atk_scale: Array = RunConfig.BOSS_PHASE_ATK_SCALE
	var int_scale: Array = RunConfig.BOSS_PHASE_ATK_INTERVAL_SCALE
	_ck("boss_phase_scales", atk_scale.size() == 3 and int_scale.size() == 3 \
		and float(atk_scale[0]) < float(atk_scale[1]) and float(atk_scale[1]) < float(atk_scale[2]) \
		and float(int_scale[0]) > float(int_scale[1]) and float(int_scale[1]) > float(int_scale[2]),
		"atk=%s interval=%s" % [str(atk_scale), str(int_scale)])
	# 非 Boss 层（第 1 层）无阶段、snapshot.boss_phase=0。
	stage_node.call("start_stage", 0, inst.deck)
	var nb: Dictionary = stage_node.call("debug_boss_probe")
	var nsnap: Dictionary = stage_node.call("snapshot")
	_ck("boss_phase_nonboss_zero", nb.is_empty() and int(nsnap.get("boss_phase", -1)) == 0,
		"probe空=%s snapshot=%d" % [str(nb.is_empty()), int(nsnap.get("boss_phase", -1))])

	# ---- 第 44 轮：Boss 远程技能（投射物，表现层，R56 未跨端对齐） ----
	_ck("boss_proj_vfx_reused", ResourceLoader.exists(
		"res://assets/vfx/frames/vfx_flying_sword_00.png"),
		"复用现有飞剑特效帧，未新增出图")
	# 回到 Boss 层（上一段测试末尾停在非 Boss 层）。
	stage_node.call("start_stage", 4, inst.deck)
	stage_node.call("debug_clear_projectiles")
	# 阶段 1 施法发 1 弹。
	var shots1: int = int(stage_node.call("debug_boss_fire_skill"))
	_ck("boss_skill_shots_phase1", shots1 == 1, "阶段1弹数=%d（应 1）" % shots1)
	# 阶段 3 施法发 3 弹。
	stage_node.call("debug_clear_projectiles")
	stage_node.call("debug_set_boss_hp_ratio", 0.2)
	var shots3: int = int(stage_node.call("debug_boss_fire_skill"))
	var snap_proj: Dictionary = stage_node.call("snapshot")
	_ck("boss_skill_shots_phase3", shots3 == 3 \
		and int(snap_proj.get("projectile_count", -1)) == 3,
		"阶段3弹数=%d snapshot=%d（应 3）" % [shots3, int(snap_proj.get("projectile_count", -1))])
	# 命中扣血：把 3 发弹瞬移到玩家身上推进一帧，HP 应下降。
	stage_node.call("debug_clear_projectiles")
	stage_node.call("debug_boss_fire_skill")
	var hp_before: float = float(stage_node.call("snapshot").get("hp", 0.0))
	stage_node.call("debug_place_projectiles_on_player")
	stage_node.call("debug_tick_projectiles", 0.016)
	var hp_after: float = float(stage_node.call("snapshot").get("hp", 0.0))
	_ck("boss_proj_hit_damages", hp_after < hp_before and int(stage_node.call("debug_projectiles").size()) == 0,
		"HP %.1f→%.1f 命中后投射物清空" % [hp_before, hp_after])
	# 闪避无敌：设 invuln>0 后投射物命中不扣血。
	stage_node.call("debug_clear_projectiles")
	stage_node.call("debug_boss_fire_skill")
	stage_node.set("invuln", 1.0)
	var hp_before_dodge: float = float(stage_node.call("snapshot").get("hp", 0.0))
	stage_node.call("debug_place_projectiles_on_player")
	stage_node.call("debug_tick_projectiles", 0.016)
	var hp_after_dodge: float = float(stage_node.call("snapshot").get("hp", 0.0))
	_ck("boss_proj_dodge_ignores", absf(hp_after_dodge - hp_before_dodge) < 0.001,
		"无敌时 HP %.1f→%.1f 不扣血" % [hp_before_dodge, hp_after_dodge])
	stage_node.set("invuln", 0.0)
	# 切层清理投射物 + 非 Boss 层不施法。
	stage_node.call("debug_boss_fire_skill")
	var n_before: int = int(stage_node.call("debug_projectiles").size())
	stage_node.call("start_stage", 0, inst.deck)
	var n_after: int = int(stage_node.call("debug_projectiles").size())
	var shots_nonboss: int = int(stage_node.call("debug_boss_fire_skill"))
	_ck("boss_proj_clear_on_stage_change", n_before > 0 and n_after == 0 and shots_nonboss == 0,
		"切层前=%d 切层后=%d 非Boss施法=%d" % [n_before, n_after, shots_nonboss])

	# ===== 第 45 轮：杂兵攻击方式差异化 =====
	# stage 6（index=6）含全部 4 种杂兵，可一次覆盖所有风格。
	stage_node.call("start_stage", 6, inst.deck)
	stage_node.call("debug_clear_projectiles")
	stage_node.set("hp", 300.0)
	stage_node.set("invuln", 0.0)
	# 1. 风格表结构 + 帧资源存在（4 种杂兵各有 vfx，未新增出图）。
	var sty_cfg: Dictionary = RunConfig.MOB_ATTACK_STYLE
	var mob_ids: Array = ["mob_shanxiao", "mob_zhi_kui", "mob_yin_bing", "mob_jian_hun"]
	var cfg_ok: bool = sty_cfg.size() == 4
	for mid in mob_ids:
		if not sty_cfg.has(mid):
			cfg_ok = false
			continue
		var mid_vfx: String = String((sty_cfg[mid] as Dictionary).get("vfx", ""))
		if mid_vfx.is_empty() \
				or not ResourceLoader.exists("res://assets/vfx/frames/%s_00.png" % mid_vfx):
			cfg_ok = false
	_ck("mob_style_table_shape", cfg_ok, "4 风格齐备且 vfx 帧存在（size=%d）" % sty_cfg.size())
	# 2. 风格确实有区分：重击 CD/伤害 > 疾刺；纸傀为远程；阴兵基准 dmg=1.0。
	var shan: Dictionary = sty_cfg["mob_shanxiao"]
	var jian: Dictionary = sty_cfg["mob_jian_hun"]
	var yin: Dictionary = sty_cfg["mob_yin_bing"]
	var zhi: Dictionary = sty_cfg["mob_zhi_kui"]
	_ck("mob_styles_distinct", float(shan["cd"]) > float(jian["cd"]) \
		and float(shan["dmg"]) > float(jian["dmg"]) \
		and bool(zhi["ranged"]) and absf(float(yin["dmg"]) - 1.0) < 0.001,
		"重击 cd=%.1f/dmg=%.2f 疾刺 cd=%.1f/dmg=%.2f 纸傀远程=%s 阴兵 dmg=%.1f" % [
			float(shan["cd"]), float(shan["dmg"]), float(jian["cd"]), float(jian["dmg"]),
			str(bool(zhi["ranged"])), float(yin["dmg"])])
	# 3. 层内敌人携带正确风格快照；Boss 层风格为空（走原行为）。
	var styles: Array = stage_node.call("debug_enemy_styles")
	var by_id: Dictionary = {}
	for s in styles:
		by_id[String(s["id"])] = s
	_ck("mob_styles_in_stage", by_id.size() == 4 \
		and bool((by_id["mob_zhi_kui"] as Dictionary)["ranged"]) \
		and not bool((by_id["mob_shanxiao"] as Dictionary)["ranged"]),
		"stage6 敌人数=%d 纸傀远程=%s 山魈远程=%s" % [by_id.size(),
			str(bool((by_id["mob_zhi_kui"] as Dictionary)["ranged"])),
			str(bool((by_id["mob_shanxiao"] as Dictionary)["ranged"]))])
	# 4. 纸傀远程发弹：强制攻击返回 1 弹，投射物 vfx 用纸傀帧（非 Boss 飞剑）。
	var unit_incoming: float = RunConfig.ENEMY_ATTACK_BASE \
		+ RunConfig.ENEMY_ATTACK_PER_STAGE * 6.0 + 34.0 * 0.12
	var zhi_shots: int = int(stage_node.call("debug_mob_attack", "mob_zhi_kui", unit_incoming))
	var zhi_projs: Array = stage_node.call("debug_projectiles")
	_ck("mob_ranged_fires", zhi_shots == 1 and zhi_projs.size() == 1,
		"纸傀发弹=%d 在飞=%d" % [zhi_shots, zhi_projs.size()])
	# 5. 远程弹命中扣血（走 _hurt_player 统一路径）。
	var hp_r_before: float = float(stage_node.call("snapshot").get("hp", 0.0))
	stage_node.call("debug_place_projectiles_on_player")
	stage_node.call("debug_tick_projectiles", 0.016)
	var hp_r_after: float = float(stage_node.call("snapshot").get("hp", 0.0))
	_ck("mob_ranged_hit_damages", hp_r_after < hp_r_before,
		"远程弹命中 HP %.1f→%.1f" % [hp_r_before, hp_r_after])
	# 6. 闪避无敌时远程弹穿过不扣血。
	stage_node.call("debug_clear_projectiles")
	stage_node.call("debug_mob_attack", "mob_zhi_kui", unit_incoming)
	stage_node.set("invuln", 1.0)
	var hp_d_before: float = float(stage_node.call("snapshot").get("hp", 0.0))
	stage_node.call("debug_place_projectiles_on_player")
	stage_node.call("debug_tick_projectiles", 0.016)
	var hp_d_after: float = float(stage_node.call("snapshot").get("hp", 0.0))
	_ck("mob_ranged_dodge_ignores", absf(hp_d_after - hp_d_before) < 0.001,
		"无敌 HP %.1f→%.1f 不扣血" % [hp_d_before, hp_d_after])
	stage_node.set("invuln", 0.0)
	stage_node.call("debug_clear_projectiles")
	# 7. 近战风格伤害比例落地：重击 > 疾刺（同一 incoming 基准，各打一次）。
	stage_node.set("hp", 300.0)
	stage_node.call("debug_mob_attack", "mob_shanxiao", unit_incoming)
	var dmg_heavy: float = 300.0 - float(stage_node.call("snapshot").get("hp", 0.0))
	stage_node.set("hp", 300.0)
	stage_node.call("debug_mob_attack", "mob_jian_hun", unit_incoming)
	var dmg_quick: float = 300.0 - float(stage_node.call("snapshot").get("hp", 0.0))
	_ck("mob_melee_dmg_scaled", dmg_heavy > dmg_quick and dmg_quick > 0.0,
		"重击扣 %.1f > 疾刺扣 %.1f" % [dmg_heavy, dmg_quick])
	# 8. Boss 层敌人风格为空（不注入杂兵风格，逐字段走第 41 轮口径）。
	stage_node.call("start_stage", 4, inst.deck)
	var bstyles: Array = stage_node.call("debug_enemy_styles")
	var boss_style_empty: bool = true
	for bs in bstyles:
		if bool((bs as Dictionary)["boss"]) and not String((bs as Dictionary)["style"]).is_empty():
			boss_style_empty = false
	_ck("mob_boss_style_unchanged", boss_style_empty, "Boss 层无杂兵风格注入")

	# ===== 第 46 轮：战斗打击感反馈 =====
	# 1. 震动专用相机存在，offset 可衰减归零（--script 不自动跑 _process，用 debug tick）。
	stage_node.call("start_stage", 0, inst.deck)
	stage_node.call("debug_tick_shake", 1.0)
	var shk0: Dictionary = stage_node.call("debug_shake")
	_ck("feedback_camera_ready", bool(shk0.get("has_camera", false)) \
		and absf(float(shk0.get("amount", -1.0))) < 0.001,
		"相机存在=%s 初始幅度=%.2f" % [str(bool(shk0.get("has_camera", false))),
			float(shk0.get("amount", -1.0))])
	# 2. 触发震动 → 幅度>0 且 offset 非零（画面抖动）；推进足够时间 → 归零。
	stage_node.call("debug_trigger_shake", RunConfig.HIT_SHAKE_KILL)
	var shk1: Dictionary = stage_node.call("debug_shake")
	stage_node.call("debug_tick_shake", 0.016)
	var shk2: Dictionary = stage_node.call("debug_shake")
	stage_node.call("debug_tick_shake", 1.0)
	var shk3: Dictionary = stage_node.call("debug_shake")
	_ck("feedback_shake_then_decay", float(shk1.get("amount", 0.0)) > 0.0 \
		and absf(float(shk2.get("offset_x", 0.0))) + absf(float(shk2.get("offset_y", 0.0))) > 0.0 \
		and absf(float(shk3.get("amount", -1.0))) < 0.001,
		"触发=%.2f offset=(%.2f,%.2f) 衰减后=%.2f" % [float(shk1.get("amount", 0.0)),
			float(shk2.get("offset_x", 0.0)), float(shk2.get("offset_y", 0.0)),
			float(shk3.get("amount", -1.0))])
	# 3. 玩家真扣血触发 hurt 震动；护盾吸收 / 闪避不应触发（数值路径不变）。
	var hs_before: int = int((stage_node.call("snapshot").get("feedback_stats", {}) as Dictionary).get("hurt_shakes", 0))
	stage_node.set("invuln", 0.0)
	stage_node.set("hp", 300.0)
	stage_node.call("debug_mob_attack", "mob_shanxiao", 50.0)
	var hs_after: int = int((stage_node.call("snapshot").get("feedback_stats", {}) as Dictionary).get("hurt_shakes", 0))
	stage_node.set("invuln", 1.0)
	stage_node.call("debug_mob_attack", "mob_shanxiao", 50.0)
	var hs_dodge: int = int((stage_node.call("snapshot").get("feedback_stats", {}) as Dictionary).get("hurt_shakes", 0))
	_ck("feedback_hurt_shake", hs_after == hs_before + 1 and hs_dodge == hs_after,
		"真扣血 %d→%d，闪避不增 %d" % [hs_before, hs_after, hs_dodge])
	stage_node.set("invuln", 0.0)
	# 4. 连击里程碑：重置后依次跨 0.5/1.0/1.5 三档，signal 发 3 次、combo_tier=2。
	stage_node.call("reset_player")
	var mc_before: int = milestone_count
	stage_node.call("debug_set_combo", 0.6)
	stage_node.call("debug_set_combo", 1.1)
	stage_node.call("debug_set_combo", 1.5)
	var m_snap: Dictionary = stage_node.call("snapshot")
	_ck("feedback_combo_milestones", milestone_count == mc_before + 3 \
		and int(m_snap.get("combo_tier", -1)) == 2 and last_milestone_tier == 2,
		"signal=%d combo_tier=%d 末档=%d" % [milestone_count - mc_before,
			int(m_snap.get("combo_tier", -1)), last_milestone_tier])
	# 5. 里程碑不重复触发：再设同档/低档不再发 signal。
	var mc_after: int = milestone_count
	stage_node.call("debug_set_combo", 0.7)
	_ck("feedback_milestone_once", milestone_count == mc_after,
		"同档重设不重复发 signal（计数 %d）" % milestone_count)
	# 6. 反馈统计字段齐备（暴击字号 / 击杀标识 / 各类震动计数可观测）。
	var fb: Dictionary = m_snap.get("feedback_stats", {}) as Dictionary
	var fb_keys: Array = ["crit_shakes", "kill_shakes", "hurt_shakes",
		"milestones", "crit_labels", "kill_labels"]
	var fb_ok: bool = true
	for k in fb_keys:
		if not fb.has(k):
			fb_ok = false
	_ck("feedback_stats_observable", fb_ok, "反馈统计字段齐备=%s" % str(fb_ok))

	# ---- 第 47 轮：玩家技能施法演出差异化（纯视觉，不改战斗数值）----
	# 1. 四技能形态表结构齐备、帧存在、形态互不相同。
	var styles_seen: Dictionary = {}
	var cast_table_ok: bool = true
	for s in RunConfig.SKILLS:
		var cfg: Dictionary = RunConfig.SKILL_CAST_STYLE.get(String(s["id"]), {}) as Dictionary
		if cfg.is_empty() or String(cfg.get("style", "")).is_empty():
			cast_table_ok = false
			continue
		var cf: String = "res://assets/vfx/frames/%s_00.png" % String(cfg.get("vfx", ""))
		if not ResourceLoader.exists(cf):
			cast_table_ok = false
		styles_seen[String(cfg["style"])] = true
	_ck("cast_style_table", cast_table_ok and styles_seen.size() == 4,
		"4 技能形态齐备=%s 形态种类=%d" % [str(cast_table_ok), styles_seen.size()])

	# 2. dash（剑气斩 idx0）：水平速度主导、垂直速度≈0，起点在身前。
	stage_node.call("debug_clear_cast_fx")
	stage_node.call("debug_spawn_cast_fx", 0)
	var dash_fx: Array = stage_node.call("debug_cast_fx") as Array
	var dash_ok: bool = dash_fx.size() == 1 and absf(dash_fx[0].get("vx", 0.0)) > 100.0 \
		and absf(dash_fx[0].get("vy", 0.0)) < 0.01 \
		and String(dash_fx[0].get("style", "")) == "dash"
	_ck("cast_dash_forward", dash_ok, "dash 节点=%d vx=%.0f vy=%.0f" % [dash_fx.size(),
		dash_fx[0].get("vx", 0.0) if dash_fx.size() > 0 else 0.0,
		dash_fx[0].get("vy", 0.0) if dash_fx.size() > 0 else 0.0])

	# 3. strike（引雷符 idx1）：垂直下落速度主导、水平≈0，起点在高处（y<GROUND_Y）。
	stage_node.call("debug_clear_cast_fx")
	stage_node.call("debug_spawn_cast_fx", 1)
	var strike_fx: Array = stage_node.call("debug_cast_fx") as Array
	var strike_ok: bool = strike_fx.size() == 1 and strike_fx[0].get("vy", 0.0) > 100.0 \
		and absf(strike_fx[0].get("vx", 0.0)) < 0.01 \
		and strike_fx[0].get("y", 999.0) < float(RunConfig.GROUND_Y) - 50.0 \
		and String(strike_fx[0].get("style", "")) == "strike"
	_ck("cast_strike_drop", strike_ok, "strike vy=%.0f y=%.0f" % [strike_fx[0].get("vy", 0.0),
		strike_fx[0].get("y", 0.0)])

	# 4. spray（丹火 idx2）：3 个节点、扇形（vy 分散，有正有负）。
	stage_node.call("debug_clear_cast_fx")
	stage_node.call("debug_spawn_cast_fx", 2)
	var spray_fx: Array = stage_node.call("debug_cast_fx") as Array
	var vy_min: float = 999.0
	var vy_max: float = -999.0
	for sx in spray_fx:
		vy_min = minf(vy_min, sx.get("vy", 0.0))
		vy_max = maxf(vy_max, sx.get("vy", 0.0))
	var spray_ok: bool = spray_fx.size() == 3 and vy_max - vy_min > 10.0
	_ck("cast_spray_fan", spray_ok, "spray 节点=%d vy范围=[%.0f,%.0f]" % [spray_fx.size(), vy_min, vy_max])

	# 5. aura（回春 idx3）：向上速度（vy<0），起点在地面附近。
	stage_node.call("debug_clear_cast_fx")
	stage_node.call("debug_spawn_cast_fx", 3)
	var aura_fx: Array = stage_node.call("debug_cast_fx") as Array
	var aura_ok: bool = aura_fx.size() == 1 and aura_fx[0].get("vy", 0.0) < 0.0 \
		and String(aura_fx[0].get("style", "")) == "aura"
	_ck("cast_aura_rise", aura_ok, "aura vy=%.0f y=%.0f" % [aura_fx[0].get("vy", 0.0),
		aura_fx[0].get("y", 0.0)])

	# 6. 位置随时间推进：dash tick 后 x 增大（向 facing 方向移动）。
	var x_before: float = dash_fx[0].get("x", 0.0)
	stage_node.call("debug_clear_cast_fx")
	stage_node.call("debug_spawn_cast_fx", 0)
	var moved: Array = stage_node.call("debug_cast_fx") as Array
	var x0: float = moved[0].get("x", 0.0)
	stage_node.call("debug_tick_cast_fx", 0.1)
	var moved2: Array = stage_node.call("debug_cast_fx") as Array
	var dx: float = absf(moved2[0].get("x", 0.0) - x0)
	_ck("cast_moves_over_time", dx > 5.0 and absf(x_before - moved2[0].get("x", 0.0)) >= 0.0,
		"tick 0.1s 后水平位移=%.1fpx" % dx)

	# 7. 生命周期：tick 超过最长 life 后演出节点全部清空。
	stage_node.call("debug_tick_cast_fx", 1.0)
	var cleared: Array = stage_node.call("debug_cast_fx") as Array
	_ck("cast_lifecycle_clean", cleared.is_empty(), "超时后残留节点=%d" % cleared.size())

	# 8. 纯视觉：生成演出不改 hp / spirit（无战斗数值副作用）。
	var pre_hp: float = float(stage_node.call("snapshot").get("hp", 0.0))
	var pre_sp: float = float(stage_node.call("snapshot").get("spirit", 0.0))
	stage_node.call("debug_spawn_cast_fx", 0)
	stage_node.call("debug_spawn_cast_fx", 1)
	var post_hp: float = float(stage_node.call("snapshot").get("hp", 0.0))
	var post_sp: float = float(stage_node.call("snapshot").get("spirit", 0.0))
	_ck("cast_visual_only", absf(post_hp - pre_hp) < 0.001 and absf(post_sp - pre_sp) < 0.001,
		"HP %.1f→%.1f 灵力 %.1f→%.1f" % [pre_hp, post_hp, pre_sp, post_sp])
	stage_node.call("debug_clear_cast_fx")
	stage_node.call("stop")

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
