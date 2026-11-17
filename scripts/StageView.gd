class_name StageView
extends Node2D

## 第 41 轮 · 单层横版战斗（docs/01 §12 节点树 Stage / Node2D）。
##
## 冻结口径只读：BattleFormula.stages() 的 9 层 HP/dps/t/d/type/mobs、
## BattleFormula.damage_formula() 的统一伤害公式与五上界钳制（R32 / DF-21）。
## PROPOSAL 数值全部集中在 RunConfig，本文件不新开数值池（R51）。
##
## 第 42 轮（R64）：卡牌「非五上界」机制效果接入表现层。效果集由 CardEffects.gd
## 从冻结卡库编译（与网页 card_effects.js 逐字段对齐，76 样本跨端验证），默认 mods
## 全 0 / 全 1 时与第 41 轮行为逐字段一致，20/20 基线不回退。仍是 PROPOSAL 表现层口径，
## 不是冻结规格、不是平衡结论；需设计确认 / 归局外系统的键不在此模拟（docs/18 / R54）。
##
## 明确未实现（不假装已做）：
##   - 46 张卡的非五上界 hook（RunState.* / VfxLayer.* / signal.* / MetaSave.*）的真系统仍不建；
##     第 42 轮只落地 20 个可观测 mods 字段（从冻结卡库编译），语义未定的键仍不模拟，
##     未映射清单见 docs/card-effects 报告；不是完整 hook 实现。
##   - 逐 tick 状态机跨端对齐（R56）；6 s 读卡窗口（R33）；本地存档 / 元进度（M2/M3）。
##   - 装备 / 词缀 / 灵韵、音频；表现层只做「按得动、看得见」的闭环。
## 第 44 轮：Boss 远程技能（投射物）——定时发扇形飞剑弹，复用现有 vfx_flying_sword 帧，
##   伤害走与近战同一条 _hurt_player() 路径（护盾/减伤/无敌/复活一致）；阶段越高弹数越多、
##   CD 越短。网页无弹幕系统，这是 Godot 表现层增强，R56 仍未跨端对齐，非冻结数值。
## 画面资源：gpt-image2 回稿转录真帧（docs/24 / docs/25），非占位 CSS。

signal stage_cleared(layer_index: int)
signal player_dead()
## 第 43 轮：Boss 血量跌破阈值切阶段时发出（phase=1/2/3），供 HUD / 表现层订阅。
signal boss_phase_changed(phase: int, mob_id: String)
## 第 44 轮：Boss 释放远程技能时发出（弹数），供 HUD / 表现层订阅。
signal boss_skill_fired(shots: int, mob_id: String)

const BattleFormula = preload("res://scripts/BattleFormula.gd")
const CardEffects = preload("res://scripts/CardEffects.gd")

const PLAYER_PREFIX := "res://assets/char/char_player"
const VFX_DIR := "res://assets/vfx/frames/"

# 效果集默认全 0 / 全 1（与 CardEffects.default_mods() 一致）。
# 选卡后由 TowerRun 调 apply_mods() 注入，未注入时整段逻辑与第 41 轮相同。
var mods: Dictionary = CardEffects.default_mods()
var max_hp_effective: float = RunConfig.PLAYER_MAX_HP
var max_spirit_effective: float = RunConfig.PLAYER_MAX_SPIRIT
var shield: float = 0.0
var revive_used: bool = false
var free_cast_used: int = 0

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
# 第 44 轮：Boss 投射物（每项 {node,sprite,x,y,vx,vy,damage,life}）。非 Boss 层恒为空。
var projectiles: Array = []
var proj_root: Node2D
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
    proj_root = Node2D.new()
    proj_root.name = "Projectiles"
    add_child(proj_root)
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
## 注入已选卡的效果集（TowerRun 每次 pick 后调用）。重算上限并把当前值夹到新上限内。
## 默认 mods 时 max_hp_effective=PLAYER_MAX_HP、max_spirit_effective=PLAYER_MAX_SPIRIT，
## 与第 41 轮逐字段一致。
func apply_mods(new_mods: Dictionary) -> void:
    mods = new_mods
    var flat_hp: float = float(mods.get("hpMaxFlat", 0.0))
    var ratio_hp: float = float(mods.get("hpMaxRatio", 0.0))
    var flat_sp: float = float(mods.get("spiritMaxFlat", 0.0))
    var ratio_sp: float = float(mods.get("spiritMaxRatio", 0.0))
    max_hp_effective = maxf(1.0, (RunConfig.PLAYER_MAX_HP + flat_hp) * (1.0 + ratio_hp))
    max_spirit_effective = maxf(1.0, (RunConfig.PLAYER_MAX_SPIRIT + flat_sp) * (1.0 + ratio_sp))
    hp = minf(hp, max_hp_effective)
    spirit = minf(spirit, max_spirit_effective)
    # 同步护盾快照：apply_mods 后紧接的 start_stage 会再刷新一次同值，保持一致。
    shield = float(mods.get("shieldMax", 0.0))


func reset_player() -> void:
    # 上限受卡牌影响；默认 mods 时两值就是 RunConfig 常量，行为不变。
    var flat_hp: float = float(mods.get("hpMaxFlat", 0.0))
    var ratio_hp: float = float(mods.get("hpMaxRatio", 0.0))
    var flat_sp: float = float(mods.get("spiritMaxFlat", 0.0))
    var ratio_sp: float = float(mods.get("spiritMaxRatio", 0.0))
    max_hp_effective = maxf(1.0, (RunConfig.PLAYER_MAX_HP + flat_hp) * (1.0 + ratio_hp))
    max_spirit_effective = maxf(1.0, (RunConfig.PLAYER_MAX_SPIRIT + flat_sp) * (1.0 + ratio_sp))
    hp = max_hp_effective
    spirit = max_spirit_effective
    stamina = RunConfig.PLAYER_MAX_STAMINA
    combo = 0.0
    cds = [0.0, 0.0, 0.0, 0.0]
    cast_lock = 0.0
    invuln = 0.0
    facing = 1
    shield = 0.0
    revive_used = false
    free_cast_used = 0
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
    # 护盾（卷甲）：每层开局按 shieldMax 刷新；默认 0，与第 41 轮一致。
    shield = float(mods.get("shieldMax", 0.0))
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
    # 第 43 轮：Boss 的 skill 真帧（判官 4 帧 / 塔主 10 帧）作为阶段变身表现。
    # 非 Boss 也会尝试加载，但 assets/enemy/ 无 skill 帧 → loaded=0 自动移除，安全。
    if is_boss:
        _add_anim(frames, "skill", prefix, "skill", 10, 12.0, false)
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
        # 第 43 轮：Boss 阶段状态。非 Boss phase=0 且不参与任何阶段逻辑。
        "boss": is_boss, "phase": 1 if is_boss else 0,
        "phase_timer": 0.0,
        # 第 44 轮：Boss 远程技能冷却计时；首次施法有独立延迟。
        "skill_cd": RunConfig.BOSS_SKILL_FIRST_DELAY if is_boss else 0.0,
    })


func _clear_enemies() -> void:
    for e in enemies:
        var n: Node2D = e["node"]
        if is_instance_valid(n):
            n.queue_free()
    enemies = []
    # 第 44 轮：切层时清掉所有在飞投射物，不跨层残留。
    _clear_projectiles()


func _clear_projectiles() -> void:
    for p in projectiles:
        var pn: Node2D = p["node"]
        if is_instance_valid(pn):
            pn.queue_free()
    projectiles = []


func stop() -> void:
    running = false
    paused = false
    visible = false
    _clear_projectiles()


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
    # 第 44 轮：Boss 远程技能与投射物飞行（非 Boss 层两者都是空操作）。
    _tick_boss_skills(delta)
    _tick_projectiles(delta)
    _check_cleared()


func _tick_player(delta: float) -> void:
    var axis: float = Input.get_axis("move_left", "move_right")
    # 移速加成（步摇）：默认 0，速度不变。
    var move_speed: float = RunConfig.MOVE_SPEED * (1.0 + float(mods.get("moveSpeedBonus", 0.0)))
    player.velocity = Vector2(axis * move_speed, 0.0)
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

    spirit = minf(max_spirit_effective, spirit + RunConfig.SPIRIT_REGEN * delta)
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
    var cost: float = float(s["spirit"]) * float(mods.get("spiritCostScale", 1.0))
    if spirit < cost:
        _float_text("灵力不足", player.position + Vector2(0, -46), RunConfig.C_PAPER_DIM)
        return
    # 免费施法（灵潮）：灵力满且还有次数时本次不耗灵；默认 freeCastOnFull=false。
    var free_cast: bool = bool(mods.get("freeCastOnFull", false)) \
        and spirit >= max_spirit_effective - 0.001 \
        and free_cast_used < int(CardEffects.CAPS["freeCastUses"])
    if not free_cast:
        spirit -= cost
    else:
        free_cast_used += 1
        _float_text("灵潮·免费", player.position + Vector2(0, -58), RunConfig.C_JADE_LIGHT)
    cds[idx] = float(s["cd"]) * float(mods.get("cdScale", 1.0))
    cast_lock = RunConfig.CAST_LOCK
    if player_sprite.sprite_frames.has_animation("cast"):
        player_sprite.play("cast")
    _spawn_vfx(String(s["vfx"]), player.position + Vector2(float(facing) * 40.0, -8.0), facing)

    if String(s["kind"]) == "heal":
        var amount: float = float(s.get("heal", 0.0))
        # heal 在卡库里语义需确认（NONE_REASON.heal），本原型只按技能固定治疗量，
        # 不按卡牌治疗比例缩放（不猜数值）；上限用 effective。
        hp = minf(max_hp_effective, hp + amount)
        _float_text("+%d" % int(amount), player.position + Vector2(0, -52), RunConfig.C_JADE_LIGHT)
        return

    var off: Dictionary = deck.offense_state() if deck != null else {}
    var base: float = float(s["base"]) + float(off.get("base_damage", 0.0))
    var pool: float = float(off.get("extra_pool", 0.0)) + float(off.get("offense_pool_used", 0.0))
    var realm: float = 1.0 + float(off.get("realm_ratio", 0.0))
    var combo_mult: float = 1.0 + combo + float(off.get("combo_multiplier", 0.0))
    var crit: float = 1.0 + float(off.get("crit_multiplier", 0.0))
    var crit_chance: float = RunConfig.CRIT_CHANCE + float(mods.get("critRateBonus", 0.0))
    var is_crit: bool = _fx_randf() < crit_chance
    if is_crit:
        crit = BattleFormula.CAP_CRIT
    var reach: float = float(s["reach"])
    var pierce: float = float(mods.get("pierceDefense", 0.0))
    var spirit_on_hit: float = float(mods.get("spiritOnHit", 0.0))
    # 分段：默认 segmentRatios=[1.0] → 用技能自带 hits，每段满伤，与第 41 轮逐字段一致。
    # 多段卡（如破云 [0.5,0.5]）→ 用该数组作为每段的伤害比例，总伤不变。
    var ratios: Array = mods.get("segmentRatios", [1.0]) as Array
    var use_ratios: bool = ratios.size() > 1
    var seg_count: int = ratios.size() if use_ratios else int(s["hits"])
    var hit_any: bool = false
    for e in enemies:
        if bool(e["dead"]):
            continue
        var n: Node2D = e["node"]
        if absf(n.position.x - player.position.x) > reach:
            continue
        hit_any = true
        var eff_defense: float = float(e["defense"]) * (1.0 - pierce)
        for h in range(seg_count):
            if bool(e["dead"]):
                break
            var ratio: float = float(ratios[h]) if use_ratios else 1.0
            var res: Dictionary = BattleFormula.damage_formula(
                base, realm, pool, combo_mult, crit, eff_defense)
            var dmg: int = maxi(1, int(float(res["damage"]) * ratio))
            e["hp"] = maxf(0.0, float(e["hp"]) - float(dmg))
            var color: Color = RunConfig.C_GOLD_LIGHT if is_crit else RunConfig.C_PAPER
            _float_text(str(dmg), n.position + Vector2(0, -44), color)
            _spawn_vfx("vfx_hit", n.position, -1)
            if spirit_on_hit > 0.0:
                spirit = minf(max_spirit_effective, spirit + spirit_on_hit)
            # 第 43 轮：扣血后按血量比检查 Boss 阶段跃迁（与网页 0.66/0.33 同口径）。
            _check_boss_phase(e)
            if float(e["hp"]) <= 0.0:
                e["dead"] = true
                var target_sp: AnimatedSprite2D = e["sprite"]
                if target_sp.sprite_frames.has_animation("death"):
                    target_sp.play("death")
                if float(mods.get("spiritOnKill", 0.0)) > 0.0:
                    spirit = minf(max_spirit_effective, spirit + float(mods["spiritOnKill"]))
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
        # 第 43 轮：Boss 阶段越高单次伤害越高；非 Boss slot=0 系数 1.0，行为不变。
        var phase_atk: float = float(RunConfig.BOSS_PHASE_ATK_SCALE[_boss_phase_slot(e)])
        var hit_incoming: float = incoming * phase_atk
        var n: Node2D = e["node"]
        var dx: float = player.position.x - n.position.x
        var dist: float = absf(dx)
        var sp: AnimatedSprite2D = e["sprite"]
        if dist > RunConfig.ENEMY_ATTACK_RANGE * 0.7:
            # 第 43 轮：Boss 阶段越高移动越快；非 Boss slot=0 系数 1.0，行为不变。
            var move_scale: float = float(RunConfig.BOSS_PHASE_MOVE_SCALE[_boss_phase_slot(e)])
            var step: float = RunConfig.ENEMY_MOVE_SPEED * float(e["speed"]) * move_scale * delta
            n.position.x += signf(dx) * minf(step, dist)
            if sp.sprite_frames.has_animation("run") and sp.animation != "run":
                sp.play("run")
        e["atk_timer"] = float(e["atk_timer"]) - delta
        if dist <= RunConfig.ENEMY_ATTACK_RANGE and float(e["atk_timer"]) <= 0.0:
            # 第 43 轮：Boss 阶段越高出手越快；非 Boss slot=0 系数 1.0，行为不变。
            var interval_scale: float = float(RunConfig.BOSS_PHASE_ATK_INTERVAL_SCALE[_boss_phase_slot(e)])
            e["atk_timer"] = RunConfig.ENEMY_ATTACK_INTERVAL * interval_scale
            if sp.sprite_frames.has_animation("atk"):
                sp.play("atk")
            if invuln > 0.0:
                _float_text("闪", player.position + Vector2(0, -46), RunConfig.C_JADE_LIGHT)
                continue
            # 第 44 轮：伤害结算抽到 _hurt_player()，近战与 Boss 投射物共用同一条路径
            # （减伤/护盾/受击无敌/回灵/复活/死亡逐字段不变），hit_incoming 已含第 43 轮阶段系数。
            var hr: int = _hurt_player(hit_incoming)
            if hr == 1:
                continue  # 复活触发，本敌本次攻击结束
            if hr == 2:
                return    # 玩家阵亡，停止本 tick


## 统一玩家受伤结算（第 44 轮抽取，近战 / Boss 投射物共用）。
## raw_incoming 是未过玩家减伤的原始伤害（投射物已乘 BOSS_PROJ_DAMAGE_SCALE）。
## 返回：0=正常受击未死，1=复活触发，2=死亡。逻辑与第 41–43 轮逐字段一致。
func _hurt_player(raw_incoming: float) -> int:
    var off: Dictionary = deck.offense_state() if deck != null else {}
    var reduction: float = clampf(float(off.get("defense_rate", 0.0)), 0.0, 0.75)
    # 承伤系数（铁皮/混元/守拙）与固定减伤（铁骨）；默认 scale=1/flat=0，与第 41 轮一致。
    var taken: float = raw_incoming * (1.0 - reduction) * float(mods.get("damageTakenScale", 1.0))
    taken = maxf(0.0, taken - float(mods.get("flatReduce", 0.0)))
    # 护盾（卷甲）先吸收；默认 shield=0，不改变原扣血路径。
    if shield > 0.0:
        var absorbed: float = minf(shield, taken)
        shield -= absorbed
        taken -= absorbed
        if absorbed > 0.0:
            _float_text("盾-%d" % int(absorbed), player.position + Vector2(-30, -52),
                RunConfig.C_JADE_LIGHT)
    if taken > 0.0:
        hp = maxf(0.0, hp - taken)
        _float_text("-%d" % int(taken), player.position + Vector2(0, -52), RunConfig.C_CINNABAR)
    # 受击无敌窗口（避水）+ 受击回灵（接气）；默认 0，与第 41 轮一致。
    var hurt_invuln: float = float(mods.get("hurtInvuln", 0.0))
    if hurt_invuln > 0.0:
        invuln = maxf(invuln, hurt_invuln)
    if float(mods.get("spiritOnHurt", 0.0)) > 0.0:
        spirit = minf(max_spirit_effective, spirit + float(mods["spiritOnHurt"]))
    if player_sprite.sprite_frames.has_animation("hit"):
        player_sprite.play("hit")
    if hp <= 0.0:
        # 复活（舍利/转生）：本局首次阵亡按比例回血；默认 reviveHp=0，行为不变。
        var revive_hp: float = float(mods.get("reviveHp", 0.0))
        if revive_hp > 0.0 and not revive_used:
            revive_used = true
            hp = maxf(1.0, max_hp_effective * revive_hp)
            invuln = 1.0
            _float_text("复活", player.position + Vector2(0, -60), RunConfig.C_GOLD_LIGHT)
            return 1
        running = false
        player_dead.emit()
        return 2
    return 0


## 第 44 轮：Boss 远程技能计时。每个存活 Boss 独立冷却，到点发一发扇形飞剑。
## 非 Boss 无 skill_cd 字段，直接跳过；阶段越高 CD 越短（RunConfig.BOSS_SKILL_CD）。
func _tick_boss_skills(delta: float) -> void:
    for e in enemies:
        if not bool(e.get("boss", false)) or bool(e["dead"]):
            continue
        var cd: float = float(e.get("skill_cd", 0.0)) - delta
        if cd > 0.0:
            e["skill_cd"] = cd
            continue
        _fire_boss_skill(e)
        var slot: int = _boss_phase_slot(e)
        var reset_cd: float = float(RunConfig.BOSS_SKILL_CD[slot])
        e["skill_cd"] = reset_cd


## 第 44 轮：Boss 发射远程技能。弹数 = BOSS_SKILL_SHOTS[阶段]，扇形展开。
## 伤害基准与近战同源（stage dps + per_stage），再乘阶段伤害系数与投射物比例。
func _fire_boss_skill(e: Dictionary) -> void:
    if not ResourceLoader.exists("res://assets/vfx/frames/%s_00.png" % RunConfig.BOSS_PROJ_VFX):
        return
    var src: Node2D = e["node"]
    var slot: int = _boss_phase_slot(e)
    var shots: int = int(RunConfig.BOSS_SKILL_SHOTS[slot])
    var data: Dictionary = RunConfig.stage_data(stage_index)
    var incoming: float = RunConfig.ENEMY_ATTACK_BASE \
        + RunConfig.ENEMY_ATTACK_PER_STAGE * float(stage_index) \
        + float(data["dps"]) * 0.12
    var phase_atk: float = float(RunConfig.BOSS_PHASE_ATK_SCALE[slot])
    var per_damage: float = incoming * phase_atk * float(RunConfig.BOSS_PROJ_DAMAGE_SCALE)
    # 朝玩家方向；多发时按 spread 均匀扇形展开。
    var to_player: Vector2 = player.position - src.position
    var base_angle: float = atan2(to_player.y, to_player.x)
    var spread: float = float(RunConfig.BOSS_PROJ_SPREAD)
    for i in range(shots):
        var offset: float = (float(i) - float(shots - 1) * 0.5) * spread
        _spawn_projectile(src.position, base_angle + offset, per_damage, String(e["id"]))
    boss_skill_fired.emit(shots, String(e["id"]))


func _spawn_projectile(origin: Vector2, angle: float, damage: float, owner_id: String) -> void:
    var frames := SpriteFrames.new()
    frames.add_animation("fly")
    frames.set_animation_speed("fly", 14.0)
    frames.set_animation_loop("fly", true)
    var loaded: int = 0
    for i in range(4):
        var path: String = "res://assets/vfx/frames/%s_%02d.png" % [RunConfig.BOSS_PROJ_VFX, i]
        if not ResourceLoader.exists(path):
            continue
        var tex := load(path) as Texture2D
        if tex != null:
            frames.add_frame("fly", tex)
            loaded += 1
    if loaded == 0:
        return
    var sp := AnimatedSprite2D.new()
    sp.name = "BossProj"
    sp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    sp.sprite_frames = frames
    sp.position = origin
    sp.play("fly")
    proj_root.add_child(sp)
    var speed: float = float(RunConfig.BOSS_PROJ_SPEED)
    projectiles.append({
        "node": sp, "x": origin.x, "y": origin.y,
        "vx": cos(angle) * speed, "vy": sin(angle) * speed,
        "damage": damage, "life": float(RunConfig.BOSS_PROJ_LIFETIME),
        "owner": owner_id,
    })


## 第 44 轮：投射物飞行 + 命中。命中判定用圆形距离（半径 18px），
## 玩家无敌（闪避 / 受击无敌）时投射物直接穿过不扣血——可闪避。
func _tick_projectiles(delta: float) -> void:
    if projectiles.is_empty():
        return
    var alive: Array = []
    for p in projectiles:
        var px: float = float(p["x"]) + float(p["vx"]) * delta
        var py: float = float(p["y"]) + float(p["vy"]) * delta
        p["x"] = px
        p["y"] = py
        p["life"] = float(p["life"]) - delta
        var sp: AnimatedSprite2D = p["node"]
        sp.position = Vector2(px, py)
        # 超时 / 飞出逻辑屏（留 32px 余量）自毁。
        if float(p["life"]) <= 0.0 or px < -32.0 or px > 512.0 or py < -32.0 or py > 302.0:
            if is_instance_valid(sp):
                sp.queue_free()
            continue
        # 命中玩家：圆形距离 18px。
        if Vector2(px, py).distance_to(player.position) <= 18.0:
            if is_instance_valid(sp):
                sp.queue_free()
            if invuln <= 0.0:
                var hr: int = _hurt_player(float(p["damage"]))
                if hr == 2:
                    # 玩家阵亡：清掉剩余投射物后停止本 tick。
                    _clear_projectiles()
                    return
            else:
                _float_text("闪", player.position + Vector2(0, -46), RunConfig.C_JADE_LIGHT)
            continue
        alive.append(p)
    projectiles = alive


## 第 43 轮：Boss 血量跌破阈值时切阶段。
## 划分与网页 tools/battle_sim.js 完全一致：ratio>0.66→1，>0.33→2，否则 3。
## 只在 Boss 上生效（phase=0 的普通怪直接返回），阶段只升不降，
## 切阶段播放 skill 变身真帧 + 飘字 + 发 signal；不改冻结 HP / dps。
func _check_boss_phase(e: Dictionary) -> void:
    if not bool(e.get("boss", false)) or bool(e["dead"]):
        return
    var ratio: float = float(e["hp"]) / maxf(1.0, float(e["max_hp"]))
    var next_phase: int = 1 if ratio > 0.66 else (2 if ratio > 0.33 else 3)
    var cur: int = int(e["phase"])
    if next_phase <= cur:
        return
    e["phase"] = next_phase
    var n: Node2D = e["node"]
    var label: String = String(RunConfig.BOSS_PHASE_LABEL[next_phase - 1]) if \
        next_phase <= RunConfig.BOSS_PHASE_LABEL.size() else "变身"
    _float_text(label, n.position + Vector2(0, -66), RunConfig.C_CINNABAR)
    var sp: AnimatedSprite2D = e["sprite"]
    if sp.sprite_frames.has_animation("skill"):
        sp.play("skill")
    boss_phase_changed.emit(next_phase, String(e["id"]))


## 取某敌人的当前阶段序号（0-based，用于索引 RunConfig.BOSS_PHASE_* 系数）。
## 非 Boss / phase=0 → 返回 0（系数数组首项均为 1.0，行为不变）。
func _boss_phase_slot(e: Dictionary) -> int:
    if not bool(e.get("boss", false)):
        return 0
    return clampi(int(e["phase"]) - 1, 0, RunConfig.BOSS_PHASE_ATK_SCALE.size() - 1)


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
    var boss_phase: int = 0  # 0 = 本层无 Boss
    for e in enemies:
        enemy_hp += float(e["hp"])
        enemy_max += float(e["max_hp"])
        if bool(e.get("boss", false)) and not bool(e["dead"]):
            boss_phase = maxi(boss_phase, int(e["phase"]))
    var data: Dictionary = RunConfig.stage_data(stage_index)
    return {
        "hp": hp, "max_hp": max_hp_effective,
        "spirit": spirit, "max_spirit": max_spirit_effective,
        "stamina": stamina, "max_stamina": RunConfig.PLAYER_MAX_STAMINA,
        "combo": combo, "enemy_hp": enemy_hp, "enemy_max_hp": maxf(1.0, enemy_max),
        "stage_index": stage_index, "stage_type": String(data["type"]),
        "cds": cds.duplicate(), "running": running,
        # 第 42 轮效果可观测字段（默认时 shield=0 / reveal=false / 其余为默认值）
        "shield": shield, "revive_used": revive_used, "free_cast_used": free_cast_used,
        "reveal": bool(mods.get("reveal", false)),
        # 第 43 轮：本层存活 Boss 当前阶段（0=无 Boss，1/2/3=有 Boss 且处于该阶段）
        "boss_phase": boss_phase,
        # 第 44 轮：在飞投射物数量（供 HUD / headless 校验），非 Boss 层恒为 0
        "projectile_count": projectiles.size(),
        "mods": mods.duplicate(true),
    }


## headless 校验用：直接判定清层，不改动冻结数据。
func debug_clear_stage() -> void:
    for e in enemies:
        e["hp"] = 0.0
        e["dead"] = true
    _check_cleared()


## 第 43 轮 headless 校验用：返回当前层首个 Boss 的阶段快照（无 Boss 返回空字典）。
func debug_boss_probe() -> Dictionary:
    for e in enemies:
        if bool(e.get("boss", false)):
            var sp: AnimatedSprite2D = e["sprite"]
            return {
                "id": String(e["id"]), "phase": int(e["phase"]),
                "hp": float(e["hp"]), "max_hp": float(e["max_hp"]),
                "has_skill_anim": sp.sprite_frames.has_animation("skill"),
                "skill_frames": sp.sprite_frames.get_frame_count("skill") \
                    if sp.sprite_frames.has_animation("skill") else 0,
                "dead": bool(e["dead"]),
            }
    return {}


## 第 43 轮 headless 校验用：把首个存活 Boss 血量设为指定比例并触发一次阶段判定。
func debug_set_boss_hp_ratio(ratio: float) -> void:
    for e in enemies:
        if bool(e.get("boss", false)) and not bool(e["dead"]):
            e["hp"] = maxf(0.0, float(e["max_hp"]) * clampf(ratio, 0.0, 1.0))
            _check_boss_phase(e)
            return


## 第 44 轮 headless 校验用：强制让首个存活 Boss 立即施放一次远程技能。
## 返回本次实际发射弹数（帧资源缺失时为 0）。
func debug_boss_fire_skill() -> int:
    for e in enemies:
        if bool(e.get("boss", false)) and not bool(e["dead"]):
            var before: int = projectiles.size()
            _fire_boss_skill(e)
            return projectiles.size() - before
    return 0


## 第 44 轮 headless 校验用：返回当前投射物快照数组（弹数 / 阶段 / 伤害）。
func debug_projectiles() -> Array:
    var out: Array = []
    for p in projectiles:
        out.append({
            "damage": float(p["damage"]), "owner": String(p["owner"]),
            "x": float(p["x"]), "y": float(p["y"]),
            "vx": float(p["vx"]), "vy": float(p["vy"]),
        })
    return out


## 第 44 轮 headless 校验用：手动推进投射物系统一帧（--script 模式不自动跑物理帧）。
func debug_tick_projectiles(delta: float) -> void:
    _tick_projectiles(delta)


## 第 44 轮 headless 校验用：把所有投射物瞬移到玩家身上，用于验证命中扣血 / 闪避。
func debug_place_projectiles_on_player() -> void:
    for p in projectiles:
        p["x"] = player.position.x
        p["y"] = player.position.y
        var sp: AnimatedSprite2D = p["node"]
        sp.position = player.position


## 第 44 轮 headless 校验用：清掉全部投射物。
func debug_clear_projectiles() -> void:
    _clear_projectiles()
