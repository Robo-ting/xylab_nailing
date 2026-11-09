# -*- coding: utf-8 -*-
"""
Markdown -> Word converter tuned for the XYLab proposal documents.

Produces a submission-ready .docx: restyled built-in heading styles (so the
navigation pane and a live TOC field work), banded bordered tables with
repeating header rows, shaded monospace code blocks, page-numbered footer, and
mermaid fenced blocks rendered to images via mermaid.ink (cached on disk).

Usage:
    python md_to_docx.py <input.md> [<input2.md> ...]
"""
from __future__ import annotations

import base64
import hashlib
import re
import sys
import time
from pathlib import Path

import requests
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

# ── typography ──
FONT_CN = "微软雅黑"
FONT_EN = "Segoe UI"
FONT_MONO = "Consolas"

CLR_TEXT = "1F2937"
CLR_HEAD = "1E3A8A"
CLR_ACCENT = "2563EB"
CLR_MUTE = "6B7280"
CLR_TBL_HEAD = "1E3A8A"
CLR_TBL_BAND = "F1F5F9"
CLR_TBL_LINE = "CBD5E1"
CLR_CODE_BG = "F8FAFC"

CONTENT_W_CM = 15.4  # A4 minus margins set in _setup_page

MERMAID_CACHE = Path(__file__).resolve().parent / "assets" / "mermaid_cache"


# ══════════════════════════════════════════════════════════════════
# low-level docx helpers
# ══════════════════════════════════════════════════════════════════
def _set_run_font(run, *, size=None, bold=None, italic=None, color=None, mono=False):
    name = FONT_MONO if mono else FONT_EN
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:eastAsia"), FONT_MONO if mono else FONT_CN)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = RGBColor.from_string(color)


def _shade(element, fill: str):
    """Apply solid shading to a paragraph pPr or table-cell tcPr owner."""
    pr = element.get_or_add_pPr() if element.tag.endswith("}p") else element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pr.append(shd)


def _para_border(paragraph, color: str, size: int = 6):
    ppr = paragraph._element.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "6")
        el.set(qn("w:color"), color)
        borders.append(el)
    ppr.append(borders)


def _table_borders(table, color: str):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tbl_pr.append(borders)


def _repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


def _cant_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))


def _field(paragraph, instr: str):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = instr
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr_el, sep, end):
        run._element.append(el)
    return run


def _enable_update_fields(doc):
    """Ask Word/WPS to refresh field results (the TOC) when the file opens."""
    settings = doc.settings.element
    el = OxmlElement("w:updateFields")
    el.set(qn("w:val"), "true")
    settings.append(el)


# ══════════════════════════════════════════════════════════════════
# document scaffolding
# ══════════════════════════════════════════════════════════════════
def _setup_page(doc):
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.4)
        section.bottom_margin = Cm(2.2)
        section.left_margin = Cm(2.8)
        section.right_margin = Cm(2.8)
        section.header_distance = Cm(1.3)
        section.footer_distance = Cm(1.2)


def _setup_styles(doc):
    normal = doc.styles["Normal"]
    normal.font.name = FONT_EN
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(CLR_TEXT)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_CN)
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.45
    pf.space_after = Pt(6)

    specs = {
        "Heading 1": (17, True, CLR_HEAD, 18, 10),
        "Heading 2": (14.5, True, CLR_HEAD, 14, 8),
        "Heading 3": (12.5, True, CLR_ACCENT, 11, 6),
    }
    for name, (size, bold, color, before, after) in specs.items():
        st = doc.styles[name]
        st.font.name = FONT_EN
        st.font.size = Pt(size)
        st.font.bold = bold
        st.font.color.rgb = RGBColor.from_string(color)
        st._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_CN)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        st.paragraph_format.line_spacing = 1.2


def _add_footer(doc, doc_title: str):
    footer = doc.sections[0].footer
    para = footer.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(f"{doc_title}    |    ")
    _set_run_font(run, size=8, color=CLR_MUTE)
    _field(para, "PAGE")
    for r in para.runs:
        if not r.text:
            _set_run_font(r, size=8, color=CLR_MUTE)
    run = para.add_run(" / ")
    _set_run_font(run, size=8, color=CLR_MUTE)
    _field(para, "NUMPAGES")
    for r in para.runs:
        if not r.text:
            _set_run_font(r, size=8, color=CLR_MUTE)


def _add_title_block(doc, title: str, subtitle: str | None):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(48)
    para.paragraph_format.space_after = Pt(10)
    run = para.add_run(title)
    _set_run_font(run, size=24, bold=True, color=CLR_HEAD)

    if subtitle:
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after = Pt(16)
        run = para.add_run(subtitle)
        _set_run_font(run, size=11.5, color=CLR_MUTE)

    rule = doc.add_paragraph()
    rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rule.paragraph_format.space_after = Pt(0)
    _para_border(rule, CLR_ACCENT, size=4)


def _add_toc(doc):
    head = doc.add_paragraph()
    head.paragraph_format.space_before = Pt(24)
    head.paragraph_format.space_after = Pt(10)
    run = head.add_run("目  录")
    _set_run_font(run, size=15, bold=True, color=CLR_HEAD)

    para = doc.add_paragraph()
    _field(para, 'TOC \\o "1-3" \\h \\z \\u')
    doc.add_page_break()


# ══════════════════════════════════════════════════════════════════
# mermaid rendering
# ══════════════════════════════════════════════════════════════════
MAX_PRINT_RATIO = 2.2  # wider than this and the labels shrink below legibility on A4


def _fetch_mermaid(code: str, attempts: int = 5) -> Path | None:
    """Render via mermaid.ink, caching by content hash. The service returns
    transient 503s under load, so retry with backoff before giving up."""
    MERMAID_CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(code.encode("utf-8")).hexdigest()[:16]
    out = MERMAID_CACHE / f"{key}.png"
    if out.exists() and out.stat().st_size > 2000:
        return out

    encoded = base64.urlsafe_b64encode(code.encode("utf-8")).decode("ascii")
    url = f"https://mermaid.ink/img/{encoded}?type=png&width=2600&bgColor=FFFFFF"
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(url, timeout=90)
            if resp.status_code == 200 and len(resp.content) >= 2000:
                out.write_bytes(resp.content)
                return out
            reason = f"HTTP {resp.status_code} len={len(resp.content)}"
        except Exception as exc:
            reason = f"{type(exc).__name__}: {str(exc)[:60]}"
        if attempt < attempts:
            wait = 3 * attempt
            print(f"    [mermaid] {reason}; retry {attempt}/{attempts - 1} in {wait}s")
            time.sleep(wait)
    print(f"    [mermaid] gave up after {attempts} attempts -> fallback to code block")
    return None


def render_mermaid(code: str) -> Path | None:
    """Render a diagram, re-laying it out vertically when the horizontal layout
    is too wide to stay legible once scaled to the A4 text width."""
    png = _fetch_mermaid(code)
    if png is None:
        return None

    with Image.open(png) as im:
        w, h = im.size
    if w / h <= MAX_PRINT_RATIO:
        return png

    rotated = re.sub(r"^(\s*(?:flowchart|graph))\s+(LR|RL)\b", r"\1 TB", code, count=1, flags=re.MULTILINE)
    if rotated == code:
        return png

    alt = _fetch_mermaid(rotated)
    if alt is None:
        return png
    with Image.open(alt) as im:
        w2, h2 = im.size
    print(f"    [mermaid] re-laid out horizontal diagram for print: "
          f"{w}x{h} (ratio {w / h:.1f}) -> {w2}x{h2} (ratio {w2 / h2:.2f})")
    return alt


# ══════════════════════════════════════════════════════════════════
# inline markdown
# ══════════════════════════════════════════════════════════════════
INLINE_RE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def add_inline(paragraph, text: str, *, size=10.5, color=CLR_TEXT, bold_all=False):
    text = text.replace("\\|", "|")
    for token in INLINE_RE.split(text):
        if not token:
            continue
        if token.startswith("**") and token.endswith("**"):
            run = paragraph.add_run(token[2:-2])
            _set_run_font(run, size=size, bold=True, color=CLR_HEAD)
        elif token.startswith("`") and token.endswith("`"):
            run = paragraph.add_run(token[1:-1])
            _set_run_font(run, size=size - 0.5, color=CLR_ACCENT, mono=True)
        elif token.startswith("[") and "](" in token:
            label = token[1: token.index("](")]
            run = paragraph.add_run(label)
            _set_run_font(run, size=size, color=color, bold=bold_all)
        else:
            run = paragraph.add_run(token)
            _set_run_font(run, size=size, color=color, bold=bold_all)


# ══════════════════════════════════════════════════════════════════
# block builders
# ══════════════════════════════════════════════════════════════════
def split_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    parts = re.split(r"(?<!\\)\|", body)
    return [p.strip() for p in parts]


def column_widths(rows: list[list[str]], ncols: int) -> list[float]:
    """Weight columns by mean visual length (CJK counts double), clamped."""
    weights = []
    for c in range(ncols):
        lengths = []
        for r in rows:
            cell = r[c] if c < len(r) else ""
            visual = sum(2 if ord(ch) > 0x2E80 else 1 for ch in cell)
            lengths.append(visual)
        weights.append(max(6.0, sum(lengths) / max(1, len(lengths))))
    total = sum(weights)
    fracs = [w / total for w in weights]
    lo, hi = 0.09, 0.52
    fracs = [min(hi, max(lo, f)) for f in fracs]
    total = sum(fracs)
    return [CONTENT_W_CM * f / total for f in fracs]


def add_table(doc, rows: list[list[str]]):
    header, body = rows[0], rows[1:]
    ncols = len(header)
    table = doc.add_table(rows=0, cols=ncols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _table_borders(table, CLR_TBL_LINE)

    widths = column_widths(rows, ncols)

    hrow = table.add_row()
    _repeat_header(hrow)
    _cant_split(hrow)
    for i, cell_text in enumerate(header):
        cell = hrow.cells[i]
        _shade(cell._tc, CLR_TBL_HEAD)
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_before = Pt(3)
        para.paragraph_format.space_after = Pt(3)
        para.paragraph_format.line_spacing = 1.15
        run = para.add_run(cell_text.replace("**", ""))
        _set_run_font(run, size=9.5, bold=True, color="FFFFFF")

    for ri, row_cells in enumerate(body):
        row = table.add_row()
        _cant_split(row)
        for i in range(ncols):
            cell = row.cells[i]
            if ri % 2 == 1:
                _shade(cell._tc, CLR_TBL_BAND)
            para = cell.paragraphs[0]
            para.paragraph_format.space_before = Pt(2)
            para.paragraph_format.space_after = Pt(2)
            para.paragraph_format.line_spacing = 1.2
            text = row_cells[i] if i < len(row_cells) else ""
            if i == 0:
                add_inline(para, text, size=9.5, bold_all=True)
            else:
                add_inline(para, text, size=9.5)

    for row in table.rows:
        for i, cell in enumerate(row.cells):
            cell.width = Cm(widths[i])

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(4)
    spacer.paragraph_format.line_spacing = 1.0


def add_code_block(doc, lines: list[str]):
    para = doc.add_paragraph()
    pf = para.paragraph_format
    pf.left_indent = Cm(0.3)
    pf.right_indent = Cm(0.2)
    pf.space_before = Pt(6)
    pf.space_after = Pt(10)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.08
    _shade(para._element, CLR_CODE_BG)
    _para_border(para, CLR_TBL_LINE, size=4)

    for idx, line in enumerate(lines):
        if idx:
            para.add_run().add_break()
        run = para.add_run(line if line else " ")
        _set_run_font(run, size=8.5, color=CLR_TEXT, mono=True)
        run._element.find(qn("w:t")).set(qn("xml:space"), "preserve")


def add_figure(doc, png: Path, caption: str | None):
    with Image.open(png) as im:
        w_px, h_px = im.size
    width_cm = min(CONTENT_W_CM, 15.4)
    height_cm = width_cm * h_px / w_px
    max_h = 20.0
    if height_cm > max_h:
        width_cm *= max_h / height_cm
        height_cm = max_h

    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(8)
    para.paragraph_format.space_after = Pt(4)
    para.paragraph_format.keep_with_next = True
    para.add_run().add_picture(str(png), width=Cm(width_cm))

    if caption:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_after = Pt(12)
        run = cap.add_run(caption)
        _set_run_font(run, size=9, color=CLR_MUTE)


def add_bullet(doc, text: str, ordered: bool, number: int | None = None):
    para = doc.add_paragraph()
    pf = para.paragraph_format
    pf.left_indent = Cm(0.85)
    pf.first_line_indent = Cm(-0.45)
    pf.space_before = Pt(1)
    pf.space_after = Pt(3)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.35
    marker = f"{number}. " if ordered else "▪  "
    run = para.add_run(marker)
    _set_run_font(run, size=10.5, color=CLR_ACCENT, bold=True)
    add_inline(para, text, size=10.5)


# ══════════════════════════════════════════════════════════════════
# main conversion
# ══════════════════════════════════════════════════════════════════
SKIP_NOTE_RE = re.compile(r"粘贴|Markdown|飞书")


def convert(md_path: Path, docx_path: Path):
    raw = md_path.read_text(encoding="utf-8").split("\n")
    print(f"\n[convert] {md_path.name}  ({len(raw)} lines)")

    doc = Document()
    _setup_page(doc)
    _setup_styles(doc)

    # peel off the H1 title and the Feishu paste note
    title, subtitle, body_start = md_path.stem, None, 0
    for i, line in enumerate(raw):
        if line.startswith("# "):
            title = line[2:].strip()
            body_start = i + 1
            break

    _add_title_block(doc, title, subtitle)
    _add_toc(doc)
    _add_footer(doc, title)

    fig_no = 0
    last_heading = ""
    i = body_start
    n = len(raw)
    stats = {"h": 0, "p": 0, "table": 0, "code": 0, "fig": 0, "li": 0}

    while i < n:
        line = raw[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # horizontal rule -> ignore (headings carry the structure)
        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped):
            i += 1
            continue

        # blockquote: drop the Feishu paste instructions, keep anything else
        if stripped.startswith(">"):
            quote_lines = []
            while i < n and raw[i].strip().startswith(">"):
                quote_lines.append(raw[i].strip().lstrip(">").strip())
                i += 1
            joined = " ".join(quote_lines)
            if joined and not SKIP_NOTE_RE.search(joined):
                para = doc.add_paragraph()
                para.paragraph_format.left_indent = Cm(0.5)
                _shade(para._element, CLR_TBL_BAND)
                add_inline(para, joined, size=10, color=CLR_MUTE)
                stats["p"] += 1
            continue

        # fenced block
        if stripped.startswith("```"):
            lang = stripped[3:].strip().lower()
            i += 1
            block = []
            while i < n and not raw[i].strip().startswith("```"):
                block.append(raw[i])
                i += 1
            i += 1
            if lang == "mermaid":
                png = render_mermaid("\n".join(block))
                if png:
                    fig_no += 1
                    add_figure(doc, png, f"图 {fig_no}　{last_heading}")
                    stats["fig"] += 1
                else:
                    add_code_block(doc, block)
                    stats["code"] += 1
            else:
                add_code_block(doc, block)
                stats["code"] += 1
            continue

        # heading
        m = re.match(r"^(#{2,6})\s+(.*)$", stripped)
        if m:
            level = min(len(m.group(1)) - 1, 3)
            text = m.group(2).strip()
            para = doc.add_heading("", level=level)
            add_inline(para, text, size={1: 17, 2: 14.5, 3: 12.5}[level])
            for run in para.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor.from_string(CLR_HEAD if level <= 2 else CLR_ACCENT)
            last_heading = re.sub(r"\*\*|`", "", text)
            stats["h"] += 1
            i += 1
            continue

        # table
        if stripped.startswith("|") and i + 1 < n and re.fullmatch(r"\|[\s:|-]+\|", raw[i + 1].strip()):
            rows = [split_row(raw[i])]
            i += 2
            while i < n and raw[i].strip().startswith("|"):
                rows.append(split_row(raw[i]))
                i += 1
            add_table(doc, rows)
            stats["table"] += 1
            continue

        # unordered list
        if re.match(r"^[-*+]\s+", stripped):
            while i < n and re.match(r"^[-*+]\s+", raw[i].strip()):
                add_bullet(doc, re.sub(r"^[-*+]\s+", "", raw[i].strip()), ordered=False)
                stats["li"] += 1
                i += 1
            continue

        # ordered list
        if re.match(r"^\d+\.\s+", stripped):
            counter = 0
            while i < n and re.match(r"^\d+\.\s+", raw[i].strip()):
                counter += 1
                add_bullet(doc, re.sub(r"^\d+\.\s+", "", raw[i].strip()), ordered=True, number=counter)
                stats["li"] += 1
                i += 1
            continue

        # trailing italic footer line
        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.paragraph_format.space_before = Pt(18)
            run = para.add_run(stripped.strip("*").strip())
            _set_run_font(run, size=9, italic=True, color=CLR_MUTE)
            i += 1
            continue

        # body paragraph
        para = doc.add_paragraph()
        para.paragraph_format.first_line_indent = Cm(0)
        add_inline(para, stripped, size=10.5)
        stats["p"] += 1
        i += 1

    _enable_update_fields(doc)
    doc.core_properties.title = title
    doc.core_properties.author = "XYLab"
    doc.save(str(docx_path))

    print(f"    headings={stats['h']} paras={stats['p']} tables={stats['table']} "
          f"figures={stats['fig']} code={stats['code']} bullets={stats['li']}")
    print(f"    saved -> {docx_path}")


def main(argv: list[str]):
    if not argv:
        print(__doc__)
        return 1
    for arg in argv:
        src = Path(arg)
        if not src.exists():
            print(f"missing: {src}")
            continue
        convert(src, src.with_suffix(".docx"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
