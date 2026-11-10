extends Control
class_name CardArtView

## 第 39 轮 · 「一卡一插画」卡面视图组件（96×144，沿用 docs/12 §2 的三层分离）。
##
## 72 张 84×56 插画位于 res://assets/ui/card_art/<card_id>.png；
## 卡框 / 类别纹样继续复用 assets/ui/cards/ 下 10 张冻结 PNG，本组件只读不写。
## 文字层用引擎默认字体（R9 字体授权未结案），卡名由调用方传入，插画本身不含文字。
##
## 用法：
##   var v := CardArtView.new()
##   add_child(v)
##   v.show_card("card_jianfeng", "common", "剑锋淬砺", "dmg")
## 或在编辑器里打开 scenes/CardArtView.tscn，直接改 card_id 导出属性。
##
## 边界：Q17 未拍板、GUI F5 未跑；本组件只负责显示，不含任何数值 / 概率 / 权重 / 规则。
## 84×56 与冻结坐标 84×57 的 1px 差异仍属 PROPOSAL，待 4× 实机排版复核。

const ART_DIR := "res://assets/ui/card_art/"
const FRAME_DIR := "res://assets/ui/cards/"
const CARD_SIZE := Vector2(96, 144)
const ART_POS := Vector2(6, 19)
const ART_SIZE := Vector2(84, 56)

@export var card_id: String = "card_jianfeng"
@export var rarity: String = "common"
@export var card_name: String = ""
@export var category: String = "dmg"

var frame_rect: TextureRect
var art_rect: TextureRect
var sigil_rect: TextureRect
var name_label: Label


func _ready() -> void:
	custom_minimum_size = CARD_SIZE
	_build_layers()
	show_card(card_id, rarity, card_name, category)


func _add_layer(node: Control, pos: Vector2, size: Vector2) -> void:
	node.position = pos
	node.size = size
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(node)


func _build_layers() -> void:
	# ① 宣纸底
	var paper := ColorRect.new()
	_add_layer(paper, Vector2.ZERO, CARD_SIZE)
	paper.color = Color(0.910, 0.875, 0.784)  # #E8DFC8

	# ② 冻结卡框（96×144）
	frame_rect = TextureRect.new()
	_add_layer(frame_rect, Vector2.ZERO, CARD_SIZE)
	frame_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

	# ③ 一卡一插画（84×56 @ 6,19），替换原先 48×48 居中纹样
	art_rect = TextureRect.new()
	_add_layer(art_rect, ART_POS, ART_SIZE)
	art_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	art_rect.stretch_mode = TextureRect.STRETCH_SCALE

	# ④ 类别纹样缩到类别条 8×8，避免与插画重叠
	sigil_rect = TextureRect.new()
	_add_layer(sigil_rect, Vector2(5, 4), Vector2(8, 8))
	sigil_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sigil_rect.stretch_mode = TextureRect.STRETCH_SCALE

	# ⑤ 卡名文字层（插画与卡面 PNG 均不含文字）
	name_label = Label.new()
	_add_layer(name_label, Vector2(4, 79), Vector2(88, 15))
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name_label.add_theme_font_size_override("font_size", 12)


func show_card(p_id: String, p_rarity: String = "common",
		p_name: String = "", p_cat: String = "dmg") -> void:
	card_id = p_id
	rarity = p_rarity
	card_name = p_name
	category = p_cat
	if frame_rect == null:
		return  # 层还没建好，_ready() 会再调一次

	var art_path := ART_DIR + p_id + ".png"
	if ResourceLoader.exists(art_path):
		art_rect.texture = load(art_path) as Texture2D
	else:
		push_warning("CardArtView: 缺插画 " + art_path)
		art_rect.texture = null

	var frame_path := FRAME_DIR + "frame_" + p_rarity + ".png"
	if not ResourceLoader.exists(frame_path):
		frame_path = FRAME_DIR + "frame_common.png"
	frame_rect.texture = load(frame_path) as Texture2D

	var sigil_path := FRAME_DIR + "sigil_" + p_cat + ".png"
	if ResourceLoader.exists(sigil_path):
		sigil_rect.texture = load(sigil_path) as Texture2D
	else:
		sigil_rect.texture = null

	name_label.text = p_name


static func art_path(p_id: String) -> String:
	## 给卡牌逻辑层 / 图鉴按 id 取资源时用；与 data/buff-card-library.json 的 id 同源。
	return ART_DIR + p_id + ".png"
