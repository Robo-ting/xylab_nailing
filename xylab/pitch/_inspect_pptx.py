# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

p = Presentation(r'D:\论文\机械臂大论文\docs\XYLab-组外交流-20260818.pptx')
for si, s in enumerate(p.slides, 1):
    print(f'===== SLIDE {si} =====')
    for sh in s.shapes:
        l, t, w, h = sh.left, sh.top, sh.width, sh.height
        if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
            print(f'  PIC  {sh.name}  L={l} T={t} W={w} H={h}')
        elif sh.has_text_frame:
            txt = sh.text_frame.text.replace('\n', ' | ')[:100]
            print(f'  TXT  {sh.name}  L={l} T={t} W={w} H={h}')
            print(f'       {txt}')
        elif sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
            fill = sh.fill.fore_color.rgb if sh.fill.type else None
            print(f'  AUTO {sh.name}  L={l} T={t} W={w} H={h}  fill={fill}')
        else:
            print(f'  SHP  {sh.name} type={sh.shape_type} L={l} T={t} W={w} H={h}')
