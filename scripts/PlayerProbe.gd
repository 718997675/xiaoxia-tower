extends CharacterBody2D
# @trace DF-04, DF-12, DF-13, DF-15
# 最小验证工程：只验证「主角 idle 3 + run 4 帧、左右跑、朝右一套 scale.x 镜像」。
# 不实现战斗 / 卡牌 / 存档 / 特效——那些属于正式工程，见 01 §12 节点树。
# 已在 Godot 4.7.2 headless 加载验证；画面目检仍需用户在编辑器按 F5。

const IDLE_FRAMES: Array[String] = [
    "res://assets/char/char_player_idle_r_00.png",
    "res://assets/char/char_player_idle_r_01.png",
    "res://assets/char/char_player_idle_r_02.png",
]

const RUN_FRAMES: Array[String] = [
    "res://assets/char/char_player_run_r_00.png",
    "res://assets/char/char_player_run_r_01.png",
    "res://assets/char/char_player_run_r_02.png",
    "res://assets/char/char_player_run_r_03.png",
]

@export var move_speed: float = 60.0
@export var idle_fps: float = 6.0
@export var run_fps: float = 8.0

signal facing_changed(facing: int)

var facing: int = 1
@onready var sprite: AnimatedSprite2D = $Sprite


func _ready() -> void:
    # 正常路径：场景里已挂 SpriteFrames 资源 assets/char/player_frames.tres（由
    # tools/build_sprite_frames.gd 用引擎生成），编辑器可直接预览帧与动画列表。
    # 兜底：资源缺失时才在此动态构建，保证脚本单独跑也不会空白。
    if sprite.sprite_frames == null:
        var frames := SpriteFrames.new()
        _add_animation(frames, "idle", IDLE_FRAMES, idle_fps)
        _add_animation(frames, "run", RUN_FRAMES, run_fps)
        sprite.sprite_frames = frames
    sprite.play("idle")


func _add_animation(frames: SpriteFrames, anim: StringName,
        paths: Array[String], fps: float) -> void:
    frames.add_animation(anim)
    frames.set_animation_speed(anim, fps)
    frames.set_animation_loop(anim, true)
    for path in paths:
        var tex := load(path) as Texture2D
        if tex == null:
            push_error("缺帧: " + path)
            continue
        frames.add_frame(anim, tex)


func _physics_process(_delta: float) -> void:
    var axis := Input.get_axis("move_left", "move_right")
    velocity = Vector2(axis * move_speed, 0.0)
    move_and_slide()
    position.x = clampf(position.x, 16.0, 464.0)

    if axis != 0.0:
        var new_facing: int = 1 if axis > 0.0 else -1
        if new_facing != facing:
            facing = new_facing
            # DF-04：只镜像 Sprite 本身，不镜像整个场景，否则文字/UI 会反向
            sprite.scale.x = float(facing)
            facing_changed.emit(facing)
        if sprite.animation != "run":
            sprite.play("run")
    elif sprite.animation != "idle":
        sprite.play("idle")
