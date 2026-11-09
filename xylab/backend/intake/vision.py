"""钉位拍照扫描。只调用现有检测器，不改选区规划。"""
from __future__ import annotations

from typing import Any

from PIL import Image

from inference.detector import get_detector

_TYPE_MAP = {
    "dead_knot": "knot_dead",
    "live_knot": "knot_live",
    "knot_dead": "knot_dead",
    "knot_live": "knot_live",
    "crack": "crack",
    "decay": "decay",
    "wormhole": "wormhole",
    "nail_exposed": "nail_exposed",
    "nail_rusted": "nail_rusted",
}


def scan_photo(image: Image.Image) -> list[dict[str, Any]]:
    """返回该钉位照片上的缺陷。bbox 为照片像素 [x, y, w, h]。"""
    raw = get_detector().detect(image)
    hits: list[dict[str, Any]] = []
    for item in raw:
        bbox = item.get("bbox") or []
        if len(bbox) != 4:
            continue
        x1, y1, x2, y2 = [float(v) for v in bbox]
        kind = _TYPE_MAP.get(str(item.get("type")), str(item.get("type")))
        hits.append(
            {
                "id": str(item.get("id") or f"v{len(hits) + 1}"),
                "type": kind,
                "confidence": float(item.get("confidence") or 0),
                "bbox": [x1, y1, max(0.0, x2 - x1), max(0.0, y2 - y1)],
            }
        )
    return hits
