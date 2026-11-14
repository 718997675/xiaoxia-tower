extends Node2D

## 第 41 轮 · 局内根，管 9 层推进与结算（docs/01 §12 节点树 TowerRun）。
##
## 这是「游戏本体」的第一个可玩闭环：主菜单 → 横版战斗清层 → 层间三选一
## → 下一层 → 败/通关结算 → 重开。此前 Godot 侧只有 MinimalRun（主角左右跑），
## 完整原型一直只存在于网页验证层，本文件不把网页结论当成实机结论。
##
## 边界（越界即违规）：
##   - 不改写 docs/01 / 11 / 12 任何冻结文档，不动 assets/ui/cards/ 10 张冻结卡面；
##   - 第 40 轮 07 风格卡框是候选（R61），本原型不采用，卡面仍用冻结卡框 + 72 张插画；
##   - 抽取规则完全交给 CardDeck（xorshift32 确定性，R47），伤害交给 BattleFormula（R32 红线）；
##   - 46 张卡的非五上界 hook 只登记不实现；M2 境界 / M3 灵韵 / 存档 / 埋点 / 音频未实现；
##   - Q17 未拍板、GUI F5 目检未跑；headless 只证明「能加载、能跑通状态机」，不代表画面已验证。

signal run_ended(result: String, layer: int)

enum State { MENU, BATTLE, DRAFT, RESULT }

const LIB_PATH := "res://data/buff-card-library.json"

var state: int = State.MENU
var deck: CardDeck
var library: Dictionary = {}
var run_id: String = ""
var stage_index: int = 0
var picks: Array = []
var result_text: String = ""

## 不用 @onready：headless --script 模式下节点入树时序与编辑器不同
## （tools/verify_minimal_run.gd 已记录同一坑），显式 get_node 让两条路径一致。
var stage: StageView
var hud: RunHUD
var picker: RewardPicker
var menu_layer: CanvasLayer
var result_layer: CanvasLayer

var menu_root: Control
var result_root: Control
var result_label: Label
var pause_label: Label
var initialized: bool = false


func _ready() -> void:
    if initialized:
        return
    initialized = true
    stage = get_node("Stage") as StageView
    hud = get_node("HUD") as RunHUD
    picker = get_node("RewardPicker") as RewardPicker
    menu_layer = get_node("MenuLayer") as CanvasLayer
    result_layer = get_node("ResultLayer") as CanvasLayer
    RunConfig.ensure_actions()
    _load_library()
    deck = CardDeck.new()
    if not deck.is_loaded():
        push_error("TowerRun: 卡库未加载 72 张：" + deck.last_error())

    stage.stage_cleared.connect(_on_stage_cleared)
    stage.player_dead.connect(_on_player_dead)
    picker.card_picked.connect(_on_card_picked)

    menu_root = _make_layer(menu_layer, "MenuRoot")
    _build_menu()
    result_root = _make_layer(result_layer, "ResultRoot")
    _build_result()
    # 暂停提示必须挂在战斗时可见的 HUD 上，挂菜单层会随菜单一起隐藏。
    pause_label = _label(hud.root, Vector2(140, 120), Vector2(200, 24),
        "已暂停 · Esc 继续", 12, RunConfig.C_GOLD_LIGHT, HORIZONTAL_ALIGNMENT_CENTER)
    pause_label.visible = false
    _enter_menu()


func _load_library() -> void:
    var f := FileAccess.open(LIB_PATH, FileAccess.READ)
    if f == null:
        push_error("TowerRun: 打不开运行时卡库 " + LIB_PATH)
        return
    var parsed: Variant = JSON.parse_string(f.get_as_text())
    f.close()
    if not (parsed is Dictionary):
        push_error("TowerRun: 卡库不是合法 JSON 对象")
        return
    var doc: Dictionary = parsed
    for raw in doc.get("cards", []):
        var card: Dictionary = raw
        library[String(card["id"])] = card


## CanvasLayer 下挂一个全屏 Control 作为该层的根，统一 CJK 主题。
func _make_layer(layer: CanvasLayer, node_name: String) -> Control:
    var c := Control.new()
    c.name = node_name
    c.theme = RunConfig.make_cjk_theme()
    c.set_anchors_preset(Control.PRESET_FULL_RECT)
    layer.add_child(c)
    return c


func _fill(parent: Control, color: Color) -> ColorRect:
    var r := ColorRect.new()
    r.set_anchors_preset(Control.PRESET_FULL_RECT)
    r.color = color
    r.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(r)
    return r


func _picture(parent: Control, path: String) -> void:
    if not ResourceLoader.exists(path):
        return
    var t := TextureRect.new()
    t.set_anchors_preset(Control.PRESET_FULL_RECT)
    t.texture = load(path) as Texture2D
    t.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    t.stretch_mode = TextureRect.STRETCH_SCALE
    t.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(t)


func _label(parent: Control, pos: Vector2, size: Vector2, text: String,
        font_size: int, color: Color, align: int = HORIZONTAL_ALIGNMENT_LEFT) -> Label:
    var l := Label.new()
    l.position = pos
    l.size = size
    l.text = text
    l.horizontal_alignment = align
    l.add_theme_font_size_override("font_size", font_size)
    l.add_theme_color_override("font_color", color)
    l.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(l)
    return l


func _button(parent: Control, pos: Vector2, size: Vector2, text: String,
        handler: Callable) -> Button:
    var b := Button.new()
    b.position = pos
    b.size = size
    b.text = text
    b.focus_mode = Control.FOCUS_NONE
    b.add_theme_font_size_override("font_size", 12)
    b.add_theme_color_override("font_color", RunConfig.C_PAPER)
    var normal := StyleBoxFlat.new()
    normal.bg_color = RunConfig.C_SLATE
    normal.border_color = RunConfig.C_GOLD
    normal.set_border_width_all(1)
    var hover := StyleBoxFlat.new()
    hover.bg_color = RunConfig.C_BLUEGRAY
    hover.border_color = RunConfig.C_GOLD_LIGHT
    hover.set_border_width_all(1)
    b.add_theme_stylebox_override("normal", normal)
    b.add_theme_stylebox_override("hover", hover)
    b.add_theme_stylebox_override("pressed", normal)
    b.pressed.connect(handler)
    parent.add_child(b)
    return b


func _build_menu() -> void:
    _fill(menu_root, RunConfig.C_INK)
    _picture(menu_root, "res://assets/bg/bg_normal/bg_normal_composite.png")
    # 只用两条不透明墨底保证文字可读，中间露出 gpt-image2 背景（不用半透明，M7）。
    _band(menu_root, 34.0, 124.0)
    _band(menu_root, 160.0, 102.0)
    _label(menu_root, Vector2(0, 44), Vector2(480, 40), "九 重 天 梯", 28,
        RunConfig.C_GOLD_LIGHT, HORIZONTAL_ALIGNMENT_CENTER)
    _label(menu_root, Vector2(0, 88), Vector2(480, 18),
        "入塔 → 9 层横版战斗 → 层间三选一 → 传承结算", 10,
        RunConfig.C_PAPER_DIM, HORIZONTAL_ALIGNMENT_CENTER)
    _button(menu_root, Vector2(178, 124), Vector2(124, 30), "开始入塔  (Enter)", _on_start_pressed)
    _label(menu_root, Vector2(0, 168), Vector2(480, 16),
        "A/D 移动 · J/K/L/I 四技能 · Space 闪避 · 鼠标选卡 · Esc 暂停", 9,
        RunConfig.C_PAPER, HORIZONTAL_ALIGNMENT_CENTER)
    _label(menu_root, Vector2(0, 190), Vector2(480, 14),
        "72 张塔层卡 / 4 档稀有度 / 一卡一插画", 9,
        RunConfig.C_JADE_LIGHT, HORIZONTAL_ALIGNMENT_CENTER)
    _label(menu_root, Vector2(0, 212), Vector2(480, 30),
        "原型边界：技能 CD / 灵力 / HP / 敌人伤害等均为 PROPOSAL 占位\n"
        + "境界·灵韵·存档·音频未实现；Q17 未拍板、GUI 画面未目检", 8,
        RunConfig.C_PAPER_DIM, HORIZONTAL_ALIGNMENT_CENTER)


func _band(parent: Control, top: float, height: float) -> void:
    var r := ColorRect.new()
    r.position = Vector2(0, top)
    r.size = Vector2(480, height)
    r.color = RunConfig.C_INK
    r.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(r)


func _build_result() -> void:
    _fill(result_root, RunConfig.C_INK)
    _picture(result_root, "res://assets/bg/bg_boss/bg_boss_composite.png")
    _band(result_root, 36.0, 198.0)
    result_label = _label(result_root, Vector2(30, 46), Vector2(420, 130), "", 11,
        RunConfig.C_PAPER, HORIZONTAL_ALIGNMENT_CENTER)
    _button(result_root, Vector2(178, 196), Vector2(124, 30), "再入一塔  (Enter)", _on_start_pressed)
    _label(result_root, Vector2(0, 238), Vector2(480, 16),
        "本原型不含局外存档 / 传承灵韵 / 境界突破（M2 / M3 未实现）", 8,
        RunConfig.C_PAPER_DIM, HORIZONTAL_ALIGNMENT_CENTER)


func _on_start_pressed() -> void:
    start_run()


## 开新局：确定性 run_id 交给 CardDeck，供 M6 埋点复现（本原型不写埋点文件）。
func start_run(p_run_id: String = "") -> void:
    run_id = p_run_id if p_run_id != "" else str(Time.get_unix_time_from_system())
    deck.new_run(run_id)
    stage.reset_player()
    picks = []
    result_text = ""
    pause_label.visible = false
    stage.set_paused(false)
    _enter_battle(0)


func _enter_menu() -> void:
    state = State.MENU
    stage.stop()
    hud.show_layer(false)
    picker.show_layer(false)
    result_root.visible = false
    menu_root.visible = true


func _enter_battle(index: int) -> void:
    state = State.BATTLE
    stage_index = clampi(index, 0, RunConfig.stage_count() - 1)
    menu_root.visible = false
    result_root.visible = false
    picker.show_layer(false)
    hud.show_layer(true)
    stage.start_stage(stage_index, deck)


func _on_stage_cleared(layer: int) -> void:
    if layer >= RunConfig.stage_count():
        _enter_result("win")
        return
    # 封牌 / 舍牌（R49）导致候选为空时不弹卡，直接推进；不伪造三选一。
    if deck.offer(layer).is_empty():
        _enter_battle(layer)
        return
    _enter_draft(layer)


func _enter_draft(layer: int) -> void:
    state = State.DRAFT
    hud.show_layer(false)
    picker.show_layer(true)
    picker.show_offer(deck.offer(layer), layer, library)


func _on_card_picked(cid: String) -> void:
    if state != State.DRAFT:
        return
    if deck.pick(cid, stage_index + 1):
        picks.append(cid)
    picker.show_layer(false)
    _enter_battle(stage_index + 1)


func _on_player_dead() -> void:
    _enter_result("lose")


func _enter_result(which: String) -> void:
    state = State.RESULT
    result_text = which
    stage.stop()
    hud.show_layer(false)
    picker.show_layer(false)
    menu_root.visible = false
    result_root.visible = true
    var head: String = "登顶 · 九层尽破" if which == "win" else "陨落 · 止步于此"
    var names: Array = []
    for cid in picks:
        names.append(String(library.get(cid, {}).get("name", cid)))
    var picked_line: String = "、".join(PackedStringArray(names)) if not names.is_empty() else "无"
    var line1: String = "%s\n到达第 %d / %d 层 · 本局选卡 %d 张\n\n本局卡牌：%s\n\n" % [
        head, stage_index + 1, RunConfig.stage_count(), picks.size(), picked_line]
    var line2: String = "伤害红线 %d / 4400 · 违规 %d 条" % [
        int(deck.peak_damage()), deck.violations().size()]
    result_label.text = line1 + line2
    run_ended.emit(which, stage_index + 1)


func _process(_delta: float) -> void:
    if state == State.BATTLE:
        hud.update_state(stage.snapshot())
        if Input.is_action_just_pressed("pause"):
            var now_paused: bool = not stage.paused
            stage.set_paused(now_paused)
            pause_label.visible = now_paused


func _unhandled_input(event: InputEvent) -> void:
    var key := event as InputEventKey
    if key == null or not key.pressed or key.echo:
        return
    if key.keycode != KEY_ENTER and key.keycode != KEY_KP_ENTER:
        return
    if state == State.MENU or state == State.RESULT:
        start_run()


## 仅 headless 校验用：不模拟输入、不伪造画面，只推进状态机取证据。
func debug_state() -> Dictionary:
    return {
        "state": state, "stage_index": stage_index, "run_id": run_id,
        "picks": picks.duplicate(), "result": result_text,
        "cards_loaded": deck.card_count() if deck != null else 0,
        "damage_ceiling_ok": deck.damage_ceiling_ok() if deck != null else false,
    }


func debug_clear_current_stage() -> void:
    stage.debug_clear_stage()


func debug_pick_first() -> void:
    if not picker.offered.is_empty():
        picker._on_pick(String(picker.offered[0]))
