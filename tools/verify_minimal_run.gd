extends SceneTree
# @trace DF-13, DF-15
# 离线验证：让 4.7.2 引擎自己解析 .tscn、编译 GDScript、加载 7 张 PNG 并跑 _ready()。
# 用法：Godot --headless --path <工程根> --script res://tools/verify_minimal_run.gd
# 这不是「画面已目检」；像素糊不糊、镜像穿不穿帮仍需用户按 F5 看。


func _init() -> void:
    var packed := load("res://scenes/MinimalRun.tscn") as PackedScene
    if packed == null:
        print("VERIFY|FAIL|scene load failed")
        quit(1)
        return

    var inst := packed.instantiate()
    root.add_child(inst)  # 触发 _ready()，SpriteFrames 在此构造
    print("VERIFY|scene=", inst.name, "|children=", inst.get_child_count())

    var player := inst.get_node_or_null("Player")
    if player == null:
        print("VERIFY|FAIL|Player node missing")
        quit(1)
        return
    print("VERIFY|player=", player.name, "|script_attached=", player.get_script() != null)

    # 碰撞体断言：CharacterBody2D 必须带 CollisionShape2D，否则编辑器节点面板会挂黄色警告，
    # 且 move_and_slide() 不会与任何物体产生碰撞。
    var body_shape := player.get_node_or_null("Body") as CollisionShape2D
    if body_shape == null:
        print("VERIFY|FAIL|Player/Body CollisionShape2D missing")
        quit(1)
        return
    var ground_body := inst.get_node_or_null("GroundBody") as StaticBody2D
    if ground_body == null:
        print("VERIFY|FAIL|GroundBody StaticBody2D missing")
        quit(1)
        return
    print("VERIFY|collision=Player/Body+GroundBody/Shape present",
          "|player_shape=", body_shape.shape.get_class(),
          "|player_bottom=", player.position.y + body_shape.position.y + body_shape.shape.size.y / 2.0,
          "|ground_top=", ground_body.position.y)

    var sp := player.get_node_or_null("Sprite") as AnimatedSprite2D
    if sp == null:
        print("VERIFY|FAIL|AnimatedSprite2D node missing")
        quit(1)
        return
    print("VERIFY|sprite_node=AnimatedSprite2D|frames_before=", sp.sprite_frames != null)
    if sp.sprite_frames == null:
        # --script 模式下 SceneTree.root 的节点入树时序与编辑器不同，
        # 显式触发一次 _ready() 以便离线取证（不改 PlayerProbe.gd 本身）。
        player.call("_ready")
    if sp.sprite_frames == null:
        print("VERIFY|FAIL|SpriteFrames 未构造")
        quit(1)
        return
    print("VERIFY|idle_frames=", sp.sprite_frames.get_frame_count("idle"),
          "|run_frames=", sp.sprite_frames.get_frame_count("run"),
          "|idle_fps=", sp.sprite_frames.get_animation_speed("idle"),
          "|run_fps=", sp.sprite_frames.get_animation_speed("run"))

    print("VERIFY|main_scene=", str(ProjectSettings.get_setting("application/run/main_scene")))
    print("VERIFY|viewport=", str(ProjectSettings.get_setting("display/window/size/viewport_width")), "x",
          str(ProjectSettings.get_setting("display/window/size/viewport_height")))
    print("VERIFY|window_override=",
          str(ProjectSettings.get_setting("display/window/size/window_width_override")), "x",
          str(ProjectSettings.get_setting("display/window/size/window_height_override")))
    print("VERIFY|stretch_mode=", str(ProjectSettings.get_setting("display/window/stretch/mode")))
    print("VERIFY|texture_filter=", str(ProjectSettings.get_setting("rendering/textures/canvas_textures/default_texture_filter")),
          " (0=Nearest)")
    print("VERIFY|input_move_left=", str(InputMap.has_action("move_left")),
          "|input_move_right=", str(InputMap.has_action("move_right")))
    print("VERIFY|PASS")
    quit()
