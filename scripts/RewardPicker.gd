class_name RewardPicker
extends CanvasLayer

## 第 41 轮 · 层间三选一（docs/01 §12 节点树 RewardPicker / CanvasLayer）。
##
## 内容全部来自 CardDeck.offer(stage) 的确定性候选（xorshift32，R47 跨端同源）；
## 卡面用 CardArtView（冻结卡框 + 72 张一卡一插画），第 40 轮 07 候选框不采用。
## 不实现 6 s 强制窗口：R33 未拍板，原型允许玩家读完再点（见 docs/29 §4）。
## 不含任何抽取规则 / 权重 / 概率判定，只负责显示与回传点击。

signal card_picked(card_id: String)

const COL_W: float = 140.0
const COL_GAP: float = 10.0
const CARD_Y: float = 44.0

var root: Control
var cards_root: Control
var title_label: Label
var hint_label: Label
var offered: Array = []
var draft_stage: int = 0


func _ready() -> void:
    root = Control.new()
    root.name = "PickerRoot"
    root.theme = RunConfig.make_cjk_theme()
    root.set_anchors_preset(Control.PRESET_FULL_RECT)
    add_child(root)
    _fill(root, RunConfig.C_INK)
    title_label = _label(root, Vector2(0, 8), Vector2(480, 22), "层间三选一", 15,
        RunConfig.C_GOLD_LIGHT, HORIZONTAL_ALIGNMENT_CENTER)
    _label(root, Vector2(0, 28), Vector2(480, 14),
        "选一张永久生效 · 数值卡即时改变伤害 · 机制卡仅登记不实现", 8,
        RunConfig.C_PAPER_DIM, HORIZONTAL_ALIGNMENT_CENTER)
    cards_root = Control.new()
    cards_root.set_anchors_preset(Control.PRESET_FULL_RECT)
    cards_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
    root.add_child(cards_root)
    hint_label = _label(root, Vector2(0, 250), Vector2(480, 16), "", 8,
        RunConfig.C_STONE, HORIZONTAL_ALIGNMENT_CENTER)
    show_layer(false)


func _fill(parent: Control, color: Color) -> ColorRect:
    var r := ColorRect.new()
    r.set_anchors_preset(Control.PRESET_FULL_RECT)
    r.color = color
    r.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(r)
    return r


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


## 不能叫 set_visible：CanvasLayer 已有原生同名方法，项目把警告提升为错误。
func show_layer(v: bool) -> void:
    if root != null:
        root.visible = v


func show_offer(p_offered: Array, p_layer: int, library: Dictionary) -> void:
    offered = p_offered.duplicate()
    draft_stage = p_layer
    for child in cards_root.get_children():
        child.queue_free()
    title_label.text = "层间三选一 · 第 %d 层" % draft_stage
    hint_label.text = "点击卡牌选择 · 不设 6s 强制窗口（R33 待实测） · 候选由确定性种子给出"

    var total: float = COL_W * float(offered.size()) + COL_GAP * float(maxi(0, offered.size() - 1))
    var start_x: float = (float(RunConfig.LOGICAL_W) - total) / 2.0
    for i in range(offered.size()):
        var cid: String = String(offered[i])
        var card: Dictionary = library.get(cid, {})
        _build_column(i, start_x, cid, card)


func _build_column(i: int, start_x: float, cid: String, card: Dictionary) -> void:
    var col_x: float = start_x + float(i) * (COL_W + COL_GAP)
    _panel(cards_root, Vector2(col_x, CARD_Y - 4), Vector2(COL_W, 200))

    var view := CardArtView.new()
    view.name = "Card_" + cid
    view.position = Vector2(col_x + (COL_W - 96.0) / 2.0, CARD_Y)
    cards_root.add_child(view)
    view.show_card(cid, String(card.get("rarity", "common")),
        String(card.get("name", cid)), String(card.get("cat", "dmg")))

    var rarity: String = String(card.get("rarity", "common"))
    _label(cards_root, Vector2(col_x + 4, CARD_Y + 148), Vector2(COL_W - 8, 14),
        "%s · %s" % [_rarity_name(rarity), _cat_name(String(card.get("cat", "dmg")))], 8,
        _rarity_color(rarity), HORIZONTAL_ALIGNMENT_CENTER)
    var desc := _label(cards_root, Vector2(col_x + 4, CARD_Y + 164), Vector2(COL_W - 8, 32),
        String(card.get("text", "")), 9, RunConfig.C_PAPER)
    desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    desc.add_theme_color_override("font_color", RunConfig.C_PAPER_DIM)

    # 透明按钮覆盖整列，避免 Button 默认样式盖住卡面
    var btn := Button.new()
    btn.position = Vector2(col_x, CARD_Y - 4)
    btn.size = Vector2(COL_W, 200)
    btn.flat = true
    btn.focus_mode = Control.FOCUS_NONE
    var empty := StyleBoxEmpty.new()
    for state in ["normal", "hover", "pressed", "disabled", "focus"]:
        btn.add_theme_stylebox_override(state, empty)
    btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
    btn.pressed.connect(_on_pick.bind(cid))
    cards_root.add_child(btn)


func _panel(parent: Control, pos: Vector2, size: Vector2) -> void:
    var bg := ColorRect.new()
    bg.position = pos
    bg.size = size
    bg.color = RunConfig.C_SLATE
    bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(bg)
    var line := ColorRect.new()
    line.position = Vector2(pos.x, pos.y)
    line.size = Vector2(size.x, 2)
    line.color = RunConfig.C_STONE
    line.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(line)


func _rarity_name(r: String) -> String:
    match r:
        "common": return "凡品"
        "rare": return "灵品"
        "legend": return "仙品"
        "curse": return "劫品"
    return r


func _rarity_color(r: String) -> Color:
    match r:
        "rare": return RunConfig.C_JADE_LIGHT
        "legend": return RunConfig.C_GOLD_LIGHT
        "curse": return RunConfig.C_CINNABAR
    return RunConfig.C_PAPER_DIM


func _cat_name(c: String) -> String:
    match c:
        "dmg": return "伤害"
        "attr": return "属性"
        "mech": return "机制"
        "syn": return "联动"
        "surv": return "生存"
        "res": return "资源"
    return c


func _on_pick(cid: String) -> void:
    card_picked.emit(cid)
