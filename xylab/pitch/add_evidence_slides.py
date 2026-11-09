# -*- coding: utf-8 -*-
"""
Remove overlay images from content slides; insert dedicated EVIDENCE slides
with descriptions (no text overlap). Self-checks layout after build.
"""
from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

HERE = Path(__file__).resolve().parent
THESIS_ROOT = HERE.parents[2]
PPT = THESIS_ROOT / "docs" / "XYLab-组外交流-20260818.pptx"
ASSETS = HERE / "assets" / "seminar"
FIG = Path(r"D:\论文\拉拔、剪切数据\figures\editable")

# ── style (match user-adjusted deck) ──
BG, BG2, BORDER = "FFFFFF", "F8FAFC", "CBD5E1"
PRIMARY, ACCENT, ACCENT_LIGHT = "1E3A5F", "2563EB", "DBEAFE"
TEAL, GREEN, PURPLE, AMBER = "0F766E", "047857", "6D28D9", "B45309"
TEXT, DIM, MUTE, WHITE = "1E293B", "475569", "64748B", "FFFFFF"
FONT, FONT_L = "微软雅黑", "Arial"
SW, SH, MX = 13.333, 7.5, 0.92
FOOTER = "浙江大学 ZJUI · 肖岩教授课题组 · 暑期学术活动日 2026.08.18"

REF_BAR = (Emu(841248), Emu(822833), Emu(128016), Emu(658368))
REF_KICKER = (Emu(1097280), Emu(475488))
REF_TITLE = (Emu(1042543), Emu(850900))
REF_UNDERLINE_T = Emu(1755648)
BADGE_BOX = (Emu(9018727), Emu(475488), Emu(2148840), Emu(438912))
BADGE_TXT = (Emu(9110167), Emu(512064))

# layout zones (inches) — evidence slides
DESC_Y, DESC_H = 2.05, 1.02
FRAME_Y, FRAME_H = 3.18, 3.62
IMG_PAD = 0.18

_page = 0


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


def add_bullet_para(tf, text, size=12, bullet_color=ACCENT, text_color=DIM, after=5, line=1.15, first=False):
    p = tf.paragraphs[0] if (first and not tf.paragraphs[0].runs) else tf.add_paragraph()
    p.space_after = Pt(after)
    if line:
        p.line_spacing = line
    indent = Pt(size * 1.35)
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(int(indent)))
    pPr.set("indent", str(int(-indent)))
    rb = p.add_run()
    rb.text = "▸"
    rb.font.size = Pt(size)
    rb.font.bold = True
    rb.font.color.rgb = C(bullet_color)
    _set_font(rb, FONT)
    rs = p.add_run()
    rs.text = " " + text
    rs.font.size = Pt(size)
    rs.font.color.rgb = C(text_color)
    _set_font(rs, FONT)


def slide_footer(slide, page_num: str):
    rect(slide, 0, SH - 0.58, SW, 0.58, BG2)
    rect(slide, MX, SH - 0.58, SW - 2 * MX, 0.012, BORDER)
    f = tb(slide, MX, SH - 0.48, 10, 0.32)
    para(f, FOOTER, 8.5, MUTE, first=True)
    pg = tb(slide, SW - MX - 0.55, SH - 0.49, 0.45, 0.34, MSO_ANCHOR.MIDDLE)
    para(pg, page_num, 10.5, MUTE, align=PP_ALIGN.RIGHT, first=True, font=FONT_L)


def evidence_header(slide, kicker, title, accent=ACCENT):
    rect(slide, 0, 0, SW, SH, BG)
    rect(slide, 0, 0, SW, 0.08, PRIMARY)
    bl, bt, bw2, bh2 = REF_BAR
    rect(slide, bl / 914400, bt / 914400, bw2 / 914400, bh2 / 914400, accent)
    kl, kt = REF_KICKER
    k = tb(slide, kl / 914400, kt / 914400, 11, 0.38)
    para(k, kicker, 12.5, accent, bold=True, first=True, font=FONT_L)
    tl, tt = REF_TITLE
    t = tb(slide, tl / 914400, tt / 914400, SW - 2 * MX - 0.2, 1.0)
    para(t, title, 28, PRIMARY, bold=True, first=True, line=1.08)
    rect(slide, MX, REF_UNDERLINE_T / 914400, SW - 2 * MX, 0.028, accent)


def remove_all_pictures(prs):
    n = 0
    for slide in prs.slides:
        for sh in list(slide.shapes):
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                sh._element.getparent().remove(sh._element)
                n += 1
    return n


def insert_blank_slide(prs, index: int):
    layout = prs.slide_layouts[6]
    new_slide = prs.slides.add_slide(layout)
    sld_id_lst = prs.slides._sldIdLst
    new_id = sld_id_lst[-1]
    sld_id_lst.remove(new_id)
    sld_id_lst.insert(index, new_id)
    return prs.slides[index]


def bbox_inches(sh):
    return (sh.left / 914400, sh.top / 914400, sh.width / 914400, sh.height / 914400)


def overlaps(a, b, margin=0.05):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh
    return not (ax2 + margin < bx or bx2 + margin < ax or ay2 + margin < by or by2 + margin < ay)


def build_evidence_slide(prs, index, page_str, kicker, title, bullets, img_path, accent, note):
    slide = insert_blank_slide(prs, index)
    evidence_header(slide, kicker, title, accent=accent)
    slide_footer(slide, page_str)

    cw = SW - 2 * MX
    card(slide, MX, DESC_Y, cw, DESC_H, BG2, accent, 0.08)
    tf = tb(slide, MX + 0.22, DESC_Y + 0.12, cw - 0.4, DESC_H - 0.2)
    for i, b in enumerate(bullets):
        add_bullet_para(tf, b, 12.5, accent, DIM, after=4 if i < len(bullets) - 1 else 0, first=(i == 0))

    rect(slide, MX, FRAME_Y, cw, FRAME_H, BG2, MSO_SHAPE.ROUNDED_RECTANGLE, BORDER, 1, radius=0.06)
    iw = cw - 2 * IMG_PAD
    ih = FRAME_H - 2 * IMG_PAD
    path = Path(img_path)
    if path.exists():
        slide.shapes.add_picture(
            str(path), Inches(MX + IMG_PAD), Inches(FRAME_Y + IMG_PAD),
            width=Inches(iw), height=Inches(ih),
        )
    else:
        tf = tb(slide, MX + IMG_PAD, FRAME_Y + IMG_PAD, iw, ih, MSO_ANCHOR.MIDDLE)
        para(tf, f"[缺失图片] {path.name}", 14, MUTE, align=PP_ALIGN.CENTER, first=True)

    slide.notes_slide.notes_text_frame.text = note.strip()
    return slide


def card(slide, x, y, w, h, rgb=BG2, line=BORDER, radius=0.06):
    return rect(slide, x, y, w, h, rgb, MSO_SHAPE.ROUNDED_RECTANGLE, line, 1, radius=radius)


# anchor = original slide index (0-based) to insert AFTER
EVIDENCE_INSERTS = [
    (3, "E4a", "MECHANICS · WITHDRAWAL", "木钉拉拔试验：荷载-位移曲线",
     ["TBK 系列 55 mm 埋深，按 EN 1382 执行拉拔试验", "曲线提供峰值荷载、刚度与能量，供 EC5 设计表达式校准", "对应小论文中与组内 glubam 连接力学研究衔接"],
     FIG / "load_displacement_x50_y5" / "withdrawal_TBK_55mm.png", TEAL,
     "这一页是拉拔试验佐证。图中为 TBK 55 mm 埋深试件的荷载-位移曲线。可以看到峰值与软化段特征，这些数据将用于后续钉位决策中的折减系数和预钻触发规则，不是经验取值。"),

    (3, "E4b", "MECHANICS · SHEAR", "木钉剪切试验：双剪荷载-位移",
     ["TBST 系列双剪试件，反映钉杆在层间剪切下的承载行为", "与拉拔试验互补，共同约束接合区破坏模式", "为「能否在此打钉」提供力学下限参考"],
     FIG / "load_displacement_x50" / "shear_TBST.png", TEAL,
     "这一页展示剪切试验曲线。拉拔与剪切分别约束不同方向的破坏模式，两者一起进入我的规范决策规则库，保证打钉位置不仅避开缺陷，也满足连接力学要求。"),

    (3, "E4c", "MECHANICS · STATISTICS", "拉拔试验统计：强度 / 刚度 / 能量",
     ["汇总 TBK / TBKS / TBKT 多组试件统计结果", "强度、刚度、能量三指标对照，支持 κ(d) 折减参数标定", "试验数据→决策规则的可追溯链路"],
     FIG / "Fig_2-9_withdrawal_statistics.png", TEAL,
     "这页是组内试验数据的统计汇总。三类指标对应 Eurocode 5 设计里常用的强度、刚度与延性概念。我的系统会把这些统计量映射到决策矩阵，而不是让 AI 凭空给阈值。"),

    (3, "E4d", "XYLAB · PLANNING", "XYLab 钉位规划模块（浏览器端真实运算）",
     ["栅格禁区膨胀 + KD-tree 最近可行点搜索", "软代价图融合缺陷置信度与规范间距约束", "输出可解释钉位方案，供后续 Agent 决策与机械臂执行"],
     ASSETS / "planning.png", ACCENT,
     "这页是 XYLab 钉位规划界面截图。左侧可见缺陷 ROI 与禁区，右侧为候选钉位。注意几何算法在浏览器端真实运算，不是动画演示——这保证规划结果可复现、可导出 JSON 日志。"),

    (4, "E5", "XYLAB · DASHBOARD", "系统总控台：感知—规划—决策—执行流水线",
     ["十一模块一体化前端，覆盖缺陷感知到施工日志", "Pipeline 状态条展示当前流程阶段", "作为大论文「系统级贡献」的核心界面"],
     ASSETS / "dashboard.png", ACCENT,
     "这页是 XYLab 总控台。可以看到感知、规划、决策、执行各模块入口，以及流水线状态。汇报中强调：我的毕业工作不是单点算法，而是可运行的具身智能系统。"),

    (6, "E7", "XYLAB · PERCEPTION", "缺陷感知模块：YOLOv8-seg 七类分割",
     ["识别活节、裂缝、腐朽、虫洞、既有铁钉等七类目标", "输出掩码与置信度，映射至板面物理坐标", "下一步：mock 权重→现场采集微调"],
     ASSETS / "perception.png", TEAL,
     "这页是缺陷感知界面。系统先分割再规划——这是「缺陷驱动打钉」与常规按图打钉的根本区别。后续将把 mock 模型替换为试验室采集的真实权重。"),

    (7, "E8", "XYLAB · AGENT", "规范决策模块：分层 Agent + 引用链",
     ["硬规则 → 决策矩阵 → LLM 语义复核三层架构", "逐钉输出 NAIL / PREDRILL / RELOCATE / SKIP", "每条决策附 Eurocode 5 规范引用，支持人工复核"],
     ASSETS / "agent.png", ACCENT,
     "这页是 Agent 决策控制台。每一颗钉的决策都有结构化 JSON 和规范引用链，满足土木领域对可解释性的要求，也便于答辩时追溯「为什么这样打」。"),

    (8, "E9", "XYLAB · TWIN", "数字孪生：上料—扫描—打钉流程仿真",
     ["Skill 原语驱动状态机：SCAN → PLAN → EXEC → LOG", "真机试钉前的安全验证与流程演练", "验证路径：孪生 → 单板 → 墙段"],
     ASSETS / "twin.png", GREEN,
     "这页是数字孪生界面，用于真机前验证完整流程。状态机与 Skill 原语和后续 KUKA 机械臂执行层一一对应，降低上真机试钉的风险。"),
]


def verify_presentation(prs):
    issues = []
    content_with_pics = []
    for i, slide in enumerate(prs.slides):
        ev = is_evidence_slide(slide)
        pics, texts = [], []
        for sh in slide.shapes:
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                pics.append(bbox_inches(sh))
            elif sh.has_text_frame and sh.text_frame.text.strip():
                if sh.top / 914400 < SH - 0.65:
                    texts.append(bbox_inches(sh))
        if pics and not ev and i > 0:
            content_with_pics.append(i + 1)
        for p in pics:
            if ev and p[1] < FRAME_Y - 0.15:
                issues.append(f"Slide {i+1}: image too high (y={p[1]:.2f})")
            for t in texts:
                if overlaps(p, t):
                    issues.append(f"Slide {i+1}: picture overlaps text")
    return issues, content_with_pics


def is_evidence_slide(slide):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip() in ("EVIDENCE",):
            return True
        if sh.has_text_frame and "MECHANICS" in sh.text_frame.text:
            return True
        if sh.has_text_frame and "XYLAB" in sh.text_frame.text and sh.top < Emu(600000):
            return True
    return False


def slide_text_snip(slide):
    for sh in slide.shapes:
        if sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if len(t) > 8:
                return t[:24]
    return "?"


def renumber_footers(prs):
    num = 0
    for slide in prs.slides:
        num += 1
        if num == 1:
            continue
        for sh in slide.shapes:
            if not sh.has_text_frame:
                continue
            if sh.top > Emu(6300000) and sh.width < Emu(1500000):
                t = sh.text_frame.text.strip()
                if t.replace("-", "").isdigit() or t == "—" or (t.isdigit() and len(t) <= 2):
                    sh.text_frame.text = f"{num:02d}"


def main():
    prs = Presentation(str(PPT))
    removed = remove_all_pictures(prs)
    print(f"Removed {removed} overlay pictures from content slides")

    offset = 0
    for anchor, page_tag, kicker, title, bullets, img, accent, note in EVIDENCE_INSERTS:
        idx = anchor + 1 + offset
        page_str = "—"  # renumber later
        build_evidence_slide(prs, idx, page_str, kicker, title, bullets, img, accent, note)
        offset += 1
        print(f"  + evidence after slide {anchor+1}: {title[:30]}…")

    renumber_footers(prs)
    issues, bad = verify_presentation(prs)
    prs.save(str(PPT))
    print(f"SAVED: {PPT}  total slides: {len(prs.slides)}")
    if bad:
        print("WARN content slides still have pictures:", bad)
    if issues:
        print("Layout issues:")
        for x in issues[:20]:
            print(" ", x)
    else:
        print("Layout check: OK — no picture/text overlap detected")


if __name__ == "__main__":
    main()
