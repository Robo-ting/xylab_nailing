# -*- coding: utf-8 -*-
"""Convert XYLab proposal Markdown into send-ready Word documents."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Pt, RGBColor
from docx.enum.section import WD_ORIENT

HERE = Path(__file__).resolve().parent
DOCS = HERE.parents[2] / "docs"
ASSETS = HERE / "assets" / "proposal_flows"

NAVY = RGBColor(0x1E, 0x3A, 0x8A)
BLUE = RGBColor(0x25, 0x63, 0xEB)
TEXT = RGBColor(0x1E, 0x29, 0x3B)
MUTE = RGBColor(0x47, 0x55, 0x69)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HEAD_FILL = "1E3A8A"
ALT_FILL = "F1F5F9"
CODE_FILL = "F8FAFC"
NOTE_FILL = "EFF6FF"


def set_run_font(run, name_cn="宋体", name_en="Calibri", size=11, bold=False, color=TEXT, italic=False):
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.name = name_en
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), name_en)
    rFonts.set(qn("w:hAnsi"), name_en)
    rFonts.set(qn("w:eastAsia"), name_cn)
    rFonts.set(qn("w:cs"), name_en)


def shade_cell(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = tcPr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcPr.append(shd)
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")


def set_cell_border(cell, color="CBD5E1", sz="4"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn("w:tcBorders"))
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for edge in ("top", "left", "bottom", "right"):
        el = tcBorders.find(qn(f"w:{edge}"))
        if el is None:
            el = OxmlElement(f"w:{edge}")
            tcBorders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:color"), color)
        el.set(qn("w:space"), "0")


def set_cell_margins(cell, top=40, bottom=40, left=80, right=80):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.find(qn("w:tcMar"))
    if tcMar is None:
        tcMar = OxmlElement("w:tcMar")
        tcPr.append(tcMar)
    for name, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = tcMar.find(qn(f"w:{name}"))
        if el is None:
            el = OxmlElement(f"w:{name}")
            tcMar.append(el)
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")


def prevent_row_split(row):
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    cant = trPr.find(qn("w:cantSplit"))
    if cant is None:
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)


def set_table_fixed(table, widths):
    table.autofit = False
    table.allow_autofit = False
    tbl = table._tbl
    tblPr = tbl.tblPr
    layout = tblPr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tblPr.append(layout)
    layout.set(qn("w:type"), "fixed")
    grid = tbl.find(qn("w:tblGrid"))
    if grid is not None:
        for i, w in enumerate(widths):
            grid_col = list(grid)[i] if i < len(list(grid)) else None
            if grid_col is not None:
                grid_col.set(qn("w:w"), str(int(w)))
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            if i < len(widths):
                cell.width = Emu(int(widths[i]) * 635) if False else widths[i]
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                tcW = tcPr.find(qn("w:tcW"))
                if tcW is None:
                    tcW = OxmlElement("w:tcW")
                    tcPr.append(tcW)
                tcW.set(qn("w:w"), str(int(widths[i])))
                tcW.set(qn("w:type"), "dxa")


def add_page_number(paragraph):
    run1 = paragraph.add_run()
    set_run_font(run1, size=9, color=MUTE)
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    run1._r.append(fld1)

    run2 = paragraph.add_run()
    set_run_font(run2, size=9, color=MUTE)
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    run2._r.append(instr)

    run3 = paragraph.add_run()
    set_run_font(run3, size=9, color=MUTE)
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run3._r.append(fld2)

    run4 = paragraph.add_run(" / ")
    set_run_font(run4, size=9, color=MUTE)

    run5 = paragraph.add_run()
    set_run_font(run5, size=9, color=MUTE)
    fld3 = OxmlElement("w:fldChar")
    fld3.set(qn("w:fldCharType"), "begin")
    run5._r.append(fld3)

    run6 = paragraph.add_run()
    set_run_font(run6, size=9, color=MUTE)
    instr2 = OxmlElement("w:instrText")
    instr2.set(qn("xml:space"), "preserve")
    instr2.text = " NUMPAGES "
    run6._r.append(instr2)

    run7 = paragraph.add_run()
    set_run_font(run7, size=9, color=MUTE)
    fld4 = OxmlElement("w:fldChar")
    fld4.set(qn("w:fldCharType"), "end")
    run7._r.append(fld4)


def setup_document(title: str, footer_left: str):
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(0.8)

    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.clear()
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = hp.add_run(title)
    set_run_font(r, name_cn="黑体", name_en="Calibri", size=9, color=NAVY, bold=True)
    hp.paragraph_format.space_after = Pt(2)

    # header line
    pBdr = hp._p.get_or_add_pPr()
    pBdr_el = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "2563EB")
    pBdr_el.append(bottom)
    pBdr.append(pBdr_el)

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.clear()
    fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = fp.add_run(footer_left + "    ")
    set_run_font(r, size=9, color=MUTE)
    add_page_number(fp)
    pBdr = fp._p.get_or_add_pPr()
    pBdr_el = OxmlElement("w:pBdr")
    top = OxmlElement("w:top")
    top.set(qn("w:val"), "single")
    top.set(qn("w:sz"), "6")
    top.set(qn("w:space"), "4")
    top.set(qn("w:color"), "CBD5E1")
    pBdr_el.append(top)
    pBdr.append(pBdr_el)

    styles = doc.styles
    styles["Normal"].font.size = Pt(11)
    styles["Normal"].font.color.rgb = TEXT
    styles["Normal"].font.name = "Calibri"
    rPr = styles["Normal"].element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), "宋体")
    pf = styles["Normal"].paragraph_format
    pf.space_after = Pt(6)
    pf.space_before = Pt(0)
    pf.line_spacing = 1.28
    return doc


def usable_dxa(doc) -> int:
    sec = doc.sections[0]
    return int((sec.page_width - sec.left_margin - sec.right_margin) / 635)


def add_heading(doc, text, level):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10 if level == 2 else 8)
    p.paragraph_format.space_after = Pt(8 if level <= 2 else 6)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.line_spacing = 1.2
    pPr = p._p.get_or_add_pPr()
    ol = OxmlElement("w:outlineLvl")
    ol.set(qn("w:val"), str(level - 1))
    pPr.append(ol)
    size = {1: 18, 2: 16, 3: 15, 4: 13}[min(level, 4)]
    cn = "黑体"
    r = p.add_run(text)
    set_run_font(r, name_cn=cn, name_en="Calibri", size=size, bold=True, color=NAVY if level <= 2 else TEXT)
    return p


def add_inline_runs(paragraph, text, size=11, color=TEXT, bold_all=False):
    # split **bold** and `code`
    pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`)")
    parts = pattern.split(text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = paragraph.add_run(part[2:-2])
            set_run_font(r, size=size, bold=True, color=color)
        elif part.startswith("`") and part.endswith("`"):
            r = paragraph.add_run(part[1:-1])
            set_run_font(r, name_cn="Consolas", name_en="Consolas", size=size - 0.5, color=RGBColor(0x0F, 0x76, 0x6E), italic=False)
        else:
            r = paragraph.add_run(part)
            set_run_font(r, size=size, bold=bold_all, color=color)


def add_body(doc, text, first_line_indent=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.32
    # 短引导句（“主要分析内容包括：”）加粗，与参照对外文档一致
    if text.endswith("：") and len(text) <= 22:
        r = p.add_run(text)
        set_run_font(r, size=11, bold=True, color=TEXT)
        p.paragraph_format.space_after = Pt(4)
        return p
    add_inline_runs(p, text)
    return p


def add_bullet(doc, text, numbered=False, idx=1):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.first_line_indent = Cm(-0.4)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.28
    prefix = f"{idx}. " if numbered else "•  "
    r = p.add_run(prefix)
    set_run_font(r, size=11, bold=True, color=BLUE)
    add_inline_runs(p, text)
    return p


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(text)
    set_run_font(r, size=9.5, color=MUTE, italic=True)
    return p


def add_image(doc, path: Path, caption: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run()
    # keep within page width ~ 16.6 cm
    run.add_picture(str(path), width=Cm(16.4))
    add_caption(doc, caption)


def add_note_box(doc, text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    shade_cell(cell, NOTE_FILL)
    set_cell_border(cell, "93C5FD", "8")
    set_cell_margins(cell, 80, 80, 120, 120)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    add_inline_runs(p, text, size=10.5, color=NAVY)
    widths = [usable_dxa(doc)]
    set_table_fixed(table, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_code_block(doc, code: str):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    shade_cell(cell, CODE_FILL)
    set_cell_border(cell, "94A3B8", "8")
    set_cell_margins(cell, 80, 80, 120, 120)
    # clear default para and write lines
    p = cell.paragraphs[0]
    lines = code.rstrip("\n").split("\n")
    if not lines:
        lines = [""]
    for i, line in enumerate(lines):
        if i == 0:
            target = p
        else:
            target = cell.add_paragraph()
        target.paragraph_format.space_after = Pt(0)
        target.paragraph_format.space_before = Pt(0)
        target.paragraph_format.line_spacing = 1.08
        r = target.add_run(line if line else " ")
        set_run_font(r, name_cn="Consolas", name_en="Consolas", size=8.5, color=RGBColor(0x0F, 0x17, 0x2A))
    set_table_fixed(table, [usable_dxa(doc)])
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def add_table(doc, rows: list[list[str]]):
    if not rows:
        return
    ncols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=ncols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    usable = usable_dxa(doc)
    # weight first column slightly narrower if many cols
    n = ncols
    if n == 2:
        weights = [0.28, 0.72]
    elif n == 3:
        weights = [0.22, 0.39, 0.39]
    elif n == 4:
        weights = [0.18, 0.28, 0.28, 0.26]
    elif n == 5:
        weights = [0.08, 0.18, 0.22, 0.30, 0.22]
    else:
        weights = [1 / n] * n
    widths = [int(usable * w) for w in weights]
    # fix rounding
    widths[-1] = usable - sum(widths[:-1])
    set_table_fixed(table, widths)

    header_fs = 9 if n >= 6 else 10
    body_fs = 8.5 if n >= 6 else 9.5 if n >= 4 else 10

    for ri, row in enumerate(rows):
        prevent_row_split(table.rows[ri])
        for ci in range(ncols):
            cell = table.cell(ri, ci)
            val = row[ci] if ci < len(row) else ""
            set_cell_margins(cell, 50, 50, 70, 70)
            set_cell_border(cell, "94A3B8", "4")
            if ri == 0:
                shade_cell(cell, HEAD_FILL)
            elif ri % 2 == 0:
                shade_cell(cell, ALT_FILL)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            # split long cell into multiple paras if it has explicit newlines
            parts = val.split("\n") if val else [""]
            for pi, part in enumerate(parts):
                target = p if pi == 0 else cell.add_paragraph()
                target.paragraph_format.space_after = Pt(0)
                target.paragraph_format.space_before = Pt(0)
                add_inline_runs(
                    target,
                    part,
                    size=header_fs if ri == 0 else body_fs,
                    color=WHITE if ri == 0 else TEXT,
                    bold_all=(ri == 0),
                )
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(8)


def parse_table(lines, start):
    rows = []
    i = start
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        # skip separator
        if all(re.match(r"^:?-+:?$", c.replace(" ", "")) for c in cells):
            i += 1
            continue
        rows.append(cells)
        i += 1
    return rows, i


def strip_md_link(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


MERMAID_MAP = {
    "internal": [
        (ASSETS / "internal_architecture.png", "图 1  总体算法架构（感知 — AI 决策 — 执行）"),
        (ASSETS / "internal_quality.png", "图 2  图像质量门控流程"),
    ],
    "external": [
        (ASSETS / "external_overall.png", "图 1  整体技术方案流程"),
        (ASSETS / "external_process.png", "图 2  系统整体实现流程"),
    ],
}


def convert(md_path: Path, out_path: Path, *, kind: str, header_title: str, footer: str, doc_title: str, subtitle: str):
    raw = md_path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    doc = setup_document(header_title, footer)

    # title block
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t.paragraph_format.space_before = Pt(6)
    t.paragraph_format.space_after = Pt(4)
    r = t.add_run(doc_title)
    set_run_font(r, name_cn="黑体", name_en="Calibri", size=22, bold=True, color=NAVY)

    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s.paragraph_format.space_after = Pt(10)
    r = s.add_run(subtitle)
    set_run_font(r, name_cn="宋体", name_en="Calibri", size=11, color=MUTE)

    mermaid_idx = 0
    i = 0
    numbered_counter = 0
    skip_title = True
    in_code = False
    code_lang = ""
    code_buf: list[str] = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # fenced code / mermaid
        if stripped.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = stripped[3:].strip().lower()
                code_buf = []
                i += 1
                continue
            else:
                in_code = False
                body = "\n".join(code_buf)
                if code_lang == "mermaid":
                    imgs = MERMAID_MAP[kind]
                    if mermaid_idx < len(imgs):
                        img, cap = imgs[mermaid_idx]
                        if img.exists():
                            add_image(doc, img, cap)
                        else:
                            add_note_box(doc, "流程图文件缺失，请重新生成。")
                        mermaid_idx += 1
                else:
                    add_code_block(doc, body)
                i += 1
                continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if not stripped:
            i += 1
            continue
        if stripped == "---":
            i += 1
            continue
        if stripped.startswith("> 粘贴说明"):
            i += 1
            while i < len(lines) and lines[i].strip().startswith(">"):
                i += 1
            continue
        if stripped.startswith(">"):
            add_note_box(doc, strip_md_link(stripped.lstrip("> ").strip()))
            i += 1
            continue

        if stripped.startswith("#"):
            m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
            level = len(m.group(1))
            text = strip_md_link(m.group(2).strip())
            if skip_title and level == 1:
                skip_title = False
                i += 1
                continue
            skip_title = False
            add_heading(doc, text, max(1, level - 1))
            numbered_counter = 0
            i += 1
            continue

        if stripped.startswith("|"):
            rows, nxt = parse_table(lines, i)
            # unescape markdown table pipes already split
            cleaned = []
            for row in rows:
                cleaned.append([strip_md_link(c.replace("<br/>", "\n").replace("<br>", "\n")) for c in row])
            add_table(doc, cleaned)
            i = nxt
            continue

        if re.match(r"^\d+\.\s+", stripped):
            numbered_counter += 1
            text = re.sub(r"^\d+\.\s+", "", stripped)
            add_bullet(doc, strip_md_link(text), numbered=True, idx=numbered_counter)
            i += 1
            continue

        if stripped.startswith("- "):
            add_bullet(doc, strip_md_link(stripped[2:]))
            numbered_counter = 0
            i += 1
            continue

        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12)
            r = p.add_run(stripped.strip("*").strip())
            set_run_font(r, size=10, color=MUTE, italic=True)
            i += 1
            continue

        # kicker line like "缺陷感知 · ..."
        if "·" in stripped and len(stripped) < 40 and not stripped.startswith("#"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(10)
            r = p.add_run(stripped)
            set_run_font(r, size=12, bold=True, color=BLUE)
            i += 1
            continue

        add_body(doc, strip_md_link(stripped), first_line_indent=True)
        numbered_counter = 0
        i += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    print("SAVED", out_path)


def main():
    convert(
        DOCS / "XYLab-打钉系统方案-飞书版.md",
        DOCS / "XYLab-打钉系统方案-内部版.docx",
        kind="internal",
        header_title="XYLab · 缺陷检测驱动的木材智能打钉系统方案（内部版）",
        footer="内部资料  |  V1.0  |  2026-08-24",
        doc_title="预制竹木构件缺陷检测驱动的机械臂智能打钉系统方案",
        subtitle="内部技术版  ·  算法方案与生产选型  ·  V1.0  ·  2026-08-24",
    )
    convert(
        DOCS / "XYLab-打钉系统方案-对外版.md",
        DOCS / "XYLab-打钉系统方案-对外版.docx",
        kind="external",
        header_title="预制竹木构件智能打钉机器人场景技术栈（对外版）",
        footer="对外交流资料  |  V1.0  |  2026-08-24",
        doc_title="预制竹木构件智能打钉机器人场景技术栈",
        subtitle="对外技术交流版  ·  V1.0  ·  2026-08-24",
    )


if __name__ == "__main__":
    main()
