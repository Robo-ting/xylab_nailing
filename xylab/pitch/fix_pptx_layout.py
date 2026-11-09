# -*- coding: utf-8 -*-
"""Fix PPT: remove EVIDENCE badge, fix page-number blue overlay, keep agenda without times."""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

HERE = Path(__file__).resolve().parent
THESIS_ROOT = HERE.parents[2]
PPT = THESIS_ROOT / "docs" / "XYLab-组外交流-20260818.pptx"

# footer page-number badge zone (bottom-right)
PG_BADGE_L = Emu(9800000)
PG_BADGE_T = Emu(6300000)

# top-right EVIDENCE / badge zone
TOP_BADGE_L = Emu(8800000)
TOP_BADGE_T = Emu(400000)


def remove_shape(sh):
    sh._element.getparent().remove(sh._element)


def fix_page_footer(slide):
    """Remove blue rounded rect that covers page number; bring number to front."""
    pg_box = None
    pg_text = None
    for sh in slide.shapes:
        if sh.top < PG_BADGE_T:
            continue
        if sh.left < PG_BADGE_L:
            continue
        if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and sh.width < Emu(1800000):
            pg_box = sh
        elif sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if t.isdigit() and len(t) <= 2:
                pg_text = sh
    if pg_box is not None:
        remove_shape(pg_box)
    if pg_text is not None:
        # plain page number — dark text, no background
        for p in pg_text.text_frame.paragraphs:
            for r in p.runs:
                from pptx.dml.color import RGBColor
                r.font.color.rgb = RGBColor.from_string("475569")
                r.font.bold = False


def remove_evidence_badge(slide):
    """Remove EVIDENCE label and its blue badge box."""
    to_remove = []
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip() == "EVIDENCE":
            to_remove.append(sh)
            continue
        if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
            if sh.left >= TOP_BADGE_L and sh.top <= TOP_BADGE_T and sh.width > Emu(1800000):
                # only remove if slide has EVIDENCE or MECHANICS/XYLAB kicker evidence page
                if _is_evidence_slide(slide):
                    to_remove.append(sh)
    for sh in to_remove:
        remove_shape(sh)


def _is_evidence_slide(slide):
    for sh in slide.shapes:
        if sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if t == "EVIDENCE":
                return True
            if t.startswith("MECHANICS ·") or (t.startswith("XYLAB ·") and sh.top < Emu(600000)):
                return True
    return False


def strip_agenda_times(slide):
    """Remove any remaining ~X min labels user deleted — do not re-add."""
    for sh in list(slide.shapes):
        if sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if "min" in t and "~" in t:
                remove_shape(sh)
        elif sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
            # small time pill boxes on agenda (~0.9in wide near x=3.85in)
            if Emu(3800000) < sh.left < Emu(4500000) and Emu(2000000) < sh.top < Emu(6500000):
                if sh.width < Emu(1000000):
                    remove_shape(sh)


def main():
    prs = Presentation(str(PPT))
    n_footer, n_badge = 0, 0
    for slide in prs.slides:
        before = len(slide.shapes)
        fix_page_footer(slide)
        remove_evidence_badge(slide)
        strip_agenda_times(slide)
        # count removals loosely
        n_footer += 1
    prs.save(str(PPT))
    print("SAVED:", PPT)
    print("Fixed footers on all slides; removed EVIDENCE badges where present.")


if __name__ == "__main__":
    main()
