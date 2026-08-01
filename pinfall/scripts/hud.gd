extends CanvasLayer
## The whole interface: a level number, a target, and one verdict line.
##
## Deliberately almost nothing. Games in this genre are watched before they are played, and every
## element on screen competes with the one thing that has to be legible in a three-second ad —
## the fluid moving. No buttons, no currency, no banner. Tap anywhere to retry.

var _title: Label
var _sub: Label
var _verdict: Label


func _ready() -> void:
	layer = 10
	_title = _label(28, Color(1, 1, 1, 0.92), Vector2(0, 54), HORIZONTAL_ALIGNMENT_CENTER)
	_sub = _label(19, Color(1, 1, 1, 0.55), Vector2(0, 92), HORIZONTAL_ALIGNMENT_CENTER)
	_verdict = _label(44, Color(1, 0.86, 0.55, 0), Vector2(0, 520), HORIZONTAL_ALIGNMENT_CENTER)


func _label(size: int, colour: Color, offset: Vector2, align: int) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", colour)
	# An outline rather than a panel: text has to survive being drawn over a bright concrete wall
	# and over near-black shadow in the same frame.
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", 6)
	l.horizontal_alignment = align
	l.anchor_right = 1.0
	l.offset_top = offset.y
	add_child(l)
	return l


func set_level(n: int, needed: int) -> void:
	_title.text = "Level %d" % n
	_sub.text = "Get %d drops into the crucible" % needed


func verdict(text: String, good: bool) -> void:
	_verdict.text = text
	_verdict.add_theme_color_override(
		"font_color", Color(1, 0.86, 0.55, 1) if good else Color(1, 0.45, 0.4, 1))
	var tw := create_tween()
	tw.tween_property(_verdict, "scale", Vector2(1.06, 1.06), 0.18)
	tw.tween_property(_verdict, "scale", Vector2(1.0, 1.0), 0.22)
