class_name StageView
extends Node2D

## 第 41 轮 · 单层横版战斗（docs/01 §12 节点树 Stage / Node2D）。
##
## 冻结口径只读：BattleFormula.stages() 的 9 层 HP/dps/t/d/type/mobs、
## BattleFormula.damage_formula() 的统一伤害公式与五上界钳制（R32 / DF-21）。
## PROPOSAL 数值全部集中在 RunConfig，本文件不新开数值池（R51）。
##
## 明确未实现（不假装已做）：
##   - 46 张卡的非五上界 hook（RunState.* / VfxLayer.* / signal.* / MetaSave.*），
##     选中后只登记在 TowerRun.picks，不改变战斗表现（docs/18 / R54）。
##   - 逐 tick 状态机跨端对齐（R56）；6 s 读卡窗口（R33）；本地存档 / 元进度（M2/M3）。
##   - Boss 三阶段色、装备 / 词缀 / 灵韵、音频；表现层只做「按得动、看得见」的闭环。
## 画面资源：gpt-image2 回稿转录真帧（docs/24 / docs/25），非占位 CSS。

signal stage_cleared(layer_index: int)
signal player_dead()

const BattleFormula = preload("res://scripts/BattleFormula.gd")

const PLAYER_PREFIX := "res://assets/char/char_player"
const VFX_DIR := "res://assets/vfx/frames/"

var deck: CardDeck
var stage_index: int = 0
var running: bool = false
var paused: bool = false

var hp: float = RunConfig.PLAYER_MAX_HP
var spirit: float = RunConfig.PLAYER_MAX_SPIRIT
var stamina: float = RunConfig.PLAYER_MAX_STAMINA
var combo: float = 0.0
var cds: Array = [0.0, 0.0, 0.0, 0.0]
var cast_lock: float = 0.0
var invuln: float = 0.0
var facing: int = 1

var backdrop: Sprite2D
var player: CharacterBody2D
var player_sprite: AnimatedSprite2D
var enemies_root: Node2D
var vfx_root: Node2D
var floats_root: Node2D
var float_theme: Theme
var enemies: Array = []
var floating: Array = []
var _fx_rng: int = 0x2f6e2b1b


func _ready() -> void:
    float_theme = RunConfig.make_cjk_theme()
    backdrop = Sprite2D.new()
    backdrop.name = "Backdrop"
    backdrop.centered = false
    backdrop.position = Vector2.ZERO
    backdrop.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    add_child(backdrop)

    enemies_root = Node2D.new()
    enemies_root.name = "Enemies"
    add_child(enemies_root)

    _build_player()

    vfx_root = Node2D.new()
    vfx_root.name = "VfxLayer"
    add_child(vfx_root)
    floats_root = Node2D.new()
    floats_root.name = "Floats"
    add_child(floats_root)
    _apply_backdrop(0)
    visible = false


func _build_player() -> void:
    player = CharacterBody2D.new()
    player.name = "Player"
    player.position = Vector2(120, RunConfig.GROUND_Y - 32.0)
    var body := CollisionShape2D.new()
    body.name = "Body"
    var shape := RectangleShape2D.new()
    shape.size = Vector2(32, 56)
    body.shape = shape
    player.add_child(body)

    player_sprite = AnimatedSprite2D.new()
    player_sprite.name = "Sprite"
    player_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    var frames := SpriteFrames.new()
    _add_anim(frames, "idle", PLAYER_PREFIX, "idle", 3, 6.0, true)
    _add_anim(frames, "run", PLAYER_PREFIX, "run", 4, 8.0, true)
    _add_anim(frames, "cast", PLAYER_PREFIX, "cast", 4, 10.0, false)
    _add_anim(frames, "hit", PLAYER_PREFIX, "hit", 1, 6.0, false)
    _add_anim(frames, "death", PLAYER_PREFIX, "death", 3, 6.0, false)
    player_sprite.sprite_frames = frames
    player_sprite.play("idle")
    player.add_child(player_sprite)
    add_child(player)


## 逐帧探测：只加载真实存在的 PNG，缺帧不报错也不伪造（素材边界如实登记）。
func _add_anim(frames: SpriteFrames, anim: String, prefix: String,
        suffix: String, count: int, fps: float, loop: bool) -> void:
    frames.add_animation(anim)
    frames.set_animation_speed(anim, fps)
    frames.set_animation_loop(anim, loop)
    var loaded: int = 0
    for i in range(count):
        var path: String = "%s_%s_r_%02d.png" % [prefix, suffix, i]
        if not ResourceLoader.exists(path):
            continue
        var tex := load(path) as Texture2D
        if tex == null:
            continue
        frames.add_frame(anim, tex)
        loaded += 1
    if loaded == 0:
        frames.remove_animation(anim)


func _apply_backdrop(index: int) -> void:
    var data: Dictionary = RunConfig.stage_data(index)
    var path: String = RunConfig.bg_path(String(data["type"]))
    if ResourceLoader.exists(path):
        backdrop.texture = load(path) as Texture2D
    else:
        push_warning("StageView: 缺背景 " + path)


## 开新局时由 TowerRun 调用；跨层不重置 HP / 灵力 / 体力（单局持续消耗）。
func reset_player() -> void:
    hp = RunConfig.PLAYER_MAX_HP
    spirit = RunConfig.PLAYER_MAX_SPIRIT
    stamina = RunConfig.PLAYER_MAX_STAMINA
    combo = 0.0
    cds = [0.0, 0.0, 0.0, 0.0]
    cast_lock = 0.0
    invuln = 0.0
    facing = 1
    player.position = Vector2(120, RunConfig.GROUND_Y - 32.0)
    player_sprite.scale.x = 1.0


## 开始第 index 层（0-based）。敌人 HP 均分冻结的 stage.hp，不改冻结值。
func start_stage(index: int, p_deck: CardDeck) -> void:
    stage_index = index
    deck = p_deck
    _apply_backdrop(index)
    _clear_enemies()
    var data: Dictionary = RunConfig.stage_data(index)
    var mobs: Array = data["mobs"]
    var each_hp: float = float(data["hp"]) / float(maxi(1, mobs.size()))
    for i in range(mobs.size()):
        _spawn_enemy(String(mobs[i]), each_hp, i, mobs.size(), float(data["d"]))
    running = true
    paused = false
    visible = true


func _spawn_enemy(mob_id: String, mob_hp: float, i: int, total: int,
        difficulty: float) -> void:
    var info: Dictionary = RunConfig.MOBS.get(mob_id, {"name": mob_id, "defense": 0.10, "speed": 1.0})
    var is_boss: bool = bool(info.get("boss", false))
    var frame_size: float = 128.0 if is_boss else 64.0
    var node := Node2D.new()
    node.name = "Enemy_%d_%s" % [i, mob_id]
    var x: float = 330.0 + 34.0 * float(i) - 12.0 * float(total - 1)
    node.position = Vector2(clampf(x, 180.0, 450.0), RunConfig.GROUND_Y - frame_size / 2.0)
    var sp := AnimatedSprite2D.new()
    sp.name = "Sprite"
    sp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    var prefix: String = RunConfig.mob_prefix(mob_id)
    var frames := SpriteFrames.new()
    _add_anim(frames, "idle", prefix, "idle", 3, 6.0, true)
    _add_anim(frames, "run", prefix, "run", 4, 8.0, true)
    _add_anim(frames, "atk", prefix, "atk", 4, 8.0, false)
    _add_anim(frames, "hit", prefix, "hit", 1, 6.0, false)
    _add_anim(frames, "death", prefix, "death", 3, 6.0, false)
    sp.sprite_frames = frames
    if frames.has_animation("idle"):
        sp.play("idle")
    node.add_child(sp)
    enemies_root.add_child(node)
    enemies.append({
        "node": node, "sprite": sp, "id": mob_id, "hp": mob_hp, "max_hp": mob_hp,
        "defense": float(info.get("defense", 0.10)),
        "speed": float(info.get("speed", 1.0)) * difficulty,
        "atk_timer": RunConfig.ENEMY_ATTACK_INTERVAL * (0.6 + 0.2 * float(i)),
        "dead": false,
    })


func _clear_enemies() -> void:
    for e in enemies:
        var n: Node2D = e["node"]
        if is_instance_valid(n):
            n.queue_free()
    enemies = []


func stop() -> void:
    running = false
    paused = false
    visible = false


func set_paused(v: bool) -> void:
    paused = v


## 自实现 xorshift32（与 CardDeck / tools/card_rules.js 同族），
## 只用于暴击等**表现层**判定，不参与任何可复算规则（R47 / R56 边界）。
func _fx_randf() -> float:
    _fx_rng ^= (_fx_rng << 13) & 0xffffffff
    _fx_rng ^= _fx_rng >> 17
    _fx_rng ^= (_fx_rng << 5) & 0xffffffff
    _fx_rng &= 0xffffffff
    return float((_fx_rng >> 8) & 0xffffff) / 16777216.0


func _physics_process(delta: float) -> void:
    if not running or paused:
        return
    _tick_player(delta)
    _tick_skills(delta)
    _tick_enemies(delta)
    _check_cleared()


func _tick_player(delta: float) -> void:
    var axis: float = Input.get_axis("move_left", "move_right")
    player.velocity = Vector2(axis * RunConfig.MOVE_SPEED, 0.0)
    player.move_and_slide()
    player.position.x = clampf(player.position.x, 16.0, 464.0)
    if axis != 0.0:
        var new_facing: int = 1 if axis > 0.0 else -1
        if new_facing != facing:
            facing = new_facing
            # DF-04：只镜像 Sprite 本身，不镜像整个场景
            player_sprite.scale.x = float(facing)
        if player_sprite.animation != "run" and cast_lock <= 0.0:
            player_sprite.play("run")
    elif cast_lock <= 0.0 and player_sprite.animation != "idle":
        player_sprite.play("idle")

    spirit = minf(RunConfig.PLAYER_MAX_SPIRIT, spirit + RunConfig.SPIRIT_REGEN * delta)
    stamina = minf(RunConfig.PLAYER_MAX_STAMINA, stamina + RunConfig.STAMINA_REGEN * delta)
    combo = maxf(0.0, combo - RunConfig.COMBO_DECAY * delta)
    cast_lock = maxf(0.0, cast_lock - delta)
    invuln = maxf(0.0, invuln - delta)


func _tick_skills(delta: float) -> void:
    for i in range(cds.size()):
        cds[i] = maxf(0.0, float(cds[i]) - delta)
    if Input.is_action_just_pressed("dodge"):
        _try_dodge()
    for i in range(RunConfig.SKILLS.size()):
        var s: Dictionary = RunConfig.SKILLS[i]
        if Input.is_action_just_pressed(String(s["action"])):
            _cast(i)


func _try_dodge() -> void:
    if stamina < RunConfig.DODGE_COST or invuln > 0.0:
        _float_text("体力不足", player.position + Vector2(0, -46), RunConfig.C_PAPER_DIM)
        return
    stamina -= RunConfig.DODGE_COST
    invuln = RunConfig.DODGE_INVULN
    player.position.x = clampf(player.position.x + float(facing) * 40.0, 16.0, 464.0)
    _float_text("闪避", player.position + Vector2(0, -46), RunConfig.C_JADE_LIGHT)
    _spawn_vfx("vfx_hit", player.position, facing)


func _cast(idx: int) -> void:
    if cast_lock > 0.0 or float(cds[idx]) > 0.0:
        return
    var s: Dictionary = RunConfig.SKILLS[idx]
    var cost: float = float(s["spirit"])
    if spirit < cost:
        _float_text("灵力不足", player.position + Vector2(0, -46), RunConfig.C_PAPER_DIM)
        return
    spirit -= cost
    cds[idx] = float(s["cd"])
    cast_lock = RunConfig.CAST_LOCK
    if player_sprite.sprite_frames.has_animation("cast"):
        player_sprite.play("cast")
    _spawn_vfx(String(s["vfx"]), player.position + Vector2(float(facing) * 40.0, -8.0), facing)

    if String(s["kind"]) == "heal":
        var amount: float = float(s.get("heal", 0.0))
        hp = minf(RunConfig.PLAYER_MAX_HP, hp + amount)
        _float_text("+%d" % int(amount), player.position + Vector2(0, -52), RunConfig.C_JADE_LIGHT)
        return

    var off: Dictionary = deck.offense_state() if deck != null else {}
    var base: float = float(s["base"]) + float(off.get("base_damage", 0.0))
    var pool: float = float(off.get("extra_pool", 0.0)) + float(off.get("offense_pool_used", 0.0))
    var realm: float = 1.0 + float(off.get("realm_ratio", 0.0))
    var combo_mult: float = 1.0 + combo + float(off.get("combo_multiplier", 0.0))
    var crit: float = 1.0 + float(off.get("crit_multiplier", 0.0))
    var is_crit: bool = _fx_randf() < RunConfig.CRIT_CHANCE
    if is_crit:
        crit = BattleFormula.CAP_CRIT
    var reach: float = float(s["reach"])
    var hits: int = int(s["hits"])
    var hit_any: bool = false
    for e in enemies:
        if bool(e["dead"]):
            continue
        var n: Node2D = e["node"]
        if absf(n.position.x - player.position.x) > reach:
            continue
        hit_any = true
        for _h in range(hits):
            if bool(e["dead"]):
                break
            var res: Dictionary = BattleFormula.damage_formula(
                base, realm, pool, combo_mult, crit, float(e["defense"]))
            var dmg: int = int(res["damage"])
            e["hp"] = maxf(0.0, float(e["hp"]) - float(dmg))
            var color: Color = RunConfig.C_GOLD_LIGHT if is_crit else RunConfig.C_PAPER
            _float_text(str(dmg), n.position + Vector2(0, -44), color)
            _spawn_vfx("vfx_hit", n.position, -1)
            if float(e["hp"]) <= 0.0:
                e["dead"] = true
                var target_sp: AnimatedSprite2D = e["sprite"]
                if target_sp.sprite_frames.has_animation("death"):
                    target_sp.play("death")
    if hit_any:
        combo = minf(1.5, combo + RunConfig.COMBO_GAIN_PER_HIT)


func _spawn_vfx(vfx_id: String, pos: Vector2, dir: int) -> void:
    # 特效帧命名 "<id>_00.png"，与角色帧 "<prefix>_<动作>_r_00.png" 不同，故单独构造。
    var frames := SpriteFrames.new()
    frames.add_animation("play")
    frames.set_animation_speed("play", 14.0)
    frames.set_animation_loop("play", false)
    var loaded: int = 0
    for i in range(4):
        var path: String = "%s%s_%02d.png" % [VFX_DIR, vfx_id, i]
        if not ResourceLoader.exists(path):
            continue
        var tex := load(path) as Texture2D
        if tex != null:
            frames.add_frame("play", tex)
            loaded += 1
    if loaded == 0:
        return
    var sp := AnimatedSprite2D.new()
    sp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    sp.sprite_frames = frames
    sp.position = pos
    sp.scale.x = float(dir)
    vfx_root.add_child(sp)
    sp.play("play")
    sp.animation_finished.connect(_on_vfx_finished.bind(sp))


func _on_vfx_finished(sp: AnimatedSprite2D) -> void:
    if is_instance_valid(sp):
        sp.queue_free()


func _float_text(text: String, pos: Vector2, color: Color) -> void:
    if floating.size() >= 12:
        var old: Dictionary = floating.pop_front()
        var old_node: Label = old["node"]
        if is_instance_valid(old_node):
            old_node.queue_free()
    var l := Label.new()
    l.theme = float_theme
    l.text = text
    l.position = pos
    l.add_theme_font_size_override("font_size", 11)
    l.add_theme_color_override("font_color", color)
    l.mouse_filter = Control.MOUSE_FILTER_IGNORE
    floats_root.add_child(l)
    floating.append({"node": l, "t": 0.0})


func _tick_enemies(delta: float) -> void:
    var data: Dictionary = RunConfig.stage_data(stage_index)
    var incoming: float = RunConfig.ENEMY_ATTACK_BASE \
        + RunConfig.ENEMY_ATTACK_PER_STAGE * float(stage_index) \
        + float(data["dps"]) * 0.12
    for e in enemies:
        if bool(e["dead"]):
            continue
        var n: Node2D = e["node"]
        var dx: float = player.position.x - n.position.x
        var dist: float = absf(dx)
        var sp: AnimatedSprite2D = e["sprite"]
        if dist > RunConfig.ENEMY_ATTACK_RANGE * 0.7:
            var step: float = RunConfig.ENEMY_MOVE_SPEED * float(e["speed"]) * delta
            n.position.x += signf(dx) * minf(step, dist)
            if sp.sprite_frames.has_animation("run") and sp.animation != "run":
                sp.play("run")
        e["atk_timer"] = float(e["atk_timer"]) - delta
        if dist <= RunConfig.ENEMY_ATTACK_RANGE and float(e["atk_timer"]) <= 0.0:
            e["atk_timer"] = RunConfig.ENEMY_ATTACK_INTERVAL
            if sp.sprite_frames.has_animation("atk"):
                sp.play("atk")
            if invuln > 0.0:
                _float_text("闪", player.position + Vector2(0, -46), RunConfig.C_JADE_LIGHT)
                continue
            var off: Dictionary = deck.offense_state() if deck != null else {}
            var reduction: float = clampf(float(off.get("defense_rate", 0.0)), 0.0, 0.75)
            var taken: float = incoming * (1.0 - reduction)
            hp = maxf(0.0, hp - taken)
            _float_text("-%d" % int(taken), player.position + Vector2(0, -52), RunConfig.C_CINNABAR)
            if player_sprite.sprite_frames.has_animation("hit"):
                player_sprite.play("hit")
            if hp <= 0.0:
                running = false
                player_dead.emit()
                return


func _check_cleared() -> void:
    if not running or enemies.is_empty():
        return
    for e in enemies:
        if not bool(e["dead"]):
            return
    running = false
    stage_cleared.emit(stage_index + 1)


func _process(delta: float) -> void:
    var alive: Array = []
    for item in floating:
        var l := item["node"] as Label
        if not is_instance_valid(l):
            continue
        item["t"] = float(item["t"]) + delta
        l.position.y -= 26.0 * delta
        if float(item["t"]) >= 0.85:
            l.queue_free()
        else:
            alive.append(item)
    floating = alive


## 供 HUD 每帧读取的状态快照（父 → 子直接调用，docs/01 §12）。
func snapshot() -> Dictionary:
    var enemy_hp: float = 0.0
    var enemy_max: float = 0.0
    for e in enemies:
        enemy_hp += float(e["hp"])
        enemy_max += float(e["max_hp"])
    var data: Dictionary = RunConfig.stage_data(stage_index)
    return {
        "hp": hp, "max_hp": RunConfig.PLAYER_MAX_HP,
        "spirit": spirit, "max_spirit": RunConfig.PLAYER_MAX_SPIRIT,
        "stamina": stamina, "max_stamina": RunConfig.PLAYER_MAX_STAMINA,
        "combo": combo, "enemy_hp": enemy_hp, "enemy_max_hp": maxf(1.0, enemy_max),
        "stage_index": stage_index, "stage_type": String(data["type"]),
        "cds": cds.duplicate(), "running": running,
    }


## headless 校验用：直接判定清层，不改动冻结数据。
func debug_clear_stage() -> void:
    for e in enemies:
        e["hp"] = 0.0
        e["dead"] = true
    _check_cleared()
