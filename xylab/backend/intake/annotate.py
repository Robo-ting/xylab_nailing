"""把检测框画到照片上，供视觉模型查看。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

_LABELS = {
    "knot_dead": "死节",
    "knot_live": "活节",
    "crack": "裂缝",
    "decay": "腐朽",
    "wormhole": "虫洞",
    "nail_exposed": "外露钉帽",
    "nail_rusted": "锈蚀钉帽",
}


def _font(size: int = 18) -> ImageFont.ImageFont:
    for path in (
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def annotate(image: Image.Image, defects: list[dict[str, Any]]) -> Image.Image:
    canvas = image.convert("RGB").copy()
    draw = ImageDraw.Draw(canvas)
    font = _font()
    for defect in defects:
        bbox = defect.get("bbox") or []
        if len(bbox) != 4:
            continue
        x, y, w, h = [float(v) for v in bbox]
        x2, y2 = x + w, y + h
        draw.rectangle([x, y, x2, y2], outline=(220, 38, 38), width=4)
        label = _LABELS.get(str(defect.get("type")), str(defect.get("type")))
        conf = float(defect.get("confidence") or 0)
        draw.text((x + 4, max(0, y - 22)), f"{label} {conf:.0%}", fill=(220, 38, 38), font=font)
    return canvas
