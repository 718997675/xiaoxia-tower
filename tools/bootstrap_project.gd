extends SceneTree
# @trace DF-13
# 工程配置引导器：让 Godot 4.7.2 自己写 project.godot，避免手猜键名与序列化格式。
# 用法（命令里的绝对路径只在文档中给出，本文件不含任何机器绝对路径）：
#   Godot --headless --path <工程根> --script res://tools/bootstrap_project.gd
# 产物：project.godot（引擎生成，非手写缓存）；重跑幂等。
# 键名已由本机 4.7.2.stable headless 的 ProjectSettings.get_setting 实测核对。


func _key(code: int) -> InputEventKey:
    var ev := InputEventKey.new()
    ev.physical_keycode = code
    return ev


func _action(codes: Array) -> Dictionary:
    var events: Array = []
    for c in codes:
        events.append(_key(int(c)))
    return {"deadzone": 0.5, "events": events}


func _init() -> void:
    # 1) 先取证：打印拉伸模式与纹理过滤的合法枚举，不臆造取值
    for p in ProjectSettings.get_property_list():
        var n := str(p.get("name", ""))
        if n == "display/window/stretch/mode" or n == "rendering/textures/canvas_textures/default_texture_filter":
            print("BOOTSTRAP|", n, "|default=", str(ProjectSettings.get_setting(n)),
                  "|hint=", str(p.get("hint_string", "")))

    # 2) 应用设置（与 04 §2 / 01 §12 / DF-13 一致）
    ProjectSettings.set_setting("application/config/name", "九重天梯 · 最小验证工程")
    ProjectSettings.set_setting("application/config/description",
        "阶段二门禁验证：480x270 逻辑分辨率 x 整数 4 倍 / Nearest 硬边 / 朝右一套 scale.x 镜像")
    ProjectSettings.set_setting("application/run/main_scene", "res://scenes/MinimalRun.tscn")
    ProjectSettings.set_setting("application/config/features", PackedStringArray(["4.7", "GL Compatibility"]))

    ProjectSettings.set_setting("display/window/size/viewport_width", 480)
    ProjectSettings.set_setting("display/window/size/viewport_height", 270)
    ProjectSettings.set_setting("display/window/size/window_width_override", 1920)
    ProjectSettings.set_setting("display/window/size/window_height_override", 1080)
    ProjectSettings.set_setting("display/window/stretch/mode", "viewport")
    ProjectSettings.set_setting("display/window/stretch/aspect", "keep")

    # 本机 4.7.2 实测默认值为 1（Linear）——像素硬边会被插值成糊团，必须显式设 0
    ProjectSettings.set_setting("rendering/textures/canvas_textures/default_texture_filter", 0)
    ProjectSettings.set_setting("rendering/textures/default_filters/use_nearest_mipmap_filter", false)

    # 3) 输入动作名与 01 §6 输入映射表逐字一致（最小工程只需左右移动）
    ProjectSettings.set_setting("input/move_left", _action([KEY_A, KEY_LEFT]))
    ProjectSettings.set_setting("input/move_right", _action([KEY_D, KEY_RIGHT]))

    var err: int = ProjectSettings.save()
    print("BOOTSTRAP|save_err=", err)
    quit()
