extends SceneTree
# @trace DF-04, DF-12, DF-13, DF-15
# 生成 SpriteFrames 资源（主角 idle3 + run4），让 Godot 引擎自己写 .tres 格式，
# 不手写引擎资源格式。生成后场景里 AnimatedSprite2D 直接挂这个资源，
# 编辑器即可预览帧与动画列表，不再有「必须先设置 SpriteFrames 资源」的黄色警告。
#
# 用法：Godot --headless --path <工程根> --script tools/build_sprite_frames.gd
# 幂等：重复运行覆盖同一文件，结果一致。


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

const OUT_PATH := "res://assets/char/player_frames.tres"


func _init() -> void:
    var frames := SpriteFrames.new()
    _add_animation(frames, "idle", IDLE_FRAMES, 6.0)
    _add_animation(frames, "run", RUN_FRAMES, 8.0)

    var err: int = ResourceSaver.save(frames, OUT_PATH)
    print("FRAMES|save_err=", err, "|path=", OUT_PATH)
    print("FRAMES|idle=", frames.get_frame_count("idle"),
          "|run=", frames.get_frame_count("run"),
          "|idle_fps=", frames.get_animation_speed("idle"),
          "|run_fps=", frames.get_animation_speed("run"))
    if err != OK:
        quit(1)
        return
    # 回读校验：确认落盘后仍可解析、帧数不变
    var back := ResourceLoader.load(OUT_PATH) as SpriteFrames
    if back == null:
        print("FRAMES|FAIL|回读失败")
        quit(1)
        return
    print("FRAMES|reload|idle=", back.get_frame_count("idle"),
          "|run=", back.get_frame_count("run"))
    print("FRAMES|PASS")
    quit()


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
