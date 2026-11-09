class_name SkillCaster
extends Node2D

## 技能释放器 —— 阶段一示范脚本，可直接粘贴运行。
## 挂在 Player 下的 SkillCaster 节点上；VfxLayer 监听 vfx_requested，战斗结算监听 damage_applied。
##
## 核心约定（对应 01-策划案.md 第 6 章 M1 / 第 12 章信号清单）：
##   判定层与表现层解耦 —— 伤害同帧结算，特效由表现层异步播放，特效时长不阻塞战斗节奏。
##   每个技能通过 @export 的 vfx_id 指定专属特效，保证「每次释放技能都有技能效果」。
##
## 适用：Godot 4.x（具体小版本以用户已安装版本为准，API 未核验官方文档）。
## 状态：未在编辑器内运行、未过工程自检 —— 标记「待验证」，不得标为已完成。
## 缩进：本工程统一 4 空格，禁用 Tab。

# ---- 信号清单（与策划案第 12 章信号表一一对应）----
signal cast_started(skill_id: StringName, facing: int)
signal vfx_requested(vfx_id: StringName, world_pos: Vector2, facing: int)
signal damage_applied(target: Node2D, amount: int, is_crit: bool)
signal cast_finished(skill_id: StringName)

# ---- 可调数值一律走导出属性 / 资源，不硬编码在逻辑里 ----
@export_group("伤害")
@export var base_damage: int = 60
@export var realm_ratio: float = 1.0
@export var extra_pool: float = 0.0
@export var combo_multiplier: float = 1.0
@export var defense_rate: float = 0.0
@export var crit_rate: float = 0.15
@export var crit_multiplier: float = 1.8

@export_group("节奏与判定")
@export var cast_lock: float = 0.35
@export var hitbox_offset_x: float = 64.0

@export_group("表现")
@export var vfx_id: StringName = &"sword_qi"
@export var facing: int = 1

const MIN_DAMAGE: int = 1
const MAX_DAMAGE: int = 9999
const MAX_DEFENSE_RATE: float = 0.75

var _is_casting: bool = false


func set_facing(dir: int) -> void:
    ## 只记录朝向；镜像由角色 Sprite2D 与 VfxLayer 各自处理，
    ## 不镜像整个场景（否则文字与 UI 会反向）。
    facing = 1 if dir >= 0 else -1


func can_cast() -> bool:
    return not _is_casting


func cast(skill_id: StringName, targets: Array[Node2D]) -> void:
    if not can_cast():
        return
    _is_casting = true
    cast_started.emit(skill_id, facing)

    # 1) 表现层：只发信号，不等回传。特效时长不影响战斗节奏。
    var origin: Vector2 = global_position + Vector2(hitbox_offset_x * float(facing), 0.0)
    vfx_requested.emit(vfx_id, origin, facing)

    # 2) 判定层：同帧结算，与特效解耦。目标可能已被释放，先判有效性。
    for target in targets:
        var t: Node2D = target
        if not is_instance_valid(t):
            continue
        var is_crit: bool = randf() < crit_rate
        var amount: int = compute_damage(is_crit)
        damage_applied.emit(t, amount, is_crit)

    # 3) 硬直：用 SceneTreeTimer，不占每帧回调。
    await get_tree().create_timer(cast_lock).timeout
    _is_casting = false
    cast_finished.emit(skill_id)


## final = clamp(round((base × realm_ratio + extra_pool) × combo × crit × (1 − defense)), 1, 9999)
## 与 01-策划案.md 8.1 及 数值框架.csv 同源，可离线复算。
func compute_damage(is_crit: bool) -> int:
    if base_damage < 0 or realm_ratio < 0.0 or extra_pool < 0.0:
        push_error("SkillCaster: 伤害参数出现负值，已钳制到下限")
    var base: float = float(maxi(base_damage, 0))
    var realm: float = maxf(realm_ratio, 0.0)
    var pool: float = maxf(extra_pool, 0.0)
    var crit_mult: float = crit_multiplier if is_crit else 1.0
    var offense: float = base * realm + pool
    var mitigation: float = 1.0 - clampf(defense_rate, 0.0, MAX_DEFENSE_RATE)
    var raw: float = offense * combo_multiplier * crit_mult * mitigation
    return clampi(int(round(raw)), MIN_DAMAGE, MAX_DAMAGE)


func _exit_tree() -> void:
    ## 切场景清理：复位状态。信号连接由接收方在其 _exit_tree 中断开（连接写在接收方）。
    _is_casting = false


## ------------------------------------------------------------------
## 最小用法（阶段二接入，本轮不落工程）：
##   # 在 Player 或父节点的 _ready 中，连接写在接收方：
##   $SkillCaster.vfx_requested.connect($VfxLayer.spawn_vfx)
##   $SkillCaster.damage_applied.connect($BattleResolver.apply_damage)
##   $SkillCaster.cast(&"sword_qi", current_targets)
##
## 验证方式（M2 验收）：
##   运行场景释放一次技能，日志应恰好出现 1 条 vfx_requested、
##   N 条 damage_applied、1 条 cast_finished；且 vfx_requested 与
##   damage_applied 的 Engine.get_process_frames() 相同（证明同帧）。
##   compute_damage 的极值验算命令见 01-策划案.md 8.1。
## ------------------------------------------------------------------
