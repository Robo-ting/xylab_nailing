# -*- coding: utf-8 -*-
"""
XYLab · 组外交流汇报 PPT（2026-08-18）
科研汇报风格 + 强化章节层级 + 演讲者念稿。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seminar_scripts import SCRIPTS  # noqa: E402

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
THESIS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(THESIS_ROOT, "docs", "XYLab-组外交流-20260818.pptx")
SCRIPT_MD = os.path.join(THESIS_ROOT, "docs", "XYLab-组外交流-20260818-讲稿.md")

# ── 配色 ──
BG = "FFFFFF"
BG2 = "F8FAFC"
PANEL = "F1F5F9"
PANEL2 = "E8EEF4"
BORDER = "CBD5E1"
PRIMARY = "1E3A5F"
ACCENT = "2563EB"
ACCENT2 = "3B82F6"
ACCENT_LIGHT = "DBEAFE"
TEAL = "0F766E"
TEAL_LIGHT = "CCFBF1"
GREEN = "047857"
AMBER = "B45309"
PURPLE = "6D28D9"
TEXT = "1E293B"
DIM = "475569"
MUTE = "64748B"
WHITE = "FFFFFF"

FONT = "微软雅黑"
FONT_L = "Arial"
SW, SH, MX = 13.333, 7.5, 0.92
FOOTER = "浙江大学 ZJUI · 肖岩教授课题组 · 暑期学术活动日 2026.08.18"
BULLET = "▸"
BULLET_INDENT = 1.35

_script_idx = 0


def C(h: str) -> RGBColor:
    return RGBColor.from_string(h)


def _set_font(run, name):
    run.font.name = name
    rPr = run.font._rPr
    for tag in ("a:latin", "a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", name)


def no_shadow(shape):
    try:
        shape.shadow.inherit = False
    except Exception:
        pass


def solid(shape, rgb, line_rgb=None, line_w=None):
    shape.fill.solid()
    shape.fill.fore_color.rgb = C(rgb)
    if line_rgb:
        shape.line.color.rgb = C(line_rgb)
        shape.line.width = Pt(line_w or 1)
    else:
        shape.line.fill.background()
    no_shadow(shape)


def rect(slide, x, y, w, h, rgb=None, shape=MSO_SHAPE.RECTANGLE, line_rgb=None, line_w=None, radius=None):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if rgb:
        solid(sp, rgb, line_rgb, line_w)
    else:
        sp.fill.background()
        if line_rgb:
            sp.line.color.rgb = C(line_rgb)
            sp.line.width = Pt(line_w or 1)
        else:
            sp.line.fill.background()
        no_shadow(sp)
    if radius is not None:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    return sp


def tb(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    return tf


def para(tf, text, size, color, bold=False, font=FONT, align=PP_ALIGN.LEFT,
         after=6, before=0, line=None, first=False):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(after)
    p.space_before = Pt(before)
    if line:
        p.line_spacing = line
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = C(color)
    _set_font(r, font)
    return p


def runs_para(tf, runs, align=PP_ALIGN.LEFT, after=6, before=0, line=None, first=False):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(after)
    p.space_before = Pt(before)
    if line:
        p.line_spacing = line
    for spec in runs:
        text, size, color, bold = spec[0], spec[1], spec[2], spec[3]
        font = spec[4] if len(spec) > 4 else FONT
        r = p.add_run()
        r.text = text
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = C(color)
        _set_font(r, font)
    return p


def card(slide, x, y, w, h, rgb=PANEL, line=BORDER, radius=0.06):
    return rect(slide, x, y, w, h, rgb, MSO_SHAPE.ROUNDED_RECTANGLE, line, 1, radius=radius)


prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
BLANK = prs.slide_layouts[6]
_page = [0]


def new_slide(footer=True):
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, SW, SH, BG)
    rect(s, 0, 0, SW, 0.08, PRIMARY)
    if footer:
        _page[0] += 1
        rect(s, 0, SH - 0.58, SW, 0.58, BG2)
        rect(s, MX, SH - 0.58, SW - 2 * MX, 0.012, BORDER)
        f = tb(s, MX, SH - 0.48, 10, 0.32)
        para(f, FOOTER, 8.5, MUTE, first=True)
        pg = tb(s, SW - MX - 0.55, SH - 0.49, 0.45, 0.34, MSO_ANCHOR.MIDDLE)
        para(pg, f"{_page[0]:02d}", 10.5, MUTE, align=PP_ALIGN.RIGHT, first=True, font=FONT_L)
    return s


def kicker_title(s, kicker, title, tsize=30, accent=ACCENT, part=None, part_color=None):
    """章节页眉：左侧色条 + 英文 kicker + 中文大标题 + 可选 PART 徽章。"""
    pc = part_color or accent
    if part:
        badge = rect(s, SW - MX - 2.55, 0.52, 2.35, 0.48, pc, line_rgb=pc, line_w=1, radius=0.08)
        tf = tb(s, SW - MX - 2.45, 0.56, 2.15, 0.4, MSO_ANCHOR.MIDDLE)
        para(tf, part, 10.5, WHITE, bold=True, align=PP_ALIGN.CENTER, first=True, font=FONT_L)
    rect(s, MX, 0.62, 0.14, 0.72, accent)
    k = tb(s, MX + 0.28, 0.52, 11, 0.38)
    para(k, kicker, 12.5, accent, bold=True, first=True, font=FONT_L)
    t = tb(s, MX, 0.95, SW - 2 * MX - (2.6 if part else 0), 1.05)
    para(t, title, tsize, PRIMARY, bold=True, first=True, line=1.08)
    rect(s, MX, 1.92, SW - 2 * MX, 0.028, accent)


def section_band(s, y, label, color=ACCENT, bg=ACCENT_LIGHT):
    """议程/分区标题条。"""
    rect(s, MX, y, SW - 2 * MX, 0.42, bg, line_rgb=color, line_w=1.2, radius=0.06)
    tf = tb(s, MX + 0.22, y + 0.06, SW - 2 * MX - 0.4, 0.32, MSO_ANCHOR.MIDDLE)
    para(tf, label, 12.5, color, bold=True, first=True)


def card_heading(slide, x, y, w, text, color):
    """卡片内小标题条。"""
    rect(slide, x, y, w, 0.42, color, line_rgb=color, line_w=0, radius=0.04)
    tf = tb(slide, x + 0.18, y + 0.05, w - 0.3, 0.34, MSO_ANCHOR.MIDDLE)
    para(tf, text, 14, WHITE, bold=True, first=True)


def add_bullet_para(tf, text, size=12, bullet_color=ACCENT, text_color=DIM,
                    after=6, line=1.18, first=False):
    p = tf.paragraphs[0] if (first and not tf.paragraphs[0].runs) else tf.add_paragraph()
    p.alignment = PP_ALIGN.LEFT
    p.space_after = Pt(after)
    p.space_before = Pt(0)
    if line:
        p.line_spacing = line
    indent = Pt(size * BULLET_INDENT)
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(int(indent)))
    pPr.set("indent", str(int(-indent)))
    rb = p.add_run()
    rb.text = BULLET
    rb.font.size = Pt(size)
    rb.font.bold = True
    rb.font.color.rgb = C(bullet_color)
    _set_font(rb, FONT)
    rs = p.add_run()
    rs.text = " " + text
    rs.font.size = Pt(size)
    rs.font.color.rgb = C(text_color)
    _set_font(rs, FONT)
    return p


def bullet_list_tf(tf, items, color=ACCENT, size=12, text_color=DIM, after=6, line=1.18,
                   start_first=False):
    for i, text in enumerate(items):
        add_bullet_para(tf, text, size, color, text_color, after, line,
                        first=(start_first and i == 0))


def bullet_list(slide, x, y, w, items, color=ACCENT, size=13, gap=0.46,
                text_color=DIM, after=6, line=1.18):
    h = len(items) * gap + 0.08
    tf = tb(slide, x, y, w, h)
    bullet_list_tf(tf, items, color, size, text_color, after, line, start_first=True)
    return y + h


def set_notes(slide, text: str):
    tf = slide.notes_slide.notes_text_frame
    tf.clear()
    tf.text = text.strip()


def note_slide(slide):
    global _script_idx
    set_notes(slide, SCRIPTS[_script_idx])
    _script_idx += 1


def export_script_md():
    titles = [
        "封面", "议程", "研究背景", "已完成基础", "系统框架",
        "核心科学问题", "感知与钉位规划", "规范决策", "机械臂执行", "工作安排", "讨论",
    ]
    lines = ["# XYLab 组外交流 · 逐页念稿\n", f"配套 PPT：`XYLab-组外交流-20260818.pptx`\n"]
    for i, (title, script) in enumerate(zip(titles, SCRIPTS), 1):
        lines.append(f"\n---\n\n## 第 {i} 页 · {title}\n\n{script.strip()}\n")
    with open(SCRIPT_MD, "w", encoding="utf-8") as f:
        f.write("".join(lines))


# ══════════════════════════════════════════════════════════════
# Slide 1 · 封面
# ══════════════════════════════════════════════════════════════
s = new_slide(footer=False)
rect(s, 0, 0, SW, 0.72, PRIMARY)
tf = tb(s, MX, 0.18, SW - 2 * MX, 0.42)
para(tf, "SUMMER ACADEMIC DAY  ·  2026.08.18", 12, WHITE, bold=True, first=True, font=FONT_L)
tf = tb(s, MX + 0.1, 0.38, 5.5, 0.28)
para(tf, "EMBODIED AI  ×  CIVIL ENGINEERING", 10.5, "93C5FD", bold=True, first=True, font=FONT_L)

# 主标题区
rect(s, MX, 1.35, 0.16, 2.55, ACCENT)
t = tb(s, MX + 0.38, 1.32, SW - 2 * MX - 0.4, 2.6)
para(t, "缺陷检测驱动的", 38, PRIMARY, bold=True, first=True, after=4)
para(t, "木材打钉系统", 38, PRIMARY, bold=True, after=4)
para(t, "设计与验证", 32, ACCENT, bold=True, after=8)

sub = tb(s, MX + 0.38, 4.05, SW - 2 * MX - 0.4, 0.85)
para(sub, "Design, development and validation of a defect-informed timber nailing system", 13.5, DIM, first=True, after=5, font=FONT_L)
para(sub, "具身智能 × 土木工程  ·  感知 — 规划 — 决策 — 执行", 13, MUTE, after=0)

# 信息卡
bar = card(s, MX, 5.05, SW - 2 * MX, 1.2, BG2, ACCENT, 0.1)
rect(s, MX, 5.05, 0.08, 1.2, ACCENT)
info = tb(s, MX + 0.35, 5.05, SW - 2 * MX - 0.6, 1.2, MSO_ANCHOR.MIDDLE)
runs_para(info, [
    ("汇报人  ", 11, MUTE, False), ("王尉廷  ", 13, TEXT, True),
    ("     导师  ", 11, MUTE, False), ("肖岩 教授  ", 13, TEXT, True),
    ("     单位  ", 11, MUTE, False), ("浙江大学 ZJUI", 13, TEXT, True),
], first=True)
note_slide(s)

# ══════════════════════════════════════════════════════════════
# Slide 2 · 议程
# ══════════════════════════════════════════════════════════════
s = new_slide()
kicker_title(s, "AGENDA", "汇报结构", tsize=32, part="OVERVIEW")

agenda = [
    ("01", "研究背景", "具身智能 × 土木：木材缺陷感知打钉", False, "一、基础回顾"),
    ("02", "已完成基础", "组内力学底座 + XYLab 系统原型", False, None),
    ("03", "系统框架", "感知—认知—执行 具身闭环", False, None),
    ("04", "核心问题", "力学参数如何进入可执行决策？", False, None),
    ("05", "感知与规划", "YOLO 真机 · 手眼标定 · 多板 ROI", True, "二、后续计划"),
    ("06", "规范决策", "Eurocode 5 RAG + 分层 Agent", True, None),
    ("07", "机械臂闭环", "Skill 原语 → 单板 → 墙段试钉", True, None),
    ("08", "时间线与讨论", "2026 Q3 – 2027 H1", True, None),
]
y = 2.05
for num, title, desc, future, band in agenda:
    if band:
        section_band(s, y, band, ACCENT if "二" in band else TEAL,
                     ACCENT_LIGHT if "二" in band else TEAL_LIGHT)
        y += 0.52
    card(s, MX, y, SW - 2 * MX, 0.52, PANEL if future else BG2, ACCENT if future else TEAL, 0.08)
    col = ACCENT if future else TEAL
    rect(s, MX, y + 0.06, 0.06, 0.4, col)
    tf = tb(s, MX + 0.2, y + 0.07, 0.55, 0.38, MSO_ANCHOR.MIDDLE)
    para(tf, num, 14, col, bold=True, font=FONT_L, align=PP_ALIGN.CENTER, first=True)
    tf = tb(s, MX + 0.72, y + 0.08, 2.8, 0.38)
    para(tf, title, 14, TEXT, bold=True, first=True)
    tf = tb(s, MX + 3.72, y + 0.09, SW - 2 * MX - 4.0, 0.38)
    para(tf, desc, 11.5, DIM, first=True)
    y += 0.57
note_slide(s)

# ══════════════════════════════════════════════════════════════
# Slide 3 · 背景
# ══════════════════════════════════════════════════════════════
s = new_slide()
kicker_title(s, "CONTEXT", "具身智能 × 土木：木材缺陷感知打钉", part="PART 01", part_color=TEAL)
cw = (SW - 2 * MX - 0.55) / 2
rows = [
    ("工程痛点", [
        "木材墙体 / 托板打钉：天然缺陷空间分布随机",
        "常规按图打钉无法避让木节、裂缝、腐朽",
        "人工依赖经验，质量难追溯、难规模化",
    ], TEAL),
    ("研究目标", [
        "缺陷视觉感知 → 规范约束下的智能钉位规划",
        "多板叠合场景融合各板缺陷与几何约束",
        "力学试验数据驱动决策，机械臂真机闭环执行",
    ], ACCENT),
]
for i, (head, bullets, col) in enumerate(rows):
    x = MX + i * (cw + 0.55)
    card(s, x, 2.12, cw, 3.55, BG2, col, 0.08)
    card_heading(s, x, 2.12, cw, head, col)
    bullet_list(s, x + 0.22, 2.68, cw - 0.4, bullets, col, 13, 0.48)
highlight = card(s, MX, 5.95, SW - 2 * MX, 0.62, ACCENT_LIGHT, ACCENT, 0.08)
tf = tb(s, MX + 0.28, 6.02, SW - 2 * MX - 0.5, 0.48, MSO_ANCHOR.MIDDLE)
runs_para(tf, [
    ("课题组优势  ", 12.5, ACCENT, True),
    ("材料 — 连接 — 结构全链条积累，为具身智能落地提供土木底座", 12.5, PRIMARY, True),
], first=True)
note_slide(s)

# ══════════════════════════════════════════════════════════════
# Slide 4 · 已完成
# ══════════════════════════════════════════════════════════════
s = new_slide()
kicker_title(s, "FOUNDATION", "组内力学底座 + XYLab 具身智能原型", part="PART 02", part_color=TEAL)
stat_w = (SW - 2 * MX - 0.45) / 4
stats = [
    ("TBK 系列", "拉拔/剪切", "试验数据", TEAL),
    ("11", "控制模块", "可运行原型", ACCENT),
    ("7", "缺陷类别", "YOLO 分割", ACCENT2),
    ("6+", "规范条目", "EC5 数字化", GREEN),
]
for i, (n, l1, l2, c) in enumerate(stats):
    x = MX + i * (stat_w + 0.15)
    card(s, x, 2.12, stat_w, 1.38, BG2, c, 0.08)
    rect(s, x, 2.12, stat_w, 0.06, c)
    tf = tb(s, x + 0.15, 2.28, stat_w - 0.25, 1.1, MSO_ANCHOR.MIDDLE)
    para(tf, n, 24, c, bold=True, font=FONT_L, first=True, after=2)
    para(tf, l1, 11.5, TEXT, bold=True, after=2)
    para(tf, l2, 10, MUTE, after=0)

half = (SW - 2 * MX - 0.4) / 2
card(s, MX, 3.72, half, 2.35, BG2, TEAL, 0.08)
card_heading(s, MX, 3.72, half, "钉连接力学 · 组内基础", TEAL)
tf = tb(s, MX + 0.22, 4.28, half - 0.38, 1.65)
bullet_list_tf(tf, [
    "木钉–Glubam 拉拔 / 双剪试验（EN 1382）",
    "强度、刚度、能量 → Johansen / Eurocode 5",
    "为钉位决策与折减系数 κ(d) 提供输入",
], TEAL, 12.5, DIM, after=7, line=1.2)

x2 = MX + half + 0.4
card(s, x2, 3.72, half, 2.35, BG2, ACCENT, 0.08)
card_heading(s, x2, 3.72, half, "XYLab 具身智能系统 · 大论文", ACCENT)
tf = tb(s, x2 + 0.22, 4.28, half - 0.38, 1.65)
bullet_list_tf(tf, [
    "缺陷感知 → 钉位规划 → 规范决策 → 机械臂执行",
    "栅格膨胀 + KD-tree + 软代价图（浏览器端真实运算）",
    "分层 Agent：打钉 / 预钻 / 换位 / 跳过",
], ACCENT, 12.5, DIM, after=7, line=1.2)
note_slide(s)

# ══════════════════════════════════════════════════════════════
# Slide 5 · 框架
# ══════════════════════════════════════════════════════════════
s = new_slide()
kicker_title(s, "FRAMEWORK", "具身智能闭环：感知 — 认知 — 执行", part="PART 03", part_color=ACCENT)
layers = [
    ("01  感知  PERCEPTION", "工业相机 + YOLOv8-seg：7 类缺陷 · ROI · 多板叠合", TEAL),
    ("02  认知  COGNITION", "Eurocode 5 RAG + 缺陷矩阵 + 分层 Agent + 引用校验", ACCENT),
    ("03  执行  ACTION", "工业机械臂 Skill 原语 · 数字孪生 · 施工日志", GREEN),
]
y = 2.12
for i, (h, d, col) in enumerate(layers):
    card(s, MX, y, 7.35, 1.12, BG2, col, 0.08)
    rect(s, MX, y, 0.1, 1.12, col)
    tf = tb(s, MX + 0.32, y + 0.12, 6.8, 0.88)
    para(tf, h, 15.5, col, bold=True, first=True, after=4, font=FONT_L)
    para(tf, d, 12, DIM, after=0)
    if i < 2:
        dn = rect(s, 7.55, y + 0.42, 0.35, 0.28, None, MSO_SHAPE.DOWN_ARROW)
        solid(dn, col)
    y += 1.28

side = card(s, 8.15, 2.12, SW - MX - 8.15, 3.72, ACCENT_LIGHT, ACCENT, 0.08)
tf = tb(s, 8.35, 2.35, SW - MX - 8.55, 3.25)
para(tf, "土木 × 具身智能", 16, ACCENT, bold=True, first=True, after=10)
para(tf, "力学试验", 13, TEAL, bold=True, after=2)
para(tf, "→ 规范硬约束 → 可解释决策 → 真机执行", 12, DIM, after=12, line=1.25)
para(tf, "每一次打钉", 13, PRIMARY, bold=True, after=2)
para(tf, "可追溯 · 可解释 · 可复核", 12.5, DIM, after=0, line=1.3)
note_slide(s)

# ══════════════════════════════════════════════════════════════
# Slide 6 · 科学问题
# ══════════════════════════════════════════════════════════════
s = new_slide()
kicker_title(s, "QUESTIONS", "待回答的关键科学问题", part="PART 04", part_color=PURPLE)
qs = [
    ("Q1", "力学参数如何进入可执行钉位决策？", "拉拔/剪切 → EC5 间距 · 折减 · 预钻触发", TEAL),
    ("Q2", "多板叠合如何融合各板缺陷？", "T 型重合区约束 + 全局最近合规钉位", ACCENT),
    ("Q3", "高变异天然材料下如何保持可解释？", "硬规则 → 矩阵 → LLM，引用校验", PURPLE),
    ("Q4", "从原型到真机闭环的关键瓶颈？", "手眼标定 · 力控/预钻 · 单板→墙段验证", AMBER),
]
ch = 1.15
for i, (q, title, sub, col) in enumerate(qs):
    yy = 2.1 + i * (ch + 0.16)
    card(s, MX, yy, SW - 2 * MX, ch, BG2, col, 0.06)
    circ = rect(s, MX + 0.2, yy + 0.22, 0.58, 0.58, col, MSO_SHAPE.OVAL, col, 2)
    tf = tb(s, MX + 0.2, yy + 0.3, 0.58, 0.44, MSO_ANCHOR.MIDDLE)
    para(tf, q, 13, WHITE, bold=True, align=PP_ALIGN.CENTER, first=True, font=FONT_L)
    tf = tb(s, MX + 0.95, yy + 0.18, SW - 2 * MX - 1.2, ch - 0.3)
    para(tf, title, 15, PRIMARY, bold=True, first=True, after=4)
    para(tf, sub, 11.5, DIM, after=0)
note_slide(s)

# ══════════════════════════════════════════════════════════════
# Slide 7 · 感知规划
# ══════════════════════════════════════════════════════════════
s = new_slide()
kicker_title(s, "NEXT 01 · PERCEPTION", "具身感知：真机视觉 + 几何优化", part="PART 05", part_color=TEAL)
items = [
    "YOLOv8-seg：mock → 真实权重 + 现场采集微调",
    "手眼标定：板面像素坐标 ↔ 机械臂工作空间",
    "多板叠合：T 型节点重合区标定",
    "ROI + 形态学膨胀 r=10mm + KD-tree 最近可行点",
    "软代价图多目标寻优，输出可解释钉位方案",
]
card(s, MX, 2.1, SW - 2 * MX - 3.4, 4.45, BG2, TEAL, 0.08)
card_heading(s, MX, 2.1, SW - 2 * MX - 3.4, "工作计划", TEAL)
tf = tb(s, MX + 0.28, 2.68, SW - 2 * MX - 3.9, 3.65)
bullet_list_tf(tf, items, TEAL, 13.5, DIM, after=9, line=1.22)
card(s, SW - MX - 3.15, 2.1, 2.85, 4.45, TEAL_LIGHT, TEAL, 0.08)
tf = tb(s, SW - MX - 2.85, 2.35, 2.25, 4.0)
para(tf, "预期产出", 15, TEAL, bold=True, first=True, after=12)
bullet_list_tf(tf, ["缺陷检出评估", "钉位规划 demo", "ROI 可视化"], TEAL, 12, DIM, after=9, line=1.2)
rect(s, SW - MX - 2.85, 5.85, 2.0, 0.38, TEAL, line_rgb=TEAL, radius=0.06)
tf2 = tb(s, SW - MX - 2.85, 5.88, 2.0, 0.32, MSO_ANCHOR.MIDDLE)
para(tf2, "2026 Q3", 12, WHITE, bold=True, align=PP_ALIGN.CENTER, first=True, font=FONT_L)
note_slide(s)

# ══════════════════════════════════════════════════════════════
# Slide 8 · 规范决策
# ══════════════════════════════════════════════════════════════
s = new_slide()
kicker_title(s, "NEXT 02 · COGNITION", "土木规范约束下的可解释打钉决策", part="PART 06", part_color=ACCENT)
items = [
    "Eurocode 5 / EN 1382 规范 PDF → RAG ingest",
    "缺陷 × 基材 × 纹理 → 决策矩阵 + κ(d) 折减",
    "分层 Agent：硬规则 → 矩阵 → LLM 复核",
    "四类动作：打钉 / 预钻 / 换位 / 跳过",
    "逐钉 JSON 日志 + 规范引用链 + 人工复核",
]
card(s, MX, 2.1, SW - 2 * MX - 3.4, 4.45, BG2, ACCENT, 0.08)
card_heading(s, MX, 2.1, SW - 2 * MX - 3.4, "工作计划", ACCENT)
tf = tb(s, MX + 0.28, 2.68, SW - 2 * MX - 3.9, 3.65)
bullet_list_tf(tf, items, ACCENT, 13.5, DIM, after=9, line=1.22)
card(s, SW - MX - 3.15, 2.1, 2.85, 4.45, ACCENT_LIGHT, ACCENT, 0.08)
tf = tb(s, SW - MX - 2.85, 2.35, 2.25, 4.0)
para(tf, "预期产出", 15, ACCENT, bold=True, first=True, after=12)
bullet_list_tf(tf, ["可解释决策日志", "规范引用校验", "力学参数接入规则库"], ACCENT, 12, DIM, after=9, line=1.2)
rect(s, SW - MX - 2.85, 5.85, 2.0, 0.38, ACCENT, line_rgb=ACCENT, radius=0.06)
tf2 = tb(s, SW - MX - 2.85, 5.88, 2.0, 0.32, MSO_ANCHOR.MIDDLE)
para(tf2, "2026 Q4", 12, WHITE, bold=True, align=PP_ALIGN.CENTER, first=True, font=FONT_L)
note_slide(s)

# ══════════════════════════════════════════════════════════════
# Slide 9 · 机械臂
# ══════════════════════════════════════════════════════════════
s = new_slide()
kicker_title(s, "NEXT 03 · ACTION", "具身执行：孪生 → 单板 → 墙段闭环", part="PART 07", part_color=GREEN)
steps = [
    ("Skill 原语", "SCAN · MOVE · PREDRILL · NAIL · SKIP", TEAL),
    ("状态机", "HOME → SCAN → PLAN → EXEC → LOG", ACCENT),
    ("验证路径", "孪生仿真 → 单板试钉 → 简单墙段", GREEN),
    ("平台", "工业机械臂（KUKA KR210，可扩展）", MUTE),
]
sw = (SW - 2 * MX - 0.45) / 4
for i, (h, d, c) in enumerate(steps):
    x = MX + i * (sw + 0.15)
    card(s, x, 2.12, sw, 2.05, BG2, c, 0.08)
    card_heading(s, x, 2.12, sw, h, c)
    tf = tb(s, x + 0.14, 2.65, sw - 0.26, 1.4)
    para(tf, d, 11, DIM, after=0, line=1.2)
    if i < 3:
        chv = rect(s, x + sw + 0.02, 3.05, 0.1, 0.32, None, MSO_SHAPE.CHEVRON)
        solid(chv, c)

card(s, MX, 4.55, SW - 2 * MX, 1.5, ACCENT_LIGHT, PRIMARY, 0.08)
tf = tb(s, MX + 0.3, 4.72, SW - 2 * MX - 0.55, 1.2)
para(tf, "验证与论文支撑", 15, PRIMARY, bold=True, first=True, after=6)
para(tf, "施工日志 JSON/CSV 回溯 · 力学试验与真机打钉效果对照 · 形成大论文闭环证据", 12.5, DIM, after=0, line=1.22)
note_slide(s)

# ══════════════════════════════════════════════════════════════
# Slide 10 · 时间线
# ══════════════════════════════════════════════════════════════
s = new_slide()
kicker_title(s, "TIMELINE", "工作安排  2026 Q3 — 2027 H1", part="PART 08", part_color=PURPLE)
milestones = [
    ("2026 Q3", "小论文定稿", "YOLO 真机 · 手眼标定", TEAL),
    ("2026 Q4", "规范决策验证", "重合区 · RAG + Agent", ACCENT),
    ("2027 H1", "机械臂闭环", "墙段试钉 · 大论文撰写", GREEN),
    ("2027 H2", "论文答辩", "性能对照 · 数据归档", PURPLE),
]
n = len(milestones)
seg = (SW - 2 * MX) / n
ly = 3.55
rect(s, MX, ly, SW - 2 * MX, 0.022, PRIMARY)
for i, (yr, h, d, col) in enumerate(milestones):
    cx = MX + seg * i + seg / 2
    solid(rect(s, cx - 0.14, ly - 0.13, 0.28, 0.28, None, MSO_SHAPE.OVAL, col, 2.5), col)
    up = i % 2 == 0
    yt = ly - 1.42 if up else ly + 0.35
    card(s, cx - seg / 2 + 0.08, yt, seg - 0.16, 1.22, BG2, col, 0.06)
    tf = tb(s, cx - seg / 2 + 0.2, yt + 0.12, seg - 0.4, 1.0)
    para(tf, yr, 17, col, bold=True, font=FONT_L, align=PP_ALIGN.CENTER, first=True, after=4)
    para(tf, h, 13, PRIMARY, bold=True, align=PP_ALIGN.CENTER, after=4)
    para(tf, d, 10.5, DIM, align=PP_ALIGN.CENTER, after=0, line=1.12)
note_slide(s)

# ══════════════════════════════════════════════════════════════
# Slide 11 · 讨论
# ══════════════════════════════════════════════════════════════
s = new_slide()
kicker_title(s, "DISCUSSION", "希望请教的问题", part="CLOSING", part_color=AMBER)
cols = [
    ("开放问题", [
        "重竹钉 / 木钉是否在决策矩阵中区分？",
        "预钻阈值如何与拉拔试验数据挂钩？",
        "真机打钉力控指标如何设定？",
    ], AMBER),
    ("需协调事项", [
        "试验室设备与机械臂平台排期",
        "Eurocode 5 条款解读与工程惯例",
        "缺陷标注数据与模型训练样本",
    ], TEAL),
]
cw = (SW - 2 * MX - 0.5) / 2
for i, (head, bullets, col) in enumerate(cols):
    x = MX + i * (cw + 0.5)
    card(s, x, 2.1, cw, 3.15, BG2, col, 0.08)
    card_heading(s, x, 2.1, cw, head, col)
    bullet_list(s, x + 0.22, 2.68, cw - 0.4, bullets, col, 13, 0.5)

t = tb(s, MX, 5.45, SW - 2 * MX, 1.0, MSO_ANCHOR.MIDDLE)
para(t, "感谢聆听 · 欢迎批评指正", 28, PRIMARY, bold=True, align=PP_ALIGN.CENTER, first=True, after=8)
para(t, "王尉廷 · 肖岩教授课题组 · 浙江大学 ZJUI", 13, MUTE, align=PP_ALIGN.CENTER, after=0)
note_slide(s)

# ── 输出 ──
os.makedirs(os.path.dirname(OUT), exist_ok=True)
export_script_md()
prs.save(OUT)
print("SAVED:", OUT)
print("SCRIPT:", SCRIPT_MD)
print("slides:", len(prs.slides))
