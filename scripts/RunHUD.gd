class_name RunHUD
extends CanvasLayer

## 第 41 轮 · 局内 HUD（docs/01 §12 节点树 HUD / CanvasLayer）。
## 只显示 StageView.snapshot() 的状态快照，不含任何规则 / 数值判定。
## 颜色全部取自 RunConfig 的 24 色锁定板；不使用半透明像素（M7）。

var root: Control
var stage_label: Label
var hp_fill: ColorRect
var spirit_fill: ColorRect
var stamina_fill: ColorRect
var enemy_fill: ColorRect
var info_label: Label
var skill_labels: Array = []
var skill_bars: Array = []
var hint_label: Label


func _ready() -> void:
    root = Control.new()
    root.name = "HUDRoot"
    root.theme = RunConfig.make_cjk_theme()
    root.mouse_filter = Control.MOUSE_FILTER_IGNORE
    root.set_anchors_preset(Control.PRESET_FULL_RECT)
    add_child(root)

    # 顶部信息条（不透明墨底）
    _rect(root, Vector2(0, 0), Vector2(480, 38), RunConfig.C_INK)
    _rect(root, Vector2(0, 37), Vector2(480, 1), RunConfig.C_STONE)
    stage_label = _label(root, Vector2(6, 2), Vector2(200, 14), "第 1/9 层", 11, RunConfig.C_GOLD_LIGHT)
    info_label = _label(root, Vector2(286, 2), Vector2(188, 14), "", 9, RunConfig.C_PAPER_DIM,
        HORIZONTAL_ALIGNMENT_RIGHT)

    _rect(root, Vector2(6, 18), Vector2(150, 7), RunConfig.C_SLATE)
    hp_fill = _rect(root, Vector2(6, 18), Vector2(150, 7), RunConfig.C_CINNABAR)
    _rect(root, Vector2(6, 27), Vector2(150, 4), RunConfig.C_SLATE)
    spirit_fill = _rect(root, Vector2(6, 27), Vector2(150, 4), RunConfig.C_JADE)
    _rect(root, Vector2(6, 33), Vector2(150, 2), RunConfig.C_SLATE)
    stamina_fill = _rect(root, Vector2(6, 33), Vector2(150, 2), RunConfig.C_PAPER_DIM)

    _rect(root, Vector2(286, 18), Vector2(188, 9), RunConfig.C_SLATE)
    enemy_fill = _rect(root, Vector2(286, 18), Vector2(188, 9), RunConfig.C_VIOLET)
    var enemy_tag := _label(root, Vector2(286, 28), Vector2(188, 9), "敌方 HP", 8,
        RunConfig.C_PAPER_DIM, HORIZONTAL_ALIGNMENT_RIGHT)
    enemy_tag.name = "EnemyTag"

    # 底部技能栏
    _rect(root, Vector2(0, 236), Vector2(480, 34), RunConfig.C_INK)
    _rect(root, Vector2(0, 235), Vector2(480, 1), RunConfig.C_STONE)
    for i in range(RunConfig.SKILLS.size()):
        var s: Dictionary = RunConfig.SKILLS[i]
        var x: float = 6.0 + float(i) * 118.0
        _rect(root, Vector2(x, 240), Vector2(112, 24), RunConfig.C_SLATE)
        var bar := _rect(root, Vector2(x, 240), Vector2(112, 24), RunConfig.C_INK)
        skill_bars.append(bar)
        skill_labels.append(_label(root, Vector2(x + 3, 242), Vector2(106, 20),
            String(s["key"]) + "  " + String(s["name"]), 10, RunConfig.C_PAPER))

    hint_label = _label(root, Vector2(6, 218), Vector2(468, 16),
        "A/D 移动 · J/K/L/I 技能 · Space 闪避 · Esc 暂停    [PROPOSAL 演示数值]", 8,
        RunConfig.C_PAPER_DIM)
    show_layer(false)


func _rect(parent: Control, pos: Vector2, size: Vector2, color: Color) -> ColorRect:
    var r := ColorRect.new()
    r.position = pos
    r.size = size
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


## 父节点（TowerRun）在 _process 里直接调用：父 → 子用直接调用（docs/01 §12 数据流）。
func update_state(s: Dictionary) -> void:
    if root == null:
        return
    var hp_ratio: float = clampf(float(s.get("hp", 0.0)) / maxf(1.0, float(s.get("max_hp", 1.0))), 0.0, 1.0)
    var sp_ratio: float = clampf(float(s.get("spirit", 0.0)) / maxf(1.0, float(s.get("max_spirit", 1.0))), 0.0, 1.0)
    var st_ratio: float = clampf(float(s.get("stamina", 0.0)) / maxf(1.0, float(s.get("max_stamina", 1.0))), 0.0, 1.0)
    var en_ratio: float = clampf(float(s.get("enemy_hp", 0.0)) / maxf(1.0, float(s.get("enemy_max_hp", 1.0))), 0.0, 1.0)
    hp_fill.size.x = 150.0 * hp_ratio
    spirit_fill.size.x = 150.0 * sp_ratio
    stamina_fill.size.x = 150.0 * st_ratio
    enemy_fill.size.x = 188.0 * en_ratio

    var idx: int = int(s.get("stage_index", 0)) + 1
    stage_label.text = "第 %d/%d 层 · %s" % [idx, RunConfig.stage_count(), String(s.get("stage_type", ""))]
    info_label.text = "HP %d/%d · 灵力 %d · Combo %.2f · 卡牌 %d" % [
        int(s.get("hp", 0.0)), int(s.get("max_hp", 0.0)), int(s.get("spirit", 0.0)),
        float(s.get("combo", 0.0)), int(s.get("picks", 0)),
    ]

    var cds: Array = s.get("cds", [])
    for i in range(skill_labels.size()):
        var skill: Dictionary = RunConfig.SKILLS[i]
        var cd: float = float(cds[i]) if i < cds.size() else 0.0
        var label: Label = skill_labels[i]
        if cd > 0.0:
            label.text = "%s  %s  %.1fs" % [String(skill["key"]), String(skill["name"]), cd]
            label.add_theme_color_override("font_color", RunConfig.C_PAPER_DIM)
        else:
            label.text = "%s  %s" % [String(skill["key"]), String(skill["name"])]
            label.add_theme_color_override("font_color", RunConfig.C_PAPER)
        var bar: ColorRect = skill_bars[i]
        bar.size.x = 112.0 * clampf(cd / maxf(0.01, float(skill["cd"])), 0.0, 1.0)
