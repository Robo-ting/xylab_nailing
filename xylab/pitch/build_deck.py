# -*- coding: utf-8 -*-
"""
XYLab 具身智能建造 · 投资路演 Pitch Deck 生成器
深色科技风，紧贴具身智能 / 多模态大模型 / VLA / 世界模型前沿叙事。
"""
from __future__ import annotations

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn, nsdecls
from pptx.oxml import parse_xml
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
THESIS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # 机械臂大论文/
OUT = os.path.join(THESIS_ROOT, "docs", "XYLab-投资路演-PitchDeck.pptx")

# ----------------------------- 主题 -----------------------------
BG = "0B1120"
BG2 = "0E1626"
PANEL = "16223C"
PANEL2 = "1B2947"
BORDER = "2A3A63"
CYAN = "38BDF8"
CYAN2 = "22D3EE"
BLUE = "2563EB"
GREEN = "22C55E"
AMBER = "F59E0B"
RED = "EF4444"
PURPLE = "8B5CF6"
PINK = "EC4899"
WHITE = "F1F6FF"
DIM = "AEBFDB"
MUTE = "6B7EA3"

FONT = "微软雅黑"
FONT_L = "Arial"

SW = 13.333
SH = 7.5
MX = 0.92


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


def set_gradient(shape, c1, c2, angle_deg=45):
    ang = int(angle_deg * 60000)
    xml = (
        '<a:gradFill %s rotWithShape="1">'
        "<a:gsLst>"
        '<a:gs pos="0"><a:srgbClr val="%s"/></a:gs>'
        '<a:gs pos="100000"><a:srgbClr val="%s"/></a:gs>'
        "</a:gsLst>"
        '<a:lin ang="%d" scaled="1"/>'
        "</a:gradFill>" % (nsdecls("a"), c1, c2, ang)
    )
    spPr = shape.fill._xPr
    for tag in ("a:noFill", "a:solidFill", "a:gradFill", "a:blipFill", "a:pattFill", "a:grpFill"):
        e = spPr.find(qn(tag))
        if e is not None:
            spPr.remove(e)
    ln = spPr.find(qn("a:ln"))
    newfill = parse_xml(xml)
    if ln is not None:
        ln.addprevious(newfill)
    else:
        spPr.append(newfill)
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


def grad_rect(slide, x, y, w, h, c1, c2, angle=45, shape=MSO_SHAPE.RECTANGLE, radius=None):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.line.fill.background()
    set_gradient(sp, c1, c2, angle)
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
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    return tf


def para(tf, text, size, color, bold=False, font=FONT, align=PP_ALIGN.LEFT,
         after=6, before=0, line=None, first=False):
    if first and not tf.paragraphs[0].runs:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
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
    """runs: list of (text, size, color, bold[, font])"""
    if first and not tf.paragraphs[0].runs:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
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


# ----------------------------- 页基座 -----------------------------
prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
BLANK = prs.slide_layouts[6]

_page = [0]


def new_slide(bg=BG, footer=True, deco=True):
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, SW, SH, bg)
    if deco:
        # 右上角光晕装饰
        e = rect(s, SW - 4.2, -2.2, 4.6, 4.6, None, MSO_SHAPE.OVAL)
        set_gradient(e, "12325A", BG, 45)
    if footer:
        _page[0] += 1
        line = rect(s, MX, SH - 0.52, SW - 2 * MX, 0.012, BORDER)
        f = tb(s, MX, SH - 0.46, 6, 0.3)
        para(f, "XYLab · 具身智能建造  Embodied AI for Construction", 8.5, MUTE, first=True)
        pg = tb(s, SW - MX - 2, SH - 0.46, 2, 0.3)
        para(pg, f"{_page[0]:02d}", 8.5, MUTE, align=PP_ALIGN.RIGHT, first=True)
    return s


def kicker_title(s, kicker, title, title_color=WHITE, tsize=30):
    rect(s, MX, 0.62, 0.34, 0.12, CYAN)
    k = tb(s, MX + 0.46, 0.5, 10, 0.35)
    para(k, kicker, 12, CYAN, bold=True, first=True)
    t = tb(s, MX, 0.92, SW - 2 * MX, 0.9)
    para(t, title, tsize, title_color, bold=True, first=True, line=1.0)


def badge(s, x, y, text, color, w=None):
    w = w or (0.22 + 0.135 * len(text))
    rect(s, x, y, w, 0.32, PANEL2, MSO_SHAPE.ROUNDED_RECTANGLE, color, 1, radius=0.5)
    tf = tb(s, x, y + 0.02, w, 0.28, MSO_ANCHOR.MIDDLE)
    para(tf, text, 9.5, color, bold=True, align=PP_ALIGN.CENTER, first=True)
    return w


def image_framed(s, path, x, y, w, border=CYAN):
    with Image.open(path) as im:
        iw, ih = im.size
    h = w * ih / iw
    rect(s, x - 0.06, y - 0.06, w + 0.12, h + 0.12, PANEL, line_rgb=border, line_w=1.25, radius=0.02)
    s.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    return h


def stat_card(s, x, y, w, h, num, label, color=CYAN, sub=None):
    card = rect(s, x, y, w, h, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE, BORDER, 1, radius=0.08)
    rect(s, x, y + 0.14, 0.06, h - 0.28, color)
    tf = tb(s, x + 0.24, y + 0.16, w - 0.34, h - 0.3, MSO_ANCHOR.MIDDLE)
    runs_para(tf, [(num, 27, color, True, FONT_L)], after=2, first=True)
    para(tf, label, 11, DIM, after=0)
    if sub:
        para(tf, sub, 8.5, MUTE, after=0)


def card(s, x, y, w, h, rgb=PANEL, line=BORDER, radius=0.06):
    return rect(s, x, y, w, h, rgb, MSO_SHAPE.ROUNDED_RECTANGLE, line, 1, radius=radius)


def arrow(s, x, y, w, h=0.5, color=CYAN):
    a = rect(s, x, y, w, h, None, MSO_SHAPE.CHEVRON)
    solid(a, color)
    return a


# ============================================================
# Slide 1 — 封面
# ============================================================
s = new_slide(footer=False)
big = rect(s, 0, 0, SW, SH, None)
set_gradient(big, "0B1120", "0A1730", 60)
# 装饰光晕
e1 = rect(s, -2, 3.5, 7, 7, None, MSO_SHAPE.OVAL)
set_gradient(e1, "10396B", BG, 30)
e2 = rect(s, SW - 5, -3, 8, 8, None, MSO_SHAPE.OVAL)
set_gradient(e2, "0E2E57", BG, 45)
# 顶部标签
rect(s, MX, 1.5, 0.34, 0.12, CYAN)
kk = tb(s, MX + 0.46, 1.38, 10, 0.4)
para(kk, "EMBODIED AI · PHYSICAL AI · INTELLIGENT CONSTRUCTION", 12, CYAN, bold=True, first=True)
# 主标题
t = tb(s, MX, 2.1, SW - 2 * MX, 2.2)
runs_para(t, [("XYLab", 66, WHITE, True, FONT_L)], after=2, first=True)
para(t, "具身智能建造大脑", 46, WHITE, bold=True, after=0)
# 副标题
sub = tb(s, MX, 4.5, SW - 2 * MX, 1.2)
runs_para(sub, [("让工业机械臂像老师傅一样 ", 17, DIM, False), ("感知 · 推理 · 决策 · 建造", 17, CYAN2, True)],
          after=6, first=True)
para(sub, "以多模态大模型 + 工业机械臂，赋能预制竹木结构的规模化工业生产", 14, MUTE, after=0)
# 底部信息条
bar = card(s, MX, 6.2, SW - 2 * MX, 0.7, PANEL, BORDER, 0.12)
info = tb(s, MX + 0.3, 6.2, SW - 2 * MX - 0.6, 0.7, MSO_ANCHOR.MIDDLE)
runs_para(info, [("融资轮次  ", 11, MUTE, False), ("天使轮 / Angel  ", 12, WHITE, True),
                 ("      赛道  ", 11, MUTE, False), ("建筑机器人 · 具身智能  ", 12, WHITE, True),
                 ("      依托  ", 11, MUTE, False), ("浙江大学 具身智能与智能建造", 12, WHITE, True)],
          first=True)

# ============================================================
# Slide 2 — 一句话 / What we do
# ============================================================
s = new_slide()
kicker_title(s, "ONE-LINER / 我们是谁", "建筑行业的“具身智能大脑”")
q = tb(s, MX, 2.4, SW - 2 * MX, 2.2, MSO_ANCHOR.MIDDLE)
runs_para(q, [("我们让机器人具备 ", 26, WHITE, False), ("感知—推理—决策—执行", 26, CYAN2, True),
              (" 的闭环能力，", 26, WHITE, False)], after=10, first=True, line=1.15)
runs_para(q, [("自主完成预制结构的", 26, WHITE, False), ("缺陷检测", 26, CYAN, True),
              ("与", 26, WHITE, False), ("毫米级精准钉合装配", 26, CYAN, True), ("。", 26, WHITE, False)],
          line=1.15)
row_y = 5.4
items = [("感知 Perception", "视觉大模型识别天然材料缺陷", CYAN),
         ("认知 Cognition", "大模型 Agent 援引规范做决策", CYAN2),
         ("执行 Action", "工业机械臂毫米级自主钉合", GREEN)]
cw = (SW - 2 * MX - 0.6) / 3
for i, (h, d, col) in enumerate(items):
    x = MX + i * (cw + 0.3)
    card(s, x, row_y, cw, 1.05)
    rect(s, x, row_y + 0.12, 0.06, 0.81, col)
    tf = tb(s, x + 0.24, row_y + 0.16, cw - 0.34, 0.8, MSO_ANCHOR.MIDDLE)
    para(tf, h, 14, col, bold=True, after=3, first=True)
    para(tf, d, 11, DIM, after=0, line=1.05)

# ============================================================
# Slide 3 — 问题
# ============================================================
s = new_slide()
kicker_title(s, "THE PROBLEM / 痛点", "全球最大、却最难自动化的行业")
probs = [
    ("用工荒与老龄化", "技术工人断层，人工成本逐年攀升，招工难成为行业顽疾", AMBER),
    ("预制装配质量不稳", "钉合/装配高度依赖老师傅经验，返工率高、一致性差", RED),
    ("天然材料高变异", "木/竹的木节、裂缝、腐朽随机分布，固定程序机器人无法应对", PURPLE),
    ("数字化程度极低", "建筑业数字化投入长期垫底，缺乏端到端智能建造闭环", CYAN),
]
cw = (SW - 2 * MX - 0.6) / 2
ch = 1.7
for i, (h, d, col) in enumerate(probs):
    x = MX + (i % 2) * (cw + 0.6)
    y = 2.2 + (i // 2) * (ch + 0.35)
    card(s, x, y, cw, ch)
    dot = rect(s, x + 0.28, y + 0.32, 0.5, 0.5, None, MSO_SHAPE.OVAL)
    set_gradient(dot, col, PANEL2, 45)
    nt = tb(s, x + 0.28, y + 0.34, 0.5, 0.5, MSO_ANCHOR.MIDDLE)
    para(nt, f"0{i+1}", 15, col, bold=True, align=PP_ALIGN.CENTER, first=True, font=FONT_L)
    tf = tb(s, x + 0.98, y + 0.3, cw - 1.2, ch - 0.5, MSO_ANCHOR.TOP)
    para(tf, h, 17, WHITE, bold=True, after=6, first=True)
    para(tf, d, 12, DIM, after=0, line=1.2)

# ============================================================
# Slide 4 — 为什么是现在
# ============================================================
s = new_slide()
kicker_title(s, "WHY NOW / 时机", "三条技术曲线同时到达拐点")
waves = [
    ("多模态大模型成熟", "GPT-4o / Gemini 等具备强视觉理解与推理，AI 首次能“看懂”并“讲清”物理场景", CYAN),
    ("具身智能 / VLA 爆发", "Vision-Language-Action 与世界模型，让 AI 从语言走向物理动作", CYAN2),
    ("机器人硬件成本骤降", "国产机械臂 + 力控 + 传感器价格下探，边际部署成本快速摊薄", GREEN),
]
y = 2.3
for i, (h, d, col) in enumerate(waves):
    card(s, MX, y, SW - 2 * MX, 1.15)
    rect(s, MX, y + 0.14, 0.06, 0.87, col)
    nt = tb(s, MX + 0.3, y, 1.4, 1.15, MSO_ANCHOR.MIDDLE)
    para(nt, f"0{i+1}", 30, col, bold=True, first=True, font=FONT_L)
    tf = tb(s, MX + 1.6, y, SW - 2 * MX - 2, 1.15, MSO_ANCHOR.MIDDLE)
    para(tf, h, 17, WHITE, bold=True, after=4, first=True)
    para(tf, d, 12, DIM, after=0, line=1.15)
    y += 1.4
bt = tb(s, MX, 6.55, SW - 2 * MX, 0.4)
runs_para(bt, [("物理 AI（Physical AI）已成为 NVIDIA、Tesla、Figure 的主战场 — ", 12.5, MUTE, False),
               ("建造，是尚未被占领的万亿蓝海。", 12.5, CYAN2, True)], first=True)

# ============================================================
# Slide 5 — 市场（自绘增长柱状）
# ============================================================
s = new_slide()
kicker_title(s, "MARKET / 市场空间", "万亿级建筑业 × 高速增长的建筑机器人")
# TAM/SAM/SOM 同心
rings = [("TAM", "全球建筑业", "$13 万亿+", CYAN, 3.0),
         ("SAM", "装配式 & 预制结构自动化", "$1,200 亿", CYAN2, 2.1),
         ("SOM", "预制木/竹结构智能钉合", "¥ 200 亿", GREEN, 1.2)]
cx, cy = 3.6, 4.4
for label, desc, val, col, d in rings:
    o = rect(s, cx - d / 2, cy - d / 2, d, d, None, MSO_SHAPE.OVAL, col, 1.5)
for i, (label, desc, val, col, d) in enumerate(rings):
    tf = tb(s, cx - 1.4, cy - 2.1 + i * 0.62, 2.8, 0.55, MSO_ANCHOR.MIDDLE)
    runs_para(tf, [(f"{label}  ", 12, col, True, FONT_L), (val, 13, WHITE, True)], align=PP_ALIGN.CENTER, first=True, after=0)
    para(tf, desc, 8.5, DIM, align=PP_ALIGN.CENTER, after=0)
# 右上：政策共振说明
ct = tb(s, 7.2, 2.15, 5.15, 1.0)
runs_para(ct, [("政策共振", 13, WHITE, True)], first=True, after=4)
para(ct, "双碳目标 · 装配式建筑 · 新型工业化", 11.5, CYAN2, after=3)
para(ct, "低碳竹木结构被写入绿色建筑与乡村振兴议程", 10.5, MUTE, after=0, line=1.1)
# 增长柱状（自绘，位于右下，避免与文字重叠）
bx, by, bw, bh = 7.3, 6.15, 4.9, 2.15
years = [("2024", 0.30, ""), ("2026", 0.48, ""), ("2028", 0.70, ""), ("2030", 1.0, "$500亿")]
barw = 0.66
gap = (bw - barw * len(years)) / (len(years) - 1)
rect(s, bx, by, bw, 0.012, BORDER)
for i, (yr, frac, val) in enumerate(years):
    x = bx + i * (barw + gap)
    hh = bh * frac
    b = rect(s, x, by - hh, barw, hh, None, MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
    set_gradient(b, CYAN, BLUE, 90)
    yl = tb(s, x - 0.15, by + 0.06, barw + 0.3, 0.28)
    para(yl, yr, 10, DIM, align=PP_ALIGN.CENTER, first=True)
    if val:
        vl = tb(s, x - 0.4, by - hh - 0.32, barw + 0.8, 0.3)
        para(vl, val, 11, CYAN2, bold=True, align=PP_ALIGN.CENTER, first=True, font=FONT_L)
# 图注（单行，位于柱状与政策文字之间）
lt = tb(s, 7.3, 3.5, 4.9, 0.35)
runs_para(lt, [("建筑机器人市场  ", 11, MUTE, False), ("CAGR ~25%", 13, CYAN2, True)],
          align=PP_ALIGN.LEFT, first=True)

# ============================================================
# Slide 6 — 解决方案（架构图）
# ============================================================
s = new_slide()
kicker_title(s, "SOLUTION / 解决方案", "一套具身智能建造全栈系统")
layers = [
    ("感知层  PERCEPTION", "工业相机 + 视觉大模型：缺陷分割 · 铁钉扫描 · 木纹/基材识别", CYAN),
    ("认知决策层  COGNITION", "大模型 Agent + RAG 规范库 + 缺陷决策矩阵 + 防幻觉校验", CYAN2),
    ("执行层  ACTION", "工业机械臂技能原语 · 力控 · 数字孪生（当前 KUKA KR210，兼容各类工业臂）", GREEN),
]
y = 2.35
for i, (h, d, col) in enumerate(layers):
    c = card(s, MX, y, SW - 2 * MX, 1.15)
    rect(s, MX, y, 0.09, 1.15, col)
    tf = tb(s, MX + 0.4, y, 5.2, 1.15, MSO_ANCHOR.MIDDLE)
    para(tf, h, 17, col, bold=True, first=True, after=2)
    para(tf, d, 11.5, DIM, after=0, line=1.1)
    if i < 2:
        dn = rect(s, 6.6, y + 1.12, 0.5, 0.32, None, MSO_SHAPE.DOWN_ARROW)
        solid(dn, col)
    y += 1.42
side = tb(s, 8.4, 2.5, SW - MX - 8.4, 3.4, MSO_ANCHOR.TOP)
runs_para(side, [("闭环飞轮", 14, WHITE, True)], first=True, after=6)
para(side, "每一次钉合 = 一次数据采集", 11.5, CYAN2, after=2)
para(side, "现场数据回流 → 缺陷模型/决策策略持续进化 → 越用越聪明", 11, DIM, after=0, line=1.2)

# ============================================================
# Slide 7 — 产品（总控台截图）
# ============================================================
s = new_slide()
kicker_title(s, "PRODUCT / 产品", "从图纸到成品的端到端控制系统")
h = image_framed(s, os.path.join(ASSETS, "shot_dashboard.png"), MX, 1.95, 8.1, CYAN)
side_x = MX + 8.5
tf = tb(s, side_x, 2.05, SW - MX - side_x, 4.6)
para(tf, "一体化控制台", 15, WHITE, bold=True, first=True, after=6)
for t in ["驱动工业机械臂产线（现 KUKA KR210）",
          "感知 → 规划 → 决策 → 执行 → 日志",
          "毫米级钉位可视化与实时重算",
          "规范可追溯、决策可解释",
          "预留大模型 / ROS 后端接口"]:
    runs_para(tf, [("▸  ", 12, CYAN, True), (t, 12, DIM, False)], after=7, line=1.1)
para(tf, "已完成可运行原型", 11, GREEN, bold=True, before=6)

# ============================================================
# Slide 8 — 核心技术①感知（规划截图）
# ============================================================
s = new_slide()
kicker_title(s, "TECH ① / 感知与规划", "毫米级、可解释的钉位智能优化")
h = image_framed(s, os.path.join(ASSETS, "shot_planning.png"), MX, 1.95, 8.1, CYAN2)
side_x = MX + 8.5
tf = tb(s, side_x, 2.05, SW - MX - side_x, 4.6)
para(tf, "算法内核（真实运算）", 15, WHITE, bold=True, first=True, after=6)
for t in ["YOLOv8-seg 七类缺陷分割",
          "栅格代价图 + 形态学膨胀",
          "KD-tree 最近可行点求解",
          "软代价场多目标寻优",
          "多板叠合 · 重合区装配约束"]:
    runs_para(tf, [("▸  ", 12, CYAN2, True), (t, 12, DIM, False)], after=7, line=1.1)
para(tf, "Eurocode 5 规范数字化落地", 11, CYAN, bold=True, before=6)

# ============================================================
# Slide 9 — 核心技术②决策大脑（agent截图）
# ============================================================
s = new_slide()
kicker_title(s, "TECH ② / 认知决策大脑", "让 AI 像结构工程师一样思考")
h = image_framed(s, os.path.join(ASSETS, "shot_agent.png"), MX, 1.95, 8.1, PURPLE)
side_x = MX + 8.5
tf = tb(s, side_x, 2.05, SW - MX - side_x, 4.6)
para(tf, "大模型决策智能体", 15, WHITE, bold=True, first=True, after=6)
for t in ["分层决策：硬规则→矩阵→LLM",
          "RAG 检索建造规范条款",
          "引用校验杜绝“AI 幻觉”",
          "四类动作：打钉/预钻/换位/跳过",
          "低置信度自动转人工复核"]:
    runs_para(tf, [("▸  ", 12, PURPLE, True), (t, 12, DIM, False)], after=7, line=1.1)
para(tf, "迈向 VLA / 建造世界模型", 11, CYAN2, bold=True, before=6)

# ============================================================
# Slide 10 — 技术护城河
# ============================================================
s = new_slide()
kicker_title(s, "MOAT / 护城河", "全栈具身智能 + 数据飞轮")
moats = [
    ("数据飞轮", "施工即采集，独家场景数据反哺模型，形成越用越强的正循环", CYAN),
    ("规范知识库", "建造规范 + 力学实验 + 老师傅 Know-how 沉淀为可检索知识资产", CYAN2),
    ("全栈闭环", "感知·规划·决策·控制·数字孪生自研一体，非拼装集成", GREEN),
    ("可信与可解释", "引用校验 + 力学参数标定，满足工程安全与合规刚需", PURPLE),
]
cw = (SW - 2 * MX - 0.6) / 2
ch = 1.7
for i, (h2, d, col) in enumerate(moats):
    x = MX + (i % 2) * (cw + 0.6)
    y = 2.2 + (i // 2) * (ch + 0.35)
    card(s, x, y, cw, ch)
    rect(s, x, y + 0.14, 0.06, ch - 0.28, col)
    tf = tb(s, x + 0.3, y + 0.28, cw - 0.55, ch - 0.5)
    para(tf, h2, 16, col, bold=True, first=True, after=6)
    para(tf, d, 12, DIM, after=0, line=1.2)

# ============================================================
# Slide 11 — 竞争格局（2x2）
# ============================================================
s = new_slide()
kicker_title(s, "LANDSCAPE / 竞争格局", "我们站在“建造专用 × 具身智能”的右上角")
qx, qy, qw, qh = MX + 1.0, 2.2, 8.0, 4.2
# 轴
rect(s, qx, qy, qw, qh, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE, BORDER, 1, radius=0.03)
rect(s, qx + qw / 2 - 0.005, qy + 0.2, 0.01, qh - 0.4, BORDER)
rect(s, qx + 0.2, qy + qh / 2 - 0.005, qw - 0.4, 0.01, BORDER)
# 轴标签
axl = tb(s, qx, qy - 0.4, qw, 0.3)
para(axl, "具身智能 / 自主决策 ▲", 10, CYAN, bold=True, align=PP_ALIGN.CENTER, first=True)
axb = tb(s, qx, qy + qh + 0.08, qw, 0.3)
para(axb, "固定程序 / 示教", 10, MUTE, align=PP_ALIGN.CENTER, first=True)
lft = tb(s, qx - 1.0, qy + qh / 2 - 0.15, 1.0, 0.3)
para(lft, "通用", 9.5, MUTE, align=PP_ALIGN.CENTER, first=True)
rgt = tb(s, qx + qw + 0.05, qy + qh / 2 - 0.15, 1.1, 0.3)
para(rgt, "建造专用", 9.5, MUTE, align=PP_ALIGN.CENTER, first=True)
# 竞品点
def dot(px, py, label, col, big=False):
    d = 0.9 if big else 0.34
    o = rect(s, px - d / 2, py - d / 2, d, d, None, MSO_SHAPE.OVAL)
    if big:
        set_gradient(o, CYAN, BLUE, 45)
    else:
        solid(o, col)
    lt = tb(s, px - 1.1, py + d / 2 + 0.02, 2.2, 0.3)
    para(lt, label, 9.5, WHITE if big else DIM, bold=big, align=PP_ALIGN.CENTER, first=True)
dot(qx + qw * 0.28, qy + qh * 0.72, "传统集成商", MUTE)
dot(qx + qw * 0.30, qy + qh * 0.30, "通用机械臂", AMBER)
dot(qx + qw * 0.70, qy + qh * 0.66, "国外建筑机器人", PURPLE)
dot(qx + qw * 0.76, qy + qh * 0.24, "XYLab", CYAN, big=True)
# 右侧说明
tf = tb(s, qx + qw + 1.3, 2.4, SW - MX - (qx + qw + 1.3), 3.6)
para(tf, "差异化", 14, WHITE, bold=True, first=True, after=6)
for t in ["通用机器人不懂建造规范", "传统集成靠示教、无泛化", "国外方案成本高、不适配国情", "我们：领域大模型 + 全栈自研"]:
    runs_para(tf, [("▸  ", 11, CYAN, True), (t, 11, DIM, False)], after=8, line=1.1)

# ============================================================
# Slide 12 — 商业模式
# ============================================================
s = new_slide()
kicker_title(s, "BUSINESS MODEL / 商业模式", "从“卖设备”到“卖产能”")
models = [
    ("产线工作站", "工业机械臂\n软硬件一体交付", CYAN, "硬件收入"),
    ("建造大脑 SaaS", "决策大脑订阅\n按席位/项目计费", CYAN2, "经常性收入"),
    ("知识库授权", "规范/工艺知识库\n数据与模型授权", PURPLE, "高毛利授权"),
    ("RaaS 产能", "机器人即服务\n按钉合量/工程量分成", GREEN, "规模化想象"),
]
cw = (SW - 2 * MX - 3 * 0.35) / 4
for i, (h2, d, col, tagt) in enumerate(models):
    x = MX + i * (cw + 0.35)
    y = 2.4
    card(s, x, y, cw, 3.4)
    rect(s, x, y, cw, 0.1, col)
    tf = tb(s, x + 0.22, y + 0.4, cw - 0.4, 2.9)
    para(tf, f"0{i+1}", 22, col, bold=True, first=True, after=6, font=FONT_L)
    para(tf, h2, 15, WHITE, bold=True, after=8)
    for ln in d.split("\n"):
        para(tf, ln, 11, DIM, after=2, line=1.1)
    badge(s, x + 0.22, y + 2.9, tagt, col, w=cw - 0.44)
bt = tb(s, MX, 6.15, SW - 2 * MX, 0.5)
runs_para(bt, [("路径：", 12.5, WHITE, True), ("先以一体机切入标杆客户 → SaaS 沉淀数据 → RaaS 撬动规模化产能分成", 12.5, DIM, False)], first=True)

# ============================================================
# Slide 13 — 路线图
# ============================================================
s = new_slide()
kicker_title(s, "ROADMAP / 路线图", "从单点工艺到通用建造具身智能")
steps = [
    ("2026", "钉合原型验证", "预制木/竹结构智能钉合，控制系统 + 核心算法跑通", GREEN),
    ("2027", "产线级部署", "多工艺装配（钉/螺栓/胶合），落地试点产线", CYAN2),
    ("2028", "建造基础模型", "Construction Foundation Model，跨构件泛化", CYAN),
    ("2029+", "通用建造平台", "跨材料/跨工艺的具身智能建造操作系统", PURPLE),
]
n = len(steps)
seg = (SW - 2 * MX) / n
ly = 3.6
rect(s, MX, ly, SW - 2 * MX, 0.02, BORDER)
for i, (yr, h2, d, col) in enumerate(steps):
    cx = MX + seg * i + seg / 2
    o = rect(s, cx - 0.14, ly - 0.13, 0.28, 0.28, None, MSO_SHAPE.OVAL)
    solid(o, col)
    up = (i % 2 == 0)
    if up:
        yt = ly - 1.5
    else:
        yt = ly + 0.35
    yl = tb(s, cx - seg / 2 + 0.2, ly - 1.5 if up else ly + 0.35, seg - 0.4, 1.15)
    para(yl, yr, 18, col, bold=True, first=True, after=3, font=FONT_L, align=PP_ALIGN.CENTER)
    para(yl, h2, 13, WHITE, bold=True, after=3, align=PP_ALIGN.CENTER)
    para(yl, d, 10, DIM, after=0, line=1.05, align=PP_ALIGN.CENTER)

# ============================================================
# Slide 14 — 进展 Traction
# ============================================================
s = new_slide()
kicker_title(s, "TRACTION / 进展", "已经落地的，与正在发生的")
stat_card(s, MX, 2.2, 2.75, 1.4, "11", "功能模块", CYAN, "全流程可运行原型")
stat_card(s, MX + 2.95, 2.2, 2.75, 1.4, "7", "缺陷类别", CYAN2, "YOLOv8-seg 分割")
stat_card(s, MX + 5.9, 2.2, 2.75, 1.4, "6+", "数字化规范", GREEN, "Eurocode 5 等")
stat_card(s, MX + 8.85, 2.2, 2.6, 1.4, "1", "软件著作权", PURPLE, "申报中")
# 已完成 vs 进行中
lx = MX
card(s, lx, 3.95, (SW - 2 * MX - 0.5) / 2, 2.7)
tf = tb(s, lx + 0.3, 4.15, (SW - 2 * MX - 0.5) / 2 - 0.55, 2.4)
para(tf, "✓  已完成", 14, GREEN, bold=True, first=True, after=8)
for t in ["端到端控制系统原型", "感知/规划/决策核心算法", "多板叠合装配约束", "力学试验方案设计", "浙大科研与导师背书"]:
    para(tf, "· " + t, 11.5, DIM, after=5, line=1.1)
rx = MX + (SW - 2 * MX - 0.5) / 2 + 0.5
card(s, rx, 3.95, (SW - 2 * MX - 0.5) / 2, 2.7)
tf = tb(s, rx + 0.3, 4.15, (SW - 2 * MX - 0.5) / 2 - 0.55, 2.4)
para(tf, "◷  进行中 / 规划", 14, AMBER, bold=True, first=True, after=8)
for t in ["工业机械臂产线集成", "试点工程与标杆客户", "现场数据飞轮搭建", "大模型决策后端接入", "核心团队补强"]:
    para(tf, "· " + t, 11.5, DIM, after=5, line=1.1)

# ============================================================
# Slide 15 — 团队
# ============================================================
s = new_slide()
kicker_title(s, "TEAM / 团队", "土木工程 × 具身智能的交叉基因")
mem = [
    ("创始人 / CEO", "浙江大学 土木水利 硕士", "具身智能 + 智能建造；主导系统架构、算法与产品", CYAN),
    ("首席科学顾问", "肖岩 教授 · 浙江大学", "现代竹木结构与工程结构权威，提供科研与工程背书", CYAN2),
    ("待引入合伙人", "AI / 机器人 / 商业化", "诚邀大模型、运动控制与市场负责人共建", PURPLE),
]
cw = (SW - 2 * MX - 0.7) / 3
for i, (role, name, d, col) in enumerate(mem):
    x = MX + i * (cw + 0.35)
    y = 2.35
    card(s, x, y, cw, 3.4)
    av = rect(s, x + cw / 2 - 0.55, y + 0.35, 1.1, 1.1, None, MSO_SHAPE.OVAL)
    set_gradient(av, col, PANEL2, 45)
    tf = tb(s, x + 0.25, y + 1.6, cw - 0.5, 1.7)
    para(tf, role, 13, col, bold=True, first=True, after=4, align=PP_ALIGN.CENTER)
    para(tf, name, 12.5, WHITE, bold=True, after=6, align=PP_ALIGN.CENTER)
    para(tf, d, 10.5, DIM, after=0, line=1.15, align=PP_ALIGN.CENTER)

# ============================================================
# Slide 16 — 融资 The Ask
# ============================================================
s = new_slide()
kicker_title(s, "THE ASK / 融资", "天使轮，携手驶入物理 AI 蓝海")
# 左：金额
lc = card(s, MX, 2.3, 4.4, 4.1)
set_gradient(lc, "10396B", "0E1A30", 60)
tf = tb(s, MX + 0.45, 2.75, 3.6, 3.2)
para(tf, "拟融资", 13, CYAN2, bold=True, first=True, after=6)
runs_para(tf, [("¥ 1,000", 40, WHITE, True, FONT_L), (" 万", 20, WHITE, True)], after=6)
para(tf, "出让 10% 股权（可议）", 12, DIM, after=16)
para(tf, "预计支撑 18 个月跑道", 12, CYAN, bold=True, after=4)
para(tf, "至样机量产 + 首批试点落地", 11, MUTE, after=0, line=1.15)
# 右：资金用途
rx = MX + 4.8
uses = [("50%", "研发与集成", "工业机械臂产线集成、大模型决策后端、算法迭代", CYAN),
        ("30%", "试点与市场", "标杆工程落地、现场数据飞轮", CYAN2),
        ("20%", "团队建设", "AI / 机器人 / 商业化核心成员", GREEN)]
y = 2.3
rw = SW - MX - rx
for pct, h2, d, col in uses:
    card(s, rx, y, rw, 1.25)
    nt = tb(s, rx + 0.3, y, 1.5, 1.25, MSO_ANCHOR.MIDDLE)
    para(nt, pct, 26, col, bold=True, first=True, font=FONT_L)
    tf = tb(s, rx + 1.9, y, rw - 2.1, 1.25, MSO_ANCHOR.MIDDLE)
    para(tf, h2, 15, WHITE, bold=True, first=True, after=3)
    para(tf, d, 11, DIM, after=0, line=1.1)
    y += 1.42

# ============================================================
# Slide 17 — 结尾愿景
# ============================================================
s = new_slide(footer=False)
big = rect(s, 0, 0, SW, SH, None)
set_gradient(big, "0B1120", "0A1A34", 60)
e1 = rect(s, SW / 2 - 3.5, 0.6, 7, 7, None, MSO_SHAPE.OVAL)
set_gradient(e1, "103A6E", BG, 30)
t = tb(s, 1.2, 2.5, SW - 2.4, 2.6, MSO_ANCHOR.MIDDLE)
para(t, "用具身智能，重建每一栋建筑", 40, WHITE, bold=True, align=PP_ALIGN.CENTER, first=True, after=14)
runs_para(t, [("Building the physical world, ", 20, CYAN2, False, FONT_L),
              ("with embodied intelligence.", 20, CYAN, True, FONT_L)], align=PP_ALIGN.CENTER)
f = tb(s, 1.2, 5.6, SW - 2.4, 0.9, MSO_ANCHOR.MIDDLE)
runs_para(f, [("XYLab 具身智能建造", 16, WHITE, True)], align=PP_ALIGN.CENTER, first=True, after=4)
para(f, "contact@xylab.ai  ·  浙江大学 · 具身智能与智能建造", 11.5, MUTE, align=PP_ALIGN.CENTER, after=0)

prs.save(OUT)
print("SAVED:", OUT)
print("slides:", len(prs.slides._sldIdLst))
