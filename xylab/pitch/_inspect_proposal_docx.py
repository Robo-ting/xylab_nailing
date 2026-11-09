# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from pptx.enum.shapes import MSO_SHAPE_TYPE  # noqa: F401
from docx import Document
from docx.oxml.ns import qn

files = [
    Path(r"D:\论文\机械臂大论文\docs\XYLab-打钉系统方案-内部版.docx"),
    Path(r"D:\论文\机械臂大论文\docs\XYLab-打钉系统方案-对外版.docx"),
]
for p in files:
    d = Document(str(p))
    print("=" * 60)
    print(p.name, "paras", len(d.paragraphs), "tables", len(d.tables))
    print("page", d.sections[0].page_width.cm, "x", d.sections[0].page_height.cm)
    print("--- first 25 non-empty paras ---")
    n = 0
    bad = []
    for par in d.paragraphs:
        t = par.text.strip()
        if not t:
            continue
        if n < 25:
            print(f"  {t[:90]}")
            n += 1
        for kw in ["粘贴说明", "mermaid", "飞书", "```"]:
            if kw in t:
                bad.append(t[:80])
    print("inline images:", sum(1 for rel in d.part.rels.values() if "image" in rel.reltype))
    print("BAD leftovers:", bad if bad else "none")
    # table sample
    if d.tables:
        t0 = d.tables[0]
        print(f"table0 {len(t0.rows)}x{len(t0.columns)} first-row:", [c.text[:18].replace(chr(10),' ') for c in t0.rows[0].cells])
    # heading sample
    heads = [par.text for par in d.paragraphs if par.text.startswith(("1.", "2.", "3.", "整体"))]
    print("headings sample:", heads[:8])
