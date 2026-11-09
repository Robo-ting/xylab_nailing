# -*- coding: utf-8 -*-
"""
Patch seminar PPT:
1. Align slides 4-11 headers to slide 3 reference (title + blue bar)
2. Capture XYLab frontend screenshots
3. Embed mechanics figures + UI screenshots
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Emu

HERE = Path(__file__).resolve().parent
THESIS_ROOT = HERE.parents[2]
PPT = THESIS_ROOT / "docs" / "XYLab-组外交流-20260818.pptx"
ASSETS = HERE / "assets" / "seminar"
FIG_ROOT = Path(r"D:\论文\拉拔、剪切数据\figures\editable")
FRONTEND = "http://127.0.0.1:5174"

# Slide 3 reference (EMU) — user-adjusted alignment
REF_BAR_L, REF_BAR_T = Emu(841248), Emu(822833)
REF_BAR_W, REF_BAR_H = Emu(128016), Emu(658368)
REF_KICKER_L, REF_KICKER_T = Emu(1097280), Emu(475488)
REF_TITLE_L, REF_TITLE_T = Emu(1042543), Emu(850900)
REF_UNDERLINE_T = Emu(1755648)

SCREENSHOTS = [
    ("dashboard.png", "#/"),
    ("perception.png", "#/perception"),
    ("planning.png", "#/planning"),
    ("agent.png", "#/agent"),
    ("twin.png", "#/twin"),
]


def capture_frontend_shots():
    ASSETS.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for fname, route in SCREENSHOTS:
            out = ASSETS / fname
            url = FRONTEND + route
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(1.2)
            page.screenshot(path=str(out), full_page=False)
            print("SHOT:", out)
        browser.close()


BADGE_BOX_L, BADGE_BOX_T = Emu(9018727), Emu(475488)
BADGE_TXT_L, BADGE_TXT_T = Emu(9110167), Emu(512064)


def align_header(slide):
    """Match title / blue-bar / underline to slide 3 reference."""
    for sh in slide.shapes:
        if sh.width == REF_BAR_W and sh.height >= Emu(600000):
            sh.left, sh.top = REF_BAR_L, REF_BAR_T
            sh.width, sh.height = REF_BAR_W, REF_BAR_H
            continue
        if sh.height <= Emu(40000) and sh.width >= Emu(9000000) and sh.top < Emu(2000000):
            sh.top = REF_UNDERLINE_T
            continue
        if not sh.has_text_frame:
            continue
        txt = sh.text_frame.text.strip()
        if not txt:
            continue
        # restore PART / OVERVIEW / CLOSING badge labels (top-right)
        if txt.startswith("PART ") or txt in ("OVERVIEW", "CLOSING"):
            sh.left, sh.top = BADGE_TXT_L, BADGE_TXT_T
            continue
        if sh.top < Emu(600000) and sh.left > Emu(8500000):
            continue
        if sh.top < Emu(600000) and len(txt) < 40 and txt == txt.upper() and "ZJUI" not in txt:
            sh.left, sh.top = REF_KICKER_L, REF_KICKER_T
            continue
        if Emu(700000) < sh.top < Emu(1100000) and sh.height >= Emu(500000) and len(txt) > 4:
            if txt.isdigit() and len(txt) <= 2:
                continue
            sh.left, sh.top = REF_TITLE_L, REF_TITLE_T


def add_pic(slide, path: Path, x, y, w, h=None):
    if not path.exists():
        print("MISSING:", path)
        return None
    if h is None:
        return slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w))
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))


def patch_slide4(slide):
    """Mechanics figures + XYLab planning screenshot."""
    w_fig = FIG_ROOT / "load_displacement_x50_y5" / "withdrawal_TBK_55mm.png"
    w_stat = FIG_ROOT / "Fig_2-9_withdrawal_statistics.png"
    s_fig = FIG_ROOT / "load_displacement_x50" / "shear_TBST.png"
    ui = ASSETS / "planning.png"

    add_pic(slide, w_fig, 3.35, 4.05, 2.15, 1.05)
    add_pic(slide, s_fig, 3.35, 5.2, 2.15, 1.05)
    add_pic(slide, w_stat, 0.98, 5.95, 5.55, 0.95)
    add_pic(slide, ui, 7.15, 4.05, 5.25, 2.85)


def patch_slide5(slide):
    add_pic(slide, ASSETS / "dashboard.png", 8.05, 2.18, 4.85, 3.45)


def patch_slide7(slide):
    add_pic(slide, ASSETS / "perception.png", 0.95, 4.55, 11.45, 1.75)


def patch_slide8(slide):
    add_pic(slide, ASSETS / "agent.png", 0.95, 4.55, 11.45, 1.75)


def patch_slide9(slide):
    add_pic(slide, ASSETS / "twin.png", 0.95, 4.55, 11.45, 1.75)


def main():
    import sys
    shots_only = "--shots" in sys.argv
    headers_only = "--headers" in sys.argv

    if not headers_only:
        print("Capturing frontend screenshots …")
        try:
            capture_frontend_shots()
        except Exception as e:
            print("Screenshot warning:", e)

    prs = Presentation(str(PPT))
    patchers = {
        3: patch_slide4,
        4: patch_slide5,
        6: patch_slide7,
        7: patch_slide8,
        8: patch_slide9,
    }
    for i, slide in enumerate(prs.slides):
        if i >= 3:
            align_header(slide)
            # restore badge box position
            for sh in slide.shapes:
                if sh.shape_type == 1 and sh.width == Emu(2148840) and sh.height == Emu(438912):
                    if sh.left > Emu(8000000):
                        sh.left, sh.top = BADGE_BOX_L, BADGE_BOX_T
        if not headers_only and i in patchers:
            patchers[i](slide)

    prs.save(str(PPT))
    print("SAVED:", PPT)


if __name__ == "__main__":
    main()
